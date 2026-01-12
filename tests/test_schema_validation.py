"""Tests for manifest schema validation."""
from __future__ import annotations

from pathlib import Path

from creatorpack.app_cli.schemas.validate import validate_manifest


def test_transcript_schema_validation() -> None:
    schema = Path("creatorpack/app_cli/schemas/transcript_schema.json")
    payload = {
        "language": "en",
        "segments": [
            {"id": 1, "start": 0.0, "end": 1.0, "text": "Hello", "speaker": "S1"},
        ],
    }
    validate_manifest(payload, schema)


def test_chapters_schema_validation() -> None:
    schema = Path("creatorpack/app_cli/schemas/chapters_schema.json")
    payload = {
        "policy": {"target_sec": 60, "alignment": "fixed"},
        "chapters": [
            {"i": 1, "start": 0.0, "end": 60.0, "title": "Chapter 1"},
        ],
    }
    validate_manifest(payload, schema)
