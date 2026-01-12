"""Export structure helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..ingest.downloader import DownloadResult
from ..media.ffmpeg_ops import ChunkOutput
from ..nlp.highlights import HighlightPlan
from ..util.io import dump_json


@dataclass
class ExportContext:
    root: Path
    chapters_dir: Path
    shorts_dir: Path
    audio_dir: Path


def build_export_structure(output_dir: Path, template: str) -> ExportContext:
    slug = template.replace(" ", "-")
    root = (output_dir / slug).resolve()
    chapters_dir = root / "chapters"
    shorts_dir = root / "shorts" / "9x16"
    audio_dir = root / "audio"
    for directory in (chapters_dir, shorts_dir, audio_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return ExportContext(root=root, chapters_dir=chapters_dir, shorts_dir=shorts_dir, audio_dir=audio_dir)


def write_assets_map(
    ctx: ExportContext,
    download: DownloadResult,
    chapter_outputs: List[ChunkOutput],
    highlight_plan: Optional[HighlightPlan],
    highlight_outputs: Optional[List[ChunkOutput]] = None,
) -> None:
    assets = {
        "source": download.original_name,
        "chunks": [
            {
                "file": output.file.name,
                "srt": output.file.with_suffix(".srt").name,
                "start": output.start,
                "end": output.end,
            }
            for output in chapter_outputs
        ],
        "shorts": [],
    }
    if highlight_plan and highlight_outputs:
        assets["shorts"] = [
            {
                "file": output.file.name,
                "start": highlight.start,
                "end": highlight.end,
                "caption": highlight.caption,
            }
            for output, highlight in zip(highlight_outputs, highlight_plan.highlights)
        ]
    dump_json(assets, ctx.root / "assets.map.json")
