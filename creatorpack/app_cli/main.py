"""CLI entry point for CreatorPack."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

from .branding.theme import load_theme
from .ingest.downloader import compute_checksum, download_to_path
from .ingest.license_gate import guard_license
from .ingest.sources import detect_adapter_with_name
from .media import ffmpeg_ops
from .media.chunking import Chunk
from .nlp import chapters as chapters_module
from .nlp import highlights as highlights_module
from .nlp import summarize as summarize_module
from .outputs import credits as credits_module
from .outputs import packaging
from .stt import transcribe as transcribe_module
from .util.errors import CreatorPackError
from .util.logging import get_logger


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CreatorPack CLI")
    parser.add_argument("run", help="Run the processing pipeline", nargs="?")
    parser.add_argument("inputs", nargs="*", help="Input URLs or files")
    parser.add_argument("--url", action="append", dest="urls")
    parser.add_argument("--file", action="append", dest="files")
    parser.add_argument("--template", default="creator-pack")
    parser.add_argument("--minutes", type=int, default=10, choices=[10, 15])
    parser.add_argument("--smart", action="store_true")
    parser.add_argument("--highlights", action="store_true")
    parser.add_argument("--brand")
    parser.add_argument("--localize")
    parser.add_argument("--diarize", action="store_true")
    parser.add_argument("--out", default="exports")
    parser.add_argument(
        "--allow-sources",
        default="pexels,nasa,commons,europeana,archive,local",
    )
    parser.add_argument("--block-nc-nd", action="store_true", default=True)
    return parser.parse_args(argv)


def _collect_inputs(args: argparse.Namespace) -> List[str]:
    inputs = []
    if args.urls:
        inputs.extend(args.urls)
    if args.files:
        inputs.extend(args.files)
    if args.inputs and args.inputs[0] != "run":
        inputs.extend(args.inputs)
    return inputs


def _validate_sources(source_name: str, allow_sources: Iterable[str]) -> None:
    if source_name not in allow_sources:
        raise CreatorPackError(
            f"Source '{source_name}' is not in the allow-list. Use --allow-sources to permit it."
        )


def _chapter_payload(chapters: List[chapters_module.Chapter], minutes: int, align: bool) -> dict:
    return {
        "policy": {"target_sec": minutes * 60, "alignment": "sentence" if align else "fixed"},
        "chapters": [
            {"i": chap.index, "start": chap.start, "end": chap.end, "title": chap.title}
            for chap in chapters
        ],
    }


def _assets_payload(
    *,
    source: Path,
    chunks: List[Chunk],
    chunk_files: List[Path],
    highlight_files: List[tuple[Path, highlights_module.HighlightCandidate]],
) -> dict:
    chunk_payload = []
    for chunk, file in zip(chunks, chunk_files):
        chunk_payload.append(
            {
                "file": file.name,
                "srt": file.with_suffix(".srt").name,
                "start": chunk.start,
                "end": chunk.end,
            }
        )
    highlight_payload = []
    for path, candidate in highlight_files:
        highlight_payload.append(
            {
                "file": path.name,
                "start": candidate.start,
                "end": candidate.end,
                "caption": candidate.caption,
            }
        )
    return {
        "source": source.name,
        "chunks": chunk_payload,
        "shorts": highlight_payload,
    }


def _write_chunk_srts(chunk_files: List[Path], transcript: transcribe_module.Transcript) -> None:
    for file in chunk_files:
        srt_path = file.with_suffix(".srt")
        with srt_path.open("w", encoding="utf-8") as handle:
            index = 1
            for segment in transcript.segments:
                handle.write(f"{index}\n")
                handle.write("00:00:00,000 --> 00:00:10,000\n")
                handle.write(segment.text.strip() + "\n\n")
                index += 1


def _generate_highlights(
    transcript: transcribe_module.Transcript,
    highlights_dir: Path,
) -> List[tuple[Path, highlights_module.HighlightCandidate]]:
    candidates = highlights_module.score_candidates(transcript.segments)
    top_candidates = candidates[:1]
    outputs: List[tuple[Path, highlights_module.HighlightCandidate]] = []
    for index, candidate in enumerate(top_candidates, start=1):
        file = highlights_dir / f"highlight-{index:02d}.mp4"
        file.write_bytes(b"")
        outputs.append((file, candidate))
    return outputs


def run(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    inputs = _collect_inputs(args)
    if not inputs:
        raise SystemExit("Provide at least one --url or --file input")

    out_dir = Path(args.out)
    logger = get_logger()

    allow_sources = set(filter(None, (s.strip() for s in args.allow_sources.split(","))))
    input_path = inputs[0]
    source_name, adapter = detect_adapter_with_name(input_path)
    _validate_sources(source_name, allow_sources)
    metadata = adapter.probe(input_path)
    logger.info("source_metadata", data=json.dumps(metadata.__dict__, default=str))

    license_probe = guard_license(
        code=metadata.license_code.value,
        name=metadata.license_name,
        url=metadata.license_url,
        block_nc_nd=args.block_nc_nd,
    )

    if args.brand:
        load_theme(Path(args.brand))

    ctx = packaging.create_context(metadata.title, out_dir)
    downloads_dir = ctx.root / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    media_path = download_to_path(metadata, downloads_dir)
    checksum = compute_checksum(media_path)
    logger.info("download_complete", file=str(media_path), checksum=checksum)

    transcript = transcribe_module.transcribe_audio(media_path)
    packaging.write_transcript(ctx, transcript.as_dict())

    chapter_entries = chapters_module.build_chapters(
        transcript, minutes=args.minutes, align_sentences=args.smart
    )
    packaging.write_chapters(ctx, _chapter_payload(chapter_entries, args.minutes, args.smart))

    chunk_ranges = [(chapter.start, chapter.end) for chapter in chapter_entries]
    chunk_files = ffmpeg_ops.segment_media(media_path, chunk_ranges, ctx.chapters_dir)
    _write_chunk_srts(chunk_files, transcript)

    highlight_files: List[tuple[Path, highlights_module.HighlightCandidate]] = []
    if args.highlights:
        highlight_files = _generate_highlights(transcript, ctx.shorts_dir)

    assets_payload = _assets_payload(
        source=media_path,
        chunks=chapter_entries,
        chunk_files=chunk_files,
        highlight_files=highlight_files,
    )
    packaging.write_assets_map(ctx, assets_payload)

    chapter_starts = [chapter.start for chapter in chapter_entries]
    summary_bullets = summarize_module.build_summary(transcript, chapter_starts)
    summary_md = summarize_module.render_summary_md(summary_bullets)
    packaging.write_summary(ctx, summary_md)

    credit_lines = credits_module.build_credits(
        title=metadata.title,
        creator=metadata.creator,
        license_probe=license_probe,
        description=metadata.description,
    )
    packaging.write_credits(ctx, credits_module.render_credits(credit_lines))
    packaging.write_provenance(
        ctx,
        {
            "source_url": metadata.url,
            "license_name": metadata.license_name,
            "license_url": metadata.license_url,
        },
    )

    logger.info("job_completed", export_dir=str(ctx.root))
    return 0


def main() -> None:
    try:
        sys.exit(run())
    except CreatorPackError as exc:
        get_logger().error("job_failed", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
