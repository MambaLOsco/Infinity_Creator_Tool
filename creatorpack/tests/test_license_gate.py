"""Tests for the license gate module."""
from __future__ import annotations

import pytest

from creatorpack.app_cli.ingest.license_gate import (
    LicenseError,
    NormalizedLicense,
    guard_license,
)


def test_nc_license_blocked() -> None:
    with pytest.raises(LicenseError):
        guard_license(
            code="cc-by",
            name="CC-BY-NC",
            url="https://example.com/license",
            block_nc_nd=True,
        )


def test_allowed_license_passes() -> None:
    probe = guard_license(
        code="cc0",
        name="CC0",
        url="https://example.com/license",
    )
    assert probe.code == NormalizedLicense.CC0
    assert not probe.attribution_required
