// Real Backend export regression. Missing exports are reported as skipped, never replaced by fake data.
import test from "node:test";
import assert from "node:assert/strict";
import { readFile, access } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateManifest, validateClip, frameAtTime, pointFor, trailSegments,
  courtTransform, clockText } from "../frontend/model.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const dataDir = path.resolve(root, process.env.SPORTVU_EXPORT ?? "outputs/s1-event-2");
let manifest, clip, entry;
try {
  await access(path.join(dataDir, "manifest.json"));
} catch (error) {
  if (process.env.SPORTVU_EXPORT || error.code !== "ENOENT") throw error;
}
try {
  manifest = JSON.parse(await readFile(path.join(dataDir, "manifest.json"), "utf8"));
  entry = manifest.clips.find(row => row.clip_id === "0021500476-e2-s001");
  assert.ok(entry, "Tests require the real event 2 export");
  clip = JSON.parse(await readFile(path.join(dataDir, entry.path), "utf8"));
  assert.equal(clip.provenance.source_file_sha256, "5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036");
  assert.equal(clip.provenance.is_synthetic, false);
} catch (error) {
  if (manifest || process.env.SPORTVU_EXPORT || error.code !== "ENOENT") throw error;
}
const real = (name, fn) => test(name, { skip: !clip && "Local real export is missing; see docs/local-viewer.md" }, fn);

real("real event validates with 525 frames, ten players, ball and source times", () => {
  assert.equal(validateManifest(manifest), manifest);
  assert.equal(validateClip(clip, entry), clip);
  assert.equal(clip.frames.length, 525);
  assert.equal(clip.players.length, 10);
  assert.equal(clip.source_event.event_id, "2");
  assert.equal(clip.timeline.duration_ms, 20959);
  for (const frame of clip.frames) {
    assert.equal(frame.players.length, 10);
    assert.ok(frame.ball);
    assert.equal(frame.source_timestamp_ms - clip.frames[0].source_timestamp_ms, frame.t_ms);
  }
});

real("time lookup uses each actual timestamp, including 39/40/41 ms intervals", () => {
  const intervals = new Set();
  assert.equal(frameAtTime(clip.frames, -1), 0);
  for (let i = 1; i < clip.frames.length; i++) {
    const t = clip.frames[i].t_ms;
    intervals.add(t - clip.frames[i - 1].t_ms);
    assert.equal(frameAtTime(clip.frames, t - 0.001), i - 1);
    assert.equal(frameAtTime(clip.frames, t), i);
  }
  assert.deepEqual([...intervals].sort(), [39, 40, 41]);
  assert.equal(frameAtTime(clip.frames, 999999), 524);
});

real("trails contain past points only and respect the millisecond window", () => {
  for (const index of [0, 100, 392, 524]) for (const track of clip.trajectories) {
    const paths = trailSegments(clip, track, index, 1000);
    for (const points of paths) for (const point of points) {
      assert.ok(point.frame_index <= index);
      assert.ok(clip.frames[point.frame_index].t_ms >= clip.frames[index].t_ms - 1000);
      const source = pointFor(clip.frames[point.frame_index], track.entity_type, track.entity_id);
      assert.equal(point.x, source.x);
      assert.equal(point.y, source.y);
    }
  }
});

real("fault injection: missing player splits the trajectory without bridging", () => {
  const fault = structuredClone(clip), track = fault.trajectories.find(t => t.entity_type === "player");
  const pid = track.entity_id;
  fault.frames[10].players = fault.frames[10].players.filter(p => p.player_id !== pid);
  fault.frames[11].players.find(p => p.player_id === pid).break_before = true;
  track.segments = [{ start_frame_index: 0, end_frame_index: 9 }, { start_frame_index: 11, end_frame_index: 524 }];
  validateClip(fault, entry);
  const paths = trailSegments(fault, track, 20, Infinity);
  assert.deepEqual(paths.map(p => [p[0].frame_index, p.at(-1).frame_index]), [[0, 9], [11, 20]]);
  assert.equal(pointFor(fault.frames[10], "player", pid), null);
  fault.frames[10].ball = null;
  assert.equal(pointFor(fault.frames[10], "ball", "ball"), null);
});

real("fault injection: reject wrong versions, traversal paths, nonmonotonic time and invalid points", () => {
  assert.throws(() => validateManifest({ ...manifest, schema_version: "9" }));
  assert.throws(() => validateManifest({ ...manifest, clips: [{ ...entry, path: "../secret.json" }] }));
  const unordered = structuredClone(clip); unordered.frames[1].t_ms = 0;
  assert.throws(() => validateClip(unordered, entry));
  const badPoint = structuredClone(clip); badPoint.frames[1].ball.x = NaN;
  assert.throws(() => validateClip(badPoint, entry));
  const broken = structuredClone(clip); broken.frames[10].players.pop();
  assert.throws(() => validateClip(broken, entry));
});

real("negative source x is retained inside the display margin; flip changes display y only", () => {
  const point = clip.frames[392].players.find(p => p.player_id === "1626204");
  assert.ok(point.x < 0);
  const normal = courtTransform(1060, 620, clip.coordinate_system);
  const flipped = courtTransform(1060, 620, clip.coordinate_system, true);
  assert.ok(normal.map(point.x, point.y).x > 0);
  assert.ok(normal.map(point.x, point.y).x < normal.map(0, 0).x);
  assert.equal(normal.map(point.x, point.y).x, flipped.map(point.x, point.y).x);
  assert.equal(normal.map(point.x, point.y).y + flipped.map(point.x, point.y).y, 620);
  assert.equal(clip.coordinate_system.display_orientation, "unconfirmed");
});

test("clock formatting handles missing clocks and minute boundaries", () => {
  assert.equal(clockText(null), "—");
  assert.equal(clockText(NaN), "—");
  assert.equal(clockText(-1), "—");
  assert.equal(clockText(59.999), "01:00.00");
  assert.equal(clockText(719.47), "11:59.47");
});
