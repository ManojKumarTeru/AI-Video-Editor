"""
Media Inspector & Validator for Phase 1.
Scans input folders, verifies integrity, and extracts detailed technical specs.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from utils.ffmpeg_utils import probe_media, check_media_integrity
import config

SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
SUPPORTED_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}


@dataclass
class MediaMetadata:
    path: Path
    filename: str
    media_type: str                  # "video", "audio", "music"
    size_mb: float
    duration_seconds: float = 0.0
    duration_formatted: str = "00:00"
    
    # Video specs
    has_video: bool = False
    video_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    
    # Audio specs
    has_audio: bool = False
    audio_codec: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    
    # Health checks
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    secs = int(round(seconds))
    mins, s = divmod(secs, 60)
    hrs, m = divmod(mins, 60)
    if hrs > 0:
        return f"{hrs:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class MediaInspector:
    """Discovers, validates, and analyzes media files."""

    def __init__(self):
        config.ensure_directories()

    def inspect_file(self, file_path: Path, media_type: str = "video") -> MediaMetadata:
        """Inspect a single media file using FFprobe and decode test."""
        file_path = Path(file_path).resolve()
        size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
        
        meta = MediaMetadata(
            path=file_path,
            filename=file_path.name,
            media_type=media_type,
            size_mb=size_mb
        )

        try:
            probe = probe_media(file_path)
        except Exception as e:
            meta.is_valid = False
            meta.issues.append(f"Probe failure: {str(e)}")
            return meta

        format_info = probe.get("format", {})
        try:
            meta.duration_seconds = float(format_info.get("duration", 0.0))
            meta.duration_formatted = format_duration(meta.duration_seconds)
        except (ValueError, TypeError):
            meta.duration_seconds = 0.0

        # Parse streams
        streams = probe.get("streams", [])
        for s in streams:
            codec_type = s.get("codec_type")
            if codec_type == "video" and not meta.has_video:
                meta.has_video = True
                meta.video_codec = s.get("codec_name")
                meta.width = s.get("width")
                meta.height = s.get("height")
                # Parse real playback FPS (prioritize avg_frame_rate over mobile container timebase)
                fps_val = None
                for f_field in ["avg_frame_rate", "r_frame_rate"]:
                    f_raw = str(s.get(f_field, "") or "")
                    if "/" in f_raw:
                        num, den = f_raw.split("/")
                        if float(den) > 0:
                            calc_f = round(float(num) / float(den), 2)
                            if 12.0 <= calc_f <= 65.0:
                                fps_val = calc_f
                                break
                if fps_val is None:
                    r_fps = str(s.get("r_frame_rate", "") or "")
                    if "/" in r_fps:
                        num, den = r_fps.split("/")
                        if float(den) > 0:
                            fps_val = round(float(num) / float(den), 2)
                meta.fps = fps_val or 30.0

            elif codec_type == "audio" and not meta.has_audio:
                meta.has_audio = True
                meta.audio_codec = s.get("codec_name")
                meta.sample_rate = int(s.get("sample_rate", 0))
                meta.channels = int(s.get("channels", 0))

        # Check for decode integrity
        is_ok, err = check_media_integrity(file_path, test_seconds=5)
        if not is_ok:
            meta.is_valid = False
            meta.issues.append(f"Integrity warning: {err}")

        # Basic validations
        if media_type == "video" and not meta.has_video:
            meta.is_valid = False
            meta.issues.append("Expected video stream but none found.")
        if media_type in ("video", "audio") and not meta.has_audio:
            meta.issues.append("Notice: No audio stream found.")

        return meta

    def scan_all_inputs(self) -> Dict[str, List[MediaMetadata]]:
        """Scans input/video, input/audio, and input/music directories."""
        results = {
            "video": [],
            "audio": [],
            "music": []
        }

        # Scan video
        if config.INPUT_VIDEO_DIR.exists():
            for p in sorted(config.INPUT_VIDEO_DIR.iterdir()):
                if p.is_file() and p.suffix.lower() in SUPPORTED_VIDEO_EXTS:
                    results["video"].append(self.inspect_file(p, "video"))

        # Scan audio
        if config.INPUT_AUDIO_DIR.exists():
            for p in sorted(config.INPUT_AUDIO_DIR.iterdir()):
                if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXTS:
                    results["audio"].append(self.inspect_file(p, "audio"))

        # Scan music
        if config.INPUT_MUSIC_DIR.exists():
            for p in sorted(config.INPUT_MUSIC_DIR.iterdir()):
                if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXTS:
                    results["music"].append(self.inspect_file(p, "music"))

        return results

    def print_report(self, results: Dict[str, List[MediaMetadata]]):
        """Displays formatted inspection report."""
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            
            table = Table(title="🎬 AI-Editor: Media Inspection Report", header_style="bold cyan")
            table.add_column("Type", style="bold yellow", width=8)
            table.add_column("File Name", style="white")
            table.add_column("Duration", justify="right", style="green")
            table.add_column("Resolution / FPS", justify="center", style="cyan")
            table.add_column("Audio Specs", justify="center", style="magenta")
            table.add_column("Status", justify="center")

            for m_type, items in results.items():
                for item in items:
                    res_fps = f"{item.width}x{item.height} @ {item.fps}fps" if item.has_video else "-"
                    audio_str = f"{item.audio_codec} {item.sample_rate}Hz {item.channels}ch" if item.has_audio else "No Audio"
                    status = "[bold green]Valid[/bold green]" if item.is_valid else f"[bold red]Issue: {', '.join(item.issues)}[/bold red]"
                    table.add_row(m_type.upper(), item.filename, item.duration_formatted, res_fps, audio_str, status)

            console.print(table)
            
            total_video_duration = sum(item.duration_seconds for item in results["video"])
            console.print(f"\n[bold]Total Raw Video Footage:[/bold] {format_duration(total_video_duration)} ({len(results['video'])} clip(s))")

        except ImportError:
            # Fallback if rich is not yet installed
            print("\n" + "=" * 70)
            print("  🎬 AI-Editor: Media Inspection Report")
            print("=" * 70)
            for m_type, items in results.items():
                print(f"\n[{m_type.upper()}] ({len(items)} found):")
                for item in items:
                    v_info = f"{item.width}x{item.height}@{item.fps}fps" if item.has_video else "N/A"
                    a_info = f"{item.sample_rate}Hz" if item.has_audio else "No Audio"
                    status = "OK" if item.is_valid else f"ISSUES: {item.issues}"
                    print(f"  • {item.filename:<24} | {item.duration_formatted} | {v_info:<16} | {a_info:<10} | {status}")
            print("=" * 70 + "\n")
