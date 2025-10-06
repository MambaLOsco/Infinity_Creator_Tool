"""Internet Archive adapter."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from ..util.errors import DownloadError, LicenseError
from .license_gate import NormalizedLicense, normalize_license_code
from .sources import SourceAdapter, SourceMetadata


@dataclass
class InternetArchiveSource(SourceAdapter):
    """Adapter for Internet Archive items limited to reuse-friendly licenses."""

    api_base = "https://archive.org/metadata/"

    def supports(self, url: str) -> bool:  # type: ignore[override]
        return "archive.org" in urlparse(url).netloc

    def probe(self, url: str) -> SourceMetadata:  # type: ignore[override]
        path = urlparse(url).path.strip("/")
        if not path:
            raise DownloadError("Archive URL missing identifier")
        identifier = path.split("/")[0]
        response = requests.get(f"{self.api_base}{identifier}", timeout=15)
        if response.status_code != 200:
            raise DownloadError("Archive metadata fetch failed")
        data = response.json()
        metadata = data.get("metadata", {})
        title = metadata.get("title", identifier)
        creator = metadata.get("creator", "Unknown")
        license_url = metadata.get("licenseurl") or metadata.get("license")
        normalized = normalize_license_code(
            license_url.split("/")[-1] if isinstance(license_url, str) else None
        )
        if normalized not in {
            NormalizedLicense.CC0,
            NormalizedLicense.CC_BY,
            NormalizedLicense.PUBLIC_DOMAIN,
        }:
            raise LicenseError("Internet Archive item must be CC0/CC-BY/PD")
        return SourceMetadata(
            url=url,
            title=title,
            creator=creator,
            license_name=license_url or "Unknown",
            license_url=license_url or url,
            license_code=normalized or NormalizedLicense.CC0,
            description=metadata.get("description"),
        )
