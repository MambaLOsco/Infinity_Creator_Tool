"""Local file ingestion."""
from __future__ import annotations

from pathlib import Path

from .license_gate import NormalizedLicense
from .sources import SourceAdapter, SourceMetadata


class LocalSource(SourceAdapter):
    """Adapter that accepts user provided local files."""

    def supports(self, url: str) -> bool:  # type: ignore[override]
        return True

    def probe(self, url: str) -> SourceMetadata:  # type: ignore[override]
        path = Path(url)
        if not path.exists():
            raise FileNotFoundError(f"Local file not found: {path}")
        title = path.stem.replace("_", " ")
        return SourceMetadata(
            url=path.as_uri(),
            title=title,
            creator="User Provided",
            license_name="User Provided",
            license_url="",
            license_code=NormalizedLicense.USER_PROVIDED,
            description=None,
            local_path=path,
        )
