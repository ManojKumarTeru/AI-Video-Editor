# 🎬 AI-Editor — Architecture & How It Works

> **Project**: Local AI-Powered Video Editor for YouTube  
> **Version**: 1.0  
> **Last Updated**: 2026-10-25

---

## Table of Contents

- [How It Works — The Big Picture](#how-it-works--the-big-picture)
- [User Workflow](#user-workflow)
- [System Architecture](#system-architecture)
- [Data Flow](#data-flow)
- [Component Deep Dive](#component-deep-dive)
- [Processing Pipeline](#processing-pipeline)
- [Configuration System](#configuration-system)
- [CLI Commands](#cli-commands)
- [Error Handling & Recovery](#error-handling--recovery)
- [Performance Characteristics](#performance-characteristics)

---

## How It Works — The Big Picture

### In One Sentence

> Drop your raw video clips, mic audio, and background music into the `input/` folder, run one command, and get a professionally edited YouTube video out of the `output/` folder.

### The 60-Second Overview

```
YOU                          AI-EDITOR                        OUTPUT
 │                              │                               │
 ├─ Record video ──────────────▶│                               │
 ├─ Record mic audio ──────────▶│  1. Scans all your files      │
 ├─ Pick background music ─────▶│  2. Transcribes your speech   │
 │                              │  3. Removes dead silences     │
 │                              │  4. Syncs & masters audio     │
 │                              │  5. Adds captions & branding  │
 │                              │  6. Exports YouTube-ready MP4 │
 │                              │         │                     │
 │                              │         ▼                     │
 │                              │  ┌─────────────────┐          │
 │                              │  │ Final Video     │──────────▶ Upload to YouTube!
 │                              │  │ 1080p MP4       │          │
 │                              │  │ Professional    │          │
 │                              │  │ Quality         │          │
 │                              │  └─────────────────┘          │
```

### What Makes It "Professional" Quality?

| What a Beginner Does | What Our Tool Does (Pro Level) |
|---------------------|-------------------------------|
| Uploads raw footage as-is | Removes dead air, keeps natural pacing |
| No subtitles | Word-by-word animated captions |
| Camera mic audio | Synced external mic + noise reduction + mastering |
| No music | Background music with auto-ducking around speech |
| No branding | Intro, outro, lower thirds, watermark |
| Default export settings | YouTube-optimized H.264 encoding |
| Hopes the file works | Automated validation before delivery |

---

## User Workflow

### Step 1: Prepare Your Files

```
input/
├── video/                    ← Drop your raw video clips here
│   ├── clip_001.mp4             (talking-head footage from camera)
│   ├── clip_002.mp4
│   └── clip_003.mp4
│
├── audio/                    ← Drop your external mic recordings here (optional)
│   ├── mic_001.wav              (must match video clips in order)
│   ├── mic_002.wav
│   └── mic_003.wav
│
└── music/                    ← Drop background music here (optional)
    └── chill_beats.mp3
```

### Step 2: Configure (Optional)

Edit `templates/project_config.yaml` to customize:
- Caption style (classic, modern pop, minimal, bold impact)
- Silence removal sensitivity
- Music volume levels
- Export format (YouTube long-form or Shorts)

### Step 3: Run the Tool

```bash
# Process everything automatically
py main.py process --input ./input --output ./output

# Or for YouTube Shorts
py main.py process --input ./input --output ./output --format shorts
```

### Step 4: Review & Upload

```
output/
├── final/
│   └── My_Video_Final.mp4    ← Upload this to YouTube!
├── subtitles/
│   ├── My_Video.srt          ← Upload to YouTube for CC
│   └── My_Video.ass          ← Burned into video already
└── logs/
    └── processing_report.txt  ← What the tool did
```

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI-EDITOR SYSTEM                            │
│                                                                     │
│  ┌───────────┐    ┌──────────────────────────────────────────────┐  │
│  │           │    │            ORCHESTRATOR (main.py)             │  │
│  │   USER    │◀──▶│                                              │  │
│  │   (CLI)   │    │  Manages pipeline flow, error handling,      │  │
│  │           │    │  progress reporting, configuration           │  │
│  └───────────┘    └────────────────────┬─────────────────────────┘  │
│                                        │                            │
│                    ┌───────────────────┼───────────────────┐        │
│                    ▼                   ▼                   ▼        │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐    │
│  │   CORE MODULES   │ │     UTILITIES    │ │     ASSETS       │    │
│  │                  │ │                  │ │                  │    │
│  │ • inspector.py   │ │ • ffmpeg_utils   │ │ • fonts/         │    │
│  │ • transcriber.py │ │ • file_utils     │ │ • intros/        │    │
│  │ • editor.py      │ │ • logger         │ │ • outros/        │    │
│  │ • audio.py       │ │ • validators     │ │ • overlays/      │    │
│  │ • visuals.py     │ │                  │ │                  │    │
│  │ • exporter.py    │ │                  │ │                  │    │
│  └────────┬─────────┘ └────────┬─────────┘ └──────────────────┘    │
│           │                    │                                    │
│           ▼                    ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    EXTERNAL TOOLS                            │   │
│  │                                                              │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │  FFmpeg   │  │faster-whisper│  │  Auto-Editor │           │   │
│  │  │  FFprobe  │  │  (CPU/int8)  │  │              │           │   │
│  │  └──────────┘  └──────────────┘  └──────────────┘           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    FILE SYSTEM                               │   │
│  │                                                              │   │
│  │  input/          workspace/         output/                  │   │
│  │  ├── video/      ├── temp/          ├── final/               │   │
│  │  ├── audio/      └── cache/         ├── subtitles/           │   │
│  │  └── music/                         └── logs/                │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Module Responsibility Map

```
main.py (Orchestrator)
│
├── config.py ─────────────── Loads YAML config, provides defaults
│
├── core/inspector.py ─────── Phase 1: "What do we have to work with?"
│   ├── Uses: utils/ffmpeg_utils.py (FFprobe calls)
│   └── Uses: utils/validators.py (format checking)
│
├── core/transcriber.py ───── Phase 2: "What is being said?"
│   ├── Uses: faster-whisper (AI model)
│   └── Uses: utils/ffmpeg_utils.py (audio extraction)
│
├── core/editor.py ────────── Phase 3: "What should we cut?"
│   ├── Uses: auto-editor (silence detection)
│   └── Uses: utils/ffmpeg_utils.py (applying cuts)
│
├── core/audio.py ─────────── Phase 4: "How should it sound?"
│   ├── Uses: pydub (audio manipulation)
│   ├── Uses: pyloudnorm (loudness measurement)
│   ├── Uses: noisereduce (denoising)
│   └── Uses: utils/ffmpeg_utils.py (encoding)
│
├── core/visuals.py ───────── Phase 5: "How should it look?"
│   ├── Uses: Pillow (image overlays)
│   ├── Uses: utils/ffmpeg_utils.py (subtitle burn-in, overlays)
│   └── Uses: assets/ (fonts, templates)
│
└── core/exporter.py ──────── Phase 6: "Package it up."
    ├── Uses: utils/ffmpeg_utils.py (final encode)
    ├── Uses: utils/validators.py (quality check)
    └── Uses: utils/file_utils.py (backup)
```

---

## Data Flow

### Complete Data Flow Through the Pipeline

```
                              ┌─────────────────────┐
                              │    INPUT FILES       │
                              │                     │
                              │  video/*.mp4        │
                              │  audio/*.wav        │
                              │  music/*.mp3        │
                              └──────────┬──────────┘
                                         │
                    ═════════════════════════════════════
                    ║  PHASE 1: INSPECT & VALIDATE      ║
                    ═════════════════════════════════════
                                         │
                              ┌──────────▼──────────┐
                              │  MediaMetadata[]    │
                              │  ValidationReport   │
                              │  FileMapping        │
                              └──────────┬──────────┘
                                         │
                    ═════════════════════════════════════
                    ║  PHASE 2: TRANSCRIBE              ║
                    ═════════════════════════════════════
                                         │
                              ┌──────────▼──────────┐
                              │  Transcription JSON │
                              │  .srt files         │
                              │  .ass files         │
                              │  Word timestamps    │
                              └──────────┬──────────┘
                                         │
                    ═════════════════════════════════════
                    ║  PHASE 3: SMART EDIT              ║
                    ═════════════════════════════════════
                                         │
                              ┌──────────▼──────────┐
                              │  Cut list JSON      │
                              │  Trimmed clips      │
                              │  Merged timeline    │
                              └──────────┬──────────┘
                                         │
                    ═════════════════════════════════════
                    ║  PHASE 4: AUDIO PIPELINE          ║
                    ═════════════════════════════════════
                                         │
                              ┌──────────▼──────────┐
                              │  Synced audio       │
                              │  Denoised audio     │
                              │  Normalized audio   │
                              │  Mixed w/ music     │
                              └──────────┬──────────┘
                                         │
                    ═════════════════════════════════════
                    ║  PHASE 5: VISUAL POLISH           ║
                    ═════════════════════════════════════
                                         │
                              ┌──────────▼──────────┐
                              │  Captioned video    │
                              │  + Intro attached   │
                              │  + Outro attached   │
                              │  + Branding overlays│
                              └──────────┬──────────┘
                                         │
                    ═════════════════════════════════════
                    ║  PHASE 6: EXPORT & VALIDATE       ║
                    ═════════════════════════════════════
                                         │
                              ┌──────────▼──────────┐
                              │  OUTPUT FILES       │
                              │                     │
                              │  final/video.mp4    │
                              │  subtitles/*.srt    │
                              │  logs/report.txt    │
                              │  backup/originals/  │
                              └─────────────────────┘
```

### File Transformations at Each Phase

```
Phase 1: input/video/clip_001.mp4
              │
              ├── [Inspect] ──▶ workspace/reports/clip_001_metadata.json
              │
Phase 2:      ├── [Extract Audio] ──▶ workspace/temp/clip_001_audio.wav (16kHz mono)
              │
              ├── [Transcribe] ──▶ workspace/cache/clip_001_transcription.json
              │                    output/subtitles/clip_001.srt
              │                    output/subtitles/clip_001.ass
              │
Phase 3:      ├── [Detect Silence] ──▶ workspace/temp/clip_001_cuts.json
              │
              ├── [Apply Cuts] ──▶ workspace/temp/clip_001_trimmed.mp4
              │
              ├── [Merge Clips] ──▶ workspace/temp/merged_timeline.mp4
              │
Phase 4:      ├── [Sync Audio] ──▶ workspace/temp/merged_synced.mp4
              │
              ├── [Denoise] ──▶ workspace/temp/audio_clean.wav
              │
              ├── [Normalize] ──▶ workspace/temp/audio_normalized.wav
              │
              ├── [Mix Music] ──▶ workspace/temp/audio_mastered.wav
              │
Phase 5:      ├── [Burn Captions] ──▶ workspace/temp/video_captioned.mp4
              │
              ├── [Add Intro] ──▶ workspace/temp/intro.mp4
              │
              ├── [Add Outro] ──▶ workspace/temp/outro.mp4
              │
              ├── [Assemble] ──▶ workspace/temp/video_assembled.mp4
              │
Phase 6:      ├── [Export] ──▶ output/final/My_Video_Final.mp4
              │
              ├── [Validate] ──▶ output/logs/validation_report.json
              │
              └── [Backup] ──▶ output/backup/originals/clip_001.mp4
```

---

## Component Deep Dive

### The Orchestrator (`main.py`)

The brain of the system. It:
1. Parses CLI arguments (using `click`)
2. Loads project configuration (from YAML)
3. Runs each phase in sequence
4. Handles errors with graceful recovery
5. Displays real-time progress (using `rich`)
6. Generates the final processing report

**Orchestration Flow**:
```python
def process(input_dir, output_dir, config):
    # Phase 1
    report = inspector.scan_and_validate(input_dir)
    if not report.all_valid:
        display_errors(report)
        return

    # Phase 2
    transcriptions = transcriber.transcribe_all(report.video_files)
    
    # Phase 3
    trimmed_files = editor.remove_silence(report.video_files, config.editing)
    merged = editor.merge_clips(trimmed_files)
    
    # Phase 4
    mastered = audio.process(
        video=merged,
        external_audio=report.audio_files,
        music=report.music_files,
        config=config.audio
    )
    
    # Phase 5
    polished = visuals.apply(
        video=mastered,
        subtitles=transcriptions,
        config=config.visuals
    )
    
    # Phase 6
    final = exporter.export(polished, config.export)
    exporter.validate(final)
    exporter.backup(input_dir)
```

### FFmpeg Utility Layer (`utils/ffmpeg_utils.py`)

A Python wrapper around FFmpeg/FFprobe that:
- Abstracts complex FFmpeg command construction
- Handles Windows path escaping (spaces in paths!)
- Captures and parses FFmpeg output
- Provides progress callbacks for long operations
- Handles errors gracefully

**Key Functions**:
```python
def probe_media(file_path) -> dict:
    """Extract metadata using FFprobe, returns parsed JSON"""

def extract_audio(video_path, output_path, sample_rate=16000) -> str:
    """Extract audio track from video file"""

def apply_filter(input_path, output_path, filter_string) -> str:
    """Apply FFmpeg filter chain to media file"""

def concat_videos(file_list, output_path, transition=None) -> str:
    """Concatenate multiple video files"""

def burn_subtitles(video_path, subtitle_path, output_path) -> str:
    """Burn ASS/SRT subtitles into video"""

def encode_final(input_path, output_path, settings) -> str:
    """Final YouTube-optimized encoding"""
```

### Logger (`utils/logger.py`)

Professional logging with:
- Console output using `rich` (colors, progress bars, tables)
- File logging to `output/logs/`
- Timing decorators for performance measurement
- Phase-level progress tracking

**Log Levels**:
```
[18:30:01] ✅ Phase 1 complete — 3 videos, 3 audio files, 1 music track
[18:30:02] 🎙️ Phase 2 starting — transcribing 3 clips (est. 12 min)
[18:35:15] │  Clip 1/3: 847 words transcribed in 5:13
[18:40:02] │  Clip 2/3: 1,023 words transcribed in 4:47
[18:42:30] │  Clip 3/3: 692 words transcribed in 2:28
[18:42:31] ✅ Phase 2 complete — 2,562 words, 47:23 of audio
```

---

## Configuration System

### Configuration Hierarchy (Priority: high → low)

```
1. CLI arguments          ──▶  py main.py process --crf 20
2. Project config file    ──▶  templates/project_config.yaml
3. Built-in defaults      ──▶  config.py DEFAULT_CONFIG
```

### Configuration Categories

```yaml
# ═══════════════════════════════════════════════
#   AI-EDITOR PROJECT CONFIGURATION
# ═══════════════════════════════════════════════

# ── Project Info ──
project:
  name: "My YouTube Video"
  format: "youtube"            # "youtube" (16:9) or "shorts" (9:16)
  resolution: "1080p"          # Output resolution

# ── Transcription Settings ──
transcription:
  model: "small"               # tiny | base | small | medium
  language: "auto"             # "auto" or ISO code like "en", "es"
  device: "cpu"                # "cpu" or "cuda"
  compute_type: "int8"         # "int8" (fast) or "float16" (accurate)

# ── Editing Settings ──
editing:
  silence_threshold: 0.04      # Lower = more aggressive cuts
  min_silence_duration: 0.8    # Only cut pauses longer than this (seconds)
  margin: 0.3                  # Padding around cuts (seconds)
  remove_filler_words: false   # Remove "um", "uh", etc.

# ── Audio Settings ──
audio:
  target_lufs: -14.0           # YouTube loudness standard
  music_volume_speech: -24.0   # Music level during speech (LUFS)
  music_volume_gap: -18.0      # Music level during silence (LUFS)
  noise_reduction: true        # Enable/disable denoising
  noise_reduction_strength: 0.75

# ── Caption Settings ──
captions:
  enabled: true
  style: "modern_pop"          # classic | modern_pop | minimal | bold_impact
  font: "Montserrat"
  font_size: 48
  highlight_color: "#00AAFF"   # Active word color
  position: "bottom"           # top | center | bottom

# ── Branding Settings ──
branding:
  intro_enabled: true
  intro_template: "default"
  intro_duration: 5.0
  outro_enabled: true
  outro_template: "default"
  outro_duration: 8.0
  watermark_enabled: false
  watermark_path: "assets/overlays/logo.png"
  watermark_opacity: 0.3

# ── Export Settings ──
export:
  codec: "h264"
  crf: 18                     # 18 = high quality, 23 = smaller file
  preset: "slow"               # slower = better quality
  audio_bitrate: "320k"
  faststart: true              # Optimize for web streaming
  backup_originals: true
```

---

## CLI Commands

### Full Pipeline

```bash
# Standard YouTube long-form video
py main.py process --input ./input --output ./output

# YouTube Shorts
py main.py process --input ./input --output ./output --format shorts

# With custom config
py main.py process --input ./input --output ./output --config custom.yaml

# Dry run (show what would happen without processing)
py main.py process --input ./input --output ./output --dry-run
```

### Individual Phase Commands

```bash
# Phase 1: Just inspect files
py main.py inspect --input ./input

# Phase 2: Just transcribe
py main.py transcribe --input ./input/video/clip.mp4 --model small

# Phase 3: Just remove silence
py main.py edit --input ./workspace/temp/clip.mp4 --margin 0.3

# Phase 4: Just process audio
py main.py audio --input ./workspace/temp/merged.mp4 --music ./input/music/bg.mp3

# Phase 5: Just add captions
py main.py captions --input ./workspace/temp/video.mp4 --subs ./output/subtitles/clip.ass

# Phase 6: Just export
py main.py export --input ./workspace/temp/final.mp4 --quality high
```

### Utility Commands

```bash
# Show current configuration
py main.py config --show

# Update a config value
py main.py config --set captions.style=bold_impact

# Check environment
py main.py doctor

# Show project info
py main.py info --input ./input
```

---

## Error Handling & Recovery

### Checkpoint System

Each phase saves its results to disk. If the pipeline fails at Phase 4, you can fix the issue and resume from Phase 4 — no need to re-transcribe or re-cut.

```
workspace/
├── checkpoints/
│   ├── phase_1_complete.json     ← Metadata & validation results
│   ├── phase_2_complete.json     ← Transcription results & cache
│   ├── phase_3_complete.json     ← Cut lists & trimmed files
│   ├── phase_4_complete.json     ← Audio processing results
│   └── phase_5_complete.json     ← Visual assembly results
```

**Resume Command**:
```bash
# Resume from last successful checkpoint
py main.py process --input ./input --output ./output --resume

# Resume from a specific phase
py main.py process --input ./input --output ./output --resume-from 4
```

### Error Categories

| Error Type | Example | Response |
|-----------|---------|----------|
| **Fatal** | FFmpeg not installed | Stop, show clear error, suggest fix |
| **Recoverable** | One clip is corrupted | Skip clip, warn user, continue with remaining |
| **Degraded** | Auto-Editor fails | Fallback to FFmpeg silence detection |
| **Warning** | Clip FPS mismatch | Normalize FPS during processing, warn in report |

### Error Messages (User-Friendly)

```
❌ ERROR: clip_003.mp4 appears to be corrupted
   → FFprobe could not read the file
   → Skipping this clip. Other clips will still be processed.
   → To include this clip, try re-exporting it from your camera.

⚠️ WARNING: Audio clips have different sample rates
   → mic_001.wav: 48000 Hz
   → mic_002.wav: 44100 Hz
   → All audio will be resampled to 48000 Hz during processing.
```

---

## Performance Characteristics

### Estimated Processing Times (16 GB RAM, CPU-only)

| Video Length | Phase 2 (Transcribe) | Phase 3 (Edit) | Phase 4 (Audio) | Phase 5 (Visuals) | Phase 6 (Export) | **Total** |
|-------------|---------------------|----------------|-----------------|-------------------|-----------------|-----------|
| **5 min** | ~2 min | ~30 sec | ~1 min | ~2 min | ~3 min | **~9 min** |
| **20 min** | ~8 min | ~1 min | ~3 min | ~5 min | ~10 min | **~27 min** |
| **40 min** | ~16 min | ~2 min | ~5 min | ~8 min | ~18 min | **~49 min** |
| **60 min** | ~25 min | ~3 min | ~7 min | ~12 min | ~25 min | **~72 min** |

### Memory Usage Estimates

| Component | Peak RAM Usage | Notes |
|-----------|---------------|-------|
| faster-whisper (small) | ~2.5 GB | Loaded once, reused for all clips |
| FFmpeg processing | ~500 MB | Stream-based, constant memory |
| Audio processing | ~1 GB | Depends on audio length |
| Total pipeline peak | ~4 GB | Well within 16 GB |

### Disk Space Requirements

| Item | Size Estimate | Notes |
|------|--------------|-------|
| faster-whisper model | ~500 MB | Downloaded once, cached |
| Intermediate files | ~2x input size | Temporary, cleaned after |
| Final output | ~0.5-1x input | Depends on CRF setting |
| Backup | ~1x input | Original file copies |
| **Total needed** | ~4-5x input | For 10 GB input, need ~50 GB free |

---

## Security & Privacy

- **100% Local**: No data leaves your machine. Ever.
- **No Cloud APIs**: All AI processing uses local models (faster-whisper on CPU).
- **No Telemetry**: The tool sends no usage data anywhere.
- **No Login**: No accounts, API keys, or subscriptions required.
- **Your Data**: Input files, transcriptions, and outputs stay on your disk.

---

## Future Enhancements (v2.0 Ideas)

| Feature | Description | Difficulty |
|---------|-------------|------------|
| **GPU Acceleration** | CUDA support for faster transcription | Medium |
| **Face Tracking Crop** | Smart crop following the speaker's face for Shorts | Hard |
| **Multi-Speaker** | Detect and label different speakers | Medium |
| **Chapter Markers** | Auto-generate YouTube chapters from topics | Easy |
| **Thumbnail Generator** | AI-selected best frame + text overlay | Medium |
| **Batch Processing** | Queue multiple videos for overnight processing | Easy |
| **Premiere Pro XML** | Export edit decisions as Premiere Pro project file | Medium |
| **Web UI** | Browser-based interface instead of CLI | Hard |
| **Scene Detection** | Auto-detect scene changes for better transitions | Medium |
| **A/B Testing** | Generate multiple versions with different cuts | Medium |
