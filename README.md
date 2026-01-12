# CreatorPack (local)

CreatorPack is a local-first content creation toolkit for desktop workflows. The core pipeline is
implemented in Python with a minimal Tauri wrapper for a desktop experience. All media processing and
transcription runs on the host machine—no network calls are required during production use.

## Features

- Validate input licenses for local or allowlisted public domain/open media sources.
- Transcribe audio/video using [`faster-whisper`](https://github.com/guillaumekln/faster-whisper) with an
  offline fallback.
- Slice content into fixed or sentence-aligned chapters and generate optional highlight clips.
- Apply light branding (watermark overlay) defined in a YAML theme.
- Export transcripts, chapter manifests, asset maps, credits, and provenance receipts.
- Log structured job information to `job.log.jsonl` for compliance.

## Installation

### Prerequisites

- Python 3.11
- [`ffmpeg`](https://ffmpeg.org/) and `ffprobe`
- Optional GPU support for faster-whisper

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

The development extras install the CLI, pytest, and tooling required for local tests.

## Quickstart

```bash
creatorpack run --file /path/to/video.mp4 --template creator-pack --minutes 10 --smart --highlights \
  --brand examples/brand_default.yaml --out exports
```

Exports are written under `exports/creator-pack/` by default.

## Packaging

Use PyInstaller to bundle the CLI into a standalone binary:

```bash
pyinstaller creatorpack.spec
```

The resulting distributables live under `dist/`.

## Desktop UI (Tauri)

The `ui_tauri` folder contains a minimal Tauri application. The Rust backend spawns the `creatorpack`
CLI and streams JSON logs to the webview. The frontend lists jobs, allows picking local files or URLs,
and renders progress updates.

## Tests

Run the unit tests with:

```bash
pytest
```

## Known Limitations

- Remote source adapters (Pexels, NASA, etc.) are not yet implemented in this offline reference build.
- Highlight scoring uses lightweight heuristics and may not reflect actual engagement metrics.
- Translation/localisation is not yet available.
