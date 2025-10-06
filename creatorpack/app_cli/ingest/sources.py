"""Source detection and metadata loading."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Protocol
from urllib.parse import urlparse

from . import pexels, nasa, commons, europeana, archive
from .license_gate import NormalizedLicense
from .local import LocalSource


@dataclass
class SourceMetadata:
    """Describes an ingested source."""

    url: str
    title: str
    creator: str
    license_name: str
    license_url: str
    license_code: NormalizedLicense
    description: Optional[str] = None
    local_path: Optional[Path] = None


class SourceAdapter(Protocol):
    """Protocol describing a metadata adapter."""

    def supports(self, url: str) -> bool:
        ...

    def probe(self, url: str) -> SourceMetadata:
        ...


ADAPTERS: Dict[str, SourceAdapter] = {
    "pexels": pexels.PexelsSource(),
    "nasa": nasa.NasaSource(),
    "commons": commons.WikimediaSource(),
    "europeana": europeana.EuropeanaSource(),
    "archive": archive.InternetArchiveSource(),
    "local": LocalSource(),
}


def detect_adapter(url_or_path: str) -> SourceAdapter:
    """Return the best adapter for *url_or_path*."""
    _, adapter = detect_adapter_with_name(url_or_path)
    return adapter


def detect_adapter_with_name(url_or_path: str) -> tuple[str, SourceAdapter]:
    """Return the adapter name and instance for *url_or_path*."""
    parsed = urlparse(url_or_path)
    if parsed.scheme in {"", "file"}:
        return "local", ADAPTERS["local"]

    for name, adapter in ADAPTERS.items():
        if adapter.supports(url_or_path):
            return name, adapter
    raise ValueError(f"No adapter available for URL: {url_or_path}")


__all__ = [
    "SourceMetadata",
    "SourceAdapter",
    "detect_adapter",
    "detect_adapter_with_name",
    "ADAPTERS",
]
