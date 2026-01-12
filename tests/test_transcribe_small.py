"""Integration test for transcription fallback."""
from __future__ import annotations

from pathlib import Path

from creatorpack.app_cli.stt.transcribe import TranscriptResult, transcribe_media


def _create_silence(tmp_path: Path) -> Path:
    path = tmp_path / "silence.wav"
    import wave

    framerate = 16000
    duration_seconds = 1
    frames = framerate * duration_seconds
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(framerate)
        wav.writeframes(b"\x00\x00" * frames)
    return path


def test_transcribe_dummy(tmp_path: Path) -> None:
    audio = _create_silence(tmp_path)
    result = transcribe_media(audio)
    assert isinstance(result, TranscriptResult)
    assert result.segments
