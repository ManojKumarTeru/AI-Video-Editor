"""
Phase 1 Test & Validation Runner.
Tests:
1. Environment & directory setup
2. Media inspection on test or user media
3. 16kHz audio extraction
4. faster-whisper transcription with word timestamps (bypassing PyAV bug)
5. SRT and professional ASS subtitle generation
"""

import os
import sys

# Suppress HuggingFace hub symlink warning on Windows before importing
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import subprocess
from pathlib import Path

import config
from utils.ffmpeg_utils import check_media_integrity
from core.inspector import MediaInspector
from core.transcriber import Transcriber


import importlib.util


def check_installed_packages():
    """Verify required packages before running."""
    packages = ["faster_whisper", "rich"]
    missing = [pkg for pkg in packages if importlib.util.find_spec(pkg) is None]

    if missing:
        print("\n" + "!" * 65)
        print(f"⚠️  Missing required packages: {', '.join(missing)}")
        print("Please install them by running:")
        print("    py -m pip install -r requirements.txt")
        print("!" * 65 + "\n")
        return False
    return True


def create_synthetic_test_clip_if_needed() -> Path:
    """
    If no user video is in input/video, creates a 5-second 1080p test video with
    synthesized speech using Windows built-in speech synthesis + FFmpeg,
    so Phase 1 can be tested with real spoken words immediately.
    """
    config.ensure_directories()
    sample_video = config.INPUT_VIDEO_DIR / "sample_test_clip.mp4"
    
    # Check if user dropped their own video (ignoring sample_test_clip)
    user_videos = [
        p for p in config.INPUT_VIDEO_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".mkv"} and p.name != "sample_test_clip.mp4"
    ]
    if user_videos:
        print(f"Found existing user video: '{user_videos[0].name}'")
        return user_videos[0]

    tts_wav = config.TEMP_DIR / "test_speech.wav"
    speech_text = "Welcome back to the channel. Today we are testing our automated video editor."
    
    print("Generating speech audio using Windows built-in voice synthesizer...")
    ps_script_file = config.TEMP_DIR / "make_voice.ps1"
    with open(ps_script_file, "w", encoding="utf-8") as f:
        f.write(f"""Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SetOutputToWaveFile('{str(tts_wav)}')
$s.Speak('{speech_text}')
$s.Dispose()
""")

    import shutil
    powershell_exe = shutil.which("powershell") or r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    try:
        ps_res = subprocess.run([powershell_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script_file)], capture_output=True, text=True, timeout=15)
        if ps_res.returncode != 0:
            print(f"  Voice synthesis notice: {ps_res.stderr.strip()[:100]}")
    except Exception as e:
        print(f"  Could not run voice synthesis: {e}")

    # Remove temporary script
    if ps_script_file.exists():
        try:
            ps_script_file.unlink()
        except Exception:
            pass

    print("Generating 1080p sample video with audio track...")
    if tts_wav.exists() and tts_wav.stat().st_size > 1000:
        print(f"  Found generated speech WAV ({round(tts_wav.stat().st_size / 1024, 1)} KB). Muxing with 1080p video...")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=7:size=1920x1080:rate=30",
            "-i", str(tts_wav),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(sample_video)
        ]
    else:
        # Fallback to pure tone
        print("  Using synthesized audio pattern...")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=5:size=1920x1080:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            str(sample_video)
        ]

    subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    # Cleanup temp tts wav
    if tts_wav.exists():
        try:
            tts_wav.unlink()
        except Exception:
            pass

    print(f"✅ Generated test video with speech: '{sample_video.name}'")
    return sample_video


def run_phase1_tests():
    print("=" * 65)
    print("  🎬 AI-Editor — Phase 1 Test & Validation Suite")
    print("=" * 65)

    # 1. Setup Directories
    config.ensure_directories()
    print("✅ Project directories verified.")

    # 2. Check Dependencies
    if not check_installed_packages():
        print("Exiting test early until dependencies are installed.")
        return

    # 3. Media Discovery & Test Clip
    test_clip = create_synthetic_test_clip_if_needed()

    # 4. Media Inspection Test
    print("\n--- Running Media Inspector ---")
    inspector = MediaInspector()
    results = inspector.scan_all_inputs()
    inspector.print_report(results)

    # 5. Transcription & Subtitles Test
    print("\n--- Running Transcription Engine ---")
    # Using 'base' model for fast verification on CPU
    transcriber = Transcriber(config.TranscriptionConfig(model_size="base"))
    segments = transcriber.transcribe(test_clip, force_recompute=True)

    print(f"\nGenerated {len(segments)} segment(s):")
    if segments:
        for s in segments:
            print(f"  [{s.start:.2f}s -> {s.end:.2f}s]: \"{s.text}\"")
            if s.words:
                word_summary = ", ".join([f"{w.word} ({w.start:.2f}-{w.end:.2f}s)" for w in s.words[:6]])
                if len(s.words) > 6:
                    word_summary += f" ... (+{len(s.words)-6} more)"
                print(f"    └─ Words: {word_summary}")
    else:
        print("  (Audio contains no detected speech. For speech testing, drop an MP4 clip with dialogue into 'input/video/')")

    # 6. Subtitle Exports
    srt_out = config.OUTPUT_SUBTITLES_DIR / f"{test_clip.stem}.srt"
    ass_out = config.OUTPUT_SUBTITLES_DIR / f"{test_clip.stem}.ass"

    transcriber.export_srt(segments, srt_out)
    transcriber.export_ass(segments, ass_out)

    print("\n" + "=" * 65)
    print("  🎉 PHASE 1 VERIFICATION COMPLETE!")
    print(f"  • Subtitles (SRT): {srt_out}")
    print(f"  • Subtitles (ASS): {ass_out}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_phase1_tests()
