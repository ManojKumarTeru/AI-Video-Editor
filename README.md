# 🎬 AI-Editor — 100% Local AI Automated Video Editor

> **Professional YouTube Video Production Pipeline for Windows 11 (CPU-Only, Zero Cloud APIs, Standalone MP4 Delivery)**  
> Engineered to achieve the pacing, polish, and auditory clarity of a **5+ Year Experienced Professional Video Editor**.

---

## 🌟 Overview & Key Capabilities

AI-Editor transforms raw footage into fully polished, broadcast-grade **YouTube Long-Form videos (16:9, 20–60 min)** or **YouTube Shorts (9:16, ≤2 min)** in a single command. It runs **100% locally on your CPU** without Adobe Premiere Pro, paid subscriptions, or GPU requirements.

```
       [ Raw Video Footage ] ───▶ [ Media Inspector & Integrity Check ]
       [ External Mic Audio] ───▶ [ Non-Destructive Backup ]
       [ Background Music  ] ───▶ [ Auto Mic Sync (Cross-Correlation) ]
                                            │
                                            ▼
                               [ Smart Silence Removal ]
                        (Conservative 5+ YOE: Pauses < 0.8s kept,
                         300ms/350ms speech padding, micro-fades)
                                            │
                                            ▼
                           [ faster-whisper AI Transcription ]
                       (Word-level timestamps, 4-7 words/card,
                        high-contrast ASS karaoke subtitle burn)
                                            │
                                            ▼
                             [ Professional Audio Mastering ]
                       (80Hz rumble cut, 12kHz hiss cut, 3kHz EQ,
                        compressor, -14 LUFS EBU R128, music ducking)
                                            │
                                            ▼
                               [ Visual Polish & Branding ]
                       (Glassmorphism lower third, corner watermark,
                        1080p Intro/Outro or Shorts 9:16 blur-fill)
                                            │
                                            ▼
                          [ YouTube Master Delivery Export ]
                       (H.264 High 4.1, 320k AAC, +faststart,
                        Closed GOP 2s, Automated QA validation)
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Place Your Raw Media Files
Drop your files into the designated input folders:
- `input/video/` — Your raw camera video recording (`.mp4`, `.mov`, `.mkv`)
- `input/audio/` *(Optional)* — Dedicated high-quality external mic recording (`.wav`, `.mp3`)
- `input/music/` *(Optional)* — Background music track to duck under speech (`.mp3`, `.wav`)

### Step 2: Run 1-Click Master Editing

#### 🎥 For Long-Form YouTube Video (16:9 1080p):
```bash
py main.py process --speaker "Your Name" --title "Channel Creator"
```

#### 📱 For YouTube Shorts (9:16 Vertical with Ambient Blur-Fill):
```bash
py main.py process --format shorts
```

### Step 3: Collect Deliverables in `output/`
- **Final Master MP4**: `output/final/*_YouTube_Master.mp4` or `output/final/*_Shorts_Master.mp4`
- **Subtitles**: `output/subtitles/*.srt` and `output/subtitles/*.ass`
- **Source Backup**: `workspace/backup/originals_YYYYMMDD_HHMMSS/` *(untouched originals)*

---

## 🛠️ CLI Command Reference

### 1. `process` — Master 1-Click Pipeline
Runs the entire 7-step pipeline from start to finish.

```bash
# Basic usage (auto-discovers inputs in input/)
py main.py process

# Target a specific video with custom presenter lower-third:
py main.py process --file input/video/my_footage.mp4 --speaker "Alex Rivera" --title "Tech Reviewer"

# Produce YouTube Shorts 9:16:
py main.py process --format shorts

# Available flags:
#   --file, -f       Path to specific video file
#   --mic, -a        Path to external microphone WAV/MP3
#   --music, -m      Path to background music file
#   --format         'youtube' (16:9, default) or 'shorts' (9:16)
#   --speaker        Presenter name for broadcast lower third (default: 'Content Creator')
#   --title          Presenter title/channel name (default: 'Video Host')
#   --model          faster-whisper model: 'tiny', 'base', 'small' (default), 'medium'
#   --crf            H.264 quality factor (default: 18, visually lossless)
#   --no-cut         Skip dead-air silence removal
#   --no-subs        Skip burning subtitles into video
#   --no-intro       Skip intro title sequence
#   --no-outro       Skip outro title sequence
#   --no-branding    Skip lower third banner and watermark
```

### 2. `inspect` — Scan Media Inputs
Examines all media in `input/` and displays durations, resolutions, codecs, and integrity status:
```bash
py main.py inspect
```

### 3. `transcribe` — Generate Subtitles Only
Transcribes speech using `faster-whisper` and generates `.srt` and `.ass` subtitles:
```bash
py main.py transcribe
py main.py transcribe --model base --force
```

### 4. `edit` — Silence Removal Only
Detects dead air and trims videos conservatively with 300ms/350ms padding:
```bash
# Preview cut plan without rendering:
py main.py edit --preview

# Apply cuts:
py main.py edit --threshold -38.0 --min-pause 0.8
```

### 5. `audio` — Audio Pipeline & Mastering Only
Syncs external mic, normalizes voice to -14 LUFS, and ducks music:
```bash
py main.py audio
py main.py audio --file input/video/my_clip.mp4 --mic input/audio/mic.wav --music input/music/bg.mp3
```

### 6. `polish` — Visual Polish Only
Burns subtitles, lower third, watermark, and attaches intro/outro:
```bash
py main.py polish --speaker "Alex Rivera" --title "Host"
```

### 7. `shorts` — YouTube Shorts 9:16 Converter
Converts any 16:9 video to 9:16 vertical using ambient blur-fill:
```bash
py main.py shorts --file output/final/my_video.mp4
```

### 8. `test` — Run Validation Test Suites
```bash
py test_phase1.py       # Phase 1: Inspector & Whisper transcription
py test_phase2.py       # Phase 2: Silence detection & conservative cuts
py test_phase3.py       # Phase 3: External mic sync, mastering, & ducking
py test_phase4.py       # Phase 4: Subtitle burn, branding, & Shorts
py test_end_to_end.py   # Phase 5: Complete 1-Click Master Pipeline test
```

### 9. `doctor` — Hardware & Environment Diagnostics
```bash
py main.py doctor
```

---

## 📁 Project Directory Structure

```
AI-Editor/
├── input/
│   ├── video/              # Raw camera recordings (.mp4, .mov, .mkv)
│   ├── audio/              # High-quality external mic audio (.wav, .mp3)
│   └── music/              # Background music tracks (.mp3, .wav)
├── output/
│   ├── final/              # Final deliverable YouTube & Shorts master MP4s
│   ├── subtitles/          # Generated .srt and .ass subtitle files
│   └── clips/              # Individual cut segments / highlights
├── workspace/
│   ├── backup/             # Safe, timestamped snapshots of original files
│   └── temp/               # Intermediate processing cache
├── core/
│   ├── inspector.py        # Input scanner, integrity verifier & reporter
│   ├── transcriber.py      # faster-whisper AI transcriber & subtitle chunker
│   ├── editor.py           # Smart silence detector & micro-fade cutter
│   ├── audio.py            # Audio sync, EQ, compression, -14 LUFS & ducking
│   ├── visuals.py          # Subtitle burner, glassmorphism overlays, 9:16 Shorts
│   └── exporter.py         # YouTube delivery encoder & automated QA validator
├── utils/
│   └── ffmpeg_utils.py     # FFprobe wrapper & audio extraction utilities
├── config.py               # Central configuration presets and directory paths
├── main.py                 # CLI orchestrator and entry point
├── test_end_to_end.py      # Phase 5 end-to-end master test suite
└── check_environment.py    # System diagnostics and hardware check
```

---

## 💎 Built for 5+ YOE Editing Standards

| Feature | Standard "Auto-Editor" Tools | AI-Editor (5+ YOE Mode) |
|---|---|---|
| **Silence Cutting** | Abrupt machine-gun jump cuts; clips words | Preserves natural pauses (< 0.8s); 300ms lead-in, 350ms lead-out, 20ms micro-fades |
| **Microphone Sync** | Manual timeline dragging | FFT cross-correlation auto-sync to millisecond precision |
| **Voice Loudness** | Unprocessed or harsh clipping | 80Hz rumble cut, 12kHz hiss cut, 3kHz presence EQ, compressor, EBU R128 (-14 LUFS) |
| **Music Mixing** | Static volume or manual volume points | Sidechain compression automatically ducks music by -14dB during speech |
| **Captions** | Giant multi-line blocks; static text | Word-level animated ASS karaoke cards (4–7 words/card) |
| **Shorts Conversion** | Black bars or stretched heads | Ambient 25-radius blurred video background fill with crisp centered 16:9 action |
| **Export Quality** | Default MP4 (slow web buffering) | YouTube delivery master (+faststart moov atom, Closed GOP 2s, H.264 High 4.1) |
| **Safety** | Overwrites or mutates source files | Non-destructive: originals safely snapshotted to `workspace/backup/` |

---

## 🔒 100% Free & Local
- **No API keys or cloud bills** (OpenAI, Anthropic, ElevenLabs, etc.)
- **No Adobe Premiere Pro required**
- **Runs entirely offline on Windows CPU** (Lenovo T480 / 16 GB RAM)
