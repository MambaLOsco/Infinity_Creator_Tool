"""Speech-to-text wrapper around faster-whisper with a graceful fallback."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

try:  # pragma: no cover - optional dependency
    from faster_whisper import WhisperModel  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    WhisperModel = None  # type: ignore


@dataclass
class TranscriptSegment:
    """Represents a transcript segment."""

    id: int
    start: float
    end: float
    text: str
    speaker: str


@dataclass
class Transcript:
    """Transcript payload compatible with ``transcript.json`` schema."""

    language: str
    segments: List[TranscriptSegment]

    def as_dict(self) -> dict:
        return {
            "language": self.language,
            "segments": [
                {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "speaker": segment.speaker,
                }
                for segment in self.segments
            ],
        }


def _fallback_transcript(path: Path, language: str | None) -> Transcript:
    """Return a simple placeholder transcript when STT is unavailable."""
    try:
        import wave

        with wave.open(str(path), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
    except Exception:
        duration = 60.0
    segment = TranscriptSegment(
        id=0,
        start=0.0,
        end=duration,
        text="[Transcription placeholder - install faster-whisper for real STT]",
        speaker="S1",
    )
    return Transcript(language=language or "en", segments=[segment])


def transcribe_audio(path: Path, language: str | None = None) -> Transcript:
    """Transcribe *path* using faster-whisper if available."""
    if WhisperModel is None:
        return _fallback_transcript(path, language)

    model = WhisperModel("small", device="cuda" if WhisperModel is not None else "cpu")
    segments, info = model.transcribe(str(path), language=language)
    transcript_segments: List[TranscriptSegment] = []
    for index, segment in enumerate(segments):
        transcript_segments.append(
            TranscriptSegment(
                id=index,
                start=float(segment.start or 0.0),
                end=float(segment.end or 0.0),
                text=segment.text.strip(),
                speaker="S1",
            )
        )
    language_code = language or getattr(info, "language", "en")
    return Transcript(language=language_code, segments=transcript_segments)


__all__ = ["Transcript", "TranscriptSegment", "transcribe_audio"]
