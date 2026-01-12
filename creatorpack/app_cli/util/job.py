"""Job id helpers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from ..ingest.sources import IngestInput


def compute_job_id(
    inputs: Iterable[IngestInput],
    *,
    template: str,
    minutes: int,
    smart: bool,
    highlights: bool,
    highlight_config: dict,
    brand_path: Path | None,
    diarize: bool,
    localize: str | None,
) -> str:
    """Return a deterministic job id based on inputs and parameters."""
    payload = {
        "inputs": [_input_fingerprint(item) for item in sorted(inputs, key=lambda i: (i.kind, i.value))],
        "template": template,
        "minutes": minutes,
        "smart": smart,
        "highlights": highlights,
        "highlight_config": highlight_config,
        "brand": _path_fingerprint(brand_path),
        "diarize": diarize,
        "localize": localize,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"job-{digest[:12]}"


def _input_fingerprint(ingest: IngestInput) -> dict:
    if ingest.kind != "local":
        return {"kind": ingest.kind, "value": ingest.value}
    path = Path(ingest.value)
    stat = path.stat()
    return {
        "kind": ingest.kind,
        "value": str(path.resolve()),
        "mtime": stat.st_mtime,
        "size": stat.st_size,
    }


def _path_fingerprint(path: Path | None) -> dict | None:
    if path is None:
        return None
    resolved = path.resolve()
    stat = resolved.stat()
    return {"path": str(resolved), "mtime": stat.st_mtime, "size": stat.st_size}
