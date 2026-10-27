"""
Virtual Multi-Cam & Dynamic Zoom Engine for AI-Editor.
Simulates a multi-camera studio production from a single camera angle by dynamically
cutting between Wide Shot (1.0x) and Medium/Tight Shot (1.15x Punch-In).

Professional Editing Standards:
- Headroom preservation: Top-weighted vertical framing (y ≈ 38%) keeps speaker's eyes on upper third.
- Cadence: Wide master holds for 5–8s; Punch-in holds for 3–5s (pattern interrupt).
- Boundary snapping: Cuts only at sentence or speech breath pauses (never mid-word).
- Resolution independent: Dynamic calculation for any resolution (1080p, 4K, 720p, 9:16 Shorts).
"""

from dataclasses import dataclass
from typing import List, Optional, Any, Tuple


@dataclass
class ZoomInterval:
    """Represents a timed virtual multi-cam close-up shot."""
    start_time: float
    end_time: float
    scale: float = 1.15
    zoom_type: str = "punch_in"   # "punch_in" (instant snap cut) or "slow_push"
    reason: Optional[str] = None


def plan_zooms(
    segments: List[Any],
    total_duration: float,
    scale: float = 1.15,
    min_wide_duration: float = 5.5,
    zoom_duration: float = 3.8,
    max_zoom_duration: float = 5.5,
    blackout_start: float = 3.0,
    blackout_end: float = 3.0
) -> List[ZoomInterval]:
    """
    Intelligently plans virtual multi-cam punch-in cuts across speech segments.
    Aligns cuts with sentence boundaries and natural speech pauses.
    
    Args:
        segments: Transcribed SubtitleSegment objects with word timestamps.
        total_duration: Total video length in seconds.
        scale: Punch-in magnification factor (default 1.15 for crisp 1080p close-up).
        min_wide_duration: Minimum seconds the wide master shot must hold before zooming.
        zoom_duration: Target close-up hold duration in seconds.
        max_zoom_duration: Maximum allowed close-up hold before returning to wide.
        blackout_start: Seconds to keep wide at the opening hook.
        blackout_end: Seconds to keep wide at the closing.
    
    Returns:
        List of non-overlapping ZoomInterval objects.
    """
    if not segments or total_duration < (blackout_start + blackout_end + min_wide_duration + zoom_duration):
        return []

    # 1. Flatten all word timestamps and collect boundary candidates
    # Each entry: (word_text, start_time, end_time)
    words: List[Tuple[str, float, float]] = []
    for seg in segments:
        seg_words = getattr(seg, "words", []) or []
        for w in seg_words:
            w_text = getattr(w, "word", "").strip()
            st = getattr(w, "start", 0.0)
            et = getattr(w, "end", st + 0.3)
            if w_text:
                words.append((w_text, st, et))

    # Also collect segment starts as prime transition points
    seg_starts = [round(getattr(s, "start", 0.0), 2) for s in segments if getattr(s, "start", 0.0) >= blackout_start]

    zoom_intervals: List[ZoomInterval] = []
    cur_t = blackout_start
    max_allowed_time = total_duration - blackout_end

    while cur_t + min_wide_duration + zoom_duration <= max_allowed_time:
        target_start = cur_t + min_wide_duration

        # Find best punch-in start candidate (nearest segment start or pause after target_start)
        best_start = None
        # Check segment starts first within [target_start, target_start + 4.0]
        for s_st in seg_starts:
            if target_start <= s_st <= target_start + 4.5:
                best_start = s_st
                break

        # Fallback to word boundary if no segment start found
        if best_start is None:
            for i, (_, w_st, w_et) in enumerate(words):
                if w_st >= target_start:
                    best_start = round(w_st, 2)
                    break

        if best_start is None or best_start + zoom_duration > max_allowed_time:
            break

        # Target end time for this close-up shot
        target_end = best_start + zoom_duration
        best_end = None

        # Look for a clean word boundary or pause near target_end within [best_start + 2.6, best_start + max_zoom_duration]
        min_allowed_end = best_start + 2.6
        max_allowed_end = min(best_start + max_zoom_duration, max_allowed_time)

        # Look for pause between words in range
        for i in range(len(words) - 1):
            curr_end = words[i][2]
            next_start = words[i + 1][1]
            if min_allowed_end <= curr_end <= max_allowed_end:
                # Pause found between words
                if (next_start - curr_end) >= 0.15:
                    best_end = round(curr_end, 2)
                    break
                elif abs(curr_end - target_end) < 0.6:
                    best_end = round(curr_end, 2)

        # Fallback if no pause matched: use segment end or target_end
        if best_end is None:
            for s in segments:
                s_et = getattr(s, "end", 0.0)
                if min_allowed_end <= s_et <= max_allowed_end:
                    best_end = round(s_et, 2)
                    break

        if best_end is None:
            best_end = round(min(target_end, max_allowed_end), 2)

        if best_end > best_start + 1.8:
            zoom_intervals.append(ZoomInterval(
                start_time=best_start,
                end_time=best_end,
                scale=scale,
                zoom_type="punch_in",
                reason=f"Multi-Cam Close-Up ({best_end - best_start:.1f}s)"
            ))
            cur_t = best_end
        else:
            cur_t = best_start + 1.0

    return zoom_intervals
