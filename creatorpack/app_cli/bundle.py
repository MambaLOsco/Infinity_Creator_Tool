"""Utilities to create a self-contained CreatorPack bundle for local use."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .util.errors import CreatorPackError

_EXCLUDE_PATTERNS: tuple[str, ...] = (
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.tmp",
    "*.DS_Store",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".git",
)


@dataclass(frozen=True)
class BundleResult:
    """Metadata for the generated bundle."""

    root: Path
    archive: Path | None
    included: List[str]


def _project_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[2]


def _copytree(source: Path, destination: Path) -> None:
    """Copy a directory tree while ignoring transient files."""

    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*_EXCLUDE_PATTERNS),
    )


def _copy_path(source: Path, destination: Path) -> None:
    """Copy a file or directory into the destination folder."""

    if source.is_dir():
        _copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _write_install_guide(bundle_dir: Path) -> None:
    """Write instructions for running the bundle locally."""

    install_path = bundle_dir / "INSTALL.md"
    install_path.write_text(
        """# CreatorPack Local Bundle\n\n"
        "## Setup\n\n"
        "1. Install Python 3.11 and ffmpeg/ffprobe on your machine.\n"
        "2. (Optional) Install Node.js if you plan to launch the Tauri desktop shell.\n"
        "3. Create a virtual environment inside this folder: `python -m venv .venv`.\n"
        "4. Activate the environment and install the project locally: `pip install -e .`.\n"
        "5. (Optional) Install extra packages for GPU transcription: `pip install 'creatorpack[stt]'`.\n\n"
        "## Usage\n\n"
        "- Run the CLI: `creatorpack run --file path/to/video.mp4 --template creator-pack`.\n"
        "- Outputs appear in the `exports/` directory next to your bundle.\n"
        "- Launch the UI (optional): `cd creatorpack/ui_tauri && npm install && npm run tauri dev`.\n"
        """,
        encoding="utf-8",
    )


def _write_manifest(bundle_dir: Path, included: Iterable[str], archive: Path | None) -> None:
    """Emit metadata describing the bundle contents."""

    manifest = {
        "name": "CreatorPack Local Bundle",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "included": sorted(set(included)),
        "archive": archive.name if archive else None,
    }
    (bundle_dir / "bundle_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def create_bundle(destination: Path, *, archive: bool = False, force: bool = False) -> BundleResult:
    """Create a ready-to-distribute folder for local use.

    Args:
        destination: Target directory for the bundle.
        archive: When True, also create a `.zip` archive alongside the folder.
        force: When True, existing contents at the destination will be removed first.

    Returns:
        BundleResult with metadata describing the generated bundle.

    Raises:
        CreatorPackError: If the destination exists and ``force`` is False.
    """

    destination = destination.expanduser().resolve()
    project_root = _project_root()

    if destination.exists():
        if not force:
            raise CreatorPackError(
                f"Destination '{destination}' already exists. Use --force to overwrite."
            )
        shutil.rmtree(destination)

    destination.mkdir(parents=True, exist_ok=True)

    include_paths = [
        project_root / "README.md",
        project_root / "pyproject.toml",
        project_root / "creatorpack",
    ]

    included: List[str] = []
    for path in include_paths:
        if not path.exists():
            continue
        target = destination / path.relative_to(project_root)
        _copy_path(path, target)
        included.append(str(path.relative_to(project_root)))

    _write_install_guide(destination)

    archive_path: Path | None = None
    if archive:
        archive_base = destination.parent / destination.name
        archive_str = shutil.make_archive(str(archive_base), "zip", destination.parent, destination.name)
        archive_path = Path(archive_str)

    _write_manifest(destination, included, archive_path)

    return BundleResult(root=destination, archive=archive_path, included=included)


__all__ = ["BundleResult", "create_bundle"]
