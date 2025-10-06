"""Timecode helpers."""
from __future__ import annotations

from typing import Iterable, List


def seconds_to_srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def cumulative_sum(values: Iterable[float]) -> List[float]:
    """Return cumulative sum of a sequence."""
    total = 0.0
    result: List[float] = []
    for value in values:
        total += value
        result.append(total)
    return result
