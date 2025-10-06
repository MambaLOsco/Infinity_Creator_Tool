"""Thumbnail utilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ThumbnailCandidate:
    """Represents an automatically selected thumbnail."""

    timecode: float
    file: Path


def select_thumbnail_frames(duration: float, count: int = 3) -> List[float]:
    """Return evenly spaced timestamps for thumbnails."""
    if duration <= 0 or count <= 0:
        return [0.0]
    step = duration / (count + 1)
    return [step * (i + 1) for i in range(count)]
