"""
Auto B-Roll & Visual Metaphor Cutaway Intelligence for AI-Editor.
Identifies spoken analogies and mental metaphors (house, website, apps, database, AI, code)
and schedules sleek 2.2s upper-left glassmorphic visual cutaway cards.
Leaves speaker visible while boosting visual pacing and retention.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

import config
from utils.graphics_generator import ensure_graphic_assets


@dataclass
class MetaphorOverlay:
    keyword: str
    card_key: str
    start_time: float
    end_time: float
    image_path: Path
    title: str
    color: str
    animated_clip_path: Optional[Path] = None


METAPHOR_DICTIONARY: Dict[str, Tuple[str, str, str]] = {
    # 1. Blueprint Architecture / House Analogy
    "house": ("blueprint_house", "System Architecture", "0x00F0FF"),
    "building": ("blueprint_house", "System Architecture", "0x00F0FF"),
    "foundation": ("blueprint_house", "System Architecture", "0x00F0FF"),
    "architecture": ("blueprint_house", "System Architecture", "0x00F0FF"),
    "structure": ("blueprint_house", "System Architecture", "0x00F0FF"),

    # 2. Modern Web Application
    "website": ("browser_website", "Web Application", "0xC084FC"),
    "frontend": ("browser_website", "Web Application", "0xC084FC"),
    "browser": ("browser_website", "Web Application", "0xC084FC"),
    "web": ("browser_website", "Web Application", "0xC084FC"),

    # 3. Mobile Ecosystem
    "mobile application": ("mobile_app", "Mobile Ecosystem", "0x00FF9D"),
    "mobile app": ("mobile_app", "Mobile Ecosystem", "0x00FF9D"),
    "application": ("mobile_app", "Mobile Ecosystem", "0x00FF9D"),
    "mobile": ("mobile_app", "Mobile Ecosystem", "0x00FF9D"),
    "android": ("mobile_app", "Mobile Ecosystem", "0x00FF9D"),
    "ios": ("mobile_app", "Mobile Ecosystem", "0x00FF9D"),

    # 4. Cloud Infrastructure & Databases
    "cloud": ("cloud_database", "Cloud Infrastructure", "0x00F0FF"),
    "database": ("cloud_database", "Cloud Infrastructure", "0x00F0FF"),
    "server": ("cloud_database", "Cloud Infrastructure", "0x00F0FF"),
    "backend": ("cloud_database", "Cloud Infrastructure", "0x00F0FF"),

    # 5. Neural Intelligence & AI
    "artificial intelligence": ("neural_brain", "Neural Intelligence", "0xFFD700"),
    "neural network": ("neural_brain", "Neural Intelligence", "0xFFD700"),
    "machine learning": ("neural_brain", "Neural Intelligence", "0xFFD700"),
    "ai engineering": ("neural_brain", "Neural Intelligence", "0xFFD700"),
    "ai": ("neural_brain", "Neural Intelligence", "0xFFD700"),

    # 6. Software Development & Python
    "software industry": ("code_terminal", "Software Engine", "0x00FF9D"),
    "python": ("code_terminal", "Software Engine", "0x00FF9D"),
    "software": ("code_terminal", "Software Engine", "0x00FF9D"),
    "developer": ("code_terminal", "Software Engine", "0x00FF9D"),
    "programming": ("code_terminal", "Software Engine", "0x00FF9D"),
    "coding": ("code_terminal", "Software Engine", "0x00FF9D"),
}


def detect_metaphor_overlays(
    segments: List[Any],
    duration: float = 2.2,
    min_interval: float = 6.5,
    blackout_start: float = 0.0,
    blackout_end: float = 7.5
) -> List[MetaphorOverlay]:
    """
    Detects spoken analogies and mental metaphors from speech timestamps.
    Returns timed MetaphorOverlay items linked to generated graphic cards in assets/graphics/.
    """
    graphic_cards = ensure_graphic_assets()
    animated_clips = {}
    try:
        from core.motion_graphics import ensure_animated_graphic_assets
        animated_clips = ensure_animated_graphic_assets()
    except Exception:
        pass

    overlays: List[MetaphorOverlay] = []
    last_overlay_time = -999.0

    # Flatten words with timing
    flat_words = []
    for seg in segments:
        words = getattr(seg, "words", []) or []
        for w in words:
            w_text = getattr(w, "word", "").strip().lower()
            st = getattr(w, "start", 0.0)
            et = getattr(w, "end", st + 0.3)
            clean_w = "".join(c for c in w_text if c.isalnum() or c == "-").strip()
            if clean_w:
                flat_words.append((clean_w, st, et))

    i = 0
    while i < len(flat_words):
        w_cur, st, et = flat_words[i]

        # Don't show during lower-third speaker banner
        if blackout_start <= st <= blackout_end:
            i += 1
            continue

        # Respect pacing cooldown
        if (st - last_overlay_time) < min_interval:
            i += 1
            continue

        matched = False
        target_key = ""
        card_title = ""
        accent_col = "0x00F0FF"
        words_consumed = 1

        # Check bigrams then unigrams
        if i + 1 < len(flat_words):
            bigram = f"{w_cur} {flat_words[i + 1][0]}"
            if bigram in METAPHOR_DICTIONARY:
                target_key, card_title, accent_col = METAPHOR_DICTIONARY[bigram]
                matched = True
                words_consumed = 2

        if not matched and w_cur in METAPHOR_DICTIONARY:
            target_key, card_title, accent_col = METAPHOR_DICTIONARY[w_cur]
            matched = True
            words_consumed = 1

        if matched and target_key in graphic_cards:
            img_file = graphic_cards[target_key]
            anim_file = animated_clips.get(target_key, None)
            end_t = round(st + duration, 2)
            overlays.append(MetaphorOverlay(
                keyword=w_cur,
                card_key=target_key,
                start_time=round(st, 2),
                end_time=end_t,
                image_path=img_file,
                title=card_title,
                color=accent_col,
                animated_clip_path=anim_file
            ))
            last_overlay_time = end_t
            i += words_consumed
        else:
            i += 1

    return overlays
