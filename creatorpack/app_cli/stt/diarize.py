"""Optional diarization hook."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List


try:  # pragma: no cover - optional dependency
    from pyannote.audio import Pipeline  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Pipeline = None  # type: ignore


def diarize_audio(path: Path) -> List[Dict[str, float]]:
    """Run diarization if ``pyannote.audio`` is available."""
    if Pipeline is None:
        return []
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
    diarization = pipeline(str(path))
    results: List[Dict[str, float]] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        results.append({
            "start": float(turn.start),
            "end": float(turn.end),
            "speaker": str(speaker),
        })
    return results
