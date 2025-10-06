"""Chapter chunking strategies."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass
class Chunk:
    """Represents a media chunk."""

    index: int
    start: float
    end: float
    title: str


def generate_fixed_chunks(duration: float, minutes: int) -> List[Chunk]:
    """Split *duration* into chunks of ``minutes`` length."""
    target = minutes * 60
    chunks: List[Chunk] = []
    start = 0.0
    index = 1
    while start < duration:
        end = min(start + target, duration)
        title = f"Part {index}"
        chunks.append(Chunk(index=index, start=start, end=end, title=title))
        start = end
        index += 1
    if not chunks:
        chunks.append(Chunk(index=1, start=0.0, end=duration, title="Part 1"))
    return chunks


def align_chunks_to_sentences(
    *,
    chunks: Sequence[Chunk],
    sentences: Iterable[tuple[float, float, str]],
    tolerance: float = 15.0,
) -> List[Chunk]:
    """Adjust chunk boundaries to the nearest sentence boundary within tolerance."""
    sentence_list = list(sentences)
    adjusted: List[Chunk] = []
    for chunk in chunks:
        start = chunk.start
        end = chunk.end
        candidates = [s for s in sentence_list if abs(s[1] - end) <= tolerance]
        if candidates:
            chosen = min(candidates, key=lambda s: abs(s[1] - end))
            end = chosen[1]
        adjusted.append(Chunk(index=chunk.index, start=start, end=end, title=chunk.title))
    for i in range(1, len(adjusted)):
        adjusted[i] = Chunk(
            index=adjusted[i].index,
            start=adjusted[i - 1].end,
            end=adjusted[i].end,
            title=adjusted[i].title,
        )
    return adjusted
