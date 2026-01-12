"""Asset downloading utilities."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from .license_gate import LicenseGate, LicenseInfo
from .sources import IngestInput
from ..util.errors import CreatorPackError, ExitCodes


class DownloadError(CreatorPackError):
    """Raised when download fails."""

    exit_code = ExitCodes.DOWNLOAD_FAILED


@dataclass
class DownloadResult:
    """Captures download outcome."""

    path: Path
    source: str
    original_name: str
    retrieved_at: datetime
    license_info: LicenseInfo


def download_inputs(inputs: List[IngestInput], download_dir: Path, license_gate: LicenseGate) -> List[DownloadResult]:
    download_dir.mkdir(parents=True, exist_ok=True)
    results: List[DownloadResult] = []

    for ingest in inputs:
        if ingest.kind == "local":
            src_path = Path(ingest.value)
            if not src_path.exists():
                raise DownloadError(f"File not found: {src_path}")
            dest = download_dir / src_path.name
            if src_path.resolve() != dest.resolve():
                shutil.copy2(src_path, dest)
            else:
                dest = src_path
            license_info = license_gate.build_info(
                source="local",
                title=src_path.stem,
                creator=None,
                license_code="pd",
                license_url=None,
            )
            results.append(
                DownloadResult(
                    path=dest,
                    source="local",
                    original_name=src_path.name,
                    retrieved_at=datetime.utcnow(),
                    license_info=license_info,
                )
            )
        else:
            raise DownloadError(
                f"Source '{ingest.kind}' is not implemented in this offline build."
            )

    if not results:
        raise DownloadError("No assets downloaded")

    return results
