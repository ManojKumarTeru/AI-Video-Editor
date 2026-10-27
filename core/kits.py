"""
Production Kit Engine for AI-Editor.
Defines modular, reusable styling and sound presets for video production.
Kits bundle typography, text highlights, badge aesthetics, color grading, and SFX profiles.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path


@dataclass
class SubtitleKit:
    font_name: str = "Arial"
    font_size: int = 50
    primary_color: str = "&H00FFFFFF"      # Crisp White (ASS format: &HAABBGGRR)
    secondary_color: str = "&H0000E5FF"    # Ultra-Bright Electric Gold active word (&H00BBGGRR)
    outline_color: str = "&H00000000"      # Pure Black
    outline_width: int = 4                 # Thicker 4px stroke for high contrast
    shadow_width: int = 2                  # 2px drop-shadow for 3D depth
    shadow_color: str = "&H80000000"      # 50% semi-transparent shadow
    margin_bottom: int = 68                # YouTube safe-zone margin
    kinetic_scale: int = 120               # 120% spring pop on active word
    background_pill: bool = True           # High-contrast backing for maximum highlight


@dataclass
class VisualGradeKit:
    contrast: float = 1.015                # Gentle natural contrast (tamed down from 1.04)
    saturation: float = 1.03               # Natural vibrance (tamed down from 1.10)
    gamma: float = 1.00                    # Preserves clean midtone skin exposure
    s_curve_str: str = "0/0 0.25/0.235 0.75/0.775 1/1"  # Mild broadcast-safe S-curve
    vignette_angle: str = "PI/14"          # Ultra-soft 12° edge falloff (tamed down from harsh PI/5)
    retention_bar_color: str = "0x00F0FF"  # Glowing Cyber Cyan progress line


@dataclass
class BadgeKit:
    card_bg_alpha: float = 0.90            # Dark obsidian glass opacity
    border_width: int = 2                  # Glowing neon border width
    category_color_map: Dict[str, Tuple[str, str]] = field(default_factory=lambda: {
        "AI": ("✦ AI", "0xC084FC"),           # Electric Violet / Purple
        "TECH": ("⚡ TECH", "0x00F0FF"),       # Cyberpunk Cyan
        "KEY": ("★ KEY", "0xFFD700"),         # Electric Gold
        "SKILL": ("● SKILL", "0x00FF9D"),     # Neon Mint Green
        "POPULAR": ("◆ TOPIC", "0xFF5252"),   # Radiant Coral
    })


@dataclass
class AudioSoundKit:
    pop_volume: float = 0.22
    whoosh_volume: float = 0.18
    thump_volume: float = 0.32
    default_pop_variant: str = "clean"
    default_whoosh_variant: str = "fast"


@dataclass
class MotionGraphicsKit:
    spring_overshoot: bool = True
    specular_sheen_wipe: bool = True
    background_defocus: bool = True
    background_defocus_sigma: float = 2.5
    chart_draw_duration: float = 0.50
    sheen_intensity: float = 0.40


@dataclass
class ProductionKit:
    name: str
    display_name: str
    description: str
    subtitles: SubtitleKit = field(default_factory=SubtitleKit)
    grading: VisualGradeKit = field(default_factory=VisualGradeKit)
    badges: BadgeKit = field(default_factory=BadgeKit)
    audio: AudioSoundKit = field(default_factory=AudioSoundKit)
    motion: MotionGraphicsKit = field(default_factory=MotionGraphicsKit)


# --- BUILT-IN PRODUCTION KITS ---

CREATOR_ELITE_KIT = ProductionKit(
    name="creator_elite",
    display_name="🏆 Creator Elite (MrBeast / Ali Abdaal Standard)",
    description="High-visibility electric gold & mint highlights, natural skin grading, and organic tactile SFX.",
    subtitles=SubtitleKit(
        font_name="Arial",
        font_size=52,
        primary_color="&H00FFFFFF",
        secondary_color="&H0000E5FF",  # Vivid Gold active highlight
        outline_width=4,
        shadow_width=2,
        margin_bottom=70,
        kinetic_scale=120,
        background_pill=True
    ),
    grading=VisualGradeKit(
        contrast=1.015,
        saturation=1.03,
        gamma=1.00,
        s_curve_str="0/0 0.25/0.235 0.75/0.775 1/1",
        vignette_angle="PI/14",
        retention_bar_color="0x00F0FF"
    ),
    badges=BadgeKit(
        card_bg_alpha=0.90,
        border_width=2
    ),
    audio=AudioSoundKit(
        pop_volume=0.24,
        whoosh_volume=0.18,
        thump_volume=0.32
    )
)

NEON_CYBER_KIT = ProductionKit(
    name="neon_cyber",
    display_name="⚡ Neon Cyberpunk (Tech & Code Focus)",
    description="Vibrant Cyber Cyan & Neon Purple accents, glassmorphic glow borders, and snappy digital micro-clicks.",
    subtitles=SubtitleKit(
        font_name="Arial",
        font_size=50,
        primary_color="&H00FFFFFF",
        secondary_color="&H00FFFF00",  # Vivid Cyan active highlight
        outline_width=4,
        shadow_width=3,
        margin_bottom=68,
        kinetic_scale=122,
        background_pill=True
    ),
    grading=VisualGradeKit(
        contrast=1.025,
        saturation=1.05,
        gamma=0.99,
        s_curve_str="0/0 0.25/0.225 0.75/0.785 1/1",
        vignette_angle="PI/12",
        retention_bar_color="0x00F0FF"
    ),
    badges=BadgeKit(
        card_bg_alpha=0.92,
        border_width=2
    ),
    audio=AudioSoundKit(
        pop_volume=0.22,
        whoosh_volume=0.20,
        thump_volume=0.35
    )
)

MINIMAL_STUDIO_KIT = ProductionKit(
    name="minimal_studio",
    display_name="🎬 Minimal Studio (Clean & Natural)",
    description="Clean white and champagne gold typography, ultra-natural broadcast grade, and soft organic acoustic SFX.",
    subtitles=SubtitleKit(
        font_name="Arial",
        font_size=48,
        primary_color="&H00FFFFFF",
        secondary_color="&H0080EAFF",  # Champagne / Warm Gold
        outline_width=3,
        shadow_width=1,
        margin_bottom=65,
        kinetic_scale=115,
        background_pill=False
    ),
    grading=VisualGradeKit(
        contrast=1.010,
        saturation=1.02,
        gamma=1.00,
        s_curve_str="0/0 0.25/0.245 0.75/0.765 1/1",
        vignette_angle="PI/18",
        retention_bar_color="0xFFD700"
    ),
    badges=BadgeKit(
        card_bg_alpha=0.85,
        border_width=1
    ),
    audio=AudioSoundKit(
        pop_volume=0.18,
        whoosh_volume=0.14,
        thump_volume=0.26
    )
)

AVAILABLE_KITS: Dict[str, ProductionKit] = {
    "creator_elite": CREATOR_ELITE_KIT,
    "neon_cyber": NEON_CYBER_KIT,
    "minimal_studio": MINIMAL_STUDIO_KIT
}


def get_production_kit(kit_name: Optional[str] = None) -> ProductionKit:
    """Returns the requested ProductionKit or defaults to 'creator_elite'."""
    if not kit_name:
        return CREATOR_ELITE_KIT
    clean_name = kit_name.strip().lower()
    return AVAILABLE_KITS.get(clean_name, CREATOR_ELITE_KIT)
