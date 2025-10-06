"""Tests for chunking logic."""
from __future__ import annotations

import pytest

from creatorpack.app_cli.media.chunking import (
    Chunk,
    align_chunks_to_sentences,
    generate_fixed_chunks,
)


def test_generate_fixed_chunks_even_split() -> None:
    chunks = generate_fixed_chunks(duration=600, minutes=5)
    assert len(chunks) == 2
    assert chunks[0].start == 0
    assert chunks[-1].end == 600


def test_align_chunks_to_sentences_snaps_within_tolerance() -> None:
    chunks = [Chunk(index=1, start=0.0, end=120.0, title="Part 1")]
    sentences = [(0.0, 118.0, "Intro"), (118.0, 125.0, "Next")]
    adjusted = align_chunks_to_sentences(chunks=chunks, sentences=sentences, tolerance=10.0)
    assert adjusted[0].end == pytest.approx(118.0)
