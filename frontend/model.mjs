// Pure helpers shared by the viewer and its real-data regression tests.
export const SCHEMA_VERSION = "0.2.0";
const finite = value => typeof value === "number" && Number.isFinite(value);

export function validateManifest(manifest) {
  if (manifest?.schema_version !== SCHEMA_VERSION || !Array.isArray(manifest.clips) || !manifest.clips.length) {
    throw new Error("無可用片段，或資料版本不是 0.2.0。");
  }
  const ids = new Set();
  for (const entry of manifest.clips) {
    if (typeof entry.clip_id !== "string" || !/^[A-Za-z0-9_-]+$/.test(entry.clip_id) || ids.has(entry.clip_id) ||
        typeof entry.path !== "string" || !/^clips\/[A-Za-z0-9_-]+\.json$/.test(entry.path)) {
      throw new Error("片段清單包含重複 ID 或不合法的路徑。");
    }
    ids.add(entry.clip_id);
  }
  return manifest;
}

export function validateClip(clip, entry) {
  if (clip?.schema_version !== SCHEMA_VERSION || clip.clip_id !== entry.clip_id ||
      !Array.isArray(clip.frames) || !clip.frames.length || clip.frames.length !== entry.frame_count ||
      !Array.isArray(clip.players) || !Array.isArray(clip.teams) || !Array.isArray(clip.trajectories)) {
    throw new Error("片段結構、ID 或影格數與清單不一致。");
  }
  if (clip.coordinate_system?.unit !== "ft" || !finite(clip.coordinate_system.court_length) ||
      !finite(clip.coordinate_system.court_width) || clip.coordinate_system.court_length <= 0 ||
      clip.coordinate_system.court_width <= 0) throw new Error("尚不支援此球場單位或尺寸。");
  const roster = new Set(clip.players.map(p => p.player_id));
  if (roster.size !== clip.players.length) throw new Error("球員名單含重複 ID。");
  let previous = -1;
  for (let i = 0; i < clip.frames.length; i++) {
    const frame = clip.frames[i];
    if (frame.frame_index !== i || !finite(frame.t_ms) || frame.t_ms <= previous ||
        !Array.isArray(frame.players)) throw new Error("影格時間或索引不合法。");
    previous = frame.t_ms;
    const ids = new Set();
    for (const point of frame.players) {
      if (!roster.has(point.player_id) || ids.has(point.player_id) || !finite(point.x) || !finite(point.y) ||
          typeof point.break_before !== "boolean") throw new Error("球員位置或 ID 不合法。");
      ids.add(point.player_id);
    }
    if (frame.ball !== null && (!frame.ball || !finite(frame.ball.x) || !finite(frame.ball.y) ||
        typeof frame.ball.break_before !== "boolean")) throw new Error("籃球位置不合法。");
  }
  if (clip.frames[0].t_ms !== 0 || previous !== entry.duration_ms ||
      previous !== clip.timeline?.duration_ms) throw new Error("片段長度與時間軸不一致。");
  for (const track of clip.trajectories) {
    if (!["player", "ball"].includes(track.entity_type) || !Array.isArray(track.segments)) {
      throw new Error("軌跡資料不合法。");
    }
    let lastEnd = -1;
    for (const segment of track.segments) {
      const { start_frame_index: start, end_frame_index: end } = segment;
      if (!Number.isInteger(start) || !Number.isInteger(end) || start <= lastEnd || end < start ||
          end >= clip.frames.length) throw new Error("軌跡分段超出片段範圍。");
      for (let i = start; i <= end; i++) {
        const point = pointFor(clip.frames[i], track.entity_type, track.entity_id);
        if (!point || point.break_before !== (i === start)) throw new Error("軌跡跨過缺漏或中斷點。");
      }
      lastEnd = end;
    }
  }
  return clip;
}

export function frameAtTime(frames, timeMs) {
  let low = 0, high = frames.length;
  while (low < high) {
    const mid = (low + high) >>> 1;
    if (frames[mid].t_ms <= timeMs) low = mid + 1;
    else high = mid;
  }
  return Math.max(0, low - 1);
}

export function pointFor(frame, type, id) {
  return type === "ball" ? frame.ball : frame.players.find(p => p.player_id === id) ?? null;
}

export function trailSegments(clip, track, frameIndex, windowMs) {
  const cutoff = clip.frames[frameIndex].t_ms - windowMs;
  const paths = [];
  for (const segment of track.segments) {
    const end = Math.min(segment.end_frame_index, frameIndex);
    if (segment.start_frame_index > end) continue;
    const points = [];
    for (let i = segment.start_frame_index; i <= end; i++) {
      if (clip.frames[i].t_ms < cutoff) continue;
      const point = pointFor(clip.frames[i], track.entity_type, track.entity_id);
      if (point) points.push({ x: point.x, y: point.y, frame_index: i });
    }
    if (points.length) paths.push(points);
  }
  return paths;
}

export function courtTransform(width, height, court, flipY = false) {
  const margin = 6;
  const scale = Math.min(width / (court.court_length + margin * 2), height / (court.court_width + margin * 2));
  const left = (width - (court.court_length + margin * 2) * scale) / 2;
  const top = (height - (court.court_width + margin * 2) * scale) / 2;
  return { scale, map: (x, y) => ({
    x: left + (x + margin) * scale,
    y: top + ((flipY ? court.court_width - y : y) + margin) * scale,
  }) };
}

export function clockText(seconds) {
  if (!finite(seconds) || seconds < 0) return "—";
  const centiseconds = Math.round(seconds * 100);
  return `${String(Math.floor(centiseconds / 6000)).padStart(2, "0")}:${(centiseconds % 6000 / 100).toFixed(2).padStart(5, "0")}`;
}

export function elapsedText(ms) { return clockText(ms / 1000); }
