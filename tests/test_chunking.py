"""Tests for chapter planning logic."""
from __future__ import annotations

from creatorpack.app_cli.media.chunking import ChapterPolicy, build_chapter_plan
from creatorpack.app_cli.stt.transcribe import TranscriptResult, TranscriptSegment


def _fake_transcript(duration: float, segments: int) -> TranscriptResult:
    segs = []
    step = duration / segments
    start = 0.0
    for idx in range(segments):
        end = min(start + step, duration)
        segs.append(TranscriptSegment(id=idx, start=start, end=end, text=f"Segment {idx}"))
        start = end
    return TranscriptResult(language="en", segments=segs)


def test_fixed_chapter_plan() -> None:
    transcript = _fake_transcript(300.0, 6)
    policy = ChapterPolicy(target_seconds=120, alignment="fixed")
    plan = build_chapter_plan(transcript, 300.0, policy)
    assert len(plan.chapters) == 3
    assert plan.chapters[0].end == 120


def test_smart_alignment_prefers_boundaries() -> None:
    transcript = _fake_transcript(900.0, 10)
    policy = ChapterPolicy(target_seconds=300, alignment="sentence", allow_smart=True)
    plan = build_chapter_plan(transcript, 900.0, policy)
    assert len(plan.chapters) == 3
    assert plan.chapters[1].start == plan.chapters[0].end
