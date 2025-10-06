"""Wikimedia Commons adapter."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode, urlparse

import requests

from ..util.errors import DownloadError, LicenseError
from .license_gate import NormalizedLicense, normalize_license_code
from .sources import SourceAdapter, SourceMetadata


API_URL = "https://commons.wikimedia.org/w/api.php"


@dataclass
class WikimediaSource(SourceAdapter):
    """Adapter for Wikimedia Commons files."""

    def supports(self, url: str) -> bool:  # type: ignore[override]
        return "commons.wikimedia.org" in urlparse(url).netloc

    def probe(self, url: str) -> SourceMetadata:  # type: ignore[override]
        title = urlparse(url).path.split("/")[-1]
        params = {
            "action": "query",
            "titles": f"File:{title}",
            "prop": "imageinfo",
            "iiprop": "extmetadata|url",
            "format": "json",
            "formatversion": "2",
        }
        response = requests.get(API_URL, params=params, timeout=15)
        if response.status_code != 200:
            raise DownloadError("Wikimedia API request failed")
        payload = response.json()
        try:
            page = payload["query"]["pages"][0]
            info = page["imageinfo"][0]
            metadata = info["extmetadata"]
        except (KeyError, IndexError) as exc:
            raise DownloadError("Malformed Wikimedia API response") from exc

        license_short = metadata.get("LicenseShortName", {}).get("value")
        license_url = metadata.get("LicenseUrl", {}).get("value", url)
        normalized = normalize_license_code(license_short)
        if normalized not in {
            NormalizedLicense.CC0,
            NormalizedLicense.CC_BY,
            NormalizedLicense.PUBLIC_DOMAIN,
        }:
            raise LicenseError("Wikimedia asset must be CC0/CC-BY/Public Domain")

        artist = metadata.get("Artist", {}).get("value", "Unknown Creator")
        description = metadata.get("ImageDescription", {}).get("value")

        return SourceMetadata(
            url=url,
            title=metadata.get("ObjectName", {}).get("value", title),
            creator=artist,
            license_name=license_short or "Unknown",
            license_url=license_url,
            license_code=normalized or NormalizedLicense.CC0,
            description=description,
        )
