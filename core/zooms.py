"""
Virtual Multi-Cam & Dynamic Zoom Engine for AI-Editor.
Simulates a multi-camera studio production from a single camera angle by dynamically
cutting between Wide Shot (1.0x) and Medium/Tight Shot (1.15x Punch-In).

Attention-Driven & Semantic Directing:
- Cuts on meaning & emotion: Prioritizes key takeaways, opening hooks, and core rules.
- Acoustic snapping: Snaps frame-accurately to the first spoken syllable of high-value clauses.
- Context-aware framing: Stays wide for list enumerations and explanations to give graphics room.
- Natural pacing: Enforces minimum hold times (no rapid flashing) and maximum hold limits.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple


@dataclass
class SpokenClause:
    """Represents a coherent spoken thought, sentence, or clause with timing and attention score."""
    text: str
    start_time: float
    end_time: float
    words: List[Tuple[str, float, float]] = field(default_factory=list)
    pause_before: float = 0.0
    attention_score: float = 0.0
    reason: str = ""


@dataclass
class ZoomInterval:
    """Represents a timed virtual multi-cam close-up shot."""
    start_time: float
    end_time: float
    scale: float = 1.15
    zoom_type: str = "punch_in"   # "punch_in" (instant snap cut) or "slow_push"
    reason: Optional[str] = None


# High-priority emphasis hooks and superlative phrases (Top editor triggers)
EMPHASIS_HOOK_PATTERNS = [
    r"\b(the\s+best\s+thing|best\s+thing|best\s+way|best\s+part)\b",
    r"\b(first\s+thing|first\s+step|number\s+one|rule\s+number|rule\s+1)\b",
    r"\b(most\s+important|very\s+important|crucial|essential|critical)\b",
    r"\b(the\s+secret\s+is|secret\s+to|the\s+key\s+is|key\s+thing)\b",
    r"\b(remember\s+this|remember\s+that|keep\s+in\s+mind|never\s+forget)\b",
    r"\b(stop\s+doing|never\s+do|don't\s+ever|do\s+not\s+ever|avoid\s+this)\b",
    r"\b(huge\s+mistake|biggest\s+mistake|wrong\s+way|common\s+error)\b",
    r"\b(if\s+you\s+want|how\s+to|how\s+you\s+can|here\s+is\s+how)\b",
    r"\b(pay\s+attention|listen\s+carefully|look\s+at\s+this|notice\s+that)\b",
]

# Actionable directives and strong semantic words
ACTION_DIRECTIVE_PATTERNS = [
    r"\b(consistency|consistent|strong\s+on|focus|mastery|skills?)\b",
    r"\b(you\s+should|you\s+must|you\s+have\s+to|need\s+to|make\s+sure)\b",
    r"\b(actually|in\s+fact|in\s+reality|instead|however|but)\b",
]

# Tech/tool keywords used to detect lists and enumerations (stay wide for lists)
LIST_TECH_KEYWORDS = {
    "python", "java", "c++", "c#", "javascript", "typescript", "node", "nodejs",
    "react", "angular", "vue", "html", "css", "sql", "nosql", "mongodb", "docker",
    "kubernetes", "aws", "azure", "gcp", "git", "github", "linux"
}


def extract_spoken_clauses(segments: List[Any]) -> List[SpokenClause]:
    """
    Extracts coherent sentences and clauses from transcription segments using
    punctuation and acoustic speech pauses.
    """
    if not segments:
        return []

    # Flatten all words with acoustic boundaries
    flat_words: List[Tuple[str, float, float]] = []
    for seg in segments:
        seg_words = getattr(seg, "words", []) or []
        for w in seg_words:
            w_text = getattr(w, "word", "").strip()
            st = getattr(w, "start", 0.0)
            et = getattr(w, "end", st + 0.25)
            if w_text:
                flat_words.append((w_text, st, et))

    if not flat_words:
        # Fallback to segment-level clauses if word timestamps are missing
        clauses = []
        for i, seg in enumerate(segments):
            text = getattr(seg, "text", "").strip()
            st = getattr(seg, "start", 0.0)
            et = getattr(seg, "end", st + 1.0)
            pause = (st - getattr(segments[i - 1], "end", 0.0)) if i > 0 else 0.0
            clauses.append(SpokenClause(text=text, start_time=st, end_time=et, pause_before=max(0.0, pause)))
        return clauses

    clauses: List[SpokenClause] = []
    curr_words: List[Tuple[str, float, float]] = []
    last_end = flat_words[0][1]

    for i, (w_text, w_st, w_et) in enumerate(flat_words):
        pause = max(0.0, w_st - last_end)
        curr_words.append((w_text, w_st, w_et))
        last_end = w_et

        # Split into a new clause if:
        # 1. Punctuation indicates thought completion (. ? ! ;)
        # 2. Or a noticeable breath/silence pause occurred (>= 0.24s)
        has_terminal_punct = any(w_text.endswith(p) for p in (".", "?", "!", ";"))
        next_pause = (flat_words[i + 1][1] - w_et) if i + 1 < len(flat_words) else 1.0

        is_pause_split = (next_pause >= 0.24 and len(curr_words) >= 3)
        is_last = (i == len(flat_words) - 1)

        if has_terminal_punct or is_pause_split or is_last:
            c_text = " ".join(w[0] for w in curr_words).strip()
            c_st = curr_words[0][1]
            c_et = curr_words[-1][2]
            c_pause = curr_words[0][1] - (clauses[-1].end_time if clauses else 0.0)

            clauses.append(SpokenClause(
                text=c_text,
                start_time=round(c_st, 2),
                end_time=round(c_et, 2),
                words=list(curr_words),
                pause_before=max(0.0, round(c_pause, 2))
            ))
            curr_words = []

    return clauses


def score_clause_attention(clause: SpokenClause, index: int, total_clauses: int) -> Tuple[float, str]:
    """
    Computes the editorial attention score for a spoken clause.
    High scores indicate key takeaways and punchlines suitable for punch-in close-up.
    """
    score = 0.0
    reasons = []
    text_lower = clause.text.lower()

    # 1. High-priority emphasis hook phrases (Top creator triggers)
    for pattern in EMPHASIS_HOOK_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            score += 3.8
            reasons.append(f"Hook: '{match.group(0)}'")
            break

    # 2. Actionable directives & core keywords
    for pattern in ACTION_DIRECTIVE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            score += 1.8
            reasons.append(f"Directive: '{match.group(0)}'")
            break

    # 3. Acoustic delivery dynamics: preceded by speech breath/pause
    if clause.pause_before >= 0.25:
        score += 1.2
        reasons.append(f"Pause ({clause.pause_before:.2f}s)")

    # 4. Opening hook bonus (first 4.5 seconds of the video)
    if clause.start_time <= 4.5:
        score += 1.5
        reasons.append("Opening Hook")

    # 5. Technical enumeration penalty: stay wide when listing technologies
    words_in_clause = set(re.findall(r"[a-z0-9\+#\.]+", text_lower))
    tech_matches = words_in_clause.intersection(LIST_TECH_KEYWORDS)
    if len(tech_matches) >= 2 or "," in clause.text and len(tech_matches) >= 1:
        score -= 3.0
        reasons.append(f"Tech List ({len(tech_matches)} items - Stay Wide)")

    # 6. Length penalty for long rambling clauses
    duration = clause.end_time - clause.start_time
    if duration > 6.0:
        score -= 1.0

    reason_str = ", ".join(reasons) if reasons else "General speech"
    return score, reason_str


def plan_zooms(
    segments: List[Any],
    total_duration: float,
    scale: float = 1.15,
    min_wide_duration: float = 2.0,
    zoom_duration: float = 3.0,
    max_zoom_duration: float = 4.2,
    blackout_start: float = 1.5,
    blackout_end: float = 1.5
) -> List[ZoomInterval]:
    """
    Directs virtual multi-cam punch-in cuts using semantic importance and acoustic pauses.
    
    Top Editor Directing Rules:
    - Punches in tightly (1.15x) on key takeaways, punchlines, and strong advice.
    - Pulls back to wide (1.0x) on explanations, listings, and context.
    - Snaps frame-accurately to the first spoken syllable of the sentence.
    - Never cuts during rapid succession (enforces hold times).
    """
    if not segments or total_duration < (blackout_start + blackout_end + 3.0):
        return []

    # 1. Segment transcript into spoken clauses
    clauses = extract_spoken_clauses(segments)
    if not clauses:
        return []

    # 2. Score each clause for editorial attention
    for i, c in enumerate(clauses):
        c.attention_score, c.reason = score_clause_attention(c, i, len(clauses))

    zoom_intervals: List[ZoomInterval] = []
    last_zoom_end = 0.0
    max_allowed_time = total_duration - blackout_end

    # 3. Schedule punch-in cuts based on importance and pacing
    for i, c in enumerate(clauses):
        c_st = c.start_time
        c_et = c.end_time
        c_dur = c_et - c_st

        # Skip clauses within blackout regions
        if c_st < blackout_start or c_st > max_allowed_time:
            continue

        # Respect minimum wide hold time from previous punch-in
        if c_st - last_zoom_end < min_wide_duration:
            continue

        # High-attention threshold: score >= 2.5 indicates high-value takeaway
        is_high_attention = (c.attention_score >= 2.5)

        # Fallback cadence: if the camera has been wide for over 6.5s and this clause has positive delivery
        has_been_wide_too_long = (c_st - last_zoom_end >= 6.5 and c.attention_score >= 0.5)

        if is_high_attention or has_been_wide_too_long:
            # Determine punch-in shot duration
            # If the clause duration is between 1.8s and max_zoom_duration, use the full clause!
            if 1.8 <= c_dur <= max_zoom_duration:
                z_start = c_st
                z_end = min(c_et, max_allowed_time)
            elif c_dur > max_zoom_duration:
                # Long sentence: find the nearest word boundary near target zoom_duration
                z_start = c_st
                target_end = c_st + zoom_duration
                z_end = min(c_st + max_zoom_duration, max_allowed_time)
                for w in c.words:
                    if target_end - 0.4 <= w[2] <= target_end + 0.6:
                        z_end = min(w[2], max_allowed_time)
                        break
            else:
                # Very short clause (<1.8s): extend into next clause if available and natural
                z_start = c_st
                z_end = min(c_st + zoom_duration, max_allowed_time)
                if i + 1 < len(clauses) and clauses[i + 1].start_time <= z_end + 0.3:
                    z_end = min(clauses[i + 1].end_time, c_st + max_zoom_duration, max_allowed_time)

            if z_end - z_start >= 1.7:
                zoom_intervals.append(ZoomInterval(
                    start_time=round(z_start, 2),
                    end_time=round(z_end, 2),
                    scale=scale,
                    zoom_type="punch_in",
                    reason=f"Attention Focus: '{c.text[:28]}...' ({c.reason})"
                ))
                last_zoom_end = z_end

    return zoom_intervals
