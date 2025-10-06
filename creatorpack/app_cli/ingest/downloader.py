"""HTTP downloader with checksum support."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

import requests

from ..util.errors import DownloadError
from ..util.io import ensure_dir
from .sources import SourceMetadata


DEFAULT_CHUNK_SIZE = 1024 * 1024


def download_to_path(metadata: SourceMetadata, dest_dir: Path) -> Path:
    """Download a remote asset or copy a local file into *dest_dir*."""
    ensure_dir(dest_dir)
    if metadata.local_path:
        target = dest_dir / metadata.local_path.name
        shutil.copy2(metadata.local_path, target)
        return target

    parsed = urlparse(metadata.url)
    filename = Path(parsed.path).name or "download.bin"
    target = dest_dir / filename
    response = requests.get(metadata.url, stream=True, timeout=30)
    if response.status_code >= 400:
        raise DownloadError(f"Failed to download asset: HTTP {response.status_code}")
    with target.open("wb") as fh:
        for chunk in response.iter_content(DEFAULT_CHUNK_SIZE):
            fh.write(chunk)
    return target


def compute_checksum(path: Path, algorithm: str = "sha256") -> str:
    """Compute the checksum for *path*."""
    hasher = hashlib.new(algorithm)
    with path.open("rb") as fh:
        while True:
            data = fh.read(DEFAULT_CHUNK_SIZE)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()
