"""faster-whisper transcription wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..util.errors import CreatorPackError, ExitCodes


class TranscriptionError(CreatorPackError):
    exit_code = ExitCodes.TRANSCRIPTION_ERROR


@dataclass
class TranscriptSegment:
    id: int
    start: float
    end: float
    text: str
    speaker: str = "S1"


@dataclass
class TranscriptResult:
    language: str
    segments: List[TranscriptSegment]

    def to_dict(self) -> dict:
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

    def to_text(self) -> str:
        return "\n".join(segment.text for segment in self.segments if segment.text).strip() + "\n"


def ensure_faster_whisper_available() -> None:
    try:
        from faster_whisper import WhisperModel  # type: ignore  # noqa: F401
    except Exception as exc:  # pragma: no cover - optional dependency
        raise TranscriptionError("faster-whisper is not available") from exc


def transcribe_media(path: Path, diarize: bool = False) -> TranscriptResult:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return _dummy_transcript(path)

    try:
        model = WhisperModel("base", device="auto")
        segments, info = model.transcribe(str(path), beam_size=1)
    except Exception as exc:  # pragma: no cover - actual inference heavy
        raise TranscriptionError(str(exc)) from exc

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

    language = getattr(info, "language", "en")
    return TranscriptResult(language=language, segments=transcript_segments)


def _dummy_transcript(path: Path) -> TranscriptResult:
    # Basic fallback splitting the duration into placeholder segments
    from ..media.ffmpeg_ops import probe_media, FFmpegError

    try:
        probe = probe_media(path)
        duration = probe.duration
    except (FFmpegError, FileNotFoundError):
        duration = 0.0
    segments: List[TranscriptSegment] = []
    chunk = max(duration / 3, 1.0)
    start = 0.0
    index = 0
    while start < duration:
        end = min(start + chunk, duration)
        segments.append(
            TranscriptSegment(
                id=index,
                start=start,
                end=end,
                text="[transcription unavailable in offline mode]",
            )
        )
        start = end
        index += 1
    if not segments:
        segments.append(TranscriptSegment(id=0, start=0.0, end=duration, text=""))
    return TranscriptResult(language="en", segments=segments)
