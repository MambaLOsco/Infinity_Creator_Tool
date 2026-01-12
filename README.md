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

## 5-minute quickstart

1. Install ffmpeg:

   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

2. Install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   pip install faster-whisper
   ```

3. Run the pipeline:

   ```bash
   creatorpack run --file /path/to/video.mp4 --template creator-pack --minutes 10 --smart --highlights \
     --brand examples/brand_default.yaml --out exports
   ```

## Canonical command

```bash
creatorpack run --file /path/to/video.mp4 --minutes 10 --smart --highlights \
  --highlights-top-k 3 --highlights-min-seconds 60 --highlights-max-seconds 90 \
  --highlights-padding-seconds 2 --out exports
```

Exports are written under `exports/<job_id>/` by default. The job id is a deterministic hash of
input path + modified time + parameters.

### Output structure

```
exports/<job_id>/
  input/
  transcript/
  chapters/
  highlights/
  branded/
  manifests/
  logs/
```

Each run writes:

- transcript (`transcript/transcript.json` + `transcript/transcript.txt`)
- chapters manifest (`manifests/chapters.json`)
- highlights manifest (`manifests/highlights.json`)
- provenance receipt (`manifests/provenance.json`)
- credits receipt (`manifests/credits.json`)
- assets map (`manifests/assets.map.json`)
- job log (`logs/job.log.jsonl`)

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

## Troubleshooting

- **ffmpeg missing**: install with `brew install ffmpeg` (macOS) or `sudo apt-get install ffmpeg` (Linux).
- **faster-whisper missing**: install with `pip install faster-whisper` and confirm the model backend is available.
