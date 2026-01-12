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


def score_highlights(transcript: TranscriptResult, duration: float) -> HighlightPlan:
    if not transcript.segments:
        return HighlightPlan(highlights=[])

    highlights: List[Highlight] = []
    for segment in transcript.segments[:3]:
        clip_end = min(segment.start + 75.0, duration)
        highlights.append(Highlight(start=segment.start, end=clip_end, caption=segment.text[:80]))
    return HighlightPlan(highlights=highlights)
