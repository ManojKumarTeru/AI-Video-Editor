# 🎬 AI-Editor — Command Cheat Sheet & Quick Reference

This cheat sheet documents all video editing modes, output formats, style presets, modular subcommands, and flags available in **AI-Editor**. Bookmark or reference this guide anytime you produce content.

---

## ⚡ Quick Platform Matrix

| Platform | Format Flag | Resolution & Aspect Ratio | Pacing & Visual Elements |
| :--- | :--- | :--- | :--- |
| **YouTube Long-Form** | `--format youtube` *(default)* | **1920×1080 (16:9 Landscape)** | • Cold open teaser hook (0:00)<br>• Animated intro & outro bumpers<br>• Lower-third ID badge at bottom-left (`y = 82%`)<br>• Conservative zoom pacing (4–5s wide / 3.8s zoom)<br>• Full YouTube upload metadata `.txt` package |
| **YouTube Shorts / Reels / TikTok** | `--format shorts` | **1080×1920 (9:16 Vertical)** | • **0 intro / 0 outro** (instant engagement hook)<br>• Host ID badge in **upper-left safe zone** (`y = 12%`) — never collides with subtitles<br>• Fast-paced retention zoom cycle (1.8s wide / 3.0s zoom)<br>• Ambient blur-fill background or central crop |

---

## 🎨 Production Style Kits (`--kit`)

Control the aesthetic theme, typography accents, and sound design with one flag:

| Kit Preset | Visual Aesthetic | Accent Color | Sound Design |
| :--- | :--- | :--- | :--- |
| **`creator_elite`** *(Default)* | Broadcast Studio Glass | **Warm Electric Gold** (`#FFD700`) | Camera flash punch-in, smooth airy whoosh, sub-bass impact |
| **`neon_cyber`** | High-Tech / Futuristic | **Cyber Cyan** (`#00F0FF`) | Cyber laser pops, futuristic swooshes |
| **`minimal_studio`** | Clean, Understated, Borderless | **Soft Crisp White** | Subtle acoustic clicks, gentle releases |

---

## 📋 Copy-Paste Command Recipes

### 1. YouTube Shorts (9:16 Vertical)
```powershell
# Basic 1-Click Shorts master
py main.py process --file input/video/my_video.mp4 --format shorts

# Shorts with custom presenter badge
py main.py process --file input/video/my_video.mp4 --format shorts --speaker "Manoj" --title "Creator"
```

### 2. Full-Length YouTube Video (16:9 Landscape)
```powershell
# Full long-form package with cold open, intro, outro, zooms & captions
py main.py process --file input/video/my_video.mp4 --format youtube --speaker "Manoj" --title "Creator"
```

### 3. Shorts with External Mic & Background Music
```powershell
# Auto-syncs external mic waveform and ducks music by -14dB during speech
py main.py process --file input/video/my_video.mp4 --format shorts --mic input/audio/mic.wav --music input/music/lofi.mp3
```

### 4. Custom Keyword Badges (Control What Pops Up on Right)
```powershell
# Specify exact words to highlight as glowing badges
py main.py process --file input/video/my_video.mp4 --format shorts --highlights "PYTHON,SOFTWARE,SALARY"
```

### 5. High-Retention Mode (Tighter cuts + top progress bar)
```powershell
# Cuts pauses down to 0.5s and adds a glowing gold progress line across the top
py main.py process --file input/video/my_video.mp4 --format shorts --min-pause 0.5 --retention-bar
```

### 6. Minimalist / Clean (No zooms, no SFX, no bumpers)
```powershell
# Clean talking head video without effects
py main.py process --file input/video/my_video.mp4 --no-zooms --no-sfx --no-intro --no-outro
```

### 7. Standalone 16:9 to 9:16 Conversion (No re-editing)
```powershell
# Ambient blur-fill background (keeps full 16:9 video centered):
py main.py shorts --file output/final/my_video.mp4 --style blur_fill

# Center-crop vertical window:
py main.py shorts --file output/final/my_video.mp4 --style center_crop
```

---

## 🔧 Modular Step-by-Step Commands

If you only want to run one specific task without running the entire pipeline:

| Command | Purpose | Example |
| :--- | :--- | :--- |
| **`inspect`** | Scans all files in `input/`, validates codecs, loudness (LUFS), and audio sync | `py main.py inspect` |
| **`edit`** | Cuts dead air / silences with configurable dB threshold | `py main.py edit --file input/video/raw.mp4 --min-pause 0.8` |
| **`audio`** | Masters voice to -14 LUFS, syncs external mic, and ducks music | `py main.py audio --file input/video/raw.mp4 --music input/music/bgm.mp3` |
| **`transcribe`** | Transcribes/translates speech and outputs `.srt` and animated `.ass` | `py main.py transcribe --file input/video/raw.mp4 --model large-v3-turbo` |
| **`polish`** | Burns subtitles, applies color grading, zoom cuts, and branding | `py main.py polish --file workspace/temp/cut.mp4 --speaker "Manoj"` |
| **`shorts`** | Direct 16:9 to 9:16 converter for any finished video | `py main.py shorts --file output/final/master.mp4` |
| **`doctor`** | Verifies FFmpeg, Python dependencies, and system fonts | `py main.py doctor` |
| **`test`** | Runs test suites for validation | `py main.py test --phase 5` |

---

## 🎛️ Complete Flags Reference (`process`)

### Media Inputs & Formats
- `--file`, `-f`: Path to specific raw video file (default: first file in `input/video/`).
- `--mic`, `-a`: Path to external microphone audio file (`.wav`, `.mp3`).
- `--music`, `-m`: Path to background music track (`.mp3`, `.wav`).
- `--format`: `'youtube'` (16:9 widescreen) or `'shorts'` (9:16 vertical).
- `--kit`: Style preset: `'creator_elite'`, `'neon_cyber'`, or `'minimal_studio'`.
- `--crf`: Video quality factor (default: `18`, visually lossless).

### Presenter & Branding
- `--speaker`: Presenter name for intro badge (e.g. `"Manoj"`).
- `--title`: Presenter title/role (e.g. `"Creator"`).
- `--no-branding`: Disables Host ID badge and watermark logo.
- `--retention-bar`: Enables dynamic glowing progress bar at top of frame.

### Subtitles & Speech
- `--language`, `-l`: Input speech language (default: `te` for Telugu input with automatic English translation).
- `--task`: `'translate'` (output English subtitles) or `'transcribe'`.
- `--model`: Whisper model: `'large-v3-turbo'` (recommended), `'small'`, `'medium'`, `'large-v3'`.
- `--force`: Bypasses transcript cache to force fresh AI transcription.
- `--no-subs`: Skips burning subtitles into the video.
- `--no-kinetic`: Disables animated word-by-word spring bounce subtitles.

### Cutting & Zooms
- `--no-cut`: Skips dead-air removal.
- `--no-zooms`: Disables virtual multi-cam punch-in zoom cuts.
- `--zoom-scale`: Scale factor for zoom close-ups (default: `1.15`).
- `--zoom-duration`: Duration to hold punch-in in seconds (default: `3.8` for YouTube, `3.0` for Shorts).
- `--zoom-interval`: Wide shot duration between zooms (default: `5.5` for YouTube, `1.8` for Shorts).

### Visuals, Graphics & SFX
- `--highlights`: Comma-separated custom keywords for right-side badges (e.g. `"PYTHON,AI,JOB"`).
- `--no-callouts`: Disables right-side keyword badges.
- `--callout-duration`: Time badge stays on screen (default: `1.3s`).
- `--callout-interval`: Min spacing between badges (default: `3.5s`).
- `--no-broll`: Disables automated B-roll visual metaphor cutaway cards.
- `--no-grade`: Disables studio color grading and vignette.
- `--no-sfx`: Disables micro-sound effects (camera flash, whooshes).
- `--no-impact`: Disables sub-bass impact thumps on key takeaways.
- `--no-intro`: Disables animated intro sequence.
- `--no-outro`: Disables outro title sequence.
- `--no-cold-open`: Disables teaser hook teaser.
- `--no-package`: Skips generating YouTube upload metadata `.txt` file.

---

## 🛡️ Subtitle Quality & Language Rules

1. **100% English Script Only**: All subtitles are guaranteed to be in English. Telugu or non-Latin Unicode characters (`[\u0C00-\u0C7F]`) are automatically detected and stripped.
2. **Hallucination Protection**: Silence, breathing, or background noise at the tail-end of videos is filtered out so random phantom subtitles never appear.
3. **Smart Tanglish Translation**: Mixed Telugu/English conversational words (e.g. *miru*, *chesukovali*, *software job lo*) are automatically normalized into natural English meaning while maintaining frame-perfect timing.
