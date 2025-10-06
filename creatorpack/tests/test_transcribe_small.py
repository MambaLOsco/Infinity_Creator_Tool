"""Tests for transcript generation."""
from __future__ import annotations

import wave
from pathlib import Path

from creatorpack.app_cli.stt.transcribe import transcribe_audio


def _create_sine_wave(path: Path) -> None:
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b'\x00\x00' * 16000)


def test_transcribe_audio_schema(tmp_path: Path) -> None:
    audio = tmp_path / 'tone.wav'
    _create_sine_wave(audio)
    transcript = transcribe_audio(audio)
    assert transcript.language
    assert transcript.segments
    first = transcript.segments[0]
    assert first.start <= first.end
    assert first.text
