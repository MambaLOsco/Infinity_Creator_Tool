"""Generate textual summaries for CreatorPack outputs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..stt.transcribe import Transcript
from ..util.timecode import seconds_to_srt_timestamp


@dataclass
class SummaryBullet:
    """Represents a summary bullet entry."""

    timecode: float
    text: str


def build_summary(transcript: Transcript, chapter_starts: Iterable[float]) -> List[SummaryBullet]:
    """Create a lightweight summary using transcript sentences."""
    bullets: List[SummaryBullet] = []
    for start in chapter_starts:
        segment = next((s for s in transcript.segments if s.start <= start <= s.end), None)
        if segment is None:
            text = "Chapter overview"
        else:
            text = segment.text.strip() or "Chapter overview"
        bullets.append(SummaryBullet(timecode=start, text=text))
    return bullets


def render_summary_md(bullets: Iterable[SummaryBullet]) -> str:
    """Render summary bullets as Markdown."""
    lines = ["## Summary"]
    for bullet in bullets:
        timestamp = seconds_to_srt_timestamp(bullet.timecode)
        lines.append(f"- [{timestamp}] {bullet.text}")
    lines.append("\n## Call to Action")
    lines.append("- Subscribe for more local-first creator workflows!")
    return "\n".join(lines)
