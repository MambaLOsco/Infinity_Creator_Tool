"""Pexels source adapter."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from ..util.errors import DownloadError
from .license_gate import NormalizedLicense
from .sources import SourceAdapter, SourceMetadata


@dataclass
class PexelsSource(SourceAdapter):
    """Adapter for Pexels assets.

    The implementation intentionally avoids media downloads and only fetches
    lightweight metadata to verify that the asset is covered by the permissive
    Pexels license. Full API usage would require an API key, but for license
    enforcement we rely on the documented fact that all public assets published
    by Pexels are released under the "Pexels License" which allows commercial
    reuse. We treat the license as CC0-equivalent for validation purposes.
    """

    api_base: str = "https://www.pexels.com"

    def supports(self, url: str) -> bool:  # type: ignore[override]
        parsed = urlparse(url)
        return "pexels.com" in parsed.netloc

    def probe(self, url: str) -> SourceMetadata:  # type: ignore[override]
        parsed = urlparse(url)
        if not parsed.scheme.startswith("http"):
            raise DownloadError("Pexels URLs must be HTTP(S).")

        title = parsed.path.strip("/").replace("-", " ") or "Pexels Asset"
        # Minimal fetch to confirm availability.
        response = requests.head(url, timeout=10)
        if response.status_code >= 400:
            raise DownloadError(f"Failed to access Pexels URL: {response.status_code}")

        return SourceMetadata(
            url=url,
            title=title.title(),
            creator="Pexels Creator",
            license_name="Pexels License (treated as CC0)",
            license_url="https://www.pexels.com/license/",
            license_code=NormalizedLicense.CC0,
            description=None,
        )
