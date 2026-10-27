"""
Intelligent Silence Removal & Smart Cutting Engine.
Applies 5+ YOE editor principles:
- Conservative dead-air removal (keeps natural pauses < 0.8s)
- Speech lead-in (300ms) and lead-out (350ms) padding
- Micro audio fades to eliminate clicks/pops at cut seams
- Generates an Edit Decision List (EDL) and preview report
"""

import re
import json
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Any, Optional

import config
from utils.ffmpeg_utils import probe_media


@dataclass
class SilenceRegion:
    start: float
    end: float
    duration: float


@dataclass
class CutInterval:
    cut_start: float
    cut_end: float
    duration: float


@dataclass
class CutPlan:
    file_path: Path
    original_duration: float
    new_duration: float
    time_saved: float
    percent_saved: float
    cuts: List[CutInterval]
    keep_intervals: List[Tuple[float, float]]


def format_time(seconds: float) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    secs = int(round(seconds))
    mins, s = divmod(secs, 60)
    hrs, m = divmod(mins, 60)
    if hrs > 0:
        return f"{hrs:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class SmartEditor:
    """Smart silence detection and non-destructive cutting engine."""

    def __init__(self, cfg: Optional[config.EditingConfig] = None):
        self.cfg = cfg or config.EditingConfig()
        config.ensure_directories()

    def is_auto_editor_available(self) -> bool:
        """Check if auto-editor CLI is installed."""
        return shutil.which("auto-editor") is not None

    def detect_silence_ffmpeg(self, media_path: Path) -> List[SilenceRegion]:
        """
        Detects audio silence regions using FFmpeg's silencedetect filter.
        Returns a list of raw detected SilenceRegions.
        """
        media_path = Path(media_path).resolve()
        cmd = [
            "ffmpeg",
            "-i", str(media_path),
            "-af", f"silencedetect=noise={self.cfg.silence_threshold_db}dB:d={self.cfg.min_silence_duration}",
            "-f", "null",
            "-"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        stderr = result.stderr

        silence_regions: List[SilenceRegion] = []
        current_start: Optional[float] = None

        # Regex patterns for FFmpeg silencedetect output
        start_pattern = re.compile(r"silence_start:\s*(-?\d+(\.\d+)?)")
        end_pattern = re.compile(r"silence_end:\s*(-?\d+(\.\d+)?)\s*\|\s*silence_duration:\s*(-?\d+(\.\d+)?)")

        for line in stderr.splitlines():
            s_match = start_pattern.search(line)
            if s_match:
                current_start = max(0.0, float(s_match.group(1)))
                continue

            e_match = end_pattern.search(line)
            if e_match and current_start is not None:
                end_time = float(e_match.group(1))
                duration = float(e_match.group(3))
                silence_regions.append(SilenceRegion(
                    start=round(current_start, 3),
                    end=round(end_time, 3),
                    duration=round(duration, 3)
                ))
                current_start = None

        return silence_regions

    def build_cut_plan(self, media_path: Path) -> CutPlan:
        """
        Analyzes media and calculates precise conservative cuts with 5+ YOE padding:
        - Leaves 350ms lead-out after speech ends (preserves room tone)
        - Leaves 300ms lead-in before speech starts (preserves consonants)
        - Drops cuts where duration after padding is < 0.25s (preserves natural cadence)
        """
        media_path = Path(media_path).resolve()
        probe = probe_media(media_path)
        format_info = probe.get("format", {})
        total_duration = float(format_info.get("duration", 0.0))

        raw_silences = self.detect_silence_ffmpeg(media_path)
        conservative_cuts: List[CutInterval] = []

        for sil in raw_silences:
            # 5+ YOE Human Rule: If silence starts at video head (t <= 0.15s),
            # there is no preceding speech to preserve room tone for. Cut from 0.0s
            # directly up to right before the first spoken syllable (leaving 150ms lead-in)!
            if sil.start <= 0.15:
                cut_start = 0.0
                cut_end = max(0.0, sil.end - 0.15)
            elif sil.end >= total_duration - 0.15:
                # Video tail silence: no following speech, cut cleanly to end of video
                cut_start = sil.start + self.cfg.lead_out_margin
                cut_end = total_duration
            else:
                # Mid-timeline conversational pause: preserve natural breath margins
                cut_start = sil.start + self.cfg.lead_out_margin
                cut_end = sil.end - self.cfg.lead_in_margin

            cut_dur = cut_end - cut_start

            # Only cut if there is substantial dead air remaining after padding
            if cut_dur >= 0.20 and cut_start < total_duration:
                cut_start = max(0.0, cut_start)
                cut_end = min(total_duration, cut_end)
                conservative_cuts.append(CutInterval(
                    cut_start=round(cut_start, 3),
                    cut_end=round(cut_end, 3),
                    duration=round(cut_end - cut_start, 3)
                ))

        # Build Keep Intervals (inverted cuts)
        keep_intervals: List[Tuple[float, float]] = []
        curr = 0.0
        for cut in conservative_cuts:
            if cut.cut_start > curr:
                keep_intervals.append((round(curr, 3), round(cut.cut_start, 3)))
            curr = cut.cut_end

        if curr < total_duration:
            keep_intervals.append((round(curr, 3), round(total_duration, 3)))

        # Fallback if no cuts were needed
        if not keep_intervals:
            keep_intervals = [(0.0, round(total_duration, 3))]

        new_duration = sum(end - start for start, end in keep_intervals)
        time_saved = total_duration - new_duration
        percent_saved = (time_saved / total_duration * 100.0) if total_duration > 0 else 0.0

        plan = CutPlan(
            file_path=media_path,
            original_duration=round(total_duration, 2),
            new_duration=round(new_duration, 2),
            time_saved=round(time_saved, 2),
            percent_saved=round(percent_saved, 1),
            cuts=conservative_cuts,
            keep_intervals=keep_intervals
        )

        # Save EDL to workspace logs
        edl_log = config.OUTPUT_LOGS_DIR / f"{media_path.stem}_cut_plan.json"
        with open(edl_log, "w", encoding="utf-8") as f:
            json.dump({
                "file": str(media_path),
                "original_duration": plan.original_duration,
                "new_duration": plan.new_duration,
                "time_saved": plan.time_saved,
                "percent_saved": plan.percent_saved,
                "cuts_count": len(plan.cuts),
                "cuts": [asdict(c) for c in plan.cuts],
                "keep_intervals": plan.keep_intervals
            }, f, indent=2)

        return plan

    def apply_cuts(self, cut_plan: CutPlan, output_path: Path) -> Path:
        """
        Executes frame-accurate cuts according to cut_plan with micro audio fades.
        Uses single-pass FFmpeg filter_complex with trim/atrim to guarantee 100%
        frame-accurate synchronization between audio and video without keyframe drift.
        """
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        source_path = cut_plan.file_path

        # If no cuts were needed, copy directly
        if len(cut_plan.cuts) == 0:
            print("No dead air detected exceeding threshold. Copying original stream...")
            cmd = ["ffmpeg", "-y", "-i", str(source_path), "-c", "copy", str(output_path)]
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path

        print(f"Applying {len(cut_plan.cuts)} smart cut(s) to '{source_path.name}'...")

        filter_lines: List[str] = []
        concat_inputs: List[str] = []

        for idx, (start_t, end_t) in enumerate(cut_plan.keep_intervals):
            seg_duration = end_t - start_t
            fade_d = min(self.cfg.crossfade_duration, seg_duration / 4.0)

            # Frame-accurate video trim and reset PTS to 0
            filter_lines.append(f"[0:v]trim=start={start_t:.3f}:end={end_t:.3f},setpts=PTS-STARTPTS[v{idx}];")

            # Sample-accurate audio trim, reset PTS, and apply micro in/out audio fades
            afade_in = f"afade=t=in:st=0:d={fade_d:.3f}"
            afade_out = f"afade=t=out:st={max(0.0, seg_duration - fade_d):.3f}:d={fade_d:.3f}"
            filter_lines.append(f"[0:a]atrim=start={start_t:.3f}:end={end_t:.3f},asetpts=PTS-STARTPTS,{afade_in},{afade_out}[a{idx}];")

            concat_inputs.append(f"[v{idx}][a{idx}]")

        n_segs = len(cut_plan.keep_intervals)
        filter_lines.append(f"{''.join(concat_inputs)}concat=n={n_segs}:v=1:a=1[outv][outa]")
        filter_content = "".join(filter_lines)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(source_path),
            "-filter_complex", filter_content,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", self.cfg.video_codec,
            "-crf", str(self.cfg.crf),
            "-preset", self.cfg.preset,
            "-c:a", "aac",
            "-b:a", "320k",
            "-movflags", "+faststart",
            str(output_path)
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg trim failed: {res.stderr.strip()}")

        print(f"✅ Cut video successfully exported -> {output_path}")
        return output_path

    def print_cut_report(self, plan: CutPlan):
        """Displays rich formatted cut decision report."""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            console = Console()

            table = Table(title="✂️ AI-Editor: Silence Cut Plan (5+ YOE Conservative Mode)", header_style="bold cyan")
            table.add_column("Metric", style="bold yellow")
            table.add_column("Value", style="bold white")

            table.add_row("Source File", plan.file_path.name)
            table.add_row("Original Duration", format_time(plan.original_duration))
            table.add_row("New Duration", f"[bold green]{format_time(plan.new_duration)}[/bold green]")
            table.add_row("Dead Air Removed", f"[bold cyan]{format_time(plan.time_saved)}[/bold cyan] ({plan.percent_saved}% shorter)")
            table.add_row("Cuts Count", str(len(plan.cuts)))
            table.add_row("Preserved Segments", str(len(plan.keep_intervals)))
            table.add_row("Lead-in / Lead-out Padding", f"{int(self.cfg.lead_in_margin*1000)}ms / {int(self.cfg.lead_out_margin*1000)}ms")

            console.print(table)

            if plan.cuts:
                sample_cuts = plan.cuts[:5]
                console.print("\n[bold]Sample Cut Timestamps:[/bold]")
                for idx, c in enumerate(sample_cuts, 1):
                    console.print(f"  [{idx}] Cut from {format_time(c.cut_start)} to {format_time(c.cut_end)} (trimmed {c.duration:.2f}s)")
                if len(plan.cuts) > 5:
                    console.print(f"  ... and {len(plan.cuts) - 5} more cuts detailed in output/logs/")

        except ImportError:
            print("\n" + "=" * 65)
            print("  ✂️ AI-Editor: Silence Cut Plan")
            print("=" * 65)
            print(f"File             : {plan.file_path.name}")
            print(f"Original Duration: {format_time(plan.original_duration)}")
            print(f"New Duration     : {format_time(plan.new_duration)}")
            print(f"Time Saved       : {format_time(plan.time_saved)} ({plan.percent_saved}%)")
            print(f"Total Cuts       : {len(plan.cuts)}")
            print("=" * 65 + "\n")
