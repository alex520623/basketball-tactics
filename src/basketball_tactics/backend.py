"""S1 conversion and local JSON export. No tactical inference or interpolation."""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile
from typing import Any

from .sportvu import SourceEvent, SportVUError, identifier, read_event


SCHEMA_VERSION = "0.2.0"


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _slug(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return value
    return "id-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _metadata(event: dict) -> tuple[list[dict], dict, dict]:
    teams, roster, membership = [], {}, {}
    for side in ("home", "visitor"):
        team = event.get(side)
        if not isinstance(team, dict):
            raise SportVUError(f"Event is missing {side} team metadata")
        team_id = identifier(team.get("teamid"))
        teams.append({"side": side, "team_id": team_id,
                      "name": team.get("name"), "abbreviation": team.get("abbreviation")})
        if not isinstance(team.get("players"), list):
            raise SportVUError(f"{side}.players must be a roster array")
        for player in team["players"]:
            if not isinstance(player, dict):
                raise SportVUError("Roster entries must be objects")
            pid = identifier(player.get("playerid"))
            mapped = {"player_id": pid, "first_name": player.get("firstname"),
                      "last_name": player.get("lastname"), "jersey": player.get("jersey"),
                      "position": player.get("position")}
            if pid in roster and (roster[pid] != mapped or membership[pid] != team_id):
                raise SportVUError(f"Conflicting roster metadata for player {pid}")
            roster[pid], membership[pid] = mapped, team_id
    if teams[0]["team_id"] == teams[1]["team_id"]:
        raise SportVUError("Home and visitor team IDs must differ")
    return teams, roster, membership


def convert_event(source: SourceEvent, *, gap_threshold_ms: int,
                  coordinate_limit_ft: float = 1000, source_commit: str | None = None) -> list[dict]:
    """Convert an event to one or more continuous clips, preserving source order.

    The coordinate limit is an explicit engineering guard, not a court boundary.
    Ordinary out-of-court observations remain unchanged and receive warnings.
    """
    if not _integer(gap_threshold_ms) or gap_threshold_ms <= 0:
        raise SportVUError("gap_threshold_ms must be a positive integer")
    if not _number(coordinate_limit_ft) or coordinate_limit_ft < 100:
        raise SportVUError("coordinate_limit_ft must be finite and at least 100 feet")
    if source_commit is not None and not re.fullmatch(r"[0-9a-fA-F]{40}", source_commit):
        raise SportVUError("source_commit must be a full 40-character Git commit SHA")
    teams, roster, membership = _metadata(source.event)
    team_ids = {t["team_id"] for t in teams}
    moments = source.event.get("moments")
    if not isinstance(moments, list) or not moments:
        raise SportVUError("Selected event has no moments")
    event_id = identifier(source.event.get("eventId"))
    warnings: list[dict] = []
    groups: list[list[dict]] = []
    group: list[dict] = []
    previous_raw = None
    pending_break = False
    discarded = duplicates = 0

    def warn(code: str, index: int, message: str, player_id: str | None = None, **details):
        warnings.append({"code": code, "message": message, "source_moment_index": index,
                         "player_id": player_id, **details})

    def clock(value, index, field):
        if value is None:
            warn("MISSING_CLOCK", index, f"{field} is unavailable", field=field)
            return None
        if not _number(value) or value < 0:
            warn("INVALID_CLOCK", index, f"Invalid {field}; exported as null", field=field)
            return None
        return value

    for index, moment in enumerate(moments):
        if (not isinstance(moment, list) or len(moment) != 6 or not isinstance(moment[5], list)
                or not _integer(moment[0]) or moment[0] <= 0
                or not _integer(moment[1]) or moment[1] < 0):
            warn("INVALID_MOMENT", index, "Malformed moment or invalid period/timestamp; omitted")
            discarded += 1
            pending_break = True
            continue
        period, timestamp = moment[:2]
        if group:
            last = group[-1]
            delta = timestamp - last["source_timestamp_ms"]
            if period == last["period"] and delta == 0:
                if moment != previous_raw:
                    raise SportVUError(f"Conflicting observations at the same timestamp, moment {index}")
                warn("DUPLICATE_TIMESTAMP", index, "Identical duplicate omitted",
                     retained_source_moment_index=last["source_moment_index"])
                duplicates += 1
                continue
            reason = ("PERIOD_CHANGE" if period != last["period"] else
                      "TIMESTAMP_ROLLBACK" if delta < 0 else
                      "TIME_GAP" if delta > gap_threshold_ms else None)
            if reason:
                warn(reason, index, "Started a separate continuous clip", delta_ms=delta)
                groups.append(group)
                group = []

        buckets: dict[str, list] = {}
        for row in moment[5]:
            if not isinstance(row, list) or len(row) != 5:
                warn("INVALID_ENTITY", index, "Malformed entity omitted")
                continue
            try:
                tid, pid = identifier(row[0]), identifier(row[1])
            except SportVUError:
                warn("INVALID_ENTITY_ID", index, "Entity with invalid ID omitted")
                continue
            if (tid == "-1") != (pid == "-1"):
                warn("INVALID_ENTITY_ID", index, "Ambiguous ball/player sentinel omitted")
                continue
            key = "ball" if pid == "-1" else pid
            buckets.setdefault(key, []).append((tid, row))

        players, ball = [], None
        for key, entries in buckets.items():
            if len(entries) != 1:
                warn("DUPLICATE_ENTITY_ID", index, "All ambiguous observations for this ID omitted", key)
                continue
            tid, row = entries[0]
            x, y, z = row[2:5]
            if not _number(x) or not _number(y):
                warn("INVALID_COORDINATE", index, "Non-finite or nonnumeric x/y omitted", key)
                continue
            if abs(x) > coordinate_limit_ft or abs(y) > coordinate_limit_ft:
                warn("EXTREME_COORDINATE", index, "Coordinate exceeds configured guard; point omitted", key)
                continue
            if x < 0 or x > 94 or y < 0 or y > 50:
                warn("OUT_OF_COURT", index, "Source coordinate retained without clipping", key, x=x, y=y)
            if z is not None and not _number(z):
                warn("INVALID_Z", index, "Invalid third coordinate exported as null", key)
                z = None
            if key == "ball":
                ball = {"x": x, "y": y, "z": z}
                if z is not None and z < 0:
                    warn("NEGATIVE_BALL_Z", index, "Negative ball z retained for review", key)
            else:
                players.append({"player_id": key, "team_id": tid, "x": x, "y": y,
                                "position_z_raw": z})
                if tid not in team_ids:
                    warn("UNKNOWN_TEAM", index, "Position team ID is absent from team metadata", key)
                if key not in roster:
                    warn("UNKNOWN_PLAYER", index, "Roster metadata unavailable for observed ID", key)
                elif membership[key] != tid:
                    warn("TEAM_MISMATCH", index, "Source position team differs from roster; raw ID retained", key)
        if ball is None:
            warn("MISSING_BALL", index, "No valid ball observation; exported as null")
        if len(players) != 10:
            warn("PLAYER_COUNT", index, "NBA frame does not contain ten valid player points",
                 observed_count=len(players))
        frame = {"source_moment_index": index, "source_timestamp_ms": timestamp, "period": period,
                 "game_clock_s": clock(moment[2], index, "game_clock_s"),
                 "shot_clock_s": clock(moment[3], index, "shot_clock_s"),
                 "source_aux": moment[4], "players": players, "ball": ball,
                 "_force_break": pending_break}
        group.append(frame)
        previous_raw = moment
        pending_break = False
    if group:
        groups.append(group)
    if not groups:
        raise SportVUError("Selected event has no valid timestamped moments")

    clips = []
    for segment_index, frames in enumerate(groups, 1):
        origin = frames[0]["source_timestamp_ms"]
        tracks: dict[tuple[str, str], dict] = {}
        last_seen: dict[tuple[str, str], tuple[int, str | None]] = {}
        observed_ids = set()
        index_map = {}
        for frame_index, frame in enumerate(frames):
            frame["frame_index"] = frame_index
            frame["t_ms"] = frame["source_timestamp_ms"] - origin
            index_map[frame["source_moment_index"]] = frame_index
            force_break = frame.pop("_force_break")
            entities = [("player", p["player_id"], p) for p in frame["players"]]
            if frame["ball"] is not None:
                entities.append(("ball", "ball", frame["ball"]))
            for kind, eid, point in entities:
                key = kind, eid
                team = point.get("team_id")
                previous = last_seen.get(key)
                broken = force_break or previous != (frame_index - 1, team)
                point["break_before"] = broken
                track = tracks.setdefault(key, {"entity_type": kind, "entity_id": eid, "segments": []})
                if broken:
                    track["segments"].append({"start_frame_index": frame_index, "end_frame_index": frame_index})
                else:
                    track["segments"][-1]["end_frame_index"] = frame_index
                last_seen[key] = frame_index, team
                if kind == "player":
                    observed_ids.add(eid)
        clip_id = f"{_slug(source.game_id)}-e{_slug(event_id)}-s{segment_index:03d}"
        clip_warnings = [{**w, "frame_index": index_map.get(w["source_moment_index"])} for w in warnings]
        clips.append({
            "schema_version": SCHEMA_VERSION, "clip_id": clip_id,
            "provenance": {"source_file": source.path.name, "source_file_sha256": source.sha256,
                           "source_commit": source_commit, "is_synthetic": False,
                           "is_excerpt": len(frames) != len(moments)},
            "game": {"game_id": source.game_id, "game_date": source.game_date},
            "source_event": {"event_id": event_id, "event_index": source.event_index,
                             "start_moment_index": frames[0]["source_moment_index"],
                             "end_moment_index": frames[-1]["source_moment_index"]},
            "coordinate_system": {"unit": "ft", "unit_basis": "external_format_reference",
                                  "frame": "source", "court_length": 94, "court_width": 50,
                                  "court_size_basis": "reference_geometry", "display_orientation": "unconfirmed"},
            "timeline": {"time_basis": "source_timestamp_delta", "source_timestamp_origin_ms": origin,
                         "duration_ms": frames[-1]["t_ms"], "nominal_interval_ms": 40,
                         "gap_threshold_ms": gap_threshold_ms},
            "teams": teams,
            "players": [roster.get(pid, {"player_id": pid, "first_name": None, "last_name": None,
                                         "jersey": None, "position": None}) for pid in sorted(observed_ids)],
            "frames": frames, "trajectories": list(tracks.values()),
            "quality": {"policy": {"coordinate_limit_ft": coordinate_limit_ft,
                                   "out_of_court": "retain_and_warn", "invalid_point": "omit_and_break",
                                   "interpolation": "none", "warning_scope": "source_event"},
                        "summary": {"source_event_input_moments": len(moments), "exported_frames": len(frames),
                                    "source_event_discarded_moments": discarded,
                                    "source_event_duplicate_moments": duplicates,
                                    "source_event_clip_count": len(groups),
                                    "source_event_warning_counts": dict(Counter(w["code"] for w in warnings))},
                        "warnings": clip_warnings},
        })
    return clips


def export_event(source_path: Path | str, output_dir: Path | str, event_id: str, *,
                 gap_threshold_ms: int, coordinate_limit_ft: float = 1000,
                 source_commit: str | None = None, expected_sha256: str | None = None) -> dict:
    """Write a new local directory atomically; never replace an existing export."""
    target = Path(output_dir).resolve()
    if target.exists():
        raise FileExistsError(f"Output already exists; choose a new directory: {target}")
    source = read_event(source_path, event_id, expected_sha256)
    clips = convert_event(source, gap_threshold_ms=gap_threshold_ms,
                          coordinate_limit_ft=coordinate_limit_ft, source_commit=source_commit)
    manifest = {"schema_version": SCHEMA_VERSION,
                "dataset": {"id": "nba-sportvu-2015-16", "name": "NBA-Player-Movements",
                            "version": source_commit, "adoption_status": "local_s1_validation",
                            "license_status": "unconfirmed", "usage_scope": "local_small_scale"},
                "clips": [{"clip_id": c["clip_id"], "label": f"{source.game_id} event {event_id} segment {i}",
                           "path": f"clips/{c['clip_id']}.json", "duration_ms": c["timeline"]["duration_ms"],
                           "frame_count": len(c["frames"])} for i, c in enumerate(clips, 1)]}
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sportvu-export-", dir=target.parent) as temporary:
        staging = Path(temporary) / "payload"
        (staging / "clips").mkdir(parents=True)
        for clip in clips:
            with (staging / "clips" / f"{clip['clip_id']}.json").open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(clip, stream, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
                stream.write("\n")
        with (staging / "manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.write("\n")
        if target.exists():
            raise FileExistsError(f"Output appeared during export; refusing to replace it: {target}")
        staging.rename(target)
    return manifest
