"""Europeana adapter."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from ..util.errors import DownloadError, LicenseError
from .license_gate import NormalizedLicense, normalize_license_code
from .sources import SourceAdapter, SourceMetadata


@dataclass
class EuropeanaSource(SourceAdapter):
    """Adapter for Europeana items with reuse-permitted rights."""

    def supports(self, url: str) -> bool:  # type: ignore[override]
        return "europeana.eu" in urlparse(url).netloc

    def probe(self, url: str) -> SourceMetadata:  # type: ignore[override]
        if "api" not in url:
            raise DownloadError(
                "Provide a Europeana API record URL (https://api.europeana.eu/...)."
            )
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            raise DownloadError("Europeana record fetch failed")
        data = response.json()
        title = data.get("title", ["Europeana Asset"])[0]
        rights = data.get("rights", [])
        if not rights:
            raise LicenseError("Europeana record missing rights metadata")
        license_url = rights[0]
        normalized = normalize_license_code(license_url.split("/")[-2] if "/" in license_url else None)
        if normalized not in {
            NormalizedLicense.CC0,
            NormalizedLicense.CC_BY,
            NormalizedLicense.PUBLIC_DOMAIN,
        }:
            raise LicenseError("Europeana asset must permit reuse (CC0/CC-BY/PD)")
        creator = data.get("dcCreator", ["Unknown"])[0]
        description = (data.get("dcDescription") or [None])[0]
        return SourceMetadata(
            url=url,
            title=title,
            creator=creator,
            license_name=normalized.value if normalized else "Unknown",
            license_url=license_url,
            license_code=normalized or NormalizedLicense.CC0,
            description=description,
        )
