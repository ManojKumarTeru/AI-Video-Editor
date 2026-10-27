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


# --- 2. WHOOSHES & TRANSITIONS ---

def generate_whoosh_fast(output_path: Path, sample_rate: int = 48000, duration: float = 0.15) -> Path:
    """Snappy 150ms camera cut whoosh (140Hz -> 380Hz -> 100Hz parabolic arc)."""
    num_samples = int(sample_rate * duration)
    rng = random.Random(101)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = math.sin(math.pi * p) ** 2.0
        freq = 140 + 240 * math.sin(math.pi * p)
        tone = math.sin(2.0 * math.pi * freq * t)
        air = (rng.random() * 2.0 - 1.0) * 0.15
        samples.append((tone * 0.85 + air) * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=22000)


def generate_whoosh_smooth(output_path: Path, sample_rate: int = 48000, duration: float = 0.24) -> Path:
    """Soft 240ms airy breeze sweep (100Hz -> 280Hz -> 80Hz bell envelope)."""
    num_samples = int(sample_rate * duration)
    rng = random.Random(202)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = math.sin(math.pi * p) ** 1.6
        freq = 100 + 180 * math.sin(math.pi * p)
        tone = math.sin(2.0 * math.pi * freq * t)
        air = (rng.random() * 2.0 - 1.0) * 0.18
        samples.append((tone * 0.82 + air) * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=20000)


def generate_whoosh_deep(output_path: Path, sample_rate: int = 48000, duration: float = 0.30) -> Path:
    """Low-end cinematic whoosh with deep sub air (85Hz -> 220Hz -> 65Hz)."""
    num_samples = int(sample_rate * duration)
    rng = random.Random(303)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        p = i / num_samples
        env = math.sin(math.pi * p) ** 1.5
        freq = 85 + 135 * math.sin(math.pi * p)
        sub = math.sin(2.0 * math.pi * freq * t)
        air = (rng.random() * 2.0 - 1.0) * 0.12
        samples.append((sub * 0.88 + air) * env)
    return _write_mono_wav(output_path, samples, sample_rate, max_amp=24000)


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


# --- SFX KIT ASSET MANAGER ---

def ensure_sfx_kit() -> Dict[str, List[Path]]:
    """
    Generates and organizes the full 12-sound tactile micro-audio kit into assets/sfx/kit/.
    Returns a dictionary mapping SFX categories to lists of variant paths.
    """
    sfx_dir = getattr(config, "SFX_DIR", config.ASSETS_DIR / "sfx")
    kit_dir = sfx_dir / "kit"
    kit_dir.mkdir(parents=True, exist_ok=True)

    pops_dir = kit_dir / "pops"
    whooshes_dir = kit_dir / "whooshes"
    accents_dir = kit_dir / "accents"
    impacts_dir = kit_dir / "impacts"

    for d in [pops_dir, whooshes_dir, accents_dir, impacts_dir]:
        d.mkdir(parents=True, exist_ok=True)

    manifest = {
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
        "pops": [],
        "whooshes": [],
        "accents": [],
        "impacts": []
    }

    for cat, items in manifest.items():
        for filename, gen_fn, target_dir in items:
            p = target_dir / filename
            if not p.exists() or p.stat().st_size == 0:
                gen_fn(p)
            categorized_paths[cat].append(p)

    # Legacy fallbacks in assets/sfx/
    legacy_pop = sfx_dir / "pop_badge.wav"
    legacy_whoosh = sfx_dir / "whoosh_zoom.wav"
    legacy_thump = sfx_dir / "thump_impact.wav"

    if not legacy_pop.exists():
        generate_pop_clean(legacy_pop)
    if not legacy_whoosh.exists():
        generate_whoosh_fast(legacy_whoosh)
    if not legacy_thump.exists():
        generate_thump_sub(legacy_thump)

    return categorized_paths


def ensure_sfx_assets() -> Tuple[Path, Path, Path]:
    """Legacy backward compatibility: returns (pop, whoosh, thump)."""
    kit = ensure_sfx_kit()
    sfx_dir = getattr(config, "SFX_DIR", config.ASSETS_DIR / "sfx")
    return sfx_dir / "pop_badge.wav", sfx_dir / "whoosh_zoom.wav", sfx_dir / "thump_impact.wav"
