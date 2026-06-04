# Video Dubber — Project Blueprint

A CLI tool that takes English YouTube videos (or local files) and produces Arabic-dubbed versions with preserved background audio, multi-speaker support, and Arabic subtitles.

---

## Goal

Enable Arabic content creators to dub English YouTube videos into Modern Standard Arabic (MSA) with natural-sounding voices that clone the original speakers, preserving background music and sound effects.

---

## Pipeline Overview

```
Input (YouTube URL or local file)
        ↓
  [1] Download & Extract Audio       yt-dlp + ffmpeg
        ↓
  [2] Source Separation              Demucs (vocals vs background)
        ↓
  [3] Speaker Diarization            pyannote.audio
        ↓
  [4] Transcription                  Whisper (local / OpenAI API / Fireworks)
        ↓
  [5] Translation                    Claude / GPT-4o / Qwen3 / Llama (via Fireworks)
        ↓
  [6] Arabic TTS + Voice Cloning     IndexTTS2 (local) / ElevenLabs / OpenAI TTS
        ↓
  [7] Audio Assembly                 Mix Arabic speech + background audio (ffmpeg)
        ↓
  [8] Subtitle Generation            .srt from translated segments + timestamps
        ↓
Output: dubbed video (_ar.mp4) + subtitle file (_ar.srt)
```

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Packaging | `uv` |
| Video download | `yt-dlp` |
| Audio/video processing | `ffmpeg` (system), `ffmpeg-python` |
| Source separation | `demucs` (Meta, htdemucs model) |
| Speaker diarization | `pyannote.audio` |
| Transcription (local) | `openai-whisper` (large-v3) |
| Transcription (cloud) | OpenAI Whisper API / Fireworks API |
| Translation | `anthropic` / `openai` / Fireworks API (Kimi K2.6, Qwen3, Llama) |
| TTS (local) | `indextts` (IndexTTS2) |
| TTS (cloud) | ElevenLabs API / OpenAI TTS API |
| CLI | `typer` |
| Progress display | `rich` |
| Config | `pydantic-settings` + `.env` + `config.yaml` |
| Caching | Local filesystem (`.cache/` directory) |

---

## Project Structure

```
video_dubber/
├── pyproject.toml
├── .env.example
├── config.yaml
├── Blueprint.md
├── src/
│   └── video_dubber/
│       ├── __init__.py
│       ├── cli.py                  # Typer CLI entrypoint
│       ├── config.py               # Pydantic settings, config loading
│       ├── pipeline.py             # Orchestrates all steps end-to-end
│       ├── cache.py                # Intermediate result caching
│       ├── steps/
│       │   ├── downloader.py       # yt-dlp: URL → video file
│       │   ├── separator.py        # Demucs: audio → vocals + background
│       │   ├── diarizer.py         # pyannote: who spoke when
│       │   ├── transcriber.py      # Whisper: speech → English text + timestamps
│       │   ├── translator.py       # LLM: English segments → Arabic segments
│       │   ├── tts.py              # TTS: Arabic text → Arabic audio (per speaker)
│       │   ├── assembler.py        # ffmpeg: mix speech + background → final audio
│       │   └── subtitles.py        # Generate .srt from translated segments
│       └── backends/
│           ├── transcription/
│           │   ├── base.py
│           │   ├── whisper_local.py
│           │   ├── openai_whisper.py
│           │   └── fireworks_whisper.py
│           ├── translation/
│           │   ├── base.py
│           │   ├── claude.py
│           │   ├── openai_gpt.py
│           │   └── fireworks_llm.py
│           └── tts/
│               ├── base.py
│               ├── indextts2.py
│               ├── elevenlabs.py
│               └── openai_tts.py
└── .cache/                         # Gitignored, stores intermediate results
```

---

## Configuration

### `config.yaml`
```yaml
transcription:
  backend: whisper_local        # whisper_local | openai_whisper | fireworks_whisper
  model: large-v3               # for local whisper

translation:
  backend: claude               # claude | openai_gpt | fireworks_llm
  model: claude-sonnet-4-6      # model id
  target_dialect: msa           # msa (Modern Standard Arabic)

tts:
  backend: indextts2            # indextts2 | elevenlabs | openai_tts
  voice_cloning: true           # clone original speaker voice

audio:
  preserve_background: true     # use Demucs to keep music/SFX
  background_volume: 0.8        # volume multiplier for background track

processing:
  chunk_size_seconds: 30        # chunk length for progress reporting
  cache_dir: .cache

output:
  suffix: _ar                   # appended to output filename
  include_subtitles: true
```

### `.env`
```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
FIREWORKS_API_KEY=
ELEVENLABS_API_KEY=
PYANNOTE_AUTH_TOKEN=
```

---

## CLI Usage

```bash
# Basic usage — YouTube URL
dub https://youtube.com/watch?v=...

# Local file
dub ./video.mp4

# Override backends
dub https://youtube.com/watch?v=... \
  --transcription openai_whisper \
  --translation fireworks_llm \
  --tts elevenlabs

# Custom output directory
dub ./video.mp4 --output ./dubbed/

# Skip cache (force reprocess)
dub ./video.mp4 --no-cache
```

---

## Step-by-Step Pipeline Detail

### 1. Download & Extract
- `yt-dlp` downloads video + audio for YouTube URLs
- Local files are used directly
- Audio extracted to `.wav` via ffmpeg

### 2. Source Separation (Demucs)
- `htdemucs` model splits audio into `vocals` and `no_vocals`
- `no_vocals` track preserved for final mix
- `vocals` track passed to diarization + transcription

### 3. Speaker Diarization (pyannote)
- Detects speaker turns with timestamps
- Outputs: `[(speaker_id, start_time, end_time), ...]`
- Each unique speaker gets a voice profile for TTS

### 4. Transcription (Whisper)
- Transcribes vocal track to English text
- Outputs segments with word-level timestamps
- Segments aligned to speaker turns from diarization

### 5. Translation (LLM)
- Each segment translated to MSA Arabic
- Full segment context passed to preserve coherence
- Speaker turns preserved in output

### 6. TTS + Voice Cloning (IndexTTS2)
- For each speaker: extract a voice sample from original audio
- Generate Arabic audio for each segment with:
  - Zero-shot voice cloning from speaker sample
  - Duration-controlled to match original segment length
- Output: one audio file per segment

### 7. Audio Assembly (ffmpeg)
- Place each Arabic segment at its original timestamp
- Mix with `no_vocals` background track
- Background at configurable volume (default 0.8x)

### 8. Subtitle Generation
- Build `.srt` from translated segments + Whisper timestamps
- Arabic text, right-to-left compatible

---

## Caching Strategy

Each step saves its output to `.cache/<video_hash>/<step>/`:

```
.cache/
└── abc123/                     # hash of input video/URL
    ├── audio.wav
    ├── vocals.wav
    ├── background.wav
    ├── diarization.json
    ├── transcription.json
    ├── translation.json
    ├── tts/
    │   ├── seg_000.wav
    │   └── seg_001.wav
    └── final/
        ├── video_ar.mp4
        └── video_ar.srt
```

Re-running skips any step whose output already exists in cache.

---

## System Requirements

- Python 3.11+
- `ffmpeg` installed (system-level)
- NVIDIA GPU recommended for local Whisper (large-v3) and IndexTTS2
  - RTX 2060 6GB VRAM — sufficient for both
- ~5GB disk per hour of video (intermediate files)

---

## Development Milestones

Each milestone is independently testable and builds on the previous one.

---

### Milestone 1 — Project Scaffold
**Goal:** A working CLI skeleton with config loading.

Tasks:
- Initialize `uv` project, `pyproject.toml`, full directory structure
- Config loading via `pydantic-settings` (`config.yaml` + `.env`)
- Basic `typer` CLI with `--help`, `--version`
- `.env.example` and `.gitignore`

**Test:** `dub --version` and `dub --help` both work. Config loads without errors.

---

### Milestone 2 — Download & Audio Extraction
**Goal:** Given a YouTube URL or local file, produce a `.wav` audio file.

Tasks:
- `yt-dlp` integration for YouTube URLs
- Local file passthrough
- `ffmpeg` audio extraction to mono 16kHz `.wav`
- Cache result under `.cache/<hash>/audio.wav`

**Test:** `dub https://youtube.com/... --only-step download` produces `audio.wav`.

---

### Milestone 3 — Source Separation
**Goal:** Split audio into `vocals.wav` and `background.wav`.

Tasks:
- `demucs` integration (`htdemucs` model)
- Accept `audio.wav`, output two tracks
- Cache both under `.cache/<hash>/`

**Test:** `dub ./video.mp4 --only-step separate` produces two audible, correctly separated tracks.

---

### Milestone 4 — Speaker Diarization
**Goal:** Detect who speaks when in the vocals track.

Tasks:
- `pyannote.audio` integration
- Accept `vocals.wav`, output `diarization.json`
- Format: `[{speaker, start, end}, ...]`

**Test:** `dub ./video.mp4 --only-step diarize` produces `diarization.json` with correct speaker turns.

---

### Milestone 5 — Transcription
**Goal:** Convert English speech to text with timestamps.

Tasks:
- Local Whisper backend (`large-v3`)
- OpenAI Whisper API backend
- Fireworks API backend
- Merge diarization speaker IDs with Whisper segments
- Output `transcription.json`: `[{speaker, start, end, text}, ...]`

**Test:** `dub ./video.mp4 --only-step transcribe` produces accurate English transcript with timestamps and speaker labels.

---

### Milestone 6 — Translation
**Goal:** Translate English segments to MSA Arabic.

Tasks:
- Claude backend
- OpenAI GPT backend
- Fireworks LLM backend (Qwen3 / Llama)
- Translate segment-by-segment preserving context
- Output `translation.json`: `[{speaker, start, end, text_en, text_ar}, ...]`

**Test:** `dub ./video.mp4 --only-step translate` produces fluent, correctly formatted Arabic text.

---

### Milestone 7 — TTS + Voice Cloning
**Goal:** Generate Arabic audio segments that sound like the original speakers.

Tasks:
- IndexTTS2 local backend with zero-shot voice cloning
- ElevenLabs API backend
- OpenAI TTS API backend
- Extract voice sample per speaker from `vocals.wav`
- Generate one `.wav` per segment with duration control
- Output to `.cache/<hash>/tts/seg_NNN.wav`

**Test:** `dub ./video.mp4 --only-step tts` produces Arabic audio segments audibly matching the original speaker's voice.

---

### Milestone 8 — Audio Assembly
**Goal:** Combine Arabic speech segments with background audio into a final track.

Tasks:
- Place each TTS segment at its original timestamp using ffmpeg
- Mix with `background.wav` at configurable volume
- Mux final audio back into the original video container
- Output `video_ar.mp4`

**Test:** `dub ./video.mp4 --only-step assemble` produces a watchable video with Arabic speech and intact background music.

---

### Milestone 9 — Subtitle Generation
**Goal:** Produce an Arabic `.srt` subtitle file.

Tasks:
- Build `.srt` entries from `translation.json` timestamps
- Correct Arabic RTL encoding (UTF-8 with BOM)
- Output `video_ar.srt`

**Test:** `dub ./video.mp4 --only-step subtitles` produces a `.srt` that displays correctly in VLC.

---

### Milestone 10 — Full Pipeline Integration
**Goal:** End-to-end run from a single command.

Tasks:
- Wire all steps in `pipeline.py` with progress bar (`rich`)
- Caching: skip already-completed steps on rerun
- `--no-cache` flag to force full reprocess
- `--output` flag for custom output directory
- Error handling: clear messages on step failure

**Test:** `dub https://youtube.com/watch?v=...` on a 2-minute video produces `video_ar.mp4` and `video_ar.srt` with correct dubbing end-to-end.

---

## Out of Scope (v1)

- Lip sync / video face manipulation
- Real-time / streaming processing
- Web UI
- Non-Arabic target languages
- Batch processing multiple videos
