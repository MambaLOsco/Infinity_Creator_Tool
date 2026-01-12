"""Command line entrypoint for CreatorPack."""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import click

from .ingest.sources import IngestInput, detect_input_sources
from .ingest.license_gate import LicenseGate
from .ingest.downloader import download_inputs
from .media.chunking import ChapterPolicy, build_chapter_plan, chapters_to_segments
from .media.ffmpeg_ops import (
    ChunkOutput,
    MediaSegment,
    chunk_media,
    plan_chunk_outputs,
    probe_media,
)
from .nlp.highlights import HighlightPlan, HighlightPolicy, score_highlights
from .branding.theme import BrandTheme, load_brand_theme
from .outputs.packaging import (
    ExportContext,
    build_export_structure,
    write_assets_map,
    write_highlights_manifest,
)
from .outputs.credits import CreditsBuilder
from .stt.transcribe import TranscriptResult, transcribe_media
from .util.errors import CreatorPackError, ExitCodes
from .util.job import compute_job_id
from .util.io import dump_json
from .util.logging import configure_logging, job_logger
from .util.preflight import run_preflight


LOGGER = logging.getLogger(__name__)


@dataclass
class RunOptions:
    """Container for parsed CLI options."""

    inputs: List[IngestInput]
    template: str
    minutes: int
    smart: bool
    highlights: bool
    highlight_policy: HighlightPolicy
    brand_path: Optional[Path]
    localize: Optional[str]
    diarize: bool
    output_dir: Path
    allow_sources: List[str]
    block_nc_nd: bool
    dry_run: bool
    job_id: str


@click.group()
@click.version_option()
def cli() -> None:
    """Root CLI group."""


@cli.command("run")
@click.option("--url", "urls", multiple=True, help="Media URL from an allowlisted source.")
@click.option("--file", "files", multiple=True, type=click.Path(exists=True, path_type=Path), help="Local media file")
@click.option("--template", type=click.Choice(["creator-pack", "podcast", "chapters-only", "shorts-only"]), default="creator-pack")
@click.option("--minutes", type=click.IntRange(min=1, max=180), default=10)
@click.option("--smart", is_flag=True, default=False, help="Use sentence-aligned chapter boundaries")
@click.option("--highlights", is_flag=True, default=False, help="Generate 60-90 second highlights")
@click.option("--highlights-top-k", type=click.IntRange(min=1, max=20), default=3)
@click.option("--highlights-min-seconds", type=click.FloatRange(min=5.0, max=180.0), default=60.0)
@click.option("--highlights-max-seconds", type=click.FloatRange(min=5.0, max=300.0), default=90.0)
@click.option("--highlights-padding-seconds", type=click.FloatRange(min=0.0, max=30.0), default=2.0)
@click.option("--brand", "brand_path", type=click.Path(exists=True, path_type=Path))
@click.option("--localize", type=str, default=None, help="Comma separated list of locales to translate captions into")
@click.option("--diarize", is_flag=True, default=False)
@click.option("--out", "output_dir", type=click.Path(file_okay=False, path_type=Path), default=Path("exports"))
@click.option("--allow-sources", default="pexels,nasa,commons,europeana,archive,local", show_default=True)
@click.option("--block-nc-nd/--no-block-nc-nd", default=True)
@click.option("--dry-run", is_flag=True, default=False, help="Write manifests/logs only (skip ffmpeg renders)")
def run_command(
    urls: Iterable[str],
    files: Iterable[Path],
    template: str,
    minutes: int,
    smart: bool,
    highlights: bool,
    highlights_top_k: int,
    highlights_min_seconds: float,
    highlights_max_seconds: float,
    highlights_padding_seconds: float,
    brand_path: Optional[Path],
    localize: Optional[str],
    diarize: bool,
    output_dir: Path,
    allow_sources: str,
    block_nc_nd: bool,
    dry_run: bool,
) -> None:
    """Execute the CreatorPack workflow."""

    allow_sources_list = [item.strip() for item in allow_sources.split(",") if item.strip()]
    inputs = detect_input_sources(list(urls), list(files), allow_sources_list)
    run_preflight(inputs)

    highlight_policy = HighlightPolicy(
        top_k=highlights_top_k,
        min_seconds=highlights_min_seconds,
        max_seconds=highlights_max_seconds,
        padding_seconds=highlights_padding_seconds,
    )
    job_id = compute_job_id(
        inputs,
        template=template,
        minutes=minutes,
        smart=smart,
        highlights=highlights,
        highlight_config=highlight_policy.__dict__,
        brand_path=brand_path,
        diarize=diarize,
        localize=localize,
    )

    options = RunOptions(
        inputs=inputs,
        template=template,
        minutes=minutes,
        smart=smart,
        highlights=highlights,
        highlight_policy=highlight_policy,
        brand_path=brand_path,
        localize=localize,
        diarize=diarize,
        output_dir=output_dir,
        allow_sources=allow_sources_list,
        block_nc_nd=block_nc_nd,
        dry_run=dry_run,
        job_id=job_id,
    )

    try:
        _run_pipeline(options)
    except CreatorPackError as exc:
        job_logger().error("job_failed", extra={"error": str(exc)})
        raise SystemExit(exc.exit_code) from exc


def _run_pipeline(options: RunOptions) -> None:
    license_gate = LicenseGate(block_nc_nd=options.block_nc_nd)
    brand: Optional[BrandTheme] = load_brand_theme(options.brand_path) if options.brand_path else None

    export_ctx = build_export_structure(options.output_dir, options.job_id)
    configure_logging(export_ctx.logs_dir)
    job_logger().info(
        "job_started",
        extra={"job_id": options.job_id, "template": options.template, "dry_run": options.dry_run},
    )

    download_results = download_inputs(options.inputs, export_ctx.input_dir, license_gate)
    job_logger().info("inputs_downloaded", extra={"count": len(download_results)})

    transcripts: List[TranscriptResult] = []
    credits_builder = CreditsBuilder()

    for download in download_results:
        license_gate.ensure_allowed(download.license_info)
        if download.license_info.requires_attribution:
            credits_builder.add_entry(download.license_info)

        probe = probe_media(download.path)
        job_logger().info("media_probed", extra={"probe": asdict(probe)})
        transcript = transcribe_media(download.path, diarize=options.diarize)
        transcripts.append(transcript)
        dump_json(transcript.to_dict(), export_ctx.transcript_dir / "transcript.json")
        (export_ctx.transcript_dir / "transcript.txt").write_text(transcript.to_text(), encoding="utf-8")

        chapter_policy = ChapterPolicy(
            target_seconds=options.minutes * 60,
            alignment="sentence" if options.smart else "fixed",
            allow_smart=options.smart,
        )
        chapter_plan = build_chapter_plan(transcript, probe.duration, chapter_policy)
        dump_json(chapter_plan.to_dict(), export_ctx.manifests_dir / "chapters.json")

        chapter_segments = chapters_to_segments(chapter_plan.chapters)
        if options.dry_run:
            chunk_outputs = plan_chunk_outputs(download.path, export_ctx.chapters_dir, chapter_segments)
        else:
            chunk_outputs = chunk_media(
                download.path,
                export_ctx.chapters_dir,
                chapter_segments,
            )
        branded_chapters: List[ChunkOutput] = []
        if brand:
            if options.dry_run:
                branded_chapters = plan_chunk_outputs(
                    download.path, export_ctx.branded_chapters_dir, chapter_segments
                )
            else:
                branded_chapters = chunk_media(
                    download.path,
                    export_ctx.branded_chapters_dir,
                    chapter_segments,
                    brand=brand,
                )

        highlight_plan: Optional[HighlightPlan] = None
        highlight_outputs: List[ChunkOutput] = []
        if options.highlights:
            highlight_plan = score_highlights(transcript, probe.duration, options.highlight_policy)
            highlight_segments = [
                MediaSegment(start=h.start, end=h.end, caption=h.caption)
                for h in highlight_plan.highlights
            ]
            if options.dry_run:
                highlight_outputs = plan_chunk_outputs(
                    download.path, export_ctx.highlights_dir, highlight_segments, short_mode=True
                )
            else:
                highlight_outputs = chunk_media(
                    download.path,
                    export_ctx.highlights_dir,
                    highlight_segments,
                    short_mode=True,
                )
        branded_highlights: List[ChunkOutput] = []
        if brand and highlight_plan:
            highlight_segments = [
                MediaSegment(start=h.start, end=h.end, caption=h.caption)
                for h in highlight_plan.highlights
            ]
            if options.dry_run:
                branded_highlights = plan_chunk_outputs(
                    download.path, export_ctx.branded_highlights_dir, highlight_segments, short_mode=True
                )
            else:
                branded_highlights = chunk_media(
                    download.path,
                    export_ctx.branded_highlights_dir,
                    highlight_segments,
                    brand=brand,
                    short_mode=True,
                )

        write_highlights_manifest(export_ctx, highlight_plan, highlight_outputs)

        write_assets_map(
            export_ctx,
            download,
            chunk_outputs,
            highlight_plan,
            highlight_outputs,
            branded_chapters=branded_chapters,
            branded_highlights=branded_highlights,
        )

        provenance_path = export_ctx.manifests_dir / "provenance.json"
        provenance_data = {
            "source": download.source,
            "license": download.license_info.to_dict(),
            "retrieved_at": download.retrieved_at.isoformat(),
            "original_filename": download.original_name,
        }
        dump_json(provenance_data, provenance_path)

    if credits_builder:
        credits_path = export_ctx.manifests_dir / "CREDITS.md"
        credits_path.write_text(credits_builder.render_markdown(), encoding="utf-8")
        dump_json(credits_builder.to_dict(), export_ctx.manifests_dir / "credits.json")
    else:
        dump_json({"entries": []}, export_ctx.manifests_dir / "credits.json")

    summary_path = export_ctx.manifests_dir / "summary.md"
    summary_path.write_text(_render_summary(transcripts), encoding="utf-8")
    dump_json(
        {
            "job_id": options.job_id,
            "template": options.template,
            "dry_run": options.dry_run,
            "inputs": [item.value for item in options.inputs],
        },
        export_ctx.manifests_dir / "job.json",
    )

    job_logger().info("job_completed", extra={"outputs": str(export_ctx.root)})


def _render_summary(transcripts: List[TranscriptResult]) -> str:
    bullets = []
    for transcript in transcripts:
        first_segment = transcript.segments[0] if transcript.segments else None
        text = first_segment.text if first_segment else """No transcript available."""
        bullets.append(f"- Segment starting at {first_segment.start:.2f}s: {text}" if first_segment else "- No transcript")
    bullets.append("- CTA: Subscribe for more updates from CreatorPack!")
    return "Summary\n======\n\n" + "\n".join(bullets) + "\n"


if __name__ == "__main__":
    cli()
