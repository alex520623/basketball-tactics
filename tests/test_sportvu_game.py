"""Full-game regression against unmodified, hash-verified real SportVU data."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from basketball_tactics.backend import export_event
from scripts.check_sportvu_sample import check_game, main, SAMPLE_SHA, SOURCE_COMMIT


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def game_path():
    explicit = os.environ.get("SPORTVU_SAMPLE")
    path = Path(explicit) if explicit else ROOT / ".tools/sportvu-review/0021500476.json"
    if not path.is_file():
        if explicit:
            pytest.fail("Explicit SPORTVU_SAMPLE does not exist")
        pytest.skip("Verified real game missing; see docs/multi-event-validation.md")
    return path


@pytest.fixture(scope="module")
def report(game_path):
    # check_game verifies every successful frame/coordinate/clock/trajectory,
    # streaming one source event at a time and retaining only aggregate counts.
    return check_game(game_path)


def test_full_game_preserves_every_convertible_source_observation(report):
    assert report["source_sha256"] == SAMPLE_SHA
    assert report["event_count"] == 489
    assert report["status_counts"] == {"converted": 482, "conflict_rejected": 2, "empty_rejected": 5}
    assert report["input_moments_including_overlaps"] == 209431
    assert report["exported_frames_including_overlaps"] == 208418
    assert report["clip_count"] == 629
    assert report["warning_counts"] == {"OUT_OF_COURT": 24310, "TIME_GAP": 147,
                                        "MISSING_CLOCK": 19817, "MISSING_BALL": 1273, "PLAYER_COUNT": 3}


@pytest.mark.parametrize("event_id,frames,clips,missing_ball,incomplete,null_clock", [
    ("2", 525, [525], 0, 0, 0),
    ("3", 450, [285, 165], 0, 0, 0),
    ("29", 194, [169, 25], 22, 0, 0),
    ("44", 419, [419], 0, 0, 156),
    ("80", 422, [125, 297], 0, 1, 115),
    ("265", 472, [189, 158, 125], 22, 0, 472),
])
def test_real_event_cases(report, event_id, frames, clips, missing_ball, incomplete, null_clock):
    row = next(r for r in report["events"] if r["event_id"] == event_id)
    assert row["status"] == "converted"
    assert row["input_moments"] == row["exported_frames"] == frames
    assert row["clip_frame_counts"] == clips
    assert row["missing_ball_frames"] == missing_ball
    assert row["incomplete_player_frames"] == incomplete
    assert row["null_shot_clock_frames"] == null_clock


def test_real_empty_events_are_rejected_not_reported_as_empty_success(report):
    rejected = [r for r in report["events"] if r["status"] == "empty_rejected"]
    assert {r["event_id"] for r in rejected} == {"447", "517", "522", "524", "544"}
    assert all(r["input_moments"] == 0 and r["error"] == "Selected event has no moments" for r in rejected)


def test_real_conflicting_timestamps_are_detected_without_choosing_an_observation(report):
    rows = [r for r in report["events"] if r["status"] == "conflict_rejected"]
    assert {r["event_id"]: r["conflicting_moment_indices"] for r in rows} == {
        "215": list(range(211, 248, 2)), "216": list(range(11, 48, 2))}
    assert sum(r["input_moments"] for r in rows) == 1013


@pytest.mark.parametrize("event_id,message", [("447", "no moments"), ("215", "Conflicting observations"),
                                            ("216", "Conflicting observations")])
def test_cli_rejection_leaves_no_partial_export(game_path, tmp_path, event_id, message):
    target = tmp_path / ("event-" + event_id)
    completed = subprocess.run([sys.executable, "-m", "basketball_tactics.cli", "--input", str(game_path),
                                "--event-id", event_id, "--output-dir", str(target), "--gap-threshold-ms", "120",
                                "--expected-sha256", SAMPLE_SHA], capture_output=True, text=True, encoding="utf-8")
    assert completed.returncode == 1
    assert message in completed.stderr
    assert not target.exists()


@pytest.mark.parametrize("event_id,expected_counts,missing_ball,incomplete,null_clock", [
    ("29", [169, 25], 22, 0, 0), ("80", [125, 297], 0, 1, 115),
])
def test_real_multiclip_export_roundtrip(game_path, tmp_path, event_id, expected_counts,
                                       missing_ball, incomplete, null_clock):
    target = tmp_path / ("event-" + event_id)
    export_event(game_path, target, event_id, gap_threshold_ms=120,
                 expected_sha256=SAMPLE_SHA, source_commit=SOURCE_COMMIT)
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    clips = [json.loads((target / e["path"]).read_text(encoding="utf-8")) for e in manifest["clips"]]
    assert [e["frame_count"] for e in manifest["clips"]] == [len(c["frames"]) for c in clips] == expected_counts
    frames = [f for c in clips for f in c["frames"]]
    assert all(c["source_event"]["event_id"] == event_id for c in clips)
    assert all(e["duration_ms"] == c["timeline"]["duration_ms"] for e, c in zip(manifest["clips"], clips))
    assert all(c["frames"][0]["t_ms"] == 0 for c in clips)
    assert sum(f["ball"] is None for f in frames) == missing_ball
    assert sum(len(f["players"]) != 10 for f in frames) == incomplete
    assert sum(f["shot_clock_s"] is None for f in frames) == null_clock


def test_validation_report_is_never_overwritten(tmp_path, capsys):
    target = tmp_path / "report.json"
    target.write_text("keep-existing-report", encoding="utf-8")
    assert main(["--input", "unused.json", "--report", str(target)]) == 1
    assert target.read_text(encoding="utf-8") == "keep-existing-report"
    assert "already exists" in capsys.readouterr().err
