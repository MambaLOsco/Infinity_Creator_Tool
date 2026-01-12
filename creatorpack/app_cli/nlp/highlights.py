"""Highlight selection heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..stt.transcribe import TranscriptResult


@dataclass
class Highlight:
    start: float
    end: float
    caption: str


@dataclass
class HighlightPlan:
    highlights: List[Highlight]


@dataclass
class HighlightPolicy:
    top_k: int = 3
    min_seconds: float = 60.0
    max_seconds: float = 90.0
    padding_seconds: float = 2.0


def score_highlights(
    transcript: TranscriptResult, duration: float, policy: HighlightPolicy | None = None
) -> HighlightPlan:
    policy = policy or HighlightPolicy()
    if not transcript.segments:
        return HighlightPlan(highlights=[])

    highlights: List[Highlight] = []
    for segment in transcript.segments[: policy.top_k]:
        highlight = _build_highlight(segment.start, segment.end, segment.text, duration, policy)
        if highlight:
            highlights.append(highlight)
    return HighlightPlan(highlights=highlights)


def _build_highlight(
    start: float, end: float, caption: str, duration: float, policy: HighlightPolicy
) -> Highlight | None:
    base_start = max(start - policy.padding_seconds, 0.0)
    base_end = max(end, start + policy.min_seconds)
    base_end = min(base_end + policy.padding_seconds, duration)
    if base_end - base_start > policy.max_seconds:
        base_end = min(base_start + policy.max_seconds, duration)
    if base_end <= base_start:
        return None
    return Highlight(start=base_start, end=base_end, caption=caption[:80])
