"""Thin ffmpeg wrappers."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from ..util.errors import MediaProcessingError
from ..util.io import ensure_dir


FFMPEG_BIN = shutil.which("ffmpeg")
FFPROBE_BIN = shutil.which("ffprobe")


def _run_command(command: Sequence[str]) -> None:
    """Run a subprocess command and raise on failure."""
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - ffmpeg failure
        raise MediaProcessingError(f"Command failed: {' '.join(command)}") from exc


def probe_media(path: Path) -> dict:
    """Return a metadata dictionary for *path* using ffprobe if available."""
    if FFPROBE_BIN:
        command = [
            FFPROBE_BIN,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)
    return {
        "format": {
            "duration": 0,
            "filename": str(path),
        },
        "streams": [],
    }


def segment_media(
    source: Path,
    segments: Iterable[Tuple[float, float]],
    dest_dir: Path,
    prefix: str = "segment",
) -> List[Path]:
    """Cut *source* into the provided segments."""
    ensure_dir(dest_dir)
    outputs: List[Path] = []
    for index, (start, end) in enumerate(segments, start=1):
        duration = max(end - start, 0.01)
        output = dest_dir / f"{prefix}-{index:03d}.mp4"
        if FFMPEG_BIN:
            command = [
                FFMPEG_BIN,
                "-y",
                "-ss",
                f"{start:.3f}",
                "-i",
                str(source),
                "-t",
                f"{duration:.3f}",
                "-c",
                "copy",
                str(output),
            ]
            try:
                _run_command(command)
            except MediaProcessingError:
                # Re-encode fallback to maintain reliability
                command = [
                    FFMPEG_BIN,
                    "-y",
                    "-ss",
                    f"{start:.3f}",
                    "-i",
                    str(source),
                    "-t",
                    f"{duration:.3f}",
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    "-movflags",
                    "+faststart",
                    str(output),
                ]
                _run_command(command)
        else:
            shutil.copy2(source, output)
        outputs.append(output)
    return outputs


def extract_audio(source: Path, target: Path) -> Path:
    """Extract audio track as MP3 using ffmpeg if available."""
    ensure_dir(target.parent)
    if FFMPEG_BIN:
        command = [
            FFMPEG_BIN,
            "-y",
            "-i",
            str(source),
            "-vn",
            "-acodec",
            "mp3",
            str(target),
        ]
        _run_command(command)
    else:  # pragma: no cover - best effort fallback
        shutil.copy2(source, target)
    return target


__all__ = ["probe_media", "segment_media", "extract_audio"]
