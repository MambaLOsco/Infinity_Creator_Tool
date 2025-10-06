"""Derive chapter boundaries from transcripts."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from ..stt.transcribe import Transcript
from ..media.chunking import generate_fixed_chunks, align_chunks_to_sentences


_SENTENCE_PATTERN = re.compile(r"(?<=[.!?]) +")


@dataclass
class Chapter:
    """Represents a chapter entry."""

    index: int
    start: float
    end: float
    title: str


def derive_sentences(transcript: Transcript) -> List[tuple[float, float, str]]:
    """Create approximate sentence segments from the transcript."""
    sentences: List[tuple[float, float, str]] = []
    for segment in transcript.segments:
        if not segment.text:
            continue
        parts = _SENTENCE_PATTERN.split(segment.text.strip())
        if not parts:
            continue
        duration = max(segment.end - segment.start, 0.01)
        piece_duration = duration / len(parts)
        starts = [segment.start + piece_duration * i for i in range(len(parts))]
        for idx, text in enumerate(parts):
            start = starts[idx]
            end = min(segment.end, start + piece_duration)
            sentences.append((start, end, text.strip()))
    return sentences


def build_chapters(
    transcript: Transcript,
    minutes: int,
    align_sentences: bool,
) -> List[Chapter]:
    """Generate chapters respecting the configuration."""
    duration = transcript.segments[-1].end if transcript.segments else 0.0
    chunks = generate_fixed_chunks(duration, minutes)
    if align_sentences and transcript.segments:
        sentences = derive_sentences(transcript)
        chunks = align_chunks_to_sentences(chunks=chunks, sentences=sentences)
    return [Chapter(index=c.index, start=c.start, end=c.end, title=c.title) for c in chunks]


__all__ = ["Chapter", "derive_sentences", "build_chapters"]
