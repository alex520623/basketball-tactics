"""Validate every event of the verified LAL@BOS sample, one event at a time.

This is a regression check for one pinned game, not an all-dataset compatibility
claim. Reports contain counts and event IDs, never raw frames or coordinates.
"""

import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import sys
import time

import ijson

from basketball_tactics.backend import convert_event
from basketball_tactics.sportvu import SourceEvent, SportVUError, read_event


SAMPLE_SHA = "5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036"
SOURCE_COMMIT = "f7d4cf2c7e607029abfd5715a0d4073bedae328e"
EMPTY_EVENTS = {"447", "517", "522", "524", "544"}
CONFLICT_EVENTS = {"215", "216"}
GAP_MS = 120


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_clips(source: SourceEvent, clips: list[dict]) -> None:
    """Compare every exported observation and trail with its unmodified source."""
    moments = source.event["moments"]
    source_indices = []
    previous_clip_last = None
    for clip in clips:
        require(clip["source_event"]["event_id"] == str(source.event["eventId"]), "event ID changed")
        require(clip["source_event"]["event_index"] == source.event_index, "event index changed")
        require(clip["provenance"]["source_file_sha256"] == SAMPLE_SHA, "source hash changed")
        require(clip["provenance"]["is_synthetic"] is False, "synthetic output")
        require(clip["coordinate_system"]["display_orientation"] == "unconfirmed", "direction inferred")
        frames = clip["frames"]
        require(bool(frames), "empty successful clip")
        origin = frames[0]["source_timestamp_ms"]
        require(clip["timeline"]["source_timestamp_origin_ms"] == origin, "wrong time origin")
        if previous_clip_last:
            require(frames[0]["period"] != previous_clip_last["period"] or
                    frames[0]["source_timestamp_ms"] - previous_clip_last["source_timestamp_ms"] > GAP_MS,
                    "clip split without a source discontinuity")
        previous_clip_last = frames[-1]
        expected_tracks, last_seen, observed = {}, {}, set()
        for index, frame in enumerate(frames):
            raw_index = frame["source_moment_index"]
            raw = moments[raw_index]
            source_indices.append(raw_index)
            require(frame["frame_index"] == index, "wrong frame index")
            require(frame["source_timestamp_ms"] == raw[1] and frame["period"] == raw[0], "source time changed")
            require(frame["t_ms"] == raw[1] - origin, "relative time changed")
            require((frame["game_clock_s"], frame["shot_clock_s"], frame["source_aux"]) == tuple(raw[2:5]),
                    "source clock/null/aux changed")
            if index:
                delta = raw[1] - frames[index - 1]["source_timestamp_ms"]
                require(frame["period"] == frames[index - 1]["period"] and 0 < delta <= GAP_MS,
                        "clip crosses a time discontinuity")
            players = {p["player_id"]: p for p in frame["players"]}
            require(len(players) == len(frame["players"]), "duplicate output player ID")
            raw_players = {str(p[1]): p for p in raw[5] if p[:2] != [-1, -1]}
            require(players.keys() == raw_players.keys(), "player lost or invented")
            raw_ball = [p for p in raw[5] if p[:2] == [-1, -1]]
            require((frame["ball"] is None) == (not raw_ball), "missing ball replaced or valid ball lost")
            points = []
            for pid, point in players.items():
                row = raw_players[pid]
                require(point["team_id"] == str(row[0]), "team ID changed")
                require([point[k] for k in ("x", "y", "position_z_raw")] == row[2:5], "player coordinates changed")
                points.append((("player", pid), point, str(row[0])))
                observed.add(pid)
            if raw_ball:
                require(len(raw_ball) == 1, "ambiguous source ball")
                require([frame["ball"][k] for k in ("x", "y", "z")] == raw_ball[0][2:5], "ball coordinates changed")
                points.append((("ball", "ball"), frame["ball"], None))
            for key, point, team in points:
                broken = last_seen.get(key) != (index - 1, team)
                require(point["break_before"] is broken, "trajectory crosses a source absence/team change")
                runs = expected_tracks.setdefault(key, [])
                if broken:
                    runs.append({"start_frame_index": index, "end_frame_index": index})
                else:
                    runs[-1]["end_frame_index"] = index
                last_seen[key] = index, team
        actual_tracks = {(t["entity_type"], t["entity_id"]): t["segments"] for t in clip["trajectories"]}
        require(len(actual_tracks) == len(clip["trajectories"]), "duplicate trajectory")
        require(actual_tracks == expected_tracks, "trajectory bounds differ from observed positions")
        roster = {p["player_id"]: p for p in clip["players"]}
        require(len(roster) == len(clip["players"]) and roster.keys() == observed, "incorrect clip roster")
        raw_roster = {str(p["playerid"]): p for side in ("home", "visitor") for p in source.event[side]["players"]}
        for pid, player in roster.items():
            raw = raw_roster[pid]
            require([player[k] for k in ("first_name", "last_name", "jersey", "position")] ==
                    [raw[k] for k in ("firstname", "lastname", "jersey", "position")], "player metadata changed")
        require(clip["timeline"]["duration_ms"] == frames[-1]["t_ms"], "wrong duration")
        require(clip["source_event"]["start_moment_index"] == frames[0]["source_moment_index"] and
                clip["source_event"]["end_moment_index"] == frames[-1]["source_moment_index"], "wrong source bounds")
        index_map = {f["source_moment_index"]: f["frame_index"] for f in frames}
        for warning in clip["quality"]["warnings"]:
            require(warning["frame_index"] == index_map.get(warning["source_moment_index"]), "wrong warning frame")
        require(Counter(w["code"] for w in clip["quality"]["warnings"]) ==
                clip["quality"]["summary"]["source_event_warning_counts"], "inconsistent warning counts")
    # The verified convertible events contain no invalid moments or identical timestamp duplicates.
    require(source_indices == list(range(len(moments))), "source moment omitted or reordered")


def check_game(path: Path | str) -> dict:
    start = time.perf_counter()
    source = read_event(path, "2", SAMPLE_SHA)
    require((source.game_id, source.game_date) == ("0021500476", "2015-12-30"), "wrong game")
    events, seen, warning_counts, status_counts = [], set(), Counter(), Counter()
    with source.path.open("rb") as stream:
        for index, event in enumerate(ijson.items(stream, "events.item", use_float=True)):
            event_id = str(event["eventId"])
            require(event_id not in seen, f"duplicate event ID {event_id}")
            seen.add(event_id)
            row = {"event_id": event_id, "event_index": index, "input_moments": len(event["moments"])}
            current = replace(source, event=event, event_index=index)
            clips = None
            try:
                clips = convert_event(current, gap_threshold_ms=GAP_MS, source_commit=SOURCE_COMMIT)
            except SportVUError as error:
                if not event["moments"]:
                    require(event_id in EMPTY_EVENTS and str(error) == "Selected event has no moments",
                            f"unexpected empty-event rejection: {event_id}: {error}")
                    row["status"] = "empty_rejected"
                else:
                    collisions = [i for i, (a, b) in enumerate(zip(event["moments"], event["moments"][1:]), 1)
                                  if a[:2] == b[:2] and a != b]
                    require(event_id in CONFLICT_EVENTS and bool(collisions) and
                            str(error) == f"Conflicting observations at the same timestamp, moment {collisions[0]}",
                            f"unexpected nonempty rejection: {event_id}: {error}")
                    row.update(status="conflict_rejected", conflicting_moment_indices=collisions)
                row["error"] = str(error)
            else:
                try:
                    check_clips(current, clips)
                except (AssertionError, KeyError, IndexError, TypeError) as error:
                    raise AssertionError(f"eventId={event_id}, event_index={index}: {error}") from error
                row.update(status="converted", clip_count=len(clips),
                           exported_frames=sum(len(c["frames"]) for c in clips),
                           clip_frame_counts=[len(c["frames"]) for c in clips],
                           missing_ball_frames=sum(f["ball"] is None for c in clips for f in c["frames"]),
                           incomplete_player_frames=sum(len(f["players"]) != 10 for c in clips for f in c["frames"]),
                           null_shot_clock_frames=sum(f["shot_clock_s"] is None for c in clips for f in c["frames"]),
                           warning_counts=clips[0]["quality"]["summary"]["source_event_warning_counts"])
                warning_counts.update(row["warning_counts"])
            status_counts[row["status"]] += 1
            events.append(row)
            # Avoid retaining a previous converted event while converting the next one.
            del clips
    require({r["event_id"] for r in events if r["status"] == "empty_rejected"} == EMPTY_EVENTS, "empty events changed")
    require({r["event_id"] for r in events if r["status"] == "conflict_rejected"} == CONFLICT_EVENTS, "conflicting events changed")
    return {"report_version": "1.0.0", "game_id": source.game_id, "game_date": source.game_date,
            "source_file": source.path.name, "source_sha256": source.sha256, "source_commit": SOURCE_COMMIT,
            "gap_threshold_ms": GAP_MS, "event_count": len(events), "status_counts": dict(status_counts),
            "input_moments_including_overlaps": sum(r["input_moments"] for r in events),
            "exported_frames_including_overlaps": sum(r.get("exported_frames", 0) for r in events),
            "clip_count": sum(r.get("clip_count", 0) for r in events), "warning_counts": dict(warning_counts),
            "elapsed_s": round(time.perf_counter() - start, 3), "events": events}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, help="Optional NEW JSON report; never overwritten")
    args = parser.parse_args(argv)
    try:
        if args.report and args.report.exists():
            raise FileExistsError(f"Report already exists: {args.report}")
        report = check_game(args.input)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(report, stream, ensure_ascii=False, allow_nan=False, indent=2)
                stream.write("\n")
        print(json.dumps({k: v for k, v in report.items() if k != "events"}, ensure_ascii=False, indent=2))
        print("Regression checks passed. Five empty events and two conflicting events were safely rejected.")
        if args.report:
            print(f"Report: {args.report}")
        return 0
    except (OSError, ValueError, AssertionError, KeyError, IndexError, TypeError) as error:
        print(f"Sample validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
