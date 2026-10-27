"""
Procedural Multi-Sound SFX Kit Generator for AI-Editor.
Generates a complete 12-sound tactile micro-audio library locally using pure Python wave & math.
No external network downloads or third-party audio libraries required.
Includes variation profiles for pops, whooshes, accents, and sub-bass impacts.
"""

import math
import wave
import struct
import random
from pathlib import Path
from typing import Tuple, Dict, List

import config


def _write_mono_wav(output_path: Path, samples: List[float], sample_rate: int = 48000, max_amp: int = 24000) -> Path:
    """Helper to write normalized float samples (-1.0 to 1.0) into 16-bit PCM WAV."""
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for s in samples:
            pcm_val = int(s * max_amp)
            frames.extend(struct.pack("<h", max(-32767, min(32767, pcm_val))))
        wav_file.writeframes(frames)
    return output_path


# --- 1. POPS & CLICKS ---

def generate_pop_clean(output_path: Path, sample_rate: int = 48000, duration: float = 0.08) -> Path:
    """Modern, clean UI pop (550Hz -> 1150Hz sweep with exponential decay)."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = (p / 0.10) if p < 0.10 else math.exp(-6.0 * (p - 0.10))
        freq = 550 + 600 * math.sin(p * (math.pi / 2))
        samples.append(math.sin(2.0 * math.pi * freq * t) * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=24000)


def generate_pop_bubble(output_path: Path, sample_rate: int = 48000, duration: float = 0.09) -> Path:
    """Acoustic water/bubble pop (420Hz -> 880Hz soft round tone with subtle overtone)."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = (p / 0.15) if p < 0.15 else math.exp(-5.5 * (p - 0.15))
        freq = 420 + 460 * (p ** 1.4)
        tone = math.sin(2.0 * math.pi * freq * t) + 0.25 * math.sin(4.0 * math.pi * freq * t)
        samples.append(tone * env * 0.8)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=22000)


def generate_pop_wooden(output_path: Path, sample_rate: int = 48000, duration: float = 0.07) -> Path:
    """Warm organic wooden block tap (damped 480Hz triangle wave with fast attack)."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = (p / 0.06) if p < 0.06 else math.exp(-9.0 * (p - 0.06))
        # Triangle harmonic mix
        f = 480 - 120 * p
        tone = math.sin(2.0 * math.pi * f * t) + 0.3 * math.sin(6.0 * math.pi * f * t)
        samples.append(tone * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=23000)


def generate_snap_click(output_path: Path, sample_rate: int = 48000, duration: float = 0.05) -> Path:
    """Snappy tactile micro-click (1400Hz sharp impulse with high-frequency pop)."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = (p / 0.04) if p < 0.04 else math.exp(-12.0 * (p - 0.04))
        f = 1400 - 800 * math.sqrt(p)
        samples.append(math.sin(2.0 * math.pi * f * t) * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=25000)


# --- 2. CAMERA SHUTTERS & WHOOSHES ---

def generate_camera_flash(output_path: Path, sample_rate: int = 48000, duration: float = 0.28) -> Path:
    """
    Authentic Studio DSLR Mechanical Shutter & Electronic Flash SFX for Zoom-In Cuts.
    Layer 1: Front mechanical curtain click & mirror flip (t=0ms to 18ms).
    Layer 2: Xenon strobe flash discharge pop & ionizing air spark (t=20ms to 60ms).
    Layer 3: Rear curtain mechanical closing snap (t=38ms to 75ms).
    Layer 4: High-voltage flash capacitor recharge whine shimmer (t=65ms to 240ms).
    """
    num_samples = int(sample_rate * duration)
    rng = random.Random(404)
    samples = []

    for i in range(num_samples):
        t = i / sample_rate

        # --- Layer 1: Front Curtain Click (Mirror Flip at t=0.004s) ---
        c1 = 0.0
        if 0.003 <= t < 0.022:
            dt1 = t - 0.003
            c1_env = math.exp(-140.0 * dt1)
            c1 = (math.sin(2.0 * math.pi * 3200.0 * dt1) * 0.6 +
                  math.sin(2.0 * math.pi * 750.0 * dt1) * 0.4) * c1_env

        # --- Layer 2: Xenon Flash Discharge Pop & Spark (Fires at t=0.018s) ---
        flash_pop = 0.0
        if 0.018 <= t < 0.080:
            dt2 = t - 0.018
            # Sudden sub-bass air displacement (160Hz sliding to 52Hz)
            sub_env = math.exp(-40.0 * dt2)
            f_sub = 160.0 - 108.0 * (dt2 / 0.062)
            sub_wave = math.sin(2.0 * math.pi * f_sub * dt2) * sub_env

            # High-voltage ionization air spark (crackle)
            spark_env = math.exp(-130.0 * dt2)
            white_spark = (rng.random() * 2.0 - 1.0) * spark_env * 0.90

            flash_pop = sub_wave * 1.25 + white_spark

        # --- Layer 3: Rear Curtain Close Snap ("Chik" at t=0.038s) ---
        c2 = 0.0
        if 0.038 <= t < 0.085:
            dt3 = t - 0.038
            c2_env = math.exp(-115.0 * dt3)
            c2 = (math.sin(2.0 * math.pi * 2400.0 * dt3) * 0.7 +
                  math.sin(2.0 * math.pi * 480.0 * dt3) * 0.5) * c2_env

        # --- Layer 4: Capacitor Recharge Whine (Gentle high-pitch shimmer t=0.065s - 0.24s) ---
        whine = 0.0
        if 0.065 <= t < 0.250:
            dt4 = t - 0.065
            p4 = dt4 / 0.185
            whine_env = math.sin(math.pi * p4) ** 1.3
            f_whine = 5800.0 + 5200.0 * (p4 ** 1.4)
            whine = math.sin(2.0 * math.pi * f_whine * t) * whine_env * 0.14

        # Composite mix with warm saturation
        raw = c1 * 0.85 + flash_pop * 1.35 + c2 * 0.95 + whine
        saturated = math.tanh(raw * 1.35)
        samples.append(saturated)

    return _write_mono_wav(output_path, samples, sample_rate, max_amp=31000)


def generate_whoosh_fast(output_path: Path, sample_rate: int = 48000, duration: float = 0.20) -> Path:
    """
    Creator-grade Whip Swoosh with Sub-Bass Thump for Punch-In Camera Zooms.
    Layer 1: Resonant 2-pole state-variable bandpass pink/brown noise sweep (320Hz -> 2600Hz).
    Layer 2: 82Hz -> 54Hz sub-bass transient punch (hits viewer with physical weight).
    Layer 3: 3.2kHz high-transient micro-whip snap right at the cut apex.
    """
    num_samples = int(sample_rate * duration)
    rng = random.Random(101)

    low = 0.0
    band = 0.0
    samples = []
    apex_p = 0.72  # Peak acoustic energy lands at 72% of duration (for 50ms pre-roll)

    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples

        # 1. Asymmetric Envelope rising quickly to apex, then cutting
        if p < apex_p:
            env_noise = (p / apex_p) ** 2.2
        else:
            env_noise = math.exp(-14.0 * (p - apex_p))

        # 2. Resonant bandpass filter sweeping upwards from 320Hz to 2800Hz
        f_cut = 320.0 + 2480.0 * (p ** 1.8)
        f_norm = 2.0 * math.sin(math.pi * min(0.45, f_cut / sample_rate))
        q = 0.38  # Resonant bandwidth

        white = rng.random() * 2.0 - 1.0
        low += f_norm * band
        high = white - low - q * band
        band += f_norm * high
        noise_val = band * env_noise

        # 3. Sub-Bass Thump (visceral 82Hz punch hitting right at apex)
        sub_val = 0.0
        if p >= apex_p - 0.16:
            t_sub = (p - (apex_p - 0.16)) * duration
            sub_env = math.exp(-22.0 * t_sub)
            sub_freq = 82.0 - 28.0 * (p - (apex_p - 0.16))
            sub_val = math.sin(2.0 * math.pi * sub_freq * t_sub) * sub_env * 0.95

        # 4. High-transient whip/snap (tactile crack at apex)
        snap_val = 0.0
        if abs(p - apex_p) < 0.08:
            snap_env = math.exp(-60.0 * abs(p - apex_p))
            snap_val = math.sin(2.0 * math.pi * 3200.0 * t) * snap_env * 0.45

        # Composite mix with warm soft-clipping saturation
        raw_mix = (noise_val * 1.35) + (sub_val * 1.10) + snap_val
        saturated = math.tanh(raw_mix * 1.25)
        samples.append(saturated)

    return _write_mono_wav(output_path, samples, sample_rate, max_amp=29000)


def generate_whoosh_smooth(output_path: Path, sample_rate: int = 48000, duration: float = 0.25) -> Path:
    """
    Smooth Airy Suction / Pressure Release for Camera Pull-Back (Wide Shot Reset).
    Sweeps downward from 2200Hz down to 360Hz with soft bell dispersion.
    Zero sub-bass thump to leave space for speech while widening the perspective.
    """
    num_samples = int(sample_rate * duration)
    rng = random.Random(202)

    low = 0.0
    band = 0.0
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples

        # Smooth bell envelope
        env = math.sin(math.pi * p) ** 1.6

        # Descending frequency sweep
        f_cut = 2200.0 - 1800.0 * (p ** 0.85)
        f_norm = 2.0 * math.sin(math.pi * min(0.45, f_cut / sample_rate))
        q = 0.45  # Softer Q for airy dispersion

        white = rng.random() * 2.0 - 1.0
        low += f_norm * band
        high = white - low - q * band
        band += f_norm * high

        # Soft harmonic undertone for acoustic warmth (without heavy bass kick)
        body = math.sin(2.0 * math.pi * (160.0 - 60.0 * p) * t) * 0.20

        raw_mix = (band * 1.20 + body) * env
        saturated = math.tanh(raw_mix * 1.15)
        samples.append(saturated)

    return _write_mono_wav(output_path, samples, sample_rate, max_amp=26000)


def generate_whoosh_deep(output_path: Path, sample_rate: int = 48000, duration: float = 0.32) -> Path:
    """
    Deep cinematic riser whoosh with sub air for high-gravity takeaways and chapter breaks.
    """
    num_samples = int(sample_rate * duration)
    rng = random.Random(303)

    low = 0.0
    band = 0.0
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples

        env = math.sin(math.pi * p) ** 1.4
        f_cut = 180.0 + 800.0 * (p ** 1.5)
        f_norm = 2.0 * math.sin(math.pi * min(0.45, f_cut / sample_rate))
        q = 0.35

        white = rng.random() * 2.0 - 1.0
        low += f_norm * band
        high = white - low - q * band
        band += f_norm * high

        sub = math.sin(2.0 * math.pi * (65.0 + 45.0 * p) * t) * 0.65
        raw_mix = (band * 0.90 + sub) * env
        saturated = math.tanh(raw_mix * 1.20)
        samples.append(saturated)

    return _write_mono_wav(output_path, samples, sample_rate, max_amp=28000)


# --- 3. ACCENTS & CHIMES ---

def generate_ding_chime(output_path: Path, sample_rate: int = 48000, duration: float = 0.18) -> Path:
    """Subtle high-value takeaway chime (1760Hz pure harmonic bell with shimmer)."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = (p / 0.05) if p < 0.05 else math.exp(-5.0 * (p - 0.05))
        tone = (
            math.sin(2.0 * math.pi * 1760.0 * t) * 0.70 +
            math.sin(2.0 * math.pi * 3520.0 * t) * 0.22 +
            math.sin(2.0 * math.pi * 5280.0 * t) * 0.08
        )
        samples.append(tone * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=20000)


def generate_tech_blip(output_path: Path, sample_rate: int = 48000, duration: float = 0.11) -> Path:
    """Two-tone futuristic UI blip (880Hz -> 1320Hz micro-arpeggio)."""
    num_samples = int(sample_rate * duration)
    half = num_samples // 2
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        if i < half:
            p = i / half
            env = math.exp(-4.5 * p)
            tone = math.sin(2.0 * math.pi * 880.0 * t)
        else:
            p = (i - half) / half
            env = math.exp(-4.5 * p)
            tone = math.sin(2.0 * math.pi * 1320.0 * t)
        samples.append(tone * env * 0.85)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=22000)


def generate_sparkle_accent(output_path: Path, sample_rate: int = 48000, duration: float = 0.14) -> Path:
    """Bright cascading micro-sparkle for key takeaways."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = math.exp(-5.5 * p)
        tone = (
            math.sin(2.0 * math.pi * (1200.0 + 800.0 * p) * t) * 0.65 +
            math.sin(2.0 * math.pi * (2400.0 + 1600.0 * p) * t) * 0.35
        )
        samples.append(tone * env * 0.8)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=21000)


# --- 4. IMPACTS & SUB DROPS ---

def generate_thump_sub(output_path: Path, sample_rate: int = 48000, duration: float = 0.18) -> Path:
    """78Hz -> 36Hz exponential sub-bass pitch drop for peak weight."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = (p / 0.08) if p < 0.08 else math.exp(-7.5 * (p - 0.08))
        freq = 78.0 - 42.0 * math.sqrt(p)
        tone = math.sin(2.0 * math.pi * freq * t)
        samples.append(tone * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=28000)


def generate_punch_hit(output_path: Path, sample_rate: int = 48000, duration: float = 0.14) -> Path:
    """Crisp punch impact: 140Hz attack click seamlessly coupled to 48Hz body."""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = (p / 0.05) if p < 0.05 else math.exp(-9.0 * (p - 0.05))
        f = 140.0 - 92.0 * (p ** 0.8)
        tone = math.sin(2.0 * math.pi * f * t)
        samples.append(tone * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=27000)


def _convert_to_wav(src_path: Path, dst_path: Path, sample_rate: int = 48000) -> Path:
    """Converts MP3 or other audio to 16-bit mono PCM WAV using FFmpeg."""
    import subprocess
    dst_path = Path(dst_path).resolve()
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src_path),
        "-ar", str(sample_rate),
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(dst_path)
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
    except Exception as e:
        print(f"⚠️ Warning: Could not convert {src_path.name} with FFmpeg: {e}")
    return dst_path


# --- SFX KIT ASSET MANAGER ---

def ensure_sfx_kit(force_rebuild: bool = False) -> Dict[str, List[Path]]:
    """
    Generates and organizes the full tactile micro-audio kit into assets/sfx/kit/.
    Supports custom user SFX overrides (WAV or MP3) from assets/sfx/ or input/sfx/.
    Returns a dictionary mapping SFX categories to lists of variant paths.
    """
    sfx_dir = getattr(config, "SFX_DIR", config.ASSETS_DIR / "sfx")
    kit_dir = sfx_dir / "kit"
    kit_dir.mkdir(parents=True, exist_ok=True)

    version_marker = kit_dir / "kit_v4.marker"
    needs_rebuild = force_rebuild or not version_marker.exists()

    pops_dir = kit_dir / "pops"
    whooshes_dir = kit_dir / "whooshes"
    flash_dir = kit_dir / "flash"
    accents_dir = kit_dir / "accents"
    impacts_dir = kit_dir / "impacts"

    for d in [pops_dir, whooshes_dir, flash_dir, accents_dir, impacts_dir]:
        d.mkdir(parents=True, exist_ok=True)

    manifest = {
        "flash": [
            ("camera_flash.wav", generate_camera_flash, flash_dir),
        ],
        "pops": [
            ("pop_clean.wav", generate_pop_clean, pops_dir),
            ("pop_bubble.wav", generate_pop_bubble, pops_dir),
            ("pop_wooden.wav", generate_pop_wooden, pops_dir),
            ("snap_click.wav", generate_snap_click, pops_dir),
        ],
        "whooshes": [
            ("whoosh_fast.wav", generate_whoosh_fast, whooshes_dir),
            ("whoosh_smooth.wav", generate_whoosh_smooth, whooshes_dir),
            ("whoosh_deep.wav", generate_whoosh_deep, whooshes_dir),
        ],
        "accents": [
            ("ding_chime.wav", generate_ding_chime, accents_dir),
            ("tech_blip.wav", generate_tech_blip, accents_dir),
            ("sparkle_accent.wav", generate_sparkle_accent, accents_dir),
        ],
        "impacts": [
            ("thump_sub.wav", generate_thump_sub, impacts_dir),
            ("punch_hit.wav", generate_punch_hit, impacts_dir),
        ]
    }

    categorized_paths: Dict[str, List[Path]] = {
        "flash": [],
        "pops": [],
        "whooshes": [],
        "accents": [],
        "impacts": []
    }

    for cat, items in manifest.items():
        for filename, gen_fn, target_dir in items:
            p = target_dir / filename
            if needs_rebuild or not p.exists() or p.stat().st_size == 0:
                gen_fn(p)
            categorized_paths[cat].append(p)

    # 1. Prioritize user's camera_flash.mp3 in assets/sfx/
    user_flash_mp3 = sfx_dir / "camera_flash.mp3"
    if user_flash_mp3.exists():
        converted_flash = flash_dir / "camera_flash.wav"
        _convert_to_wav(user_flash_mp3, converted_flash)
        _convert_to_wav(user_flash_mp3, sfx_dir / "camera_flash.wav")
        categorized_paths["flash"].insert(0, converted_flash)

    # 2. Check for other custom user SFX overrides (WAV or MP3 in assets/sfx, assets/sfx/custom or input/sfx)
    custom_dirs = [sfx_dir, sfx_dir / "custom", config.INPUT_DIR / "sfx"]
    for cdir in custom_dirs:
        if cdir.exists():
            for ext in ("*.wav", "*.mp3"):
                for custom_file in cdir.glob(ext):
                    if kit_dir in custom_file.parents or custom_file.name in ("pop_badge.wav", "whoosh_zoom.wav", "thump_impact.wav", "camera_flash.wav", "camera_flash.mp3"):
                        continue
                    active_file = custom_file
                    if custom_file.suffix.lower() == ".mp3":
                        conv_wav = kit_dir / f"{custom_file.stem}_user.wav"
                        _convert_to_wav(custom_file, conv_wav)
                        active_file = conv_wav

                    stem_lower = custom_file.stem.lower()
                    if any(k in stem_lower for k in ("flash", "camera", "shutter", "snap")):
                        categorized_paths["flash"].insert(0, active_file)
                    elif any(k in stem_lower for k in ("whoosh_in", "zoom_in", "whip", "punch_in")):
                        categorized_paths["whooshes"].insert(0, active_file)
                    elif any(k in stem_lower for k in ("whoosh_out", "zoom_out", "release", "pull_back")):
                        categorized_paths["whooshes"].insert(1 if len(categorized_paths["whooshes"]) > 0 else 0, active_file)
                    elif any(k in stem_lower for k in ("pop", "click")):
                        categorized_paths["pops"].insert(0, active_file)
                    elif any(k in stem_lower for k in ("thump", "impact", "bass")):
                        categorized_paths["impacts"].insert(0, active_file)

    # Legacy fallbacks in assets/sfx/
    legacy_flash = sfx_dir / "camera_flash.wav"
    legacy_pop = sfx_dir / "pop_badge.wav"
    legacy_whoosh = sfx_dir / "whoosh_zoom.wav"
    legacy_thump = sfx_dir / "thump_impact.wav"

    if (needs_rebuild or not legacy_flash.exists()) and not user_flash_mp3.exists():
        generate_camera_flash(legacy_flash)
    if needs_rebuild or not legacy_pop.exists():
        generate_pop_clean(legacy_pop)
    if needs_rebuild or not legacy_whoosh.exists():
        generate_whoosh_fast(legacy_whoosh)
    if needs_rebuild or not legacy_thump.exists():
        generate_thump_sub(legacy_thump)

    if needs_rebuild:
        try:
            version_marker.write_text("v4_user_mp3_support", encoding="utf-8")
        except Exception:
            pass

    return categorized_paths


def ensure_sfx_assets() -> Tuple[Path, Path, Path]:
    """Legacy backward compatibility: returns (pop, whoosh, thump)."""
    kit = ensure_sfx_kit()
    sfx_dir = getattr(config, "SFX_DIR", config.ASSETS_DIR / "sfx")
    return sfx_dir / "pop_badge.wav", sfx_dir / "whoosh_zoom.wav", sfx_dir / "thump_impact.wav"
