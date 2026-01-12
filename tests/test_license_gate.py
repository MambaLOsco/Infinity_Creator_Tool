"""Tests for the LicenseGate enforcement rules."""
from __future__ import annotations

import pytest

from creatorpack.app_cli.ingest.license_gate import LicenseGate, LicenseViolationError


def test_allows_pd_license() -> None:
    gate = LicenseGate()
    info = gate.build_info(source="local", title="Test", creator=None, license_code="pd", license_url=None)
    assert info.license_code == "pd"


def test_blocks_nc_license() -> None:
    gate = LicenseGate(block_nc_nd=True)
    with pytest.raises(LicenseViolationError):
        gate.build_info(source="local", title="Test", creator=None, license_code="cc-by-nc", license_url=None)
