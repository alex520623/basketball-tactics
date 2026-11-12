"""Read one SportVU event without loading a whole game into Python objects."""

from dataclasses import dataclass
from datetime import date
import hashlib
from pathlib import Path
import re
from typing import Any

import ijson


class SportVUError(ValueError):
    """Invalid or ambiguous source data; no successful export should be published."""


def identifier(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise SportVUError("IDs must be nonempty strings or integers")
    result = str(value)
    if not result or result != result.strip():
        raise SportVUError("IDs must be nonempty and have no surrounding whitespace")
    return result


@dataclass(frozen=True)
class SourceEvent:
    path: Path
    game_id: str
    game_date: str
    event_index: int
    event: dict[str, Any]
    sha256: str


def read_event(path: Path | str, event_id: str, expected_sha256: str | None = None) -> SourceEvent:
    """Scan one game, keeping only the requested event and the current event in memory.

    Scan to EOF to reject truncated JSON and ambiguous duplicate event IDs. The
    metadata pass also supports JSON with game metadata after the events array.
    """
    path = Path(path)
    wanted = identifier(event_id)
    if expected_sha256 is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise SportVUError("Expected SHA-256 must contain 64 hexadecimal characters")
    before = path.stat()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if expected_sha256 is not None and digest != expected_sha256.lower():
        raise SportVUError("Source SHA-256 does not match the expected file")

    metadata: dict[str, Any] = {}
    selected = None
    selected_index = -1
    try:
        with path.open("rb") as stream:
            for prefix, kind, value in ijson.parse(stream, use_float=True):
                if prefix in ("gameid", "gamedate") and kind in ("string", "number", "null"):
                    metadata[prefix] = value
                if len(metadata) == 2:
                    break
        with path.open("rb") as stream:
            for index, event in enumerate(ijson.items(stream, "events.item", use_float=True)):
                if not isinstance(event, dict):
                    raise SportVUError(f"events[{index}] must be an object")
                if "eventId" not in event or identifier(event["eventId"]) != wanted:
                    continue
                if selected is not None:
                    raise SportVUError(f"eventId {wanted!r} occurs more than once; selection is ambiguous")
                selected, selected_index = event, index
    except (ijson.JSONError, UnicodeError, OverflowError) as exc:
        raise SportVUError(f"Cannot parse SportVU JSON: {exc}") from exc

    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise SportVUError("Source changed while it was being read")
    if selected is None:
        raise SportVUError(f"eventId {wanted!r} was not found")
    if "gameid" not in metadata or not isinstance(metadata.get("gamedate"), str):
        raise SportVUError("Source must provide gameid and gamedate")
    try:
        date.fromisoformat(metadata["gamedate"])
    except ValueError as exc:
        raise SportVUError("gamedate must be an ISO calendar date") from exc
    return SourceEvent(path, identifier(metadata["gameid"]), metadata["gamedate"],
                       selected_index, selected, digest)
