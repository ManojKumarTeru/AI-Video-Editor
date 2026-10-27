"""
FFmpeg and FFprobe wrapper utilities for media inspection and audio extraction.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


def escape_filter_path(path: Path) -> str:
    """
    Format Windows filesystem path for FFmpeg filter arguments:
    - Forward slashes
    - Escape colon following the drive letter (e.g. C\\:/path/...)
    - Escape single quotes
    """
    p_str = path.resolve().as_posix()
    if len(p_str) > 1 and p_str[1] == ":":
        p_str = p_str[0] + r"\:" + p_str[2:]
    return p_str.replace("'", r"\'")


def escape_drawtext(text: str) -> str:
    """
    Escape text string for FFmpeg drawtext filter.
    Escapes backslashes, single quotes, colons, and percent signs.
    """
    return (
        text.replace("\\", "\\\\")
        .replace("'", r"\'")
        .replace(":", r"\:")
        .replace("%", r"\%")
    )


def run_ffmpeg_checked(cmd: List[str], desc: str = "FFmpeg") -> subprocess.CompletedProcess:
    """Runs FFmpeg command and raises a descriptive RuntimeError with stderr on failure."""
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        err_msg = res.stderr.strip() if res.stderr else "Unknown error"
        raise RuntimeError(f"❌ {desc} failed (exit code {res.returncode}):\n{err_msg}\nCommand: {' '.join(cmd)}")
    return res


def probe_media(file_path: Path) -> Dict[str, Any]:
    """
    Extract complete stream and format metadata using ffprobe.
    Returns parsed dictionary from FFprobe's JSON output.
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Media file not found: {file_path}")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"FFprobe failed on '{file_path.name}': {result.stderr.strip()}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse FFprobe output for '{file_path.name}': {e}")


def check_media_integrity(file_path: Path, test_seconds: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Performs a fast decode test on the media file to verify it is not corrupted.
    Returns (is_valid, error_message_if_any).
    """
    file_path = Path(file_path).resolve()
    cmd = [
        "ffmpeg",
        "-v", "error",
        "-i", str(file_path),
        "-t", str(test_seconds),
        "-f", "null",
        "-"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, None


def extract_audio_for_transcription(input_path: Path, output_wav_path: Path, sample_rate: int = 16000) -> Path:
    """
    Extracts audio from video as 16kHz mono 16-bit uncompressed PCM WAV.
    This is the ideal format for faster-whisper on CPU.
    """
    input_path = Path(input_path).resolve()
    output_wav_path = Path(output_wav_path).resolve()
    output_wav_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        str(output_wav_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed for '{input_path.name}': {result.stderr.strip()}")

    return output_wav_path
