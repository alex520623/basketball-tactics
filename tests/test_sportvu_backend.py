"""Real-sample regression tests plus explicitly altered copies for fault injection.

No raw dataset is committed. Set SPORTVU_SAMPLE to the verified single-game JSON
on another machine; the integration cases skip explicitly when it is absent.
"""

from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

import ijson
import pytest

from basketball_tactics.backend import convert_event
from basketball_tactics.sportvu import SportVUError, read_event


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_SHA = "5ad649c3b741cc45c01c586cbf073d56d67da0f2315fe7acedb477bc43116036"
SOURCE_COMMIT = "f7d4cf2c7e607029abfd5715a0d4073bedae328e"


@pytest.fixture(scope="session")
def sample_path():
    path = Path(os.environ.get("SPORTVU_SAMPLE", ROOT / ".tools/sportvu-review/0021500476.json"))
    if not path.is_file():
        if "SPORTVU_SAMPLE" in os.environ:
            pytest.fail(f"Explicit SPORTVU_SAMPLE does not exist: {path}")
        pytest.skip("Real SportVU sample not present; set SPORTVU_SAMPLE to 0021500476.json")
    return path


@pytest.fixture(scope="session")
def source(sample_path):
    return read_event(sample_path, "2", SAMPLE_SHA)


@pytest.fixture
def fault_source(source):
    # Fault injection only: keep real team/roster data and the first 3 real moments.
    event = deepcopy(source.event)
    event["moments"] = event["moments"][:3]
    return replace(source, event=event)


def convert(source, **kwargs):
    return convert_event(source, gap_threshold_ms=120, source_commit=SOURCE_COMMIT, **kwargs)


def codes(clip):
    return {w["code"] for w in clip["quality"]["warnings"]}


def player(frame, pid="202340"):
    return next(p for p in frame["players"] if p["player_id"] == pid)


def test_real_event_identity_and_source_hash(source):
    assert (source.game_id, source.game_date, source.event_index) == ("0021500476", "2015-12-30", 1)
    assert source.event["eventId"] == "2"  # eventId selection, not events[2].
    assert source.sha256 == SAMPLE_SHA
    assert len(source.event["moments"]) == 525


def test_all_real_frames_preserve_positions_ids_and_three_clocks(source):
    (clip,) = convert(source)
    assert clip["schema_version"] == "0.2.0"
    assert len(clip["frames"]) == 525
    assert clip["timeline"]["duration_ms"] == 20959
    assert clip["coordinate_system"]["unit"] == "ft"
    assert clip["coordinate_system"]["display_orientation"] == "unconfirmed"
    assert clip["source_event"]["event_id"] == "2"
    assert not clip["provenance"]["is_synthetic"] and not clip["provenance"]["is_excerpt"]
    assert {t["team_id"] for t in clip["teams"]} == {"1610612738", "1610612747"}
    assert next(p for p in clip["players"] if p["player_id"] == "977")["jersey"] == "24"
    assert player(clip["frames"][0])["x"] == 48.30817
    assert clip["frames"][0]["ball"]["x"] == 44.12405
    assert clip["frames"][1]["t_ms"] == 39
    for index, (frame, raw) in enumerate(zip(clip["frames"], source.event["moments"], strict=True)):
        assert frame["frame_index"] == frame["source_moment_index"] == index
        assert frame["t_ms"] == raw[1] - source.event["moments"][0][1]
        assert (frame["source_timestamp_ms"], frame["period"], frame["game_clock_s"], frame["shot_clock_s"]) == (
            raw[1], raw[0], raw[2], raw[3])
        assert len(frame["players"]) == 10
        for point in raw[5]:
            if point[:2] == [-1, -1]:
                assert [frame["ball"][k] for k in ("x", "y", "z")] == point[2:5]
            else:
                p = player(frame, str(point[1]))
                assert p["team_id"] == str(point[0])
                assert [p[k] for k in ("x", "y", "position_z_raw")] == point[2:5]
    times = [f["t_ms"] for f in clip["frames"]]
    deltas = {b - a for a, b in zip(times, times[1:])}
    assert {39, 40, 41} <= deltas
    assert all(b > a for a, b in zip(times, times[1:]))
    assert len(clip["trajectories"]) == 11
    for track in clip["trajectories"]:
        assert track["segments"] == [{"start_frame_index": 0, "end_frame_index": 524}]


def test_cli_exports_real_json_and_never_overwrites(sample_path, tmp_path):
    output = tmp_path / "s1"
    command = [sys.executable, "-m", "basketball_tactics.cli", "--input", str(sample_path),
               "--event-id", "2", "--output-dir", str(output), "--gap-threshold-ms", "120",
               "--expected-sha256", SAMPLE_SHA, "--source-commit", SOURCE_COMMIT]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["clips"][0]
    clip_file = output / entry["path"]
    original_bytes = clip_file.read_bytes()
    clip = json.loads(original_bytes)
    assert entry["frame_count"] == len(clip["frames"]) == 525
    assert entry["duration_ms"] == clip["timeline"]["duration_ms"] == 20959
    assert manifest["dataset"]["license_status"] == "unconfirmed"
    assert clip["provenance"]["source_file_sha256"] == SAMPLE_SHA
    repeated = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    assert repeated.returncode == 1
    assert "already exists" in repeated.stderr
    assert clip_file.read_bytes() == original_bytes


def test_real_out_of_court_coordinates_are_not_clamped(source):
    # Find an actual out-of-court observation in the local game, not invented coordinates.
    with source.path.open("rb") as stream:
        for event_index, event in enumerate(ijson.items(stream, "events.item", use_float=True)):
            for moment in event["moments"]:
                outside = [p for p in moment[5] if p[2] < 0 or p[2] > 94 or p[3] < 0 or p[3] > 50]
                if outside:
                    event["moments"] = [moment]
                    (clip,) = convert(replace(source, event=event, event_index=event_index))
                    assert "OUT_OF_COURT" in codes(clip)
                    p = outside[0]
                    exported = clip["frames"][0]["ball"] if p[:2] == [-1, -1] else player(clip["frames"][0], str(p[1]))
                    assert (exported["x"], exported["y"]) == (p[2], p[3])
                    return
    pytest.fail("Expected actual out-of-court observation in the verified sample")


def test_missing_ball_does_not_misidentify_first_player(fault_source):
    del fault_source.event["moments"][1][5][0]
    (clip,) = convert(fault_source)
    assert clip["frames"][1]["ball"] is None
    assert len(clip["frames"][1]["players"]) == 10
    assert "MISSING_BALL" in codes(clip)
    track = next(t for t in clip["trajectories"] if t["entity_type"] == "ball")
    assert track["segments"] == [{"start_frame_index": 0, "end_frame_index": 0},
                                 {"start_frame_index": 2, "end_frame_index": 2}]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), "invalid", 2000])
def test_invalid_or_extreme_point_is_omitted_and_trajectory_breaks(fault_source, bad):
    row = next(p for p in fault_source.event["moments"][1][5] if p[1] == 202340)
    row[2] = bad  # Explicit corruption of a real row, not a replacement dataset.
    (clip,) = convert(fault_source)
    assert not any(p["player_id"] == "202340" for p in clip["frames"][1]["players"])
    assert player(clip["frames"][2])["break_before"]
    assert {"INVALID_COORDINATE", "EXTREME_COORDINATE"} & codes(clip)
    json.dumps(clip, allow_nan=False)


def test_duplicate_entity_is_not_silently_chosen(fault_source):
    rows = fault_source.event["moments"][1][5]
    rows.append(deepcopy(next(p for p in rows if p[1] == 202340)))
    (clip,) = convert(fault_source)
    assert "DUPLICATE_ENTITY_ID" in codes(clip)
    assert len(clip["frames"][1]["players"]) == 9
    assert player(clip["frames"][2])["break_before"]


def test_identical_timestamp_duplicate_preserves_source_indices(fault_source):
    moments = fault_source.event["moments"]
    moments.insert(1, deepcopy(moments[0]))
    (clip,) = convert(fault_source)
    assert [f["source_moment_index"] for f in clip["frames"]] == [0, 2, 3]
    assert clip["quality"]["summary"]["source_event_duplicate_moments"] == 1
    assert not player(clip["frames"][1])["break_before"]


def test_conflicting_same_timestamp_fails(fault_source):
    moments = fault_source.event["moments"]
    moments[1][1] = moments[0][1]
    with pytest.raises(SportVUError, match="Conflicting observations"):
        convert(fault_source)


@pytest.mark.parametrize("change,reason", [("gap", "TIME_GAP"), ("rollback", "TIMESTAMP_ROLLBACK"),
                                           ("period", "PERIOD_CHANGE")])
def test_discontinuous_time_splits_without_inventing_timestamps(fault_source, change, reason):
    moments = fault_source.event["moments"]
    if change == "gap":
        moments[2][1] += 1000
    elif change == "rollback":
        moments[2][1] = moments[0][1] - 1
    else:
        moments[2][0] += 1
    clips = convert(fault_source)
    assert [len(c["frames"]) for c in clips] == [2, 1]
    assert all(c["source_event"]["event_id"] == "2" for c in clips)
    assert clips[1]["source_event"]["start_moment_index"] == 2
    assert clips[1]["frames"][0]["t_ms"] == 0
    assert clips[1]["frames"][0]["source_timestamp_ms"] == moments[2][1]
    assert reason in codes(clips[1])


def test_bad_moment_is_reported_and_breaks_trails(fault_source):
    fault_source.event["moments"][1][1] = None
    (clip,) = convert(fault_source)
    assert len(clip["frames"]) == 2
    assert player(clip["frames"][1])["break_before"]
    assert clip["frames"][1]["t_ms"] == 79
    assert "INVALID_MOMENT" in codes(clip)


def test_unknown_roster_player_is_not_given_invented_metadata(fault_source):
    roster = fault_source.event["home"]["players"]
    roster[:] = [p for p in roster if p["playerid"] != 202340]
    (clip,) = convert(fault_source)
    meta = next(p for p in clip["players"] if p["player_id"] == "202340")
    assert meta["first_name"] is None and meta["jersey"] is None
    assert "UNKNOWN_PLAYER" in codes(clip)


def test_null_and_invalid_clocks_do_not_replace_timestamp(fault_source):
    fault_source.event["moments"][1][2:4] = [None, -1]
    (clip,) = convert(fault_source)
    frame = clip["frames"][1]
    assert frame["game_clock_s"] is None and frame["shot_clock_s"] is None
    assert frame["t_ms"] == 39
    assert {"MISSING_CLOCK", "INVALID_CLOCK"} <= codes(clip)


@pytest.mark.parametrize("threshold", [0, -1, True, None])
def test_gap_policy_is_required(fault_source, threshold):
    with pytest.raises(SportVUError, match="positive integer"):
        convert_event(fault_source, gap_threshold_ms=threshold)


def test_empty_event_has_clear_error(fault_source):
    fault_source.event["moments"] = []
    with pytest.raises(SportVUError, match="no moments"):
        convert(fault_source)


def test_reader_supports_metadata_after_events_and_rejects_ambiguous_ids(fault_source, tmp_path):
    path = tmp_path / "real-excerpt.json"
    content = {"events": [fault_source.event], "gameid": fault_source.game_id,
               "gamedate": fault_source.game_date}
    path.write_text(json.dumps(content), encoding="utf-8")
    assert read_event(path, "2").game_id == "0021500476"
    with pytest.raises(SportVUError, match="not found"):
        read_event(path, "not-an-event")
    with pytest.raises(SportVUError, match="SHA-256"):
        read_event(path, "2", "0" * 64)
    content["events"].append(fault_source.event)
    path.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(SportVUError, match="ambiguous"):
        read_event(path, "2")
