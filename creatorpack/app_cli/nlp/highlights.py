"""Highlight scoring heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..stt.transcribe import TranscriptSegment


@dataclass
class HighlightCandidate:
    """Represents a potential highlight clip."""

    start: float
    end: float
    caption: str
    score: float


DEFAULT_ALPHA = 0.6
DEFAULT_BETA = 0.3
DEFAULT_GAMMA = 0.1


def score_candidates(
    segments: Iterable[TranscriptSegment],
    *,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
) -> List[HighlightCandidate]:
    """Compute highlight scores based on heuristics."""
    candidates: List[HighlightCandidate] = []
    for segment in segments:
        duration = max(segment.end - segment.start, 0.01)
        keyword_density = min(len(segment.text.split()) / 40.0, 1.0)
        energy = min(len(segment.text) / 120.0, 1.0)
        duration_penalty = max(0.0, (duration - 75.0) / 75.0)
        score = alpha * keyword_density + beta * energy - gamma * duration_penalty
        candidates.append(
            HighlightCandidate(
                start=segment.start,
                end=min(segment.end, segment.start + 90.0),
                caption=segment.text.strip(),
                score=score,
            )
        )
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
