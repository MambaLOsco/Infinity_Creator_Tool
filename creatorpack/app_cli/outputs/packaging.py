"""Packaging utilities for CreatorPack outputs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable

from ..util.io import ensure_dir, slugify, write_json, write_text


@dataclass
class ExportContext:
    """Holds context for an export job."""

    base_dir: Path
    slug: str

    @property
    def root(self) -> Path:
        return self.base_dir / self.slug

    @property
    def chapters_dir(self) -> Path:
        return self.root / "chapters"

    @property
    def shorts_dir(self) -> Path:
        return self.root / "shorts" / "9x16"

    @property
    def audio_dir(self) -> Path:
        return self.root / "audio"


def create_context(title: str, base_dir: Path) -> ExportContext:
    slug = slugify(title)
    ctx = ExportContext(base_dir=ensure_dir(base_dir), slug=slug)
    ensure_dir(ctx.root)
    ensure_dir(ctx.chapters_dir)
    ensure_dir(ctx.shorts_dir)
    ensure_dir(ctx.audio_dir)
    return ctx


def write_provenance(ctx: ExportContext, metadata: Dict[str, str]) -> None:
    payload = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        **metadata,
    }
    write_json(ctx.root / "provenance.json", payload)


def write_transcript(ctx: ExportContext, payload: dict) -> None:
    write_json(ctx.root / "transcript.json", payload)


def write_chapters(ctx: ExportContext, payload: dict) -> None:
    write_json(ctx.root / "chapters.json", payload)


def write_assets_map(ctx: ExportContext, payload: dict) -> None:
    write_json(ctx.root / "assets.map.json", payload)


def write_summary(ctx: ExportContext, markdown: str) -> None:
    write_text(ctx.root / "summary.md", markdown)


def write_credits(ctx: ExportContext, credits: str) -> None:
    write_text(ctx.root / "CREDITS.md", credits)


def write_job_log(ctx: ExportContext, lines: Iterable[str]) -> None:
    write_text(ctx.root / "job.log.jsonl", "".join(lines))
