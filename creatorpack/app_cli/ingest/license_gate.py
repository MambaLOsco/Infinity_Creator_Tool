"""License validation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

from ..util.errors import LicenseError


class NormalizedLicense(str, Enum):
    """Normalized view of supported licenses."""

    CC_BY = "CC-BY"
    CC0 = "CC0"
    PUBLIC_DOMAIN = "PD"
    IODL2 = "IODL-2.0"
    USER_PROVIDED = "USER"


ALLOWED_LICENSES = {
    NormalizedLicense.CC_BY,
    NormalizedLicense.CC0,
    NormalizedLicense.PUBLIC_DOMAIN,
    NormalizedLicense.IODL2,
    NormalizedLicense.USER_PROVIDED,
}


@dataclass
class LicenseProbe:
    """Result of a license validation attempt."""

    code: NormalizedLicense
    name: str
    url: str
    attribution_required: bool


def normalize_license_code(code: str | None) -> Optional[NormalizedLicense]:
    """Normalize raw license strings to the internal enum."""
    if code is None:
        return None
    normalized = code.strip().lower()
    if normalized in {"cc-by", "cc_by", "creative commons attribution"}:
        return NormalizedLicense.CC_BY
    if normalized in {"cc0", "cc-0", "public domain", "pd"}:
        return NormalizedLicense.CC0
    if normalized in {"pd", "public-domain", "public domain mark", "pdm"}:
        return NormalizedLicense.PUBLIC_DOMAIN
    if normalized in {"iodl2", "iodl-2.0", "iodl 2.0"}:
        return NormalizedLicense.IODL2
    if normalized in {"user", "user-provided"}:
        return NormalizedLicense.USER_PROVIDED
    return None


def guard_license(
    *,
    code: str | None,
    name: str,
    url: str,
    block_nc_nd: bool = True,
    allow_codes: Iterable[NormalizedLicense] | None = None,
) -> LicenseProbe:
    """Validate a license tuple and return the normalized structure."""
    normalized = normalize_license_code(code)
    allow_set = set(allow_codes) if allow_codes is not None else ALLOWED_LICENSES
    if normalized is None or normalized not in allow_set:
        raise LicenseError(
            "Asset license is not allowed. Provide PD/CC0/CC-BY/IODL2 or a local file."
        )

    if block_nc_nd and "nc" in name.lower():
        raise LicenseError("Non-commercial licenses are not permitted.")
    if block_nc_nd and "nd" in name.lower():
        raise LicenseError("No-derivatives licenses are not permitted.")

    return LicenseProbe(
        code=normalized,
        name=name,
        url=url,
        attribution_required=normalized in {NormalizedLicense.CC_BY, NormalizedLicense.IODL2},
    )


__all__ = ["NormalizedLicense", "LicenseProbe", "guard_license", "normalize_license_code"]
