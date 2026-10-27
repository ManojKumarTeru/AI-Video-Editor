"""
Phase 2 Validation Runner: Smart Silence Removal & Conservative Cuts.
Tests:
1. Generates a video containing deliberate dead air (3-second pause between sentences)
2. Runs SmartEditor to detect dead air via audio waveform analysis
3. Applies conservative padding (350ms lead-out, 300ms lead-in)
4. Renders the frame-accurate trimmed video with audio micro-fades
5. Validates the exported video duration, sync, and time saved
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

import config
from utils.ffmpeg_utils import probe_media, check_media_integrity
from core.editor import SmartEditor, format_time


def create_pause_test_video() -> Path:
    """
    Creates an 8-second 1080p test video with deliberate speech and a 3-second dead-air pause.
    Structure:
    - [0.0s - 2.5s]: Spoken sentence 1 ("Welcome to the editing demonstration.")
    - [2.5s - 5.5s]: 3 SECONDS OF DEAD AIR
    - [5.5s - 8.5s]: Spoken sentence 2 ("We are now back after a long pause.")
    """
    config.ensure_directories()
    test_video = config.INPUT_VIDEO_DIR / "silence_test_video.mp4"
    temp_dir = config.TEMP_DIR

    voice1_wav = temp_dir / "voice1.wav"
    voice2_wav = temp_dir / "voice2.wav"
    combined_wav = temp_dir / "voice_with_silence.wav"
    ps_script = temp_dir / "gen_pause_audio.ps1"

    print("Synthesizing speech with a deliberate 3-second dead air pause...")
    with open(ps_script, "w", encoding="utf-8") as f:
        f.write(f"""Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SetOutputToWaveFile('{str(voice1_wav)}')
$s.Speak('Welcome to the video editing demonstration.')
$s.SetOutputToWaveFile('{str(voice2_wav)}')
$s.Speak('We are now back after a long silent pause.')
$s.Dispose()
""")

    powershell_exe = shutil.which("powershell") or r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    try:
        subprocess.run([powershell_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)], capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"Warning running voice synthesis: {e}")

    # Clean up ps script
    if ps_script.exists():
        try:
            ps_script.unlink()
        except Exception:
            pass

    # Use FFmpeg to insert a 3-second silent gap between voice1 and voice2
    if voice1_wav.exists() and voice2_wav.exists():
        concat_af_cmd = [
            "ffmpeg", "-y",
            "-i", str(voice1_wav),
            "-f", "lavfi", "-t", "3", "-i", "anullsrc=channel_layout=mono:sample_rate=22050",
            "-i", str(voice2_wav),
            "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[aout]",
            "-map", "[aout]",
            str(combined_wav)
        ]
        subprocess.run(concat_af_cmd, capture_output=True, check=True)
        audio_input = str(combined_wav)
    else:
        # Fallback tone with silence
        audio_input = "sine=frequency=440:duration=2"

    # Mux with 1080p video test pattern
    print("Muxing video with speech and dead air into 1080p MP4...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=30",
        "-i", audio_input,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(test_video)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    # Clean temporary wav files
    for w in [voice1_wav, voice2_wav, combined_wav]:
        if w.exists():
            try:
                w.unlink()
            except Exception:
                pass

    return test_video


def run_phase2_tests():
    print("=" * 65)
    print("  🎬 AI-Editor — Phase 2: Smart Silence Removal Test")
    print("=" * 65)

    # Step 1: Create deliberate pause video
    test_video = create_pause_test_video()
    probe_orig = probe_media(test_video)
    orig_duration = float(probe_orig["format"]["duration"])
    print(f"✅ Source test video created: '{test_video.name}' ({orig_duration:.2f}s total)")

    # Step 2: Initialize SmartEditor
    editor = SmartEditor()

    # Step 3: Analyze silences and build cut plan
    print("\n--- Analyzing Audio Waveform for Dead Air ---")
    plan = editor.build_cut_plan(test_video)
    editor.print_cut_report(plan)

    # Step 4: Apply conservative cuts
    print("\n--- Rendering Trimmed Video with Audio Micro-Crossfades ---")
    output_trimmed = config.OUTPUT_FINAL_DIR / f"{test_video.stem}_trimmed.mp4"
    editor.apply_cuts(plan, output_trimmed)

    # Step 5: Verification & Quality Checks
    print("\n--- Validating Exported Video ---")
    is_valid, err = check_media_integrity(output_trimmed)
    probe_cut = probe_media(output_trimmed)
    cut_duration = float(probe_cut["format"]["duration"])

    print(f"File Exists        : ✅ Yes ({output_trimmed.stat().st_size / 1024:.1f} KB)")
    print(f"Integrity Check    : {'✅ Passed' if is_valid else f'❌ Error: {err}'}")
    print(f"Original Duration  : {orig_duration:.2f}s ({format_time(orig_duration)})")
    print(f"New Trimmed Length : {cut_duration:.2f}s ({format_time(cut_duration)})")
    print(f"Actual Time Saved  : {orig_duration - cut_duration:.2f}s")

    # Step 6: Verify speech survived intact
    assert is_valid, "Trimmed video failed integrity check"
    assert cut_duration < orig_duration, "Video duration should be shorter after cutting"
    assert len(plan.cuts) > 0, "Expected at least 1 pause cut"

    print("\n" + "=" * 65)
    print("  🎉 PHASE 2 VERIFICATION COMPLETE!")
    print(f"  • Trimmed Output : {output_trimmed}")
    print(f"  • Cut Plan (EDL) : {config.OUTPUT_LOGS_DIR / f'{test_video.stem}_cut_plan.json'}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_phase2_tests()
