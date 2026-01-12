"""License gate enforcement."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..util.errors import CreatorPackError, ExitCodes


ALLOWED_LICENSES = {
    "pd": False,
    "public-domain": False,
    "cc0": False,
    "cc-by": True,
    "cc-by-4.0": True,
    "cc-by-3.0": True,
    "iodl-2.0": True,
}


@dataclass
class LicenseInfo:
    """Metadata about a media asset's license."""

    source: str
    title: str
    creator: Optional[str]
    license_code: str
    license_url: Optional[str]
    requires_attribution: bool

    def to_dict(self) -> dict[str, Optional[str]]:
        return {
            "source": self.source,
            "title": self.title,
            "creator": self.creator,
            "license_code": self.license_code,
            "license_url": self.license_url,
            "requires_attribution": self.requires_attribution,
        }


class LicenseViolationError(CreatorPackError):
    """Raised when a license is not allowed."""

    exit_code = ExitCodes.LICENSE_BLOCKED


class LicenseGate:
    """Validates license metadata according to compliance policy."""

    def __init__(self, block_nc_nd: bool = True) -> None:
        self.block_nc_nd = block_nc_nd

    def ensure_allowed(self, info: LicenseInfo) -> None:
        license_code = info.license_code.lower().strip()
        if license_code.endswith("-sa") or license_code.endswith("-nc") or license_code.endswith("-nd"):
            raise LicenseViolationError(f"License '{info.license_code}' is not permitted")

        allowed = None
        for key, requires_attr in ALLOWED_LICENSES.items():
            if license_code == key:
                allowed = requires_attr
                break
        if allowed is None:
            raise LicenseViolationError(f"License '{info.license_code}' is not in the allowlist")

        if self.block_nc_nd and ("nc" in license_code or "nd" in license_code):
            raise LicenseViolationError("NC/ND licenses blocked by policy")

    def build_info(
        self,
        *,
        source: str,
        title: str,
        creator: Optional[str],
        license_code: str,
        license_url: Optional[str],
    ) -> LicenseInfo:
        normalized_code = license_code.lower().strip()
        requires_attr = ALLOWED_LICENSES.get(normalized_code, False)
        info = LicenseInfo(
            source=source,
            title=title,
            creator=creator,
            license_code=license_code,
            license_url=license_url,
            requires_attribution=requires_attr,
        )
        self.ensure_allowed(info)
        return info
