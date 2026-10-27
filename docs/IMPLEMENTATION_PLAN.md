# 🎬 AI-Editor — Implementation Plan

> **Project**: Local AI-Powered Video Editor for YouTube  
> **Version**: 1.0  
> **Last Updated**: 2026-10-25  
> **Status**: ✅ All Phases 1–6 Completed & Verified (100%)

---

## Table of Contents

- [Project Overview](#project-overview)
- [High-Level Plan](#high-level-plan)
- [Low-Level Plan](#low-level-plan)
- [Technology Stack](#technology-stack)
- [Dependencies](#dependencies)
- [Project Structure](#project-structure)
- [Implementation Timeline](#implementation-timeline)
- [Risk Mitigation](#risk-mitigation)

---

## Project Overview

### What We're Building

A **local-first, AI-powered video editing automation pipeline** that transforms raw talking-head footage into professional YouTube videos — matching the quality of a **5+ year experienced professional editor**.

### Input

| Input Type | Description | Required? |
|-----------|-------------|-----------|
| **Raw Video Clips** | Talking-head footage (MP4, MOV, MKV) | ✅ Required |
| **Raw Audio Clips** | External microphone recordings (WAV, MP3) | ❌ Optional |
| **Background Music** | Music tracks for mixing (MP3, WAV, OGG) | ❌ Optional |

### Output

| Output Type | Description |
|------------|-------------|
| **YouTube Long-form** | 1080p MP4, 16:9, 20–60 minutes, H.264, AAC |
| **YouTube Shorts** | 1080p MP4, 9:16, ≤ 2 minutes, H.264, AAC |

### Output Quality Target

A video that feels like it was edited by a professional with 5+ years of experience:
- Clean, natural cuts (no robotic editing)
- Properly balanced and mastered audio
- Professional animated captions
- Cohesive branding (intro, outro, lower thirds)
- YouTube-optimized encoding

---

## High-Level Plan

### The 6-Phase Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PHASE 1    │    │  PHASE 2    │    │  PHASE 3    │
│  Inspect &  │───▶│  Transcribe │───▶│  Smart Edit │
│  Validate   │    │  Speech     │    │  Cuts       │
└─────────────┘    └─────────────┘    └─────────────┘
                                            │
┌─────────────┐    ┌─────────────┐          │
│  PHASE 6    │    │  PHASE 5    │    ┌─────▼───────┐
│  Export &   │◀───│  Visual     │◀───│  PHASE 4    │
│  Validate   │    │  Polish     │    │  Audio      │
└─────────────┘    └─────────────┘    │  Pipeline   │
       │                              └─────────────┘
       ▼
  📦 Final MP4
```

| Phase | Name | What It Does | Key Technology |
|-------|------|-------------|----------------|
| **1** | Inspect & Validate | Scans inputs, extracts metadata, validates formats | FFprobe |
| **2** | Transcribe | Speech-to-text with word-level timestamps | faster-whisper |
| **3** | Smart Edit | Conservative silence removal, smart cuts | Auto-Editor + FFmpeg |
| **4** | Audio Pipeline | Sync, denoise, normalize, mix music | pydub, pyloudnorm |
| **5** | Visual Polish | Captions, intro/outro, branding overlays | FFmpeg ASS filters |
| **6** | Export & Validate | YouTube-optimized render, quality check | FFmpeg H.264 |

### Design Principles

1. **Local-First** — Everything runs on your machine. No cloud APIs, no subscriptions.
2. **Non-Destructive** — Original files are never modified. Everything works on copies.
3. **Conservative Editing** — Keeps natural speech pauses. No robotic pacing.
4. **Checkpoint Recovery** — Each phase saves results. Resume from any point on failure.
5. **CPU-Compatible** — Runs on CPU with 16 GB RAM. GPU optional for acceleration.
6. **Modular** — Each phase can run independently or as part of the full pipeline.

---

## Low-Level Plan

### Phase 1: Environment Check, Media Inspection & Validation

**Files**: `core/inspector.py`, `utils/ffmpeg_utils.py`, `utils/validators.py`  
**Estimated Time**: 1-2 days

#### 1.1 Environment Checker

**Purpose**: Verify all required tools are installed before processing begins.

**Implementation Details**:
```
check_environment()
├── Check Python version ≥ 3.10
│   └── sys.version_info >= (3, 10)
├── Check FFmpeg is available
│   └── subprocess.run(["ffmpeg", "-version"])
│   └── Parse version string, verify ≥ 5.0
├── Check FFprobe is available
│   └── subprocess.run(["ffprobe", "-version"])
├── Check disk space
│   └── shutil.disk_usage() — need ≥ 10 GB free
├── Check RAM availability
│   └── psutil or /proc/meminfo — need ≥ 4 GB free
└── Return EnvironmentReport with pass/fail for each
```

**Data Structures**:
```python
@dataclass
class EnvironmentReport:
    python_version: str          # "3.14.5"
    python_ok: bool              # True if >= 3.10
    ffmpeg_version: str          # "9.0.2"
    ffmpeg_ok: bool              # True if >= 5.0
    ffprobe_version: str         # "9.0.2"
    ffprobe_ok: bool             # True
    disk_space_gb: float         # 45.2
    disk_space_ok: bool          # True if >= 10 GB
    ram_gb: float                # 16.0
    ram_ok: bool                 # True if >= 4 GB
    all_ok: bool                 # True if all checks pass
```

#### 1.2 Media Scanner

**Purpose**: Scan input directories and discover all media files.

**Implementation Details**:
```
scan_input_directory(input_path)
├── Walk input/video/ directory
│   └── Find files with extensions: .mp4, .mov, .mkv, .avi, .webm
├── Walk input/audio/ directory
│   └── Find files with extensions: .wav, .mp3, .aac, .flac, .ogg
├── Walk input/music/ directory
│   └── Find files with extensions: .mp3, .wav, .ogg, .flac
├── Sort files by name (natural sort) or creation date
└── Return categorized file lists
```

#### 1.3 Media Inspector

**Purpose**: Extract detailed metadata from every input file.

**FFprobe Command**:
```bash
ffprobe -v quiet -print_format json -show_format -show_streams <file>
```

**Extracted Metadata**:
```python
@dataclass
class MediaMetadata:
    file_path: str
    file_size_mb: float
    duration_seconds: float
    # Video stream (if present)
    video_codec: str             # "h264"
    video_width: int             # 1920
    video_height: int            # 1080
    video_fps: float             # 30.0
    video_bitrate_kbps: int      # 8000
    pixel_format: str            # "yuv420p"
    # Audio stream (if present)
    audio_codec: str             # "aac"
    audio_sample_rate: int       # 48000
    audio_channels: int          # 2
    audio_bitrate_kbps: int      # 320
    # Validation
    is_valid: bool
    issues: List[str]
```

#### 1.4 Media Validator

**Purpose**: Verify files are not corrupted and are in supported formats.

**Validation Steps**:
```
validate_media(file_path)
├── Check file exists and size > 0
├── Run FFprobe metadata extraction
│   └── If FFprobe fails → file is corrupted
├── Validate video codec (H.264, H.265, VP9 supported)
├── Validate audio codec (AAC, PCM, MP3, Opus supported)
├── Validate container (MP4, MOV, MKV, AVI, WebM supported)
├── Quick decode test (decode first 5 seconds)
│   └── ffmpeg -i input -t 5 -f null -
│   └── If exit code ≠ 0 → file may be corrupted
└── Return ValidationResult with pass/fail + issues list
```

#### 1.5 Inspection Report Generator

**Purpose**: Generate a human-readable summary of all input files.

**Output Format**:
```
📊 AI-Editor — Inspection Report
══════════════════════════════════════════════
📹 Video Clips: 3 found (total: 47:23)
  ├── clip_001.mp4 │ 1920×1080 │ H.264 │ 30fps │ 15:42
  ├── clip_002.mp4 │ 1920×1080 │ H.264 │ 30fps │ 18:01
  └── clip_003.mp4 │ 1920×1080 │ H.264 │ 30fps │ 13:40

🎙️ Audio Clips: 3 found (total: 47:20)
  ├── mic_001.wav │ PCM 16-bit │ 48kHz │ Stereo │ 15:42
  ├── mic_002.wav │ PCM 16-bit │ 48kHz │ Stereo │ 18:01
  └── mic_003.wav │ PCM 16-bit │ 48kHz │ Stereo │ 13:37

🎵 Music: 1 found
  └── bg_music.mp3 │ MP3 │ 320kbps │ 04:32

✅ All files valid — Ready to process
══════════════════════════════════════════════
```

---

### Phase 2: Speech Transcription & Subtitle Generation

**Files**: `core/transcriber.py`  
**Estimated Time**: 2-3 days

#### 2.1 Audio Extraction

**Purpose**: Extract clean audio from video clips for transcription.

**FFmpeg Command**:
```bash
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav
```

**Parameters Explained**:
- `-vn` — Discard video stream
- `-acodec pcm_s16le` — Uncompressed 16-bit PCM (best for speech recognition)
- `-ar 16000` — 16kHz sample rate (optimal for Whisper models)
- `-ac 1` — Mono (speech recognition doesn't need stereo)

#### 2.2 faster-whisper Transcription

**Purpose**: Convert speech to text with word-level timestamps.

**Model Selection for 16 GB RAM (CPU)**:

| Model | Size | RAM Usage | Speed (CPU) | Accuracy | Our Pick |
|-------|------|-----------|-------------|----------|----------|
| tiny | 39 MB | ~1 GB | 10x real-time | ★★☆☆☆ | ❌ Too inaccurate |
| base | 74 MB | ~1.5 GB | 7x real-time | ★★★☆☆ | ❌ Okay for testing |
| small | 244 MB | ~2.5 GB | 4x real-time | ★★★★☆ | ✅ **Best tradeoff** |
| medium | 769 MB | ~5 GB | 2x real-time | ★★★★★ | ⚠️ Slow on CPU |

**Implementation**:
```python
from faster_whisper import WhisperModel

model = WhisperModel(
    "small",                    # Model size
    device="cpu",               # CPU mode
    compute_type="int8",        # Quantized for speed
    cpu_threads=4               # Use 4 threads
)

segments, info = model.transcribe(
    audio_path,
    beam_size=5,                # Accuracy vs speed
    word_timestamps=True,       # Word-level timing
    vad_filter=True,            # Skip non-speech segments
    vad_parameters=dict(
        min_silence_duration_ms=500,
        speech_pad_ms=200
    )
)
```

**Processing Flow**:
```
Video → Extract Audio (16kHz WAV)
     → faster-whisper transcribe
     → Raw segments with word timestamps
     → Group words into subtitle lines
     → Generate SRT file
     → Generate ASS file (styled)
     → Cache results to JSON
```

#### 2.3 Subtitle Generation — SRT Format

**Purpose**: Standard subtitle format for compatibility.

**Grouping Algorithm**:
```
For each segment from faster-whisper:
    Group words into lines where:
    ├── Max characters per line: 42
    ├── Max lines per subtitle: 2
    ├── Min display duration: 1.0 seconds
    ├── Max display duration: 7.0 seconds
    └── Break at natural boundaries (punctuation, pauses)
```

**SRT Output Example**:
```srt
1
00:00:01,200 --> 00:00:04,800
Hey everyone, welcome back
to another video.

2
00:00:05,100 --> 00:00:08,300
Today I'm going to show you
something really cool.
```

#### 2.4 Subtitle Generation — ASS Format

**Purpose**: Styled subtitles with animations for professional captions.

**ASS Style Presets**:

| Style | Font | Size | Colors | Animation | Best For |
|-------|------|------|--------|-----------|----------|
| Classic | Roboto | 48 | White + black outline | Fade in/out | Long-form |
| Modern Pop | Montserrat Bold | 56 | White + colored highlight | Word-by-word | Shorts |
| Minimal | Inter | 40 | White + semi-transparent BG | Slide up | Corporate |
| Bold Impact | Impact | 72 | Yellow + black stroke | Scale pop | Motivational |

**Word-by-Word Highlight** (Modern Pop style):
```
Uses ASS \kf tags for karaoke-style progressive highlighting:
- Each word appears in white
- Active word highlights in accent color (e.g., #00AAFF)
- Creates the "bouncing word" effect popular on YouTube/TikTok
```

#### 2.5 Transcription Cache

**Purpose**: Avoid re-transcribing the same file on re-runs.

**Cache Strategy**:
```
workspace/cache/
├── {file_hash}_transcription.json    # Full transcription data
├── {file_hash}_segments.json         # Segment-level data
└── {file_hash}_words.json            # Word-level timestamps

Cache key = SHA256 hash of first 1MB + file size + modification time
On re-run: check cache → if hit, skip transcription → save ~25 min on 60-min video
```

---

### Phase 3: Intelligent Silence Removal & Smart Cuts

**Files**: `core/editor.py`  
**Estimated Time**: 2-3 days

#### 3.1 Silence Detection

**Purpose**: Identify silence/pause regions in the audio.

**Detection Algorithm**:
```
analyze_silence(audio_path, config)
├── Load audio waveform
├── Compute RMS energy per frame (frame_size=2048, hop=512)
├── Apply threshold: frames below -40dB = silence
├── Group consecutive silent frames into regions
├── Filter: keep only regions > 0.8 seconds
├── Apply margin: shrink each region by 0.3s on each side
└── Return List[SilenceRegion(start, end, duration)]
```

**Conservative Cut Rules (Pro Editor Philosophy)**:
```
✅ KEEP:
├── Pauses < 0.8 seconds (natural breathing)
├── Pauses after key statements (dramatic effect)
├── Brief "um"s and "ah"s (sounds natural)
└── Pauses at topic transitions

❌ REMOVE:
├── Dead air > 0.8 seconds (speaker clearly paused)
├── Long "ummm"s > 1.5 seconds
├── False starts followed by correction
└── Off-camera silence (shuffling papers, etc.)
```

#### 3.2 Auto-Editor Integration

**Purpose**: Use Auto-Editor as the primary cut engine.

**Command**:
```bash
auto-editor input.mp4 \
    --margin 0.3sec \
    --edit audio:threshold=0.04 \
    --video-codec copy \
    --no-open
```

**Parameters**:
- `--margin 0.3sec` — Keep 300ms of padding around speech
- `--edit audio:threshold=0.04` — Sensitivity level (0.04 = conservative)
- `--video-codec copy` — Don't re-encode during trimming (fast)
- `--no-open` — Don't open result in media player

**Fallback** (if Auto-Editor fails):
```python
# Pure FFmpeg silence detection
ffmpeg -i input.mp4 -af silencedetect=noise=-40dB:d=0.8 -f null -
# Parse output → extract silence timestamps → apply cuts manually
```

#### 3.3 Cut List Generation & Review

**Purpose**: Generate a reviewable list of proposed cuts before applying.

**Cut List Format**:
```json
{
  "source_file": "clip_001.mp4",
  "original_duration": 942.5,
  "cuts": [
    {"start": 45.2, "end": 47.8, "duration": 2.6, "type": "silence"},
    {"start": 123.1, "end": 124.5, "duration": 1.4, "type": "silence"},
    {"start": 301.7, "end": 305.2, "duration": 3.5, "type": "dead_air"}
  ],
  "total_cut_duration": 7.5,
  "new_duration": 935.0,
  "reduction_percent": 0.8
}
```

#### 3.4 Multi-Clip Merging

**Purpose**: Concatenate multiple trimmed clips into a single timeline.

**FFmpeg Concat**:
```bash
# Create file list
echo "file 'clip_001_trimmed.mp4'" > concat_list.txt
echo "file 'clip_002_trimmed.mp4'" >> concat_list.txt
echo "file 'clip_003_trimmed.mp4'" >> concat_list.txt

# Concatenate
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy merged.mp4
```

---

### Phase 4: Audio Pipeline

**Files**: `core/audio.py`  
**Estimated Time**: 2-3 days

#### 4.1 External Audio Synchronization

**Purpose**: Align external mic audio with video's camera audio.

**Algorithm — Cross-Correlation Alignment**:
```
sync_audio(video_audio, external_audio)
├── Extract audio from both sources (16kHz mono)
├── Compute cross-correlation between waveforms
│   └── numpy.correlate() or scipy.signal.correlate()
├── Find peak correlation → time offset in samples
├── Convert sample offset to seconds
├── Apply offset: trim or pad external audio
├── Verify sync: compare 3 random segments visually
└── Replace video audio with synced external audio
```

**FFmpeg Audio Replace**:
```bash
ffmpeg -i video.mp4 -i synced_mic.wav \
    -c:v copy -c:a aac -b:a 320k \
    -map 0:v:0 -map 1:a:0 \
    output_synced.mp4
```

#### 4.2 Noise Reduction

**Purpose**: Clean up background noise from the recording.

**Implementation**:
```python
import noisereduce as nr
import numpy as np

# Load audio
audio_data, sample_rate = load_audio(file_path)

# Option A: Stationary noise reduction (constant background hum)
cleaned = nr.reduce_noise(
    y=audio_data,
    sr=sample_rate,
    stationary=True,
    prop_decrease=0.75      # 75% noise reduction (not too aggressive)
)

# Option B: Non-stationary (variable noise like AC, traffic)
cleaned = nr.reduce_noise(
    y=audio_data,
    sr=sample_rate,
    stationary=False,
    prop_decrease=0.6
)
```

#### 4.3 Audio Equalization

**Purpose**: Apply EQ to clean up voice frequencies.

**FFmpeg EQ Chain**:
```bash
ffmpeg -i input.wav -af "
    highpass=f=80,           # Remove rumble below 80Hz
    lowpass=f=12000,         # Remove hiss above 12kHz
    equalizer=f=200:t=q:w=1:g=-2,   # Reduce muddiness
    equalizer=f=3000:t=q:w=1:g=3,   # Boost presence/clarity
    equalizer=f=5000:t=q:w=1:g=2    # Boost brightness
" output_eq.wav
```

#### 4.4 Dynamic Compression

**Purpose**: Even out volume levels (reduce difference between loud and quiet parts).

**FFmpeg Compressor**:
```bash
ffmpeg -i input.wav -af "
    compand=attacks=0.02:decays=0.3:points=-80/-80|-45/-30|-27/-20|-10/-10|0/-5:gain=3
" output_compressed.wav
```

#### 4.5 Loudness Normalization

**Purpose**: Match YouTube's loudness standard (EBU R128, -14 LUFS).

**Implementation**:
```python
import pyloudnorm as pyln

# Measure current loudness
meter = pyln.Meter(sample_rate)
current_lufs = meter.integrated_loudness(audio_data)

# Normalize to target
target_lufs = -14.0  # YouTube standard
normalized = pyln.normalize.loudness(audio_data, current_lufs, target_lufs)
```

**YouTube Audio Standards**:
```
Platform     │ Target LUFS │ True Peak
─────────────┼─────────────┼──────────
YouTube      │ -14 LUFS    │ -1.0 dBTP
Spotify      │ -14 LUFS    │ -1.0 dBTP
Apple Music  │ -16 LUFS    │ -1.0 dBTP
Broadcast    │ -23 LUFS    │ -1.0 dBTP
```

#### 4.6 Background Music Mixing & Ducking

**Purpose**: Mix background music at proper levels with automatic speech ducking.

**Ducking Algorithm**:
```
mix_with_ducking(speech_audio, music_audio, config)
├── Detect speech activity regions from transcription
│   └── Use word timestamps from Phase 2
├── Create volume envelope for music:
│   ├── During speech: -24 LUFS (quiet, behind voice)
│   ├── During gaps > 2s: -18 LUFS (slightly louder)
│   ├── Intro/Outro: -12 LUFS (featured)
│   └── Transitions: smooth 500ms fade between levels
├── Apply envelope to music track
├── Loop music if shorter than video
│   └── Crossfade loop points (2s overlap)
├── Mix speech + ducked music
└── Final loudness check on mixed output
```

**FFmpeg Sidechain Ducking**:
```bash
ffmpeg -i speech.wav -i music.wav -filter_complex "
    [1:a]volume=0.15[music_quiet];
    [0:a][music_quiet]amix=inputs=2:duration=first:dropout_transition=2
" mixed_output.wav
```

#### 4.7 Full Audio Mastering Chain

**Purpose**: Combine all audio processing in the correct order.

```
Raw Audio
  │
  ▼
┌───────────────────┐
│ Noise Reduction   │  Remove background noise
│ (noisereduce)     │  prop_decrease=0.75
└───────┬───────────┘
        ▼
┌───────────────────┐
│ EQ / Filtering    │  HPF 80Hz, LPF 12kHz
│ (FFmpeg)          │  Presence boost +3dB @ 3kHz
└───────┬───────────┘
        ▼
┌───────────────────┐
│ Compression       │  Even out dynamics
│ (FFmpeg compand)  │  Ratio ~3:1
└───────┬───────────┘
        ▼
┌───────────────────┐
│ Normalization     │  Target: -14 LUFS
│ (pyloudnorm)      │  True Peak: -1.0 dBTP
└───────┬───────────┘
        ▼
┌───────────────────┐
│ Music Ducking     │  Speech: -14 LUFS
│ & Mixing          │  Music (speech): -24 LUFS
│                   │  Music (gaps): -18 LUFS
└───────┬───────────┘
        ▼
  Final Mastered Audio
```

---

### Phase 5: Visual Polish & Branding

**Files**: `core/visuals.py`  
**Estimated Time**: 3-4 days

#### 5.1 Professional Caption Rendering

**Purpose**: Burn styled subtitles into the video.

**FFmpeg ASS Subtitle Burn-in**:
```bash
ffmpeg -i input.mp4 -vf "ass=subtitles.ass" -c:a copy output.mp4
```

**Caption Style Implementation (ASS)**:
```ass
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ModernPop,Montserrat,56,&H00FFFFFF,&H0000AAFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,50,50,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.20,0:00:04.80,ModernPop,,0,0,0,,{\kf30}Hey {\kf25}everyone, {\kf35}welcome {\kf20}back
```

**Word-by-Word Highlight Logic**:
```
For each subtitle segment:
├── Get word-level timestamps from transcription
├── Calculate display duration per word
├── Generate \kf tags (karaoke fill timing)
│   └── \kf{duration_in_centiseconds}
├── Apply style: inactive=white, active=accent color
└── Add fade-in/fade-out transitions between segments
```

#### 5.2 Intro Generation

**Purpose**: Create a professional intro sequence.

**Approaches (from simplest to most polished)**:

| Level | Method | Quality |
|-------|--------|---------|
| Basic | Title card with fade-in text | ★★★☆☆ |
| Good | Animated text + background image | ★★★★☆ |
| Pro | Pre-made template video + dynamic text overlay | ★★★★★ |

**FFmpeg Title Card**:
```bash
ffmpeg -f lavfi -i "color=c=0x1a1a2e:s=1920x1080:d=5" \
    -vf "drawtext=text='Video Title':fontfile=fonts/Montserrat-Bold.ttf:
         fontsize=72:fontcolor=white:x=(w-tw)/2:y=(h-th)/2:
         alpha='if(lt(t,1),t,if(gt(t,4),5-t,1))'" \
    -c:v libx264 -t 5 intro.mp4
```

#### 5.3 Outro Generation

**Purpose**: Create an end screen with subscribe CTA and video recommendations.

**Outro Layout**:
```
┌──────────────────────────────────────┐
│                                      │
│         Thanks for Watching!         │
│                                      │
│    ┌──────────┐    ┌──────────┐      │
│    │  Video 1 │    │  Video 2 │      │
│    │  (link)  │    │  (link)  │      │
│    └──────────┘    └──────────┘      │
│                                      │
│        🔔 Subscribe & Like!          │
│                                      │
└──────────────────────────────────────┘
```

#### 5.4 Lower Third Overlays

**Purpose**: Display speaker name/title at the bottom of the screen.

**FFmpeg Overlay**:
```bash
ffmpeg -i main_video.mp4 -i lower_third.png \
    -filter_complex "
        [1:v]format=rgba,fade=in:st=5:d=0.5:alpha=1,
             fade=out:st=12:d=0.5:alpha=1[lt];
        [0:v][lt]overlay=x=50:y=H-h-80:enable='between(t,5,12.5)'
    " output.mp4
```

#### 5.5 Watermark Application

**Purpose**: Add a semi-transparent channel logo.

**FFmpeg Watermark**:
```bash
ffmpeg -i input.mp4 -i logo.png \
    -filter_complex "[1:v]scale=120:-1,format=rgba,
        colorchannelmixer=aa=0.3[logo];
        [0:v][logo]overlay=W-w-20:H-h-20" \
    output.mp4
```

#### 5.6 YouTube Shorts Conversion (9:16)

**Purpose**: Crop horizontal footage to vertical for Shorts.

**Strategy**:
```
crop_for_shorts(video_path)
├── Detect face position in each scene
│   └── Use FFmpeg cropdetect or simple center-bias
├── Calculate 9:16 crop region centered on face
│   └── crop_width = height * 9/16
│   └── crop_x = face_center_x - crop_width/2
├── Apply crop + scale to 1080x1920
│   └── ffmpeg -vf "crop=607:1080:656:0,scale=1080:1920"
└── Re-render captions for vertical layout (larger text, center)
```

#### 5.7 Final Assembly

**Purpose**: Concatenate intro + main content + outro with transitions.

**FFmpeg Concat with Crossfade**:
```bash
ffmpeg -i intro.mp4 -i main_edited.mp4 -i outro.mp4 \
    -filter_complex "
        [0:v][1:v]xfade=transition=fade:duration=1:offset=4[v1];
        [v1][2:v]xfade=transition=fade:duration=1:offset=MAIN_DUR[vout];
        [0:a][1:a]acrossfade=d=1[a1];
        [a1][2:a]acrossfade=d=1[aout]
    " -map "[vout]" -map "[aout]" final.mp4
```

---

### Phase 6: Export, Validation & Backup

**Files**: `core/exporter.py`  
**Estimated Time**: 1-2 days

#### 6.1 YouTube-Optimized Export

**Long-form (16:9) Export Settings**:
```bash
ffmpeg -i input.mp4 \
    -c:v libx264 \
    -preset slow \                # Quality over speed
    -crf 18 \                     # High quality (18-23 range)
    -profile:v high \             # H.264 High Profile
    -level 4.1 \                  # Compatibility
    -pix_fmt yuv420p \            # Universal compatibility
    -bf 2 \                       # B-frames for compression
    -g 48 \                       # Keyframe every 2 sec (at 24fps)
    -c:a aac \
    -b:a 320k \                   # High quality audio
    -ar 48000 \                   # 48kHz sample rate
    -ac 2 \                       # Stereo
    -movflags +faststart \        # Web streaming optimization
    -metadata title="Video Title" \
    output_final.mp4
```

**Shorts (9:16) Export Settings**:
```bash
ffmpeg -i input_vertical.mp4 \
    -c:v libx264 -preset slow -crf 20 \
    -s 1080x1920 \                # Vertical resolution
    -c:a aac -b:a 256k -ar 48000 \
    -movflags +faststart \
    -t 120 \                      # Max 2 minutes
    output_short.mp4
```

#### 6.2 Export Validation

**Automated Quality Checks**:
```
validate_export(output_path)
├── File exists and size > 0 bytes
├── FFprobe metadata extraction succeeds
├── Video stream checks:
│   ├── Codec: H.264
│   ├── Resolution: 1920×1080 (or 1080×1920 for Shorts)
│   ├── Frame rate: ≥ 24fps
│   └── Pixel format: yuv420p
├── Audio stream checks:
│   ├── Codec: AAC
│   ├── Sample rate: 48000 Hz
│   └── Channels: 2 (stereo)
├── Duration check:
│   └── Within ±2 seconds of expected duration
├── Quick integrity scan:
│   └── ffmpeg -v error -i output.mp4 -f null -
│   └── Check for decode errors
├── A/V sync check:
│   └── Verify audio and video durations match (within 50ms)
└── Return ValidationResult
```

#### 6.3 Backup & File Preservation

**Backup Structure**:
```
project_backup_YYYYMMDD_HHMMSS/
├── originals/                    # Untouched source files
│   ├── video/
│   │   ├── clip_001.mp4
│   │   ├── clip_002.mp4
│   │   └── clip_003.mp4
│   ├── audio/
│   │   ├── mic_001.wav
│   │   └── mic_002.wav
│   └── music/
│       └── bg_track.mp3
├── intermediates/                # Processing artifacts
│   ├── transcriptions/
│   │   ├── clip_001.srt
│   │   └── clip_001.ass
│   ├── cut_lists/
│   │   └── cuts.json
│   └── temp_renders/
│       ├── clip_001_trimmed.mp4
│       └── merged.mp4
├── final/                        # Final outputs
│   ├── output_youtube.mp4
│   └── output_short.mp4
├── project_config.yaml           # Settings used for this render
└── processing_log.txt            # Full processing log
```

---

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Runtime** | Python | 3.14.5 | Core language |
| **Video Processing** | FFmpeg | 9.0.2 | Video/audio encode/decode |
| **Media Analysis** | FFprobe | 9.0.2 | Metadata extraction |
| **Speech AI** | faster-whisper | ≥1.0 | Local speech-to-text |
| **Auto Editing** | Auto-Editor | ≥25.0 | Silence removal |
| **Audio** | pydub | ≥0.25 | Audio manipulation |
| **Loudness** | pyloudnorm | ≥0.1 | EBU R128 normalization |
| **Noise** | noisereduce | ≥3.0 | Audio denoising |
| **Subtitles** | pysrt | ≥1.1 | SRT processing |
| **Images** | Pillow | ≥10.0 | Overlay graphics |
| **Math** | numpy | ≥1.24 | Signal processing |
| **CLI** | rich + click | ≥13.0 / ≥8.0 | Beautiful terminal UI |
| **Config** | pyyaml | ≥6.0 | Configuration files |

---

## Dependencies

### `requirements.txt`
```
# AI & Speech
faster-whisper>=1.0.0

# Video Editing
auto-editor>=25.0.0

# Audio Processing
pydub>=0.25.1
pyloudnorm>=0.1.1
noisereduce>=3.0.0

# Subtitle Processing
pysrt>=1.1.2

# Image Processing
Pillow>=10.0.0

# Numerical Computing
numpy>=1.24.0

# CLI & UX
rich>=13.0.0
click>=8.0.0
tqdm>=4.65.0
colorama>=0.4.6

# Configuration
pyyaml>=6.0
```

### Installation Command
```bash
py -m pip install -r requirements.txt
```

---

## Project Structure

```
AI-Editor/
├── docs/                          # 📖 Documentation (you are here)
│   ├── IMPLEMENTATION_PLAN.md     # This file
│   └── ARCHITECTURE.md            # How the tool works
│
├── main.py                        # 🚀 CLI entry point & orchestrator
├── config.py                      # ⚙️ Project-wide settings & defaults
├── requirements.txt               # 📦 Python dependencies
├── setup_ffmpeg.py                # 🔧 FFmpeg installer (one-time setup)
│
├── core/                          # 🧠 Core pipeline modules
│   ├── __init__.py
│   ├── inspector.py               # Phase 1: Media inspection
│   ├── transcriber.py             # Phase 2: Speech-to-text
│   ├── editor.py                  # Phase 3: Smart cuts
│   ├── audio.py                   # Phase 4: Audio pipeline
│   ├── visuals.py                 # Phase 5: Captions & branding
│   └── exporter.py                # Phase 6: Export & validate
│
├── utils/                         # 🔨 Shared utilities
│   ├── __init__.py
│   ├── ffmpeg_utils.py            # FFmpeg/FFprobe wrappers
│   ├── file_utils.py              # File management
│   ├── logger.py                  # Structured logging
│   └── validators.py              # Input/output validation
│
├── assets/                        # 🎨 Branding resources
│   ├── fonts/                     # Custom fonts
│   ├── intros/                    # Intro templates
│   ├── outros/                    # Outro templates
│   └── overlays/                  # Lower thirds, watermarks
│
├── templates/                     # 📐 Templates & presets
│   ├── caption_styles.ass         # ASS subtitle presets
│   └── project_config.yaml        # Default project config
│
├── input/                         # 📥 Drop raw files here
│   ├── video/                     # Raw video clips
│   ├── audio/                     # External mic recordings
│   └── music/                     # Background music
│
├── output/                        # 📤 Final exports
│   ├── final/                     # Rendered videos
│   ├── subtitles/                 # Generated subtitle files
│   └── logs/                      # Processing logs
│
├── workspace/                     # 🔄 Intermediate files
│   ├── temp/                      # Temporary processing
│   └── cache/                     # Transcription cache
│
├── tools/                         # 🔧 Local tool binaries
│   └── ffmpeg-9.0.2-.../          # FFmpeg installation
│       └── bin/
│           ├── ffmpeg.exe
│           ├── ffprobe.exe
│           └── ffplay.exe
│
└── tests/                         # 🧪 Test suite
    ├── test_inspector.py
    ├── test_transcriber.py
    ├── test_editor.py
    └── test_samples/              # Small test media files
```

---

## Implementation Timeline

```
Week 1                          Week 2                          Week 3
├── Day 1-2: Phase 1            ├── Day 7-8: Phase 4            ├── Day 12-13: Phase 6
│   ├── Environment checker     │   ├── Audio sync              │   ├── Export settings
│   ├── Media scanner           │   ├── Noise reduction          │   ├── Validation
│   ├── FFprobe inspector       │   ├── Loudness normalization   │   ├── Backup system
│   └── Validation              │   └── Music ducking            │   └── Report generation
│                               │                                │
├── Day 3-4: Phase 2            ├── Day 9-11: Phase 5            ├── Day 14: Integration
│   ├── Audio extraction        │   ├── Caption renderer         │   ├── End-to-end testing
│   ├── faster-whisper setup    │   ├── Intro/outro gen          │   ├── CLI polish
│   ├── SRT generation          │   ├── Lower thirds             │   └── Documentation
│   └── ASS generation          │   ├── Watermarks               │
│                               │   └── Shorts cropping          │
├── Day 5-6: Phase 3            │                                │
│   ├── Silence detection       │                                │
│   ├── Auto-Editor setup       │                                │
│   ├── Cut list generation     │                                │
│   └── Clip merging            │                                │
```

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| faster-whisper slow on CPU | Transcription takes 30+ min for long videos | Use `small` model with int8, enable VAD filter to skip silence |
| Auto-Editor compatibility issues | Can't detect silence properly | Fallback to FFmpeg silencedetect filter |
| Audio sync drift | External mic gets out of sync | Cross-correlation alignment + manual offset option |
| Large file sizes (60 min) | Memory issues during processing | Process in chunks, use FFmpeg stream processing |
| Font rendering differences | Captions look different on different systems | Bundle fonts in assets/fonts/, use absolute paths |
| Python 3.14 compatibility | Some packages may not support 3.14 yet | Pin compatible versions, test during setup |

---

## Success Criteria

The tool is "done" when it can:

- [x] Scan and validate input media files *(Phase 1 — `core/inspector.py`)*
- [x] Transcribe speech on CPU with word-level timestamps *(Phase 2 — `core/transcriber.py`)*
- [x] Remove dead air while keeping natural speech flow *(Phase 3 — `core/editor.py`)*
- [x] Sync external mic audio within ±50ms accuracy *(Phase 4 — `core/audio.py`)*
- [x] Normalize audio to -14 LUFS YouTube standard *(Phase 4 — `core/audio.py`)*
- [x] Mix background music with automatic sidechain ducking *(Phase 4 — `core/audio.py`)*
- [x] Render professional animated ASS captions *(Phase 5 — `core/visuals.py`)*
- [x] Generate intro/outro sequences with title fades *(Phase 5 — `core/visuals.py`)*
- [x] Export YouTube-optimized 1080p MP4 (+faststart, Closed GOP) *(Phase 6 — `core/exporter.py`)*
- [x] Export 9:16 Shorts with ambient blur-fill *(Phase 5/6 — `core/visuals.py`)*
- [x] Validate every export automatically with QA checks *(Phase 6 — `core/exporter.py`)*
- [x] Preserve all original files in backup *(Phase 6 — `core/exporter.py`)*
- [x] Process video end-to-end unattended in 1-Click *(Phase 6 — `main.py process`)*
