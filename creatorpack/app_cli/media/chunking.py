"""Chapter planning utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..media.ffmpeg_ops import MediaSegment
from ..stt.transcribe import TranscriptResult


@dataclass
class ChapterPolicy:
    target_seconds: int
    alignment: str
    allow_smart: bool = False


@dataclass
class Chapter:
    index: int
    start: float
    end: float
    title: str


@dataclass
class ChapterPlan:
    policy: ChapterPolicy
    chapters: List[Chapter]

    def to_dict(self) -> dict:
        return {
            "policy": {
                "target_sec": self.policy.target_seconds,
                "alignment": self.policy.alignment,
            },
            "chapters": [
                {"i": chapter.index, "start": chapter.start, "end": chapter.end, "title": chapter.title}
                for chapter in self.chapters
            ],
        }


def build_chapter_plan(transcript: TranscriptResult, duration: float, policy: ChapterPolicy) -> ChapterPlan:
    duration = max(duration, 0.0)
    segments = _smart_segments(transcript, duration) if policy.allow_smart else []
    chapters: List[Chapter] = []

    cursor = 0.0
    index = 1
    while cursor < duration:
        target_end = min(cursor + policy.target_seconds, duration)
        if segments:
            boundary = _find_boundary(segments, cursor, target_end, flex=15.0)
            if boundary is not None:
                target_end = min(boundary, duration)
        if target_end <= cursor:
            target_end = min(cursor + policy.target_seconds, duration)
            if target_end <= cursor:
                break
        chapters.append(Chapter(index=index, start=cursor, end=target_end, title=f"Chapter {index}"))
        cursor = target_end
        index += 1

    return ChapterPlan(policy=policy, chapters=chapters)


def _smart_segments(transcript: TranscriptResult, duration: float) -> List[float]:
    return [min(segment.end, duration) for segment in transcript.segments if segment.end > 0]


def _find_boundary(segments: Iterable[float], start: float, desired_end: float, flex: float) -> float | None:
    lower = max(start, desired_end - flex)
    upper = desired_end + flex
    candidates = [value for value in segments if lower <= value <= upper]
    if not candidates:
        return None
    return min(candidates, key=lambda value: abs(value - desired_end))


def chapters_to_segments(chapters: Iterable[Chapter]) -> List[MediaSegment]:
    return [MediaSegment(start=chapter.start, end=chapter.end, caption=chapter.title) for chapter in chapters]
