"""Local-only S1 export: python -m basketball_tactics.cli --help."""

import argparse
import json
from pathlib import Path
import sys

from .backend import export_event
from .sportvu import SportVUError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export one real SportVU event to S1 JSON 0.2.0")
    parser.add_argument("--input", required=True, type=Path, help="Existing single-game JSON file")
    parser.add_argument("--event-id", required=True, help="Source eventId, not array index or possession label")
    parser.add_argument("--output-dir", required=True, type=Path, help="New local output directory; never overwritten")
    parser.add_argument("--gap-threshold-ms", required=True, type=int, help="Positive timestamp gap limit; larger gaps split clips")
    parser.add_argument("--coordinate-limit-ft", type=float, default=1000,
                        help="Gross coordinate guard, not court bounds (default: 1000 feet)")
    parser.add_argument("--source-commit", help="Optional full commit SHA of the source archive")
    parser.add_argument("--expected-sha256", help="Optional expected SHA-256 of the uncompressed JSON")
    args = parser.parse_args(argv)
    try:
        manifest = export_event(args.input, args.output_dir, args.event_id,
                                gap_threshold_ms=args.gap_threshold_ms,
                                coordinate_limit_ft=args.coordinate_limit_ft,
                                source_commit=args.source_commit, expected_sha256=args.expected_sha256)
    except (OSError, SportVUError, TypeError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"manifest": str(args.output_dir / "manifest.json"),
                      "clips": manifest["clips"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
