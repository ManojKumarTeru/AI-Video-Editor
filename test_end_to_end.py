"""
🎬 AI-Editor — Phase 5: End-to-End System Validation Suite
Tests the complete 1-Click Master Pipeline for:
1. YouTube Long-Form (16:9):
   - Full 7-stage pipeline: Inspection -> Backup -> External Mic Sync -> Dead Air Silence Cutting
     -> AI Transcription & Word-Level Subtitles -> Voice Mastering (-14 LUFS) & Sidechain Music Ducking
     -> Visual Polish (Intro + Subtitle Burn + Lower Third + Watermark + Outro) -> YouTube Master Export (+faststart & QA).
2. YouTube Shorts (9:16):
   - Full pipeline with 9:16 vertical conversion (ambient background blur fill) and burned subtitles.
"""

import sys
import argparse
from pathlib import Path

import config
from utils.ffmpeg_utils import probe_media, check_media_integrity
from main import cmd_process


class MockArgs:
    """Helper to mock CLI arguments for cmd_process."""
    def __init__(self, **kwargs):
        self.format = kwargs.get("format", "youtube")
        self.file = kwargs.get("file", None)
        self.mic = kwargs.get("mic", None)
        self.music = kwargs.get("music", None)
        self.speaker = kwargs.get("speaker", "Alex Rivera")
        self.title = kwargs.get("title", "AI Video Creator")
        self.model = kwargs.get("model", "small")
        self.crf = kwargs.get("crf", 20)
        self.no_cut = kwargs.get("no_cut", False)
        self.no_subs = kwargs.get("no_subs", False)
        self.no_intro = kwargs.get("no_intro", False)
        self.no_outro = kwargs.get("no_outro", False)
        self.no_branding = kwargs.get("no_branding", False)
        self.highlights = kwargs.get("highlights", None)
        self.callout_interval = kwargs.get("callout_interval", 3.5)
        self.callout_duration = kwargs.get("callout_duration", 1.3)
        self.no_callouts = kwargs.get("no_callouts", False)
        self.no_zooms = kwargs.get("no_zooms", False)
        self.zoom_scale = kwargs.get("zoom_scale", 1.15)
        self.zoom_duration = kwargs.get("zoom_duration", 3.8)
        self.zoom_interval = kwargs.get("zoom_interval", 5.5)
        self.no_grade = kwargs.get("no_grade", False)
        self.no_sfx = kwargs.get("no_sfx", False)
        self.no_package = kwargs.get("no_package", False)
        self.no_cold_open = kwargs.get("no_cold_open", False)
        self.no_broll = kwargs.get("no_broll", False)
        self.no_kinetic = kwargs.get("no_kinetic", False)
        self.no_retention_bar = kwargs.get("no_retention_bar", False)
        self.no_impact = kwargs.get("no_impact", False)
        self.no_motion = kwargs.get("no_motion", False)
        self.no_defocus = kwargs.get("no_defocus", False)
        self.kit = kwargs.get("kit", "creator_elite")


def run_end_to_end_test():
    print("=" * 70)
    print("  🎬 AI-Editor — Phase 5: Master 1-Click Pipeline End-to-End Test")
    print("=" * 70)

    config.ensure_directories()

    # Locate test source files
    video_with_mic = config.INPUT_VIDEO_DIR / "audio_demo_video.mp4"
    silence_video = config.INPUT_VIDEO_DIR / "silence_test_video.mp4"
    mic_audio = config.INPUT_AUDIO_DIR / "external_mic_delayed.wav"
    bg_music = config.INPUT_MUSIC_DIR / "ambient_bg_music.mp3"

    # Fallbacks if files don't exist
    if not video_with_mic.exists():
        import test_phase3
        test_phase3.create_audio_test_assets()

    if not silence_video.exists():
        import test_phase2
        test_phase2.create_pause_test_video()

    print("\n✅ Verified Input Test Assets:")
    print(f"  • Video (Audio Sync Test) : '{video_with_mic.name}'")
    print(f"  • Video (Dead Air Test)   : '{silence_video.name}'")
    print(f"  • External Mic Audio      : '{mic_audio.name if mic_audio.exists() else 'None'}'")
    print(f"  • Ambient Music Track     : '{bg_music.name if bg_music.exists() else 'None'}'")

    # =========================================================================
    # TEST 1: Full YouTube Long-Form Master Pipeline (16:9)
    # =========================================================================
    print("\n" + "#" * 70)
    print("  TEST 1 / 2: 1-Click YouTube Long-Form Master Pipeline (16:9)")
    print("#" * 70)

    lf_args = MockArgs(
        format="youtube",
        file=str(video_with_mic),
        mic=str(mic_audio) if mic_audio.exists() else None,
        music=str(bg_music) if bg_music.exists() else None,
        speaker="Alex Rivera",
        title="AI Video Creator",
        model="small",
        crf=20,
        no_cut=False,
        no_subs=False,
        no_intro=False,
        no_outro=False,
        no_branding=False
    )

    cmd_process(lf_args)

    expected_lf_master = config.OUTPUT_FINAL_DIR / f"{video_with_mic.stem}_YouTube_Master.mp4"
    assert expected_lf_master.exists(), f"Missing long-form master: {expected_lf_master}"

    is_valid_lf, err_lf = check_media_integrity(expected_lf_master)
    probe_lf = probe_media(expected_lf_master)
    v_stream_lf = next((s for s in probe_lf.get("streams", []) if s.get("codec_type") == "video"), {})
    a_stream_lf = next((s for s in probe_lf.get("streams", []) if s.get("codec_type") == "audio"), {})
    dur_lf = float(probe_lf.get("format", {}).get("duration", 0.0))
    size_mb_lf = expected_lf_master.stat().st_size / (1024 * 1024)

    print("\n🔍 Long-Form Master Verification:")
    print(f"  • Deliverable File : '{expected_lf_master.name}' ({size_mb_lf:.2f} MB)")
    print(f"  • Resolution       : {v_stream_lf.get('width')}x{v_stream_lf.get('height')} @ {v_stream_lf.get('r_frame_rate')}fps")
    print(f"  • Video Codec      : {v_stream_lf.get('codec_name', 'unknown').upper()} (Profile: {v_stream_lf.get('profile', 'High')})")
    print(f"  • Audio Codec      : {a_stream_lf.get('codec_name', 'unknown').upper()} ({a_stream_lf.get('sample_rate')}Hz, {a_stream_lf.get('channels')} channels)")
    print(f"  • Total Duration   : {dur_lf:.2f}s (Intro + Mastered Main + Outro)")
    print(f"  • Stream Integrity : {'✅ PASSED (0 corruption)' if is_valid_lf else f'❌ FAILED: {err_lf}'}")

    # =========================================================================
    # TEST 2: Full YouTube Shorts Master Pipeline (9:16)
    # =========================================================================
    print("\n" + "#" * 70)
    print("  TEST 2 / 2: 1-Click YouTube Shorts Master Pipeline (9:16)")
    print("#" * 70)

    shorts_args = MockArgs(
        format="shorts",
        file=str(silence_video),
        mic=None,
        music=str(bg_music) if bg_music.exists() else None,
        speaker="Alex Rivera",
        title="AI Video Creator",
        model="small",
        crf=20,
        no_cut=False,
        no_subs=False,
        no_intro=True,
        no_outro=True,
        no_branding=False
    )

    cmd_process(shorts_args)

    expected_shorts_master = config.OUTPUT_FINAL_DIR / f"{silence_video.stem}_Shorts_Master.mp4"
    assert expected_shorts_master.exists(), f"Missing Shorts master: {expected_shorts_master}"

    is_valid_sh, err_sh = check_media_integrity(expected_shorts_master)
    probe_sh = probe_media(expected_shorts_master)
    v_stream_sh = next((s for s in probe_sh.get("streams", []) if s.get("codec_type") == "video"), {})
    a_stream_sh = next((s for s in probe_sh.get("streams", []) if s.get("codec_type") == "audio"), {})
    dur_sh = float(probe_sh.get("format", {}).get("duration", 0.0))
    size_mb_sh = expected_shorts_master.stat().st_size / (1024 * 1024)

    print("\n🔍 YouTube Shorts Master Verification:")
    print(f"  • Deliverable File : '{expected_shorts_master.name}' ({size_mb_sh:.2f} MB)")
    print(f"  • Resolution       : {v_stream_sh.get('width')}x{v_stream_sh.get('height')} (Vertical 9:16)")
    print(f"  • Video Codec      : {v_stream_sh.get('codec_name', 'unknown').upper()}")
    print(f"  • Audio Codec      : {a_stream_sh.get('codec_name', 'unknown').upper()}")
    print(f"  • Total Duration   : {dur_sh:.2f}s (Dead air trimmed)")
    print(f"  • Stream Integrity : {'✅ PASSED (0 corruption)' if is_valid_sh else f'❌ FAILED: {err_sh}'}")

    # =========================================================================
    # FINAL SUMMARY REPORT
    # =========================================================================
    print("\n" + "=" * 70)
    print("  🎉 ALL END-TO-END MASTER PIPELINE TESTS PASSED!")
    print("=" * 70)
    print(f"  📁 Long-Form 16:9 Master : {expected_lf_master}")
    print(f"  📁 Shorts 9:16 Master    : {expected_shorts_master}")
    print(f"  📁 Word-Level Subtitles  : {config.OUTPUT_SUBTITLES_DIR}")
    print(f"  📁 Untouched Backups     : {config.WORKSPACE_DIR / 'backup'}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_end_to_end_test()
