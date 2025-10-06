# CreatorPack (Local)

CreatorPack is a local-first desktop toolkit for compliant media repurposing. It combines a Python processing core
with a lightweight Tauri desktop shell so creators can ingest licensed footage, generate transcripts, chapters, and
short highlights, and export ready-to-publish packages without relying on the cloud.

## Features

- **License-aware ingestion** for local files, Pexels, NASA, Wikimedia Commons, Europeana, and Internet Archive assets.
- **Offline transcription pipeline** built on faster-whisper with a deterministic fallback for environments without GPUs.
- **Automatic chapterization** with optional sentence alignment and highlight extraction heuristics.
- **Branding support** driven by YAML themes for watermarks, intros/outros, and caption styles.
- **Export packaging** that emits MP4 chapters, caption sidecars, highlight placeholders, provenance receipts, and credit
  summaries suitable for CC-BY and IODL attribution requirements.

## Project Layout

```
creatorpack/
  app_cli/             # Python processing core
  ui_tauri/            # Minimal Tauri shell wrapping the CLI
  examples/            # Sample brand configuration
  tests/               # pytest suite
```

Run `python -m creatorpack.app_cli.main run --help` for command usage.

## Installation

1. Install [Python 3.11](https://www.python.org/downloads/) and ensure `pip` is available.
2. Install [ffmpeg](https://ffmpeg.org/download.html) and `ffprobe` so media operations can re-encode when required.
3. Clone this repository and install dependencies:

```bash
pip install -e .
```

Optional components:

- `faster-whisper` for GPU-accelerated transcription.
- `pyannote.audio` for diarization.

## Quickstart

```bash
creatorpack run --file path/to/video.mp4 \
  --template creator-pack \
  --minutes 15 \
  --smart \
  --highlights \
  --brand examples/brand_default.yaml
```

Outputs are written to `exports/<slug>/` including transcripts, chapters, highlight placeholders, credits, and
provenance metadata.

## Create a local bundle

Package the repository into a ready-to-share folder (and optional `.zip`) without any git metadata:

```bash
creatorpack bundle --output CreatorPack-local --archive
```

The command copies the source tree, emits `INSTALL.md` with setup steps, and writes `bundle_manifest.json`
describing the included assets so you can zip and transfer the toolkit to another machine.

## Development

Run the automated tests:

```bash
pytest
```

To exercise the CLI without network calls, provide a local media file. The CLI validates licenses and will block
non-commercial (NC) or no-derivatives (ND) content by default.

## Packaging

A PyInstaller spec is provided at `creatorpack/packaging.spec`. Build binaries after installing the project in a clean
virtual environment:

```bash
pyinstaller creatorpack/packaging.spec
```

## Known Limitations

- Fallback transcription is a placeholder when faster-whisper is unavailable. Install the model for production work.
- Highlight exports are placeholders; integrate ffmpeg trimming to produce real short-form assets.
- Network-based source adapters perform lightweight metadata checks and may require API credentials for complex use cases.
- The Tauri UI wraps the CLI and streams log output but does not yet expose granular editing controls.
