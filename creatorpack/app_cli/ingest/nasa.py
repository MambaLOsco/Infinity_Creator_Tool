"""NASA media adapter."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from ..util.errors import DownloadError
from .license_gate import NormalizedLicense
from .sources import SourceAdapter, SourceMetadata


@dataclass
class NasaSource(SourceAdapter):
    """Adapter for NASA public domain media."""

    allowed_hosts = {"images.nasa.gov", "www.nasa.gov"}

    def supports(self, url: str) -> bool:  # type: ignore[override]
        parsed = urlparse(url)
        return parsed.netloc in self.allowed_hosts

    def probe(self, url: str) -> SourceMetadata:  # type: ignore[override]
        response = requests.head(url, timeout=10)
        if response.status_code >= 400:
            raise DownloadError("NASA asset not reachable")
        title = urlparse(url).path.split("/")[-1] or "NASA Asset"
        return SourceMetadata(
            url=url,
            title=title.replace("-", " ").title(),
            creator="NASA",
            license_name="NASA Public Domain",
            license_url="https://www.nasa.gov/multimedia/guidelines/index.html",
            license_code=NormalizedLicense.PUBLIC_DOMAIN,
            description="NASA imagery is generally public domain but NASA logos must not be used.",
        )
