"""
Global configuration and directory constants for AI-Editor.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# --- Base Directories ---
BASE_DIR = Path(__file__).resolve().parent

# Input Directories
INPUT_DIR = BASE_DIR / "input"
INPUT_VIDEO_DIR = INPUT_DIR / "video"
INPUT_AUDIO_DIR = INPUT_DIR / "audio"
INPUT_MUSIC_DIR = INPUT_DIR / "music"

# Output Directories
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FINAL_DIR = OUTPUT_DIR / "final"
OUTPUT_SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
OUTPUT_LOGS_DIR = OUTPUT_DIR / "logs"

# Workspace & Cache Directories
WORKSPACE_DIR = BASE_DIR / "workspace"
TEMP_DIR = WORKSPACE_DIR / "temp"
CACHE_DIR = WORKSPACE_DIR / "cache"

# Assets & Templates
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
SFX_DIR = ASSETS_DIR / "sfx"
GRAPHICS_DIR = ASSETS_DIR / "graphics"
ANIMATED_GRAPHICS_DIR = GRAPHICS_DIR / "animated"
TEMPLATES_DIR = BASE_DIR / "templates"


def ensure_directories():
    """Ensure all required project directories exist."""
    dirs = [
        INPUT_VIDEO_DIR,
        INPUT_AUDIO_DIR,
        INPUT_MUSIC_DIR,
        OUTPUT_FINAL_DIR,
        OUTPUT_SUBTITLES_DIR,
        OUTPUT_LOGS_DIR,
        TEMP_DIR,
        CACHE_DIR,
        FONTS_DIR,
        SFX_DIR,
        GRAPHICS_DIR,
        ANIMATED_GRAPHICS_DIR,
        TEMPLATES_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    try:
        from utils.sfx_generator import ensure_sfx_assets
        ensure_sfx_assets()
    except Exception:
        pass

    try:
        from utils.graphics_generator import ensure_graphic_assets
        ensure_graphic_assets()
    except Exception:
        pass


@dataclass
class TranscriptionConfig:
    model_size: str = "large-v3-turbo"          # tiny, base, small, medium, large-v3-turbo
    device: str = "cpu"                # cpu or cuda
    compute_type: str = "int8"         # int8 quantization for CPU performance
    cpu_threads: int = 4               # optimal for 8-core CPU without freezing system
    language: Optional[str] = "te"     # Default to Telugu ("te") or "auto"
    task: str = "translate"            # Default: translates foreign speech (e.g. Telugu) to English script
    initial_prompt: str = "Telugu speech translated into fluent, modern English subtitles for YouTube video."
    beam_size: int = 5
    word_timestamps: bool = True
    vad_filter: bool = True            # Voice Activity Detection (skips silence)
    vad_min_silence_ms: int = 400
    vad_speech_pad_ms: int = 250


@dataclass
class SubtitleConfig:
    max_chars_per_line: int = 38       # Pro guideline: 32-42 chars for YouTube/Shorts
    max_lines: int = 2
    font_name: str = "Arial"           # Universal fallback; custom fonts in assets/fonts
    font_size: int = 52                # 1080p scale
    primary_color: str = "&H00FFFFFF"  # White text (ASS format: &HAABBGGRR)
    secondary_color: str = "&H0000E5FF"# Ultra-bright Electric Gold accent for active words
    outline_color: str = "&H00000000"  # Black outline
    outline_width: int = 4             # High-contrast 4px outline
    shadow_width: int = 2              # 2px drop-shadow for 3D depth
    margin_bottom: int = 68            # Bottom safe zone (above player controls)
    kinetic_bounce_enabled: bool = True# Spring bounce scale animation on active spoken word
    background_box: bool = False       # Optional opaque bounding box


@dataclass
class EditingConfig:
    engine: str = "auto"                 # "auto", "ffmpeg", "auto-editor"
    silence_threshold_db: float = -38.0  # Silence threshold in dB (typical speech noise floor: -35 to -42)
    min_silence_duration: float = 0.8    # 5+ YOE rule: only cut pauses >= 0.8s (preserves breathing room)
    lead_in_margin: float = 0.30         # 300ms speech lead-in padding (prevents clipped consonants)
    lead_out_margin: float = 0.35        # 350ms speech lead-out padding (preserves room tone)
    crossfade_duration: float = 0.02     # 20ms audio micro-fade to eliminate clicks/pops
    video_codec: str = "libx264"         # H.264 encode
    crf: int = 18                        # Visually lossless quality
    preset: str = "fast"                 # Balanced quality & encoding speed for laptop


@dataclass
class AudioConfig:
    target_lufs: float = -14.0           # YouTube standard integrated loudness (-14 LUFS)
    true_peak: float = -1.0              # YouTube standard True Peak (-1.0 dBTP)
    lra: float = 11.0                    # Target Loudness Range
    high_pass_hz: int = 80               # High-pass filter cuts mic thumps & desk rumble
    low_pass_hz: int = 12000             # Low-pass filter cuts high-frequency hiss
    presence_boost_db: float = 2.5       # Vocal clarity boost at 3000 Hz
    compression_threshold_db: float = -21.0
    compression_ratio: float = 3.0       # Gentle 3:1 voice leveling

    # Human-Grade Noise Suppression & Audio Comfort
    noise_gate_enabled: bool = True      # Silences phone handling noise, rustling, and loud breaths
    noise_gate_threshold_db: float = -36.0 # Mutes any sound quieter than -36 dB
    noise_gate_attack_ms: int = 10
    noise_gate_release_ms: int = 120
    spectral_denoise_enabled: bool = True # Removes background room hiss, AC hum, and preamp noise
    spectral_denoise_amount: float = 12.0 # afftdn noise reduction in dB
    spectral_noise_floor: float = -25.0
    micro_fade_in_sec: float = 0.10      # 100ms micro audio fade-in to prevent harsh start clicks/pops

    music_base_volume: float = 0.16      # Background music baseline level (16%)
    ducking_ratio: float = 6.0           # Sidechain ducking compression ratio
    ducking_threshold: float = 0.03      # Sensitivity threshold for speech ducking
    deesser_enabled: bool = True         # Vocal de-esser tames harsh S/T sibilance
    sfx_enabled: bool = True             # Micro-sound effects for badge popups & camera zooms
    sfx_pop_volume: float = 0.22         # Subtle pop level
    sfx_flash_volume: float = 0.45       # Camera shutter & electronic flash cut level (45%)
    sfx_whoosh_volume: float = 0.40      # Tactile whoosh cut level (40%)
    sfx_thump_volume: float = 0.35       # Sub-bass thump impact level


@dataclass
class VisualsConfig:
    intro_enabled: bool = True
    intro_title: str = "AI Video Editor"
    intro_subtitle: str = "Automated Production Pipeline"
    intro_duration: float = 3.5          # Seconds

    outro_enabled: bool = True
    outro_title: str = "Thanks for Watching!"
    outro_subtitle: str = "Like & Subscribe for More Content"
    outro_duration: float = 4.0          # Seconds

    lower_third_enabled: bool = True
    speaker_name: str = "Content Creator"
    speaker_title: str = "Video Host"
    lower_third_start: float = 2.0
    lower_third_duration: float = 5.0

    watermark_enabled: bool = True
    watermark_text: str = "@MyChannel"
    watermark_opacity: float = 0.40

    # Right-side Highlight Callout Badges (attention-grabbing keyword popups)
    callouts_enabled: bool = True
    callout_duration: float = 1.3         # Active hold duration in seconds (~1.3s with micro-fade)
    callout_min_interval: float = 3.5     # Minimum seconds between callout appearances
    custom_highlights: Optional[str] = None  # Comma-separated custom keywords (e.g. "AI, Python")

    # Dynamic Virtual Multi-Cam Zooms (Punch-In / Punch-Out pattern interrupts)
    zooms_enabled: bool = True
    zoom_scale: float = 1.15              # 1.15x close-up framing keeps full 1080p sharpness
    zoom_duration: float = 3.8            # Average close-up hold duration (seconds)
    zoom_min_interval: float = 5.5        # Minimum seconds wide master holds between zooms
    zoom_headroom_factor: float = 0.38    # 38% top-anchor preserves professional eye-level headroom

    # Cinematic Visual Polish (Natural Studio Grade & YouTube package)
    color_grade_enabled: bool = True      # Studio broadcast polish (gentle contrast & skin tones)
    grade_contrast: float = 1.015         # Tamed natural contrast
    grade_saturation: float = 1.03        # Tamed natural vibrance
    grade_gamma: float = 1.00             # Preserves midtone skin exposure
    grade_s_curve: str = "0/0 0.25/0.235 0.75/0.775 1/1"  # Mild broadcast-safe S-curve
    grade_vignette: str = "PI/14"         # Ultra-soft 12° edge falloff
    vignette_enabled: bool = True         # Soft edge vignette naturally focuses viewer on speaker
    youtube_package_enabled: bool = True  # Generate upload-ready YouTube description & chapters

    # High-Retention 5+ YOE Features
    cold_open_enabled: bool = True        # 4s dynamic hook teaser prepended to video
    cold_open_duration: float = 4.0       # Hook teaser length (seconds)
    broll_enabled: bool = True            # Automatic analogy visual cutaways (house, website, apps)
    retention_bar_enabled: bool = False   # Disabled: clean borderless top of video frame
    retention_bar_color: str = "0x00F0FF" # Cyber Cyan retention line (if enabled)
    impact_enabled: bool = True           # Sub-bass thump & micro-shake on peak takeaways
    kit_name: str = "creator_elite"       # Default production kit
    motion_graphics_enabled: bool = True  # 5+ YOE kinetic animated motion graphics (.mov alpha overlay)
    background_defocus_enabled: bool = False # Disabled: keep video 100% sharp and unblurred

    shorts_mode: bool = False             # 9:16 vertical mode (1080x1920)
    shorts_crop_style: str = "blur_fill"  # "blur_fill" or "center_crop"



