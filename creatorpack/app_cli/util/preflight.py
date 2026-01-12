"""Preflight validation for CLI runs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from ..ingest.sources import IngestInput
from ..media.ffmpeg_ops import FFmpegError, ensure_ffmpeg_available
from ..stt.transcribe import ensure_faster_whisper_available
from ..util.errors import CreatorPackError, ExitCodes


class PreflightError(CreatorPackError):
    """Raised when preflight checks fail."""

    exit_code = ExitCodes.INVALID_INPUT


def run_preflight(inputs: Iterable[IngestInput]) -> None:
    """Validate runtime dependencies and input files."""
    for ingest in inputs:
        if ingest.kind != "local":
            continue
        path = Path(ingest.value)
        if not path.exists():
            raise PreflightError(
                f"Input file not found: {path}. Provide a valid --file path."
            )
        if not path.is_file():
            raise PreflightError(
                f"Input path is not a file: {path}. Provide a file path via --file."
            )
        if not os.access(path, os.R_OK):
            raise PreflightError(
                f"Input file not readable: {path}. Fix permissions (chmod +r) and retry."
            )

    try:
        ensure_ffmpeg_available()
    except FFmpegError as exc:
        raise PreflightError(
            "ffmpeg/ffprobe not found. Install with `brew install ffmpeg` (macOS) or "
            "`sudo apt-get install ffmpeg` (Linux)."
        ) from exc

    try:
        ensure_faster_whisper_available()
    except CreatorPackError as exc:
        raise PreflightError(
            "Missing faster-whisper dependency. Install with "
            "`pip install faster-whisper` and ensure CUDA/CPU backends are available."
        ) from exc
