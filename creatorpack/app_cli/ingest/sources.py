"""Source detection and metadata retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

from ..util.errors import CreatorPackError, ExitCodes


ALLOWED_DOMAINS = {
    "pexels.com": "pexels",
    "www.pexels.com": "pexels",
    "images.nasa.gov": "nasa",
    "commons.wikimedia.org": "commons",
    "upload.wikimedia.org": "commons",
    "www.europeana.eu": "europeana",
    "archive.org": "archive",
}


@dataclass
class IngestInput:
    """Represents an ingestable asset."""

    kind: str
    value: str


class SourceDetectionError(CreatorPackError):
    """Raised when inputs cannot be resolved."""

    exit_code = ExitCodes.INVALID_INPUT


def detect_input_sources(urls: List[str], files: List[Path], allow_sources: Iterable[str]) -> List[IngestInput]:
    """Detect and normalise ingest inputs."""

    allow = set(source.strip().lower() for source in allow_sources)
    inputs: List[IngestInput] = []

    for file_path in files:
        if "local" not in allow:
            raise SourceDetectionError("Local files are not allowed by current configuration")
        inputs.append(IngestInput("local", str(file_path)))

    for url in urls:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain not in ALLOWED_DOMAINS:
            raise SourceDetectionError(f"Domain '{domain}' is not allowlisted")
        source_kind = ALLOWED_DOMAINS[domain]
        if source_kind not in allow:
            raise SourceDetectionError(f"Source '{source_kind}' blocked by --allow-sources")
        inputs.append(IngestInput(source_kind, url))

    if not inputs:
        raise SourceDetectionError("No valid inputs provided. Use --url or --file.")

    return inputs
