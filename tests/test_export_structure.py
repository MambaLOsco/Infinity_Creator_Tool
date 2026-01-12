"""Tests for export structure creation."""
from __future__ import annotations

from pathlib import Path

from creatorpack.app_cli.outputs.packaging import build_export_structure


def test_build_export_structure_creates_dirs(tmp_path: Path) -> None:
    ctx = build_export_structure(tmp_path, "job-abc123")
    assert ctx.root.exists()
    assert ctx.input_dir.exists()
    assert ctx.transcript_dir.exists()
    assert ctx.chapters_dir.exists()
    assert ctx.highlights_dir.exists()
    assert ctx.branded_dir.exists()
    assert ctx.manifests_dir.exists()
    assert ctx.logs_dir.exists()
