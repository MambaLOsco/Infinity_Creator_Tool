"""ffmpeg helper wrappers."""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from ..branding.theme import BrandTheme
from ..util.errors import CreatorPackError, ExitCodes


class FFmpegError(CreatorPackError):
    """Raised when ffmpeg operations fail."""

    exit_code = ExitCodes.MEDIA_ERROR


@dataclass
class MediaProbe:
    """Minimal probe information about a media file."""

    duration: float
    streams: List[str]


def ensure_ffmpeg_available() -> None:
    """Ensure ffmpeg binaries are available in PATH."""

    for binary in ("ffmpeg", "ffprobe"):
        if shutil.which(binary) is None:
            raise FFmpegError(f"Required binary '{binary}' not found in PATH")


def _run_command(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - depends on external binary
        joined = ' '.join(args)
        message = "ffmpeg command failed: {}\n{}".format(joined, exc.stderr)
        raise FFmpegError(message) from exc


def probe_media(path: Path) -> MediaProbe:
    """Return duration and stream summary for the provided media."""

    args = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = _run_command(args)
    payload = json.loads(result.stdout)
    duration = float(payload.get("format", {}).get("duration", 0.0))
    streams = [stream.get("codec_type", "unknown") for stream in payload.get("streams", [])]
    return MediaProbe(duration=duration, streams=streams)


def chunk_media(
    source: Path,
    target_dir: Path,
    segments: Iterable["MediaSegment"],
    *,
    brand: BrandTheme | None = None,
    short_mode: bool = False,
) -> List["ChunkOutput"]:
    """Cut a media file into smaller segments."""

    target_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[ChunkOutput] = []
    for index, segment in enumerate(segments, start=1):
        suffix = "short" if short_mode else "part"
        out_name = f"{source.stem}_{suffix}-{index:03d}.mp4"
        dest = target_dir / out_name
        _execute_cut(source, dest, segment.start, segment.end, brand=brand)
        _write_srt(dest.with_suffix('.srt'), segment)
        outputs.append(ChunkOutput(file=dest, start=segment.start, end=segment.end))
    return outputs


@dataclass
class MediaSegment:
    """Represents a segment boundary for cutting media."""

    start: float
    end: float
    caption: str | None = None


@dataclass
class ChunkOutput:
    """Metadata about a generated chunk."""

    file: Path
    start: float
    end: float


def _execute_cut(
    source: Path,
    destination: Path,
    start: float,
    end: float,
    *,
    brand: BrandTheme | None = None,
) -> None:
    duration = max(end - start, 0.1)
    args = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(source),
        "-t",
        f"{duration:.3f}",
    ]

    if brand and brand.watermark_path:
        filter_complex = (
            "movie='{wm}'[wm];[0:v][wm]overlay={pos}".format(
                wm=brand.watermark_path.as_posix(),
                pos=brand.watermark_position,
            )
        )
        args.extend(["-filter_complex", filter_complex])

    args.extend(["-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-movflags", "+faststart", str(destination)])
    _run_command(args)


def _write_srt(path: Path, segment: "MediaSegment") -> None:
    """Write a simple SRT caption file for the provided segment."""

    text = segment.caption or "CreatorPack segment"

    def _format(ts: float) -> str:
        hours = int(ts // 3600)
        minutes = int((ts % 3600) // 60)
        seconds = int(ts % 60)
        millis = int((ts - int(ts)) * 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

    lines = ["1", f"{_format(segment.start)} --> {_format(segment.end)}", text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
