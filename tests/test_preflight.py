"""Tests for preflight validation."""
from __future__ import annotations

from pathlib import Path

import pytest

from creatorpack.app_cli.ingest.sources import IngestInput
from creatorpack.app_cli.util.preflight import PreflightError, run_preflight


def test_preflight_missing_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("creatorpack.app_cli.util.preflight.ensure_ffmpeg_available", lambda: None)
    monkeypatch.setattr("creatorpack.app_cli.util.preflight.ensure_faster_whisper_available", lambda: None)
    with pytest.raises(PreflightError):
        run_preflight([IngestInput(kind="local", value="missing.mp4")])


def test_preflight_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file_path = tmp_path / "input.mp4"
    file_path.write_text("ok", encoding="utf-8")
    monkeypatch.setattr("creatorpack.app_cli.util.preflight.ensure_ffmpeg_available", lambda: None)
    monkeypatch.setattr("creatorpack.app_cli.util.preflight.ensure_faster_whisper_available", lambda: None)
    run_preflight([IngestInput(kind="local", value=str(file_path))])
