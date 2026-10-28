"""
Visual Polish & Branding Engine for YouTube & Shorts.
Applies:
- High-contrast styled ASS subtitle burn-in with karaoke timing
- Dynamic broadcast lower-third banners and corner watermarks
- 1080p Intro and Outro title sequences with smooth fade transitions
- YouTube Shorts 9:16 vertical conversion (blurred background fill + centered video)
- Seamless multi-segment concatenation (Intro -> Main -> Outro)
"""

import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Any, Set, Tuple, Dict

import config
from utils.ffmpeg_utils import probe_media, escape_filter_path, escape_drawtext, run_ffmpeg_checked


@dataclass
class HighlightCallout:
    """Represents an attention-grabbing keyword badge appearing on the right side."""
    text: str
    start_time: float
    end_time: float
    color: str = "0x00F0FF"         # Vibrant FFmpeg hex color (0xRRGGBB)
    category: Optional[str] = None  # e.g. "AI", "TECH", "KEY", "SKILL"


# Curated dictionary of popular tech, AI, and career phrases with high-impact color grading & icons
POPULAR_TECH_PHRASES: Dict[str, Tuple[str, str, str]] = {
    # 1. AI, Machine Learning & Future Tech (Electric Purple: 0xC084FC)
    "ai engineering": ("✦ AI ENGINEERING", "0xC084FC", "AI"),
    "ai engineer": ("✦ AI ENGINEER", "0xC084FC", "AI"),
    "artificial intelligence": ("✦ ARTIFICIAL INTELLIGENCE", "0xC084FC", "AI"),
    "machine learning": ("✦ MACHINE LEARNING", "0xC084FC", "AI"),
    "deep learning": ("✦ DEEP LEARNING", "0xC084FC", "AI"),
    "neural networks": ("✦ NEURAL NETWORKS", "0xC084FC", "AI"),
    "neural network": ("✦ NEURAL NETWORK", "0xC084FC", "AI"),
    "large language model": ("✦ LARGE LANGUAGE MODEL", "0xC084FC", "AI"),
    "large language models": ("✦ LARGE LANGUAGE MODELS", "0xC084FC", "AI"),
    "data science": ("✦ DATA SCIENCE", "0xC084FC", "AI"),
    "data scientist": ("✦ DATA SCIENTIST", "0xC084FC", "AI"),
    "generative ai": ("✦ GENERATIVE AI", "0xC084FC", "AI"),
    "prompt engineering": ("✦ PROMPT ENGINEERING", "0xC084FC", "AI"),
    "computer vision": ("✦ COMPUTER VISION", "0xC084FC", "AI"),
    "chatgpt": ("✦ CHATGPT", "0xC084FC", "AI"),
    "openai": ("✦ OPENAI", "0xC084FC", "AI"),
    "ai agent": ("✦ AI AGENT", "0xC084FC", "AI"),
    "ai agents": ("✦ AI AGENTS", "0xC084FC", "AI"),
    "ai tools": ("✦ AI TOOLS", "0xC084FC", "AI"),
    "llm": ("✦ LLM", "0xC084FC", "AI"),
    "nlp": ("✦ NLP", "0xC084FC", "AI"),
    "ai": ("✦ AI", "0xC084FC", "AI"),

    # 2. Programming, Code & Architecture (Cyberpunk Cyan: 0x00F0FF)
    "software industry": ("◆ SOFTWARE INDUSTRY", "0x00F0FF", "TECH"),
    "software engineering": ("◆ SOFTWARE ENGINEERING", "0x00F0FF", "TECH"),
    "software engineer": ("◆ SOFTWARE ENGINEER", "0x00F0FF", "TECH"),
    "software developer": ("◆ SOFTWARE DEVELOPER", "0x00F0FF", "TECH"),
    "software applications": ("◆ SOFTWARE APPLICATIONS", "0x00F0FF", "TECH"),
    "software application": ("◆ SOFTWARE APPLICATION", "0x00F0FF", "TECH"),
    "programming skills": ("⚡ PROGRAMMING SKILLS", "0x00F0FF", "TECH"),
    "programming skill": ("⚡ PROGRAMMING SKILL", "0x00F0FF", "TECH"),
    "programming language": ("⚡ PROGRAMMING LANGUAGE", "0x00F0FF", "TECH"),
    "programming languages": ("⚡ PROGRAMMING LANGUAGES", "0x00F0FF", "TECH"),
    "mobile application": ("◆ MOBILE APPLICATION", "0x00F0FF", "TECH"),
    "mobile applications": ("◆ MOBILE APPLICATIONS", "0x00F0FF", "TECH"),
    "web development": ("◆ WEB DEVELOPMENT", "0x00F0FF", "TECH"),
    "website": ("◆ WEBSITE", "0x00F0FF", "TECH"),
    "websites": ("◆ WEBSITES", "0x00F0FF", "TECH"),
    "full stack": ("⚡ FULL STACK", "0x00F0FF", "TECH"),
    "full stack developer": ("⚡ FULL STACK DEVELOPER", "0x00F0FF", "TECH"),
    "system design": ("◆ SYSTEM DESIGN", "0x00F0FF", "TECH"),
    "cloud computing": ("◆ CLOUD COMPUTING", "0x00F0FF", "TECH"),
    "python": ("⚡ PYTHON", "0x00F0FF", "TECH"),
    "javascript": ("⚡ JAVASCRIPT", "0x00F0FF", "TECH"),
    "typescript": ("⚡ TYPESCRIPT", "0x00F0FF", "TECH"),
    "golang": ("⚡ GOLANG", "0x00F0FF", "TECH"),
    "rust": ("⚡ RUST", "0x00F0FF", "TECH"),
    "java": ("⚡ JAVA", "0x00F0FF", "TECH"),
    "c++": ("⚡ C++", "0x00F0FF", "TECH"),
    "c#": ("⚡ C#", "0x00F0FF", "TECH"),
    "sql": ("⚡ SQL", "0x00F0FF", "TECH"),
    "docker": ("◆ DOCKER", "0x00F0FF", "TECH"),
    "kubernetes": ("◆ KUBERNETES", "0x00F0FF", "TECH"),
    "backend": ("◆ BACKEND", "0x00F0FF", "TECH"),
    "frontend": ("◆ FRONTEND", "0x00F0FF", "TECH"),
    "database": ("◆ DATABASE", "0x00F0FF", "TECH"),
    "programming": ("⚡ PROGRAMMING", "0x00F0FF", "TECH"),
    "coding": ("⚡ CODING", "0x00F0FF", "TECH"),
    "developer": ("⚡ DEVELOPER", "0x00F0FF", "TECH"),
    "framework": ("◆ FRAMEWORK", "0x00F0FF", "TECH"),
    "api": ("⚙️ API", "0x00F0FF", "TECH"),
    "rest api": ("⚙️ REST API", "0x00F0FF", "TECH"),
    "git": ("◆ GIT", "0x00F0FF", "TECH"),
    "github": ("◆ GITHUB", "0x00F0FF", "TECH"),
    "algorithms": ("⚡ ALGORITHMS", "0x00F0FF", "TECH"),
    "algorithm": ("⚡ ALGORITHM", "0x00F0FF", "TECH"),

    # 3. High Impact & Key Takeaways (Electric Gold: 0xFFD700)
    "first skill": ("★ FIRST SKILL", "0xFFD700", "KEY"),
    "top skill": ("★ TOP SKILL", "0xFFD700", "KEY"),
    "key concept": ("★ KEY CONCEPT", "0xFFD700", "KEY"),
    "requirement": ("★ REQUIREMENT", "0xFFD700", "KEY"),
    "requirements": ("★ REQUIREMENTS", "0xFFD700", "KEY"),
    "architecture": ("★ ARCHITECTURE", "0xFFD700", "KEY"),
    "automation": ("★ AUTOMATION", "0xFFD700", "KEY"),
    "roadmap": ("★ ROADMAP", "0xFFD700", "KEY"),
    "strategy": ("★ STRATEGY", "0xFFD700", "KEY"),
    "game changer": ("★ GAME CHANGER", "0xFFD700", "KEY"),
    "high income": ("★ HIGH INCOME", "0xFFD700", "KEY"),
    "mastery": ("★ MASTERY", "0xFFD700", "KEY"),
    "scale": ("★ SCALE", "0xFFD700", "KEY"),
    "speed": ("★ SPEED", "0xFFD700", "KEY"),

    # 4. Career & Human Skills (Neon Mint / Emerald Green: 0x00FF9D)
    "communication skills": ("● COMMUNICATION SKILLS", "0x00FF9D", "SKILL"),
    "communication skill": ("● COMMUNICATION SKILL", "0x00FF9D", "SKILL"),
    "problem solving": ("● PROBLEM SOLVING", "0x00FF9D", "SKILL"),
    "career growth": ("● CAREER GROWTH", "0x00FF9D", "SKILL"),
    "communication": ("● COMMUNICATION", "0x00FF9D", "SKILL"),
    "interview": ("● INTERVIEW", "0x00FF9D", "SKILL"),
    "consistency": ("● CONSISTENCY", "0x00FF9D", "SKILL"),
    "productivity": ("● PRODUCTIVITY", "0x00FF9D", "SKILL"),
    "portfolio": ("● PORTFOLIO", "0x00FF9D", "SKILL"),
    "experience": ("● EXPERIENCE", "0x00FF9D", "SKILL"),
}

# Common low-impact and filler words to ignore during automatic keyword extraction
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had",
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd",
    "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
    "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when",
    "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
    "yours", "yourself", "yourselves", "yeah", "okay", "gonna", "wanna", "gotta", "actually",
    "really", "just", "like", "well", "right", "said", "say", "saying", "think", "know",
    "look", "come", "make", "take", "give", "want", "need", "going", "thing", "things", "something"
}


def extract_highlight_callouts(
    segments: List[Any],
    custom_keywords: Optional[List[str]] = None,
    duration: float = 1.3,
    min_interval: float = 3.5,
    blackout_start: float = 0.0,
    blackout_end: float = 1.5
) -> List[HighlightCallout]:
    """
    Extracts standout tech, AI, and popular keyword moments from speech segments.
    Supports multi-word n-grams (e.g. 'AI Engineering', 'Software Industry') and
    assigns dynamic vibrant color palettes to pop on the right side of the screen.
    """
    callouts: List[HighlightCallout] = []
    last_callout_time = -999.0

    # 1. Flatten all words across segments with clean tokens
    flat_words: List[Tuple[str, float, float]] = []
    for seg in segments:
        words = getattr(seg, "words", []) or []
        for w in words:
            w_text = getattr(w, "word", "").strip()
            st = getattr(w, "start", 0.0)
            et = getattr(w, "end", st + 0.3)
            clean_w = "".join(c for c in w_text if c.isalnum() or c in ("$", "%", "#", "-", "+")).strip()
            if clean_w:
                flat_words.append((clean_w, st, et))

    # Normalized custom keywords list if provided
    normalized_custom = [k.strip().lower() for k in custom_keywords if k.strip()] if custom_keywords else []

    # Dynamic rotating palette for custom and general popular words
    PALETTE = ["0x00F0FF", "0xC084FC", "0xFFD700", "0x00FF9D", "0xFF5252"]
    palette_idx = 0

    i = 0
    while i < len(flat_words):
        w_cur, start_t, _ = flat_words[i]

        # Don't overlap with lower third window
        if blackout_start <= start_t <= blackout_end:
            i += 1
            continue

        # Ensure minimum interval between badges
        if (start_t - last_callout_time) < min_interval:
            i += 1
            continue

        matched = False
        display_text = ""
        matched_color = "0x00F0FF"
        matched_cat = "TECH"
        words_consumed = 1

        # Build candidate n-grams
        tri_phrase = " ".join(flat_words[j][0] for j in range(i, min(i + 3, len(flat_words)))).lower()
        bi_phrase = " ".join(flat_words[j][0] for j in range(i, min(i + 2, len(flat_words)))).lower()
        uni_word = w_cur.lower()

        # Check custom keywords first if provided
        if normalized_custom:
            for ck in normalized_custom:
                if i + 2 < len(flat_words) and ck in tri_phrase:
                    matched = True
                    display_text = tri_phrase.upper()
                    matched_color = PALETTE[palette_idx % len(PALETTE)]
                    words_consumed = 3
                    break
                elif i + 1 < len(flat_words) and ck in bi_phrase:
                    matched = True
                    display_text = bi_phrase.upper()
                    matched_color = PALETTE[palette_idx % len(PALETTE)]
                    words_consumed = 2
                    break
                elif ck in uni_word:
                    matched = True
                    display_text = uni_word.upper()
                    matched_color = PALETTE[palette_idx % len(PALETTE)]
                    words_consumed = 1
                    break

        # Check built-in popular tech phrases dictionary (tri-gram -> bi-gram -> unigram)
        if not matched:
            if i + 2 < len(flat_words) and tri_phrase in POPULAR_TECH_PHRASES:
                disp, col, cat = POPULAR_TECH_PHRASES[tri_phrase]
                matched = True
                display_text = disp
                matched_color = col
                matched_cat = cat
                words_consumed = 3
            elif i + 1 < len(flat_words) and bi_phrase in POPULAR_TECH_PHRASES:
                disp, col, cat = POPULAR_TECH_PHRASES[bi_phrase]
                matched = True
                display_text = disp
                matched_color = col
                matched_cat = cat
                words_consumed = 2
            elif uni_word in POPULAR_TECH_PHRASES:
                disp, col, cat = POPULAR_TECH_PHRASES[uni_word]
                matched = True
                display_text = disp
                matched_color = col
                matched_cat = cat
                words_consumed = 1

        # Fallback automatic keyword detection for other standout terms
        if not matched and not normalized_custom:
            has_digit = any(c.isdigit() for c in w_cur)
            is_acronym = len(w_cur) >= 2 and w_cur.isupper()
            is_punchy = len(w_cur) >= 6 and uni_word not in STOP_WORDS

            if has_digit:
                matched = True
                display_text = w_cur.upper()
                matched_color = "0xFFD700"  # Electric Gold
                matched_cat = "KEY"
                words_consumed = 1
            elif is_acronym:
                matched = True
                display_text = w_cur.upper()
                matched_color = "0x00F0FF"  # Cyberpunk Cyan
                matched_cat = "TECH"
                words_consumed = 1
            elif is_punchy:
                matched = True
                display_text = w_cur.upper()
                matched_color = PALETTE[palette_idx % len(PALETTE)]
                matched_cat = "POPULAR"
                words_consumed = 1

        if matched:
            end_t = round(start_t + duration, 2)
            callouts.append(HighlightCallout(
                text=display_text,
                start_time=round(start_t, 2),
                end_time=end_t,
                color=matched_color,
                category=matched_cat
            ))
            last_callout_time = end_t
            palette_idx += 1
            i += words_consumed
        else:
            i += 1

    return callouts


class VisualEngine:
    """Renders professional visuals, branding overlays, intros, and Shorts conversions."""

    def __init__(self, cfg: Optional[config.VisualsConfig] = None):
        self.cfg = cfg or config.VisualsConfig()
        config.ensure_directories()

    def burn_subtitles(self, video_path: Path, ass_path: Path, output_path: Path) -> Path:
        """Burns styled ASS subtitles directly into video frames with hardware-accurate styling."""
        video_path = Path(video_path).resolve()
        ass_path = Path(ass_path).resolve()
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        escaped_ass = escape_filter_path(ass_path)
        print(f"Burning styled captions into '{video_path.name}'...")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"ass=filename='{escaped_ass}'",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "copy",
            str(output_path)
        ]
        run_ffmpeg_checked(cmd, desc="Subtitle burn-in")
        return output_path

    def apply_dynamic_zooms(
        self,
        video_path: Path,
        output_path: Path,
        zoom_intervals: Optional[List[Any]] = None
    ) -> Path:
        """
        Applies dynamic virtual multi-cam punch-in zoom cuts to video footage.
        Simulates switching between Wide Shot (1.0x) and Medium Close-Up (1.15x).
        Preserves professional eye-level headroom without blur or frame distortion.
        """
        video_path = Path(video_path).resolve()
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.cfg.zooms_enabled or not zoom_intervals:
            shutil.copy2(video_path, output_path)
            return output_path

        probe = probe_media(video_path)
        v_st = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), {})
        width = int(v_st.get("width", 1920))
        height = int(v_st.get("height", 1080))

        scale = self.cfg.zoom_scale
        crop_w = int(width / scale)
        crop_w = crop_w if crop_w % 2 == 0 else crop_w - 1
        crop_h = int(height / scale)
        crop_h = crop_h if crop_h % 2 == 0 else crop_h - 1
        crop_x = int((width - crop_w) / 2)
        crop_y = int((height - crop_h) * self.cfg.zoom_headroom_factor)

        # Build overlay enable expression from intervals
        enable_expr = "+".join(f"between(t,{z.start_time:.2f},{z.end_time:.2f})" for z in zoom_intervals)
        filter_complex = (
            f"[0:v]split=2[base][zsrc];"
            f"[zsrc]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={width}:{height}:flags=bicubic[zoomed];"
            f"[base][zoomed]overlay=0:0:enable='{enable_expr}'[vout]"
        )

        print(f"Applying virtual multi-cam punch-in cuts ({len(zoom_intervals)} close-up camera angles)...")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "copy",
            str(output_path)
        ]
        run_ffmpeg_checked(cmd, desc="Virtual multi-cam zoom cuts")
        return output_path

    def add_branding_overlays(
        self,
        video_path: Path,
        output_path: Path,
        callouts: Optional[List[HighlightCallout]] = None,
        broll_overlays: Optional[List[Any]] = None
    ) -> Path:
        """
        Adds professional broadcast branding:
        - Animated lower-third banner with accent line for speaker identification
        - Subtle, semi-transparent watermark logo in the corner
        - Attention-grabbing keyword badges on the right side for key moments
        - Dynamic glowing retention progress bar at top of screen
        - Sleek glassmorphic B-roll metaphor cutaway cards in upper-left quadrant
        Dynamically adapts to ANY video resolution and aspect ratio without hardcoding.
        """
        video_path = Path(video_path).resolve()
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filters = []
        lt_start = self.cfg.lower_third_start
        lt_end = lt_start + self.cfg.lower_third_duration

        # Probe video dimensions dynamically for exact calculations
        probe = probe_media(video_path)
        v_st = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), {})
        width = int(v_st.get("width", 1920))
        height = int(v_st.get("height", 1080))
        total_dur = float(probe.get("format", {}).get("duration", 0.0))

        # 0. Natural Broadcast Studio Color Grading (gentle contrast & vibrant skin tones without harsh oversaturation)
        if getattr(self.cfg, "color_grade_enabled", True):
            contrast_val = getattr(self.cfg, "grade_contrast", 1.015)
            saturation_val = getattr(self.cfg, "grade_saturation", 1.03)
            gamma_val = getattr(self.cfg, "grade_gamma", 1.00)
            s_curve = getattr(self.cfg, "grade_s_curve", "0/0 0.25/0.235 0.75/0.775 1/1")
            vignette_angle = getattr(self.cfg, "grade_vignette", "PI/14")

            filters.append(f"curves=all='{s_curve}'")
            filters.append(f"eq=saturation={saturation_val:.3f}:contrast={contrast_val:.3f}:gamma={gamma_val:.2f}")
            if getattr(self.cfg, "vignette_enabled", True):
                filters.append(f"vignette=angle={vignette_angle}:eval=init")

        # 1. Lower Third / Host ID Intro Graphic (scaled dynamically to resolution)
        if self.cfg.lower_third_enabled:
            is_shorts = (getattr(self.cfg, "format", "landscape") == "shorts" or height > width)

            box_x = int(width * 0.05)
            # In Shorts, position in upper-left (height * 0.12) to leave the entire bottom area
            # unobstructed for subtitles, while maintaining balanced broadcaster framing!
            # In 16:9 Long-form, position at standard lower-third (height * 0.82)
            box_y = int(height * 0.12) if is_shorts else int(height * 0.82)
            box_h = int(height * 0.082)
            bar_w = max(4, int(width * 0.005))

            name_size = max(16, int(height * 0.032))
            title_size = max(11, int(height * 0.019))

            name_x = box_x + bar_w + int(width * 0.018)
            name_y = box_y + int(box_h * 0.16)
            title_x = name_x
            title_y = box_y + int(box_h * 0.56)

            # Proportional badge width to cleanly wrap speaker name & title with comfortable padding
            est_text_chars = max(len(self.cfg.speaker_name), len(self.cfg.speaker_title))
            est_tw = int(est_text_chars * name_size * 0.68)
            min_w = int(width * 0.22) if is_shorts else int(width * 0.26)
            box_w = max(min_w, (name_x - box_x) + est_tw + int(width * 0.035))

            esc_name = escape_drawtext(self.cfg.speaker_name)
            esc_title = escape_drawtext(self.cfg.speaker_title)

            accent_line_col = getattr(self.cfg, "retention_bar_color", "0xFFD700")
            # Solid, clean glassmorphic badge card (no stray outline lines across the frame)
            filters.append(f"drawbox=x={box_x}:y={box_y}:w={box_w}:h={box_h}:color=0x0b0f17@0.92:t=fill:enable='between(t,{lt_start},{lt_end})'")
            filters.append(f"drawbox=x={box_x}:y={box_y}:w={bar_w}:h={box_h}:color={accent_line_col}@1.0:t=fill:enable='between(t,{lt_start},{lt_end})'")
            name_alpha = f"if(lt(t,{lt_start + 0.12:.2f}), 0, if(lt(t,{lt_start + 0.38:.2f}), (t-{lt_start + 0.12:.2f})/0.26, if(gt(t,{lt_end - 0.22:.2f}), ({lt_end:.2f}-t)/0.22, 1)))"
            filters.append(f"drawtext=text='{esc_name}':x={name_x}:y={name_y}:fontsize={name_size}:fontcolor=white:shadowcolor=black@0.85:shadowx=2:shadowy=2:alpha='{name_alpha}':enable='between(t,{lt_start},{lt_end})'")
            title_alpha = f"if(lt(t,{lt_start + 0.18:.2f}), 0, if(lt(t,{lt_start + 0.44:.2f}), (t-{lt_start + 0.18:.2f})/0.26, if(gt(t,{lt_end - 0.22:.2f}), ({lt_end:.2f}-t)/0.22, 1)))"
            filters.append(f"drawtext=text='{esc_title}':x={title_x}:y={title_y}:fontsize={title_size}:fontcolor=0xD0D0D0:shadowcolor=black@0.85:shadowx=1:shadowy=1:alpha='{title_alpha}':enable='between(t,{lt_start},{lt_end})'")

        # 2. Watermark (responsive top-right corner)
        if self.cfg.watermark_enabled:
            wm_size = max(12, int(height * 0.022))
            margin_right = int(width * 0.025)
            wm_y = int(height * 0.035)
            esc_wm = escape_drawtext(self.cfg.watermark_text)
            filters.append(f"drawtext=text='{esc_wm}':x=w-tw-{margin_right}:y={wm_y}:fontsize={wm_size}:fontcolor=white@{self.cfg.watermark_opacity}:shadowcolor=black@0.70:shadowx=1:shadowy=1")

        # 3. High-Contrast Dual-Layer Glassmorphic Callout Badges with Kinetic Damped Spring Bounce
        # Placed in top-right header safe zone (height * 0.08) to completely clear speaker's head/face
        if self.cfg.callouts_enabled and callouts:
            callout_y = int(height * 0.08)
            card_h = max(36, int(height * 0.070))
            font_size = max(16, int(height * 0.029))
            accent_w = max(6, int(width * 0.007))

            # Detect best ultra-bold font file on system (Arial Black, Segoe UI Bold, or custom)
            bold_font_param = "font='Arial:style=Bold'"
            font_candidates = [
                config.FONTS_DIR / "Montserrat-Black.ttf",
                config.FONTS_DIR / "Inter-ExtraBold.ttf",
                Path("C:/Windows/Fonts/ariblk.ttf"),      # Arial Black (Ultra-thick, modern punch)
                Path("C:/Windows/Fonts/segoeuib.ttf"),    # Segoe UI Bold (Modern clean tech)
                Path("C:/Windows/Fonts/arialbd.ttf"),     # Arial Bold
            ]
            for fc in font_candidates:
                if fc.exists():
                    bold_font_param = f"fontfile='{escape_filter_path(fc)}'"
                    break

            for c in callouts:
                st = c.start_time
                et = c.end_time
                esc_c_text = escape_drawtext(c.text)
                color = getattr(c, "color", "0x00F0FF")

                # Proportional pill width based on character count with padding
                est_tw = int(len(c.text) * font_size * 0.76)
                card_w = max(int(width * 0.22), est_tw + int(width * 0.06))
                card_x = width - card_w - int(width * 0.04)

                fade_alpha = f"if(lt(t,{st + 0.15:.2f}), (t-{st:.2f})/0.15, if(gt(t,{et - 0.16:.2f}), ({et:.2f}-t)/0.16, 1))"

                # Layer 1: Dark Obsidian Glass backdrop
                filters.append(
                    f"drawbox=x={card_x}:y={callout_y}:w={card_w}:h={card_h}:color=0x0b0f17@0.92:t=fill:enable='between(t,{st:.2f},{et:.2f})'"
                )
                # Layer 2: Glowing outline border (2px) in vibrant category neon
                filters.append(
                    f"drawbox=x={card_x}:y={callout_y}:w={card_w}:h={card_h}:color={color}@0.95:t=2:enable='between(t,{st:.2f},{et:.2f})'"
                )
                # Layer 3: Left solid accent bar (6px)
                filters.append(
                    f"drawbox=x={card_x}:y={callout_y}:w={accent_w}:h={card_h}:color={color}@1.0:t=fill:enable='between(t,{st:.2f},{et:.2f})'"
                )
                # Layer 4: Centered ultra-bold keyword with black border stroke and 3D drop shadow
                filters.append(
                    f"drawtext=text='{esc_c_text}':x={card_x}+({card_w}-tw)/2:y={callout_y}+({card_h}-th)/2:"
                    f"{bold_font_param}:fontsize={font_size}:fontcolor=white:borderw=2:bordercolor=black@0.90:"
                    f"shadowcolor=black@0.95:shadowx=2:shadowy=2:alpha='{fade_alpha}':enable='between(t,{st:.2f},{et:.2f})'"
                )

        # 4. Check for valid B-roll metaphor cutaways (Animated 30fps .mov or High-Res PNG)
        valid_brolls = []
        if getattr(self.cfg, "broll_enabled", True) and broll_overlays:
            for b in broll_overlays:
                p_anim = getattr(b, "animated_clip_path", None)
                p_img = getattr(b, "image_path", None)
                if p_anim and Path(p_anim).exists() and Path(p_anim).stat().st_size > 1024:
                    valid_brolls.append((b, p_anim, True))
                elif p_img and Path(p_img).exists():
                    valid_brolls.append((b, p_img, False))

        if not filters and not valid_brolls:
            shutil.copy2(video_path, output_path)
            return output_path

        badge_count = len(callouts) if (self.cfg.callouts_enabled and callouts) else 0
        broll_count = len(valid_brolls)
        print(f"Applying broadcast branding overlays ({badge_count} badge(s), {broll_count} B-roll motion card(s))...")

        if valid_brolls:
            inputs = ["-i", str(video_path)]
            for b, media_p, is_anim in valid_brolls:
                inputs.extend(["-i", str(media_p)])

            v_chain_parts = []
            if filters:
                v_chain_parts.append(f"[0:v]{','.join(filters)}[vbase]")
                prev_tag = "[vbase]"
            else:
                prev_tag = "[0:v]"

            # Professional 16:9 PIP broadcast card dimensions (upper-left negative space, 0 blur on camera)
            card_w = int(width * 0.32)
            card_h = int(card_w * 9 / 16)
            card_x = int(width * 0.04)
            card_y = int(height * 0.08)

            for idx, (b, media_p, is_anim) in enumerate(valid_brolls, start=1):
                next_tag = f"[v_broll{idx}]"
                st = b.start_time
                et = b.end_time
                fade_d = 0.20
                if is_anim:
                    # Synchronize transparent animated video with smooth alpha fade
                    v_chain_parts.append(
                        f"[{idx}:v]setpts=PTS-STARTPTS+{st:.2f}/TB,scale={card_w}:{card_h},"
                        f"format=rgba,fade=t=in:st={st:.2f}:d={fade_d:.2f}:alpha=1,"
                        f"fade=t=out:st={et - fade_d:.2f}:d={fade_d:.2f}:alpha=1[bimg{idx}];"
                        f"{prev_tag}[bimg{idx}]overlay={card_x}:{card_y}:enable='between(t,{st:.2f},{et:.2f})'{next_tag}"
                    )
                else:
                    # Broadcast 16:9 card with cyan accent rim, dark glass border, and buttery-smooth alpha fade
                    v_chain_parts.append(
                        f"[{idx}:v]scale={card_w}:{card_h},"
                        f"pad=w={card_w + 6}:h={card_h + 6}:x=3:y=3:color=0x38bdf8@0.85,"
                        f"pad=w={card_w + 12}:h={card_h + 12}:x=3:y=3:color=0x0b0f17@0.95,"
                        f"format=rgba,fade=t=in:st={st:.2f}:d={fade_d:.2f}:alpha=1,"
                        f"fade=t=out:st={et - fade_d:.2f}:d={fade_d:.2f}:alpha=1[bimg{idx}];"
                        f"{prev_tag}[bimg{idx}]overlay={card_x}:{card_y}:enable='between(t,{st:.2f},{et:.2f})'{next_tag}"
                    )
                prev_tag = next_tag

            filter_complex_str = ";".join(v_chain_parts)
            cmd = [
                "ffmpeg", "-y",
                *inputs,
                "-filter_complex", filter_complex_str,
                "-map", prev_tag,
                "-map", "0:a?",
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "fast",
                "-c:a", "copy",
                str(output_path)
            ]
        else:
            vf_string = ",".join(filters)
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vf", vf_string,
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "fast",
                "-c:a", "copy",
                str(output_path)
            ]
        run_ffmpeg_checked(cmd, desc="Visual branding overlays")
        return output_path

    def create_intro(
        self,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
        fps: float = 30.0,
        sample_rate: int = 48000
    ) -> Path:
        """Generates a modern title intro card with ambient background matching source video specs."""
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dur = self.cfg.intro_duration

        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1

        title_size = max(22, int(height * 0.059))
        sub_size = max(13, int(height * 0.026))
        y_offset_title = int(height * 0.035)
        y_offset_sub = int(height * 0.045)

        esc_title = escape_drawtext(self.cfg.intro_title)
        esc_sub = escape_drawtext(self.cfg.intro_subtitle)

        print(f"Generating Intro sequence ({dur}s @ {width}x{height}, {fps}fps)...")
        vf = (
            f"drawtext=text='{esc_title}':x=(w-tw)/2:y=(h-th)/2-{y_offset_title}:fontsize={title_size}:fontcolor=white:"
            f"alpha='if(lt(t,0.8),t/0.8,if(gt(t,{dur - 0.8:.2f}),({dur}-t)/0.8,1))',"
            f"drawtext=text='{esc_sub}':x=(w-tw)/2:y=(h-th)/2+{y_offset_sub}:fontsize={sub_size}:fontcolor=0x00D4FF:"
            f"alpha='if(lt(t,1.2),(t-0.4)/0.8,if(gt(t,{dur - 0.8:.2f}),({dur}-t)/0.8,1))'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=0x0d1117:s={width}x{height}:d={dur}:r={fps}",
            "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={sample_rate}:d={dur}",
            "-vf", vf,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ]
        run_ffmpeg_checked(cmd, desc="Intro generation")
        return output_path

    def create_outro(
        self,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
        fps: float = 30.0,
        sample_rate: int = 48000
    ) -> Path:
        """Generates an end-screen outro sequence matching source video specs."""
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dur = self.cfg.outro_duration

        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1

        title_size = max(24, int(height * 0.063))
        sub_size = max(14, int(height * 0.028))
        y_offset_title = int(height * 0.038)
        y_offset_sub = int(height * 0.045)

        esc_title = escape_drawtext(self.cfg.outro_title)
        esc_sub = escape_drawtext(self.cfg.outro_subtitle)

        print(f"Generating Outro sequence ({dur}s @ {width}x{height}, {fps}fps)...")
        vf = (
            f"drawtext=text='{esc_title}':x=(w-tw)/2:y=(h-th)/2-{y_offset_title}:fontsize={title_size}:fontcolor=white:"
            f"alpha='if(lt(t,0.8),t/0.8,if(gt(t,{dur - 0.8:.2f}),({dur}-t)/0.8,1))',"
            f"drawtext=text='{esc_sub}':x=(w-tw)/2:y=(h-th)/2+{y_offset_sub}:fontsize={sub_size}:fontcolor=0xFFCC00:"
            f"alpha='if(lt(t,1.0),t/1.0,if(gt(t,{dur - 0.8:.2f}),({dur}-t)/0.8,1))'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=0x0a0e14:s={width}x{height}:d={dur}:r={fps}",
            "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={sample_rate}:d={dur}",
            "-vf", vf,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ]
        run_ffmpeg_checked(cmd, desc="Outro generation")
        return output_path

    def convert_to_shorts_9_16(
        self,
        video_path: Path,
        output_path: Path,
        style: Optional[str] = None
    ) -> Path:
        """
        Converts horizontal video to 9:16 vertical format (1080x1920).
        Uses blurred background fill + centered crisp video for maximum aesthetic quality.
        """
        video_path = Path(video_path).resolve()
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        crop_style = style or self.cfg.shorts_crop_style

        print(f"Converting '{video_path.name}' to YouTube Shorts 9:16 (1080x1920, style={crop_style})...")

        if crop_style == "center_crop":
            # Direct central 9:16 window crop
            filter_str = "crop=ih*9/16:ih:(iw-ow)/2:0,scale=1080:1920"
        else:
            # Pro blur-fill: Blurred ambient background + centered sharp frame maintaining aspect ratio
            filter_str = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
                "[0:v]scale=1080:-2[fg];"
                "[bg][fg]overlay=0:(H-h)/2[vout]"
            )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-filter_complex", filter_str,
            "-map", "[vout]" if crop_style != "center_crop" else "0:v",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "copy",
            str(output_path)
        ]
        run_ffmpeg_checked(cmd, desc="Shorts 9:16 conversion")
        return output_path

    def assemble_full_package(
        self,
        main_video_path: Path,
        output_path: Path,
        ass_subtitles: Optional[Path] = None,
        callouts: Optional[List[HighlightCallout]] = None,
        zoom_intervals: Optional[List[Any]] = None,
        broll_overlays: Optional[List[Any]] = None,
        cold_open_clip: Optional[Tuple[float, float, str]] = None
    ) -> Path:
        """
        Assembles complete production-ready video:
        1. Applies dynamic virtual multi-cam punch-ins (if enabled)
        2. Burns in subtitles & applies branding overlays, callouts & B-roll to main footage
        3. Generates Cold Open Hook Teaser, Intro & Outro sequences
        4. Concatenates [Cold Open] -> [Intro] -> [Main Video] -> [Outro] into final MP4
        """
        main_video_path = Path(main_video_path).resolve()
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 0: Apply dynamic virtual multi-cam punch-ins to video track
        temp_zoomed = None
        current_source = main_video_path
        if self.cfg.zooms_enabled and zoom_intervals:
            temp_zoomed = config.TEMP_DIR / f"{main_video_path.stem}_zoomed.mp4"
            self.apply_dynamic_zooms(main_video_path, temp_zoomed, zoom_intervals=zoom_intervals)
            current_source = temp_zoomed

        # Step 1: Polish main video (burn subs if available, add branding, callouts & broll)
        temp_branded = config.TEMP_DIR / f"{main_video_path.stem}_branded.mp4"
        if ass_subtitles and Path(ass_subtitles).exists():
            temp_subtitled = config.TEMP_DIR / f"{main_video_path.stem}_subbed.mp4"
            self.burn_subtitles(current_source, Path(ass_subtitles), temp_subtitled)
            self.add_branding_overlays(temp_subtitled, temp_branded, callouts=callouts, broll_overlays=broll_overlays)
            if temp_subtitled.exists():
                try:
                    temp_subtitled.unlink()
                except Exception:
                    pass
        else:
            self.add_branding_overlays(current_source, temp_branded, callouts=callouts, broll_overlays=broll_overlays)

        if temp_zoomed and temp_zoomed.exists():
            try:
                temp_zoomed.unlink()
            except Exception:
                pass

        # Step 2: Assemble Cold Open Teaser / Intro / Outro matching video's native resolution and frame rate
        segments_to_concat: List[Path] = []
        temp_cold_open = None
        temp_intro = config.TEMP_DIR / "intro_card.mp4"
        temp_outro = config.TEMP_DIR / "outro_card.mp4"

        # Query main video stream specs dynamically (resolution, real frame rate, audio sample rate)
        probe = probe_media(main_video_path)
        v_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), {})
        w = int(v_stream.get("width", 1920))
        h = int(v_stream.get("height", 1080))

        fps = 30.0
        avg_fps = v_stream.get("avg_frame_rate", "")
        r_fps = v_stream.get("r_frame_rate", "")
        for f_val in [avg_fps, r_fps]:
            f_str = str(f_val or "")
            if "/" in f_str:
                num, den = f_str.split("/")
                if float(den) > 0:
                    val = round(float(num) / float(den), 2)
                    if 12.0 <= val <= 65.0:
                        fps = val
                        break

        sr = 48000
        for s in probe.get("streams", []):
            if s.get("codec_type") == "audio":
                sr = int(s.get("sample_rate", 48000))
                break

        # A. Cold Open Hook Teaser (if enabled and quote found)
        if getattr(self.cfg, "cold_open_enabled", True) and cold_open_clip:
            from core.hooks import create_cold_open_teaser
            temp_cold_open = config.TEMP_DIR / f"{main_video_path.stem}_cold_open.mp4"
            try:
                create_cold_open_teaser(
                    main_video_path,
                    temp_cold_open,
                    start_time=cold_open_clip[0],
                    end_time=cold_open_clip[1],
                    width=w,
                    height=h,
                    fps=fps,
                    sample_rate=sr
                )
                segments_to_concat.append(temp_cold_open)
            except Exception as e:
                print(f"⚠️ Warning: Could not generate cold open teaser: {e}")

        # B. Ambient Intro Card
        if self.cfg.intro_enabled:
            self.create_intro(temp_intro, width=w, height=h, fps=fps, sample_rate=sr)
            segments_to_concat.append(temp_intro)

        # C. Main Content Video
        segments_to_concat.append(temp_branded)

        # D. Outro End-Screen Card
        if self.cfg.outro_enabled:
            self.create_outro(temp_outro, width=w, height=h, fps=fps, sample_rate=sr)
            segments_to_concat.append(temp_outro)

        # Step 3: Concat all parts using filter_complex concat for frame-accurate A/V sync
        if len(segments_to_concat) == 1:
            shutil.copy2(temp_branded, output_path)
        else:
            print(f"Assembling {len(segments_to_concat)} segments into master video...")
            input_args: List[str] = []
            filter_lines: List[str] = []
            concat_inputs: List[str] = []
            for i, seg in enumerate(segments_to_concat):
                input_args.extend(["-i", str(seg)])
                filter_lines.append(f"[{i}:v]setsar=1,fps={fps}[v{i}]")
                filter_lines.append(f"[{i}:a]aformat=sample_rates={sr}:channel_layouts=stereo[a{i}]")
                concat_inputs.append(f"[v{i}][a{i}]")

            n_segs = len(segments_to_concat)
            concat_filter = f"{';'.join(filter_lines)};{''.join(concat_inputs)}concat=n={n_segs}:v=1:a=1[outv][outa]"

            concat_cmd = [
                "ffmpeg", "-y",
                *input_args,
                "-filter_complex", concat_filter,
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "320k",
                "-movflags", "+faststart",
                str(output_path)
            ]
            run_ffmpeg_checked(concat_cmd, desc="Concat video segments")

        # Cleanup temp intro/outro/cold_open/branded files
        for f in [temp_cold_open, temp_intro, temp_outro, temp_branded]:
            if f and f.exists():
                try:
                    f.unlink()
                except Exception:
                    pass

        print(f"🎬 Full visual package successfully assembled -> '{output_path.name}'")
        return output_path
