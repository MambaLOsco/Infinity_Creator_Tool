from __future__ import annotations

import json
from pathlib import Path

import pytest

from creatorpack.app_cli import bundle
from creatorpack.app_cli.util.errors import CreatorPackError


def test_create_bundle_generates_structure(tmp_path: Path) -> None:
    destination = tmp_path / "bundle"
    result = bundle.create_bundle(destination, archive=False)
    assert destination.exists()
    assert result.root == destination.resolve()
    assert (destination / "README.md").exists()
    assert (destination / "INSTALL.md").exists()
    manifest_path = destination / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "creatorpack" in manifest["included"]
    assert manifest["archive"] is None


def test_create_bundle_force_overwrites(tmp_path: Path) -> None:
    destination = tmp_path / "bundle"
    bundle.create_bundle(destination)
    marker = destination / "marker.txt"
    marker.write_text("keep?", encoding="utf-8")
    bundle.create_bundle(destination, force=True)
    assert not marker.exists()


@pytest.mark.parametrize("create_archive", [False, True])
def test_create_bundle_archive_flag(tmp_path: Path, create_archive: bool) -> None:
    destination = tmp_path / "bundle_archive"
    result = bundle.create_bundle(destination, archive=create_archive)
    if create_archive:
        assert result.archive is not None
        assert result.archive.exists()
    else:
        assert result.archive is None


def test_create_bundle_without_force_errors(tmp_path: Path) -> None:
    destination = tmp_path / "bundle"
    bundle.create_bundle(destination)
    with pytest.raises(CreatorPackError):
        bundle.create_bundle(destination)
