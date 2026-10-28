"""
Speech Transcription & Subtitle Engine using faster-whisper.
Runs 100% locally on CPU with int8 quantization.
Generates word-level timestamps, standard .srt, and professional styled .ass subtitles.
"""

import os
import sys

# Suppress HuggingFace hub symlink warning on Windows before importing AI libs
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import re
import json
import hashlib
import wave
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

import numpy as np

import config
from utils.ffmpeg_utils import extract_audio_for_transcription


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    probability: float


@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str
    words: List[WordTimestamp]


def format_srt_time(seconds: float) -> str:
    """Format seconds into SRT timestamp: HH:MM:SS,mmm"""
    millis = int(round(seconds * 1000))
    s, ms = divmod(millis, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp: H:MM:SS.cc (centiseconds)"""
    centis = int(round(seconds * 100))
    s, cs = divmod(centis, 100)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"


def compute_file_hash(file_path: Path) -> str:
    """Compute lightweight hash based on file size and partial content for fast caching."""
    hasher = hashlib.sha256()
    size = file_path.stat().st_size
    hasher.update(str(size).encode("utf-8"))
    with open(file_path, "rb") as f:
        # Read first 512KB and last 512KB
        hasher.update(f.read(512 * 1024))
        if size > 1024 * 1024:
            f.seek(-512 * 1024, os.SEEK_END)
            hasher.update(f.read(512 * 1024))
    return hasher.hexdigest()[:16]


def load_wav_as_numpy(wav_path: Path) -> np.ndarray:
    """
    Load a 16kHz mono WAV file directly into a float32 numpy array normalized to [-1.0, 1.0].
    Passing a numpy array directly to faster-whisper completely bypasses PyAV/av.open,
    avoiding any library incompatibilities or 'metadata_errors' keyword argument bugs.
    """
    with wave.open(str(wav_path), "rb") as wf:
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        audio_bytes = wf.readframes(n_frames)

    if sampwidth == 2:
        # 16-bit PCM
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        # 32-bit PCM
        audio = np.frombuffer(audio_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        # 8-bit unsigned
        audio = (np.frombuffer(audio_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0

    return audio


class Transcriber:
    """Transcription engine powered by faster-whisper on CPU."""

    def __init__(self, cfg: Optional[config.TranscriptionConfig] = None):
        self.cfg = cfg or config.TranscriptionConfig()
        self.model = None

    def _get_model(self) -> Any:
        """Lazy load the Whisper model into memory only when needed, returning the active instance."""
        if self.model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise RuntimeError(
                    "faster-whisper is not installed. Please run: py -m pip install -r requirements.txt"
                )

            print(f"Loading faster-whisper model '{self.cfg.model_size}' (device={self.cfg.device}, compute={self.cfg.compute_type})...")
            try:
                self.model = WhisperModel(
                    model_size_or_path=self.cfg.model_size,
                    device=self.cfg.device,
                    compute_type=self.cfg.compute_type,
                    cpu_threads=self.cfg.cpu_threads
                )
            except Exception as e:
                if self.cfg.model_size != "small":
                    print(f"⚠️ Could not load '{self.cfg.model_size}' ({e}). Falling back to 'small' model...")
                    self.cfg.model_size = "small"
                    self.model = WhisperModel(
                        model_size_or_path="small",
                        device=self.cfg.device,
                        compute_type=self.cfg.compute_type,
                        cpu_threads=self.cfg.cpu_threads
                    )
                else:
                    raise
            print("Model loaded successfully into memory.")
        return self.model

    def transcribe(self, input_media_path: Path, force_recompute: bool = False) -> List[SubtitleSegment]:
        """
        Transcribes speech from a video or audio file.
        Uses caching to avoid re-transcribing identical media.
        """
        input_media_path = Path(input_media_path).resolve()
        config.ensure_directories()

        # Step 1: Check cache (include task and language so switching translation never uses stale bad cache)
        file_hash = compute_file_hash(input_media_path)
        task_name = getattr(self.cfg, "task", "translate")
        lang_name = str(getattr(self.cfg, "language", "te") or "auto")
        cache_file = config.CACHE_DIR / f"{input_media_path.stem}_{file_hash}_{task_name}_{lang_name}.json"

        if cache_file.exists() and not force_recompute:
            print(f"Found cached transcription for '{input_media_path.name}'. Loading from cache...")
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            from core.tanglish import translate_tanglish_segments
            loaded_segs = [
                SubtitleSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"],
                    words=[WordTimestamp(**w) for w in seg["words"]]
                )
                for seg in cached_data
            ]
            return translate_tanglish_segments(loaded_segs)

        # Step 2: Extract audio as 16kHz mono WAV for Whisper
        temp_wav = config.TEMP_DIR / f"{input_media_path.stem}_16k.wav"
        print(f"Extracting 16kHz audio from '{input_media_path.name}'...")
        extract_audio_for_transcription(input_media_path, temp_wav)

        # Step 3: Load audio directly into NumPy array (avoids PyAV metadata_errors bug)
        audio_array = load_wav_as_numpy(temp_wav)

        # Clean up temporary 16k wav
        if temp_wav.exists():
            try:
                temp_wav.unlink()
            except Exception:
                pass

        # Step 4: Run inference
        model = self._get_model()
        task = getattr(self.cfg, "task", "translate")
        target_lang = self.cfg.language if self.cfg.language not in (None, "auto") else None
        init_prompt = getattr(self.cfg, "initial_prompt", "English subtitles only. Professional YouTube video captions in pure English script. No Telugu script.")

        print(f"Transcribing '{input_media_path.name}' (task={task}, language={target_lang or 'auto'}, model={self.cfg.model_size})...")

        segments_gen, info = model.transcribe(
            audio_array,
            beam_size=self.cfg.beam_size,
            word_timestamps=self.cfg.word_timestamps,
            vad_filter=self.cfg.vad_filter,
            vad_parameters=dict(
                min_silence_duration_ms=self.cfg.vad_min_silence_ms,
                speech_pad_ms=self.cfg.vad_speech_pad_ms
            ),
            language=target_lang,
            task=task,
            initial_prompt=init_prompt,
            condition_on_previous_text=False,
            no_speech_threshold=0.6
        )

        detected_lang = info.language
        lang_prob = round(info.language_probability * 100, 1)
        print(f"Detected speech language: {detected_lang.upper()} ({lang_prob}% confidence) -> Output: English script")

        parsed_segments: List[SubtitleSegment] = []
        for segment in segments_gen:
            words = []
            if segment.words:
                for w in segment.words:
                    clean_w = re.sub(r"[【】「」\[\]]", "", w.word).strip()
                    # Strictly filter out any words containing Telugu or Indic script characters
                    if clean_w and not re.search(r"[\u0C00-\u0C7F\u0900-\u0D7F]", clean_w):
                        words.append(WordTimestamp(
                            word=clean_w,
                            start=round(w.start, 2),
                            end=round(w.end, 2),
                            probability=round(w.probability, 2)
                        ))
            clean_text = re.sub(r"[【】「」\[\]]", "", segment.text).strip()
            # Strictly remove any Telugu/Indic script characters from segment text
            clean_text = re.sub(r"[\u0C00-\u0C7F\u0900-\u0D7F]+", "", clean_text).strip()
            clean_text = re.sub(r"\s+", " ", clean_text).strip(" :,-.")
            if clean_text and words:
                parsed_segments.append(SubtitleSegment(
                    start=round(segment.start, 2),
                    end=round(segment.end, 2),
                    text=clean_text,
                    words=words
                ))

        # Step 4.5: Tanglish Semantic Translation & Normalization
        # Converts code-switched Telugu words (e.g. 'miru' -> 'you', 'software job lo' -> 'in a software job')
        # into natural English meaning while preserving word-level animation timestamps
        from core.tanglish import translate_tanglish_segments
        parsed_segments = translate_tanglish_segments(parsed_segments)

        # Step 5: Save cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump([asdict(s) for s in parsed_segments], f, indent=2, ensure_ascii=False)

        print(f"Transcription complete: {len(parsed_segments)} segment(s) generated.")
        return parsed_segments

    def chunk_segments_for_subtitles(
        self,
        segments: List[SubtitleSegment],
        max_words: int = 7,
        max_chars: int = 36,
        max_duration: float = 3.2
    ) -> List[SubtitleSegment]:
        """
        Splits long Whisper speech segments into short, punchy subtitle cards (5+ YOE editor style).
        Keeps captions readable, prevents edge-overflow, and preserves high viewer engagement.
        """
        chunked: List[SubtitleSegment] = []
        for seg in segments:
            if not seg.words or len(seg.words) <= max_words:
                chunked.append(seg)
                continue

            curr_words: List[WordTimestamp] = []
            curr_chars = 0

            for w in seg.words:
                curr_words.append(w)
                curr_chars += len(w.word) + 1
                curr_duration = curr_words[-1].end - curr_words[0].start
                is_punct = w.word.endswith((".", "?", "!", ":", ";"))

                if is_punct or len(curr_words) >= max_words or curr_chars >= max_chars or curr_duration >= max_duration:
                    chunk_text = " ".join([cw.word for cw in curr_words])
                    chunked.append(SubtitleSegment(
                        start=curr_words[0].start,
                        end=curr_words[-1].end,
                        text=chunk_text,
                        words=list(curr_words)
                    ))
                    curr_words = []
                    curr_chars = 0

            if curr_words:
                chunk_text = " ".join([cw.word for cw in curr_words])
                chunked.append(SubtitleSegment(
                    start=curr_words[0].start,
                    end=curr_words[-1].end,
                    text=chunk_text,
                    words=list(curr_words)
                ))

        return chunked

    def export_srt(self, segments: List[SubtitleSegment], output_srt_path: Path) -> Path:
        """Generates standard SRT subtitles with natural line wrapping."""
        output_srt_path = Path(output_srt_path).resolve()
        output_srt_path.parent.mkdir(parents=True, exist_ok=True)

        # Apply pro pacing chunker
        formatted_segments = self.chunk_segments_for_subtitles(segments)

        lines = []
        idx = 1
        for seg in formatted_segments:
            # Strictly filter out any Telugu or Indic characters or blank entries
            clean_text = re.sub(r"[\u0C00-\u0C7F\u0900-\u0D7F]+", "", seg.text).strip()
            clean_text = re.sub(r"\s+", " ", clean_text).strip(" :,-.")
            if not clean_text:
                continue
            lines.append(str(idx))
            lines.append(f"{format_srt_time(seg.start)} --> {format_srt_time(seg.end)}")
            lines.append(clean_text)
            lines.append("")
            idx += 1

        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"SRT subtitles saved -> {output_srt_path}")
        return output_srt_path

    def export_ass(
        self,
        segments: List[SubtitleSegment],
        output_ass_path: Path,
        style_cfg: Optional[config.SubtitleConfig] = None
    ) -> Path:
        """
        Generates professional styled ASS subtitles with:
        - Safe bottom margin (no overlap with YouTube UI)
        - Crisp outlines for readability on any background
        - Word-by-word progressive karaoke timing (\\kf tags)
        - Card-by-card pacing so text never overflows off-screen
        """
        output_ass_path = Path(output_ass_path).resolve()
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)
        s_cfg = style_cfg or config.SubtitleConfig()

        # Apply pro pacing chunker
        formatted_segments = self.chunk_segments_for_subtitles(segments)

        outline_w = getattr(s_cfg, "outline_width", 4)
        shadow_w = getattr(s_cfg, "shadow_width", 2)
        border_style = 3 if getattr(s_cfg, "background_box", False) else 1
        font_size = getattr(s_cfg, "font_size", 52)
        margin_v = getattr(s_cfg, "margin_bottom", 68)

        header = f"""[Script Info]
Title: AI-Editor Professional Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ProCaptions,{s_cfg.font_name},{font_size},{s_cfg.primary_color},{s_cfg.secondary_color},{s_cfg.outline_color},&H80000000,-1,0,0,0,100,100,0,0,{border_style},{outline_w},{shadow_w},2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        event_lines = []
        sec_color = s_cfg.secondary_color if s_cfg.secondary_color.endswith("&") else f"{s_cfg.secondary_color}&"

        for seg in formatted_segments:
            # Strictly verify segment contains valid English words and no Telugu script
            clean_seg_text = re.sub(r"[\u0C00-\u0C7F\u0900-\u0D7F]+", "", seg.text).strip()
            clean_seg_text = re.sub(r"\s+", " ", clean_seg_text).strip(" :,-.")
            valid_words = [
                w for w in (seg.words or [])
                if not re.search(r"[\u0C00-\u0C7F\u0900-\u0D7F]", w.word) and w.word.strip()
            ]
            if not clean_seg_text or not valid_words:
                continue

            if getattr(s_cfg, "kinetic_bounce_enabled", True):
                # 5+ YOE Kinetic Word-by-Word Pop: Spoken word scales up by 120%, thickens stroke & glows accent color
                num_words = len(valid_words)
                for i, active_w in enumerate(valid_words):
                    w_start = active_w.start
                    if i + 1 < num_words:
                        next_w = valid_words[i + 1]
                        if next_w.start > w_start and (next_w.start - active_w.end) < 0.40:
                            w_end = next_w.start
                        else:
                            w_end = max(active_w.end, round(w_start + 0.12, 2))
                    else:
                        w_end = max(active_w.end, seg.end)

                    if w_end <= w_start:
                        w_end = round(w_start + 0.15, 2)

                    start_str = format_ass_time(w_start)
                    end_str = format_ass_time(w_end)

                    chunk_display = []
                    for j, w in enumerate(valid_words):
                        if j == i:
                            # Active popping word with 120% spring scale, heavy stroke contrast & vibrant color accent
                            pop_word = f"{{\\c{sec_color}\\b1\\bord5\\shad3\\fscx120\\fscy120\\t(0,100,\\fscx108\\fscy108)}}{w.word}{{\\r}}"
                            chunk_display.append(pop_word)
                        else:
                            chunk_display.append(w.word)

                    line_text = " ".join(chunk_display)
                    event_lines.append(f"Dialogue: 0,{start_str},{end_str},ProCaptions,,0,0,0,,{line_text}")
            else:
                # Classic progressive karaoke timing (\kf tags)
                start_str = format_ass_time(seg.start)
                end_str = format_ass_time(seg.end)
                kf_parts = []
                for w in valid_words:
                    duration_cs = max(1, int(round((w.end - w.start) * 100)))
                    kf_parts.append(f"{{\\kf{duration_cs}}}{w.word}")
                dialogue_text = " ".join(kf_parts)
                event_lines.append(f"Dialogue: 0,{start_str},{end_str},ProCaptions,,0,0,0,,{dialogue_text}")

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(event_lines) + "\n")

        print(f"Styled ASS subtitles saved -> {output_ass_path}")
        return output_ass_path
