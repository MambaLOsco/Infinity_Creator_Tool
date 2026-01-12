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
    input_dir: Path
    transcript_dir: Path
    chapters_dir: Path
    highlights_dir: Path
    branded_dir: Path
    branded_chapters_dir: Path
    branded_highlights_dir: Path
    manifests_dir: Path
    logs_dir: Path


def build_export_structure(output_dir: Path, job_id: str) -> ExportContext:
    root = (output_dir / job_id).resolve()
    input_dir = root / "input"
    transcript_dir = root / "transcript"
    chapters_dir = root / "chapters"
    highlights_dir = root / "highlights"
    branded_dir = root / "branded"
    branded_chapters_dir = branded_dir / "chapters"
    branded_highlights_dir = branded_dir / "highlights"
    manifests_dir = root / "manifests"
    logs_dir = root / "logs"
    for directory in (
        input_dir,
        transcript_dir,
        chapters_dir,
        highlights_dir,
        branded_dir,
        branded_chapters_dir,
        branded_highlights_dir,
        manifests_dir,
        logs_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return ExportContext(
        root=root,
        input_dir=input_dir,
        transcript_dir=transcript_dir,
        chapters_dir=chapters_dir,
        highlights_dir=highlights_dir,
        branded_dir=branded_dir,
        branded_chapters_dir=branded_chapters_dir,
        branded_highlights_dir=branded_highlights_dir,
        manifests_dir=manifests_dir,
        logs_dir=logs_dir,
    )


def write_assets_map(
    ctx: ExportContext,
    download: DownloadResult,
    chapter_outputs: List[ChunkOutput],
    highlight_plan: Optional[HighlightPlan],
    highlight_outputs: Optional[List[ChunkOutput]] = None,
    branded_chapters: Optional[List[ChunkOutput]] = None,
    branded_highlights: Optional[List[ChunkOutput]] = None,
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
    if branded_chapters:
        assets["branded_chapters"] = [
            {"file": output.file.name, "start": output.start, "end": output.end} for output in branded_chapters
        ]
    if branded_highlights:
        assets["branded_highlights"] = [
            {"file": output.file.name, "start": output.start, "end": output.end} for output in branded_highlights
        ]
    dump_json(assets, ctx.manifests_dir / "assets.map.json")


def write_highlights_manifest(
    ctx: ExportContext,
    highlight_plan: Optional[HighlightPlan],
    highlight_outputs: Optional[List[ChunkOutput]],
) -> None:
    data = {
        "highlights": [],
    }
    if highlight_plan and highlight_outputs:
        data["highlights"] = [
            {
                "file": output.file.name,
                "start": highlight.start,
                "end": highlight.end,
                "caption": highlight.caption,
            }
            for output, highlight in zip(highlight_outputs, highlight_plan.highlights)
        ]
    dump_json(data, ctx.manifests_dir / "highlights.json")
