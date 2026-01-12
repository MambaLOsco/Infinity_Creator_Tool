"""Integration test for the end-to-end pipeline."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from creatorpack.app_cli.ingest.sources import IngestInput
from creatorpack.app_cli.main import RunOptions, _run_pipeline
from creatorpack.app_cli.nlp.highlights import HighlightPolicy
from creatorpack.app_cli.stt.transcribe import TranscriptionError, ensure_faster_whisper_available


def _require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("ffmpeg/ffprobe not available")


def _require_whisper() -> None:
    try:
        ensure_faster_whisper_available()
    except TranscriptionError:
        pytest.skip("faster-whisper not available")


def _make_sample_media(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=128x72:rate=24:duration=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=1",
            "-shortest",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    _require_ffmpeg()
    _require_whisper()

    media_path = tmp_path / "sample.mp4"
    _make_sample_media(media_path)

    options = RunOptions(
        inputs=[IngestInput(kind="local", value=str(media_path))],
        template="creator-pack",
        minutes=1,
        smart=False,
        highlights=False,
        highlight_policy=HighlightPolicy(),
        brand_path=None,
        localize=None,
        diarize=False,
        output_dir=tmp_path,
        allow_sources=["local"],
        block_nc_nd=True,
        dry_run=False,
        job_id="job-test",
    )

    _run_pipeline(options)
    root = tmp_path / "job-test"
    assert (root / "transcript" / "transcript.json").exists()
    assert (root / "transcript" / "transcript.txt").exists()
    assert (root / "manifests" / "chapters.json").exists()
    assert (root / "manifests" / "provenance.json").exists()
    assert (root / "manifests" / "credits.json").exists()
    assert (root / "logs" / "job.log.jsonl").exists()
