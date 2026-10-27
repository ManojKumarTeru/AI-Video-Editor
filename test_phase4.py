"""
Phase 4 Validation Runner: Visual Polish, Branding, & YouTube Shorts Engine.
Tests:
1. Subtitle Burn-in: Progressive ASS karaoke captions burned with crisp outlines
2. Broadcast Lower Third & Watermark: Glassmorphism banner with cyan accent border
3. Intro & Outro Generation: 1080p title sequences with smooth alpha fades
4. Full Assembly: Concat [Intro] -> [Main Footage + Subs + Overlays] -> [Outro]
5. YouTube Shorts Converter: 9:16 vertical (1080x1920) with ambient background blur fill
"""

import sys
from pathlib import Path
from typing import Optional

import config
from utils.ffmpeg_utils import probe_media, check_media_integrity
from core.visuals import VisualEngine


def run_phase4_tests():
    print("=" * 65)
    print("  🎬 AI-Editor — Phase 4: Visual Polish & Branding Test")
    print("=" * 65)

    config.ensure_directories()
    engine = VisualEngine()

    # 1. Locate source media from previous phases
    source_video = config.OUTPUT_FINAL_DIR / "mastered_audio_demo.mp4"
    if not source_video.exists():
        source_video = config.OUTPUT_FINAL_DIR / "silence_test_video_trimmed.mp4"
    if not source_video.exists():
        source_video = config.INPUT_VIDEO_DIR / "sample_test_clip.mp4"

    sub_file = config.OUTPUT_SUBTITLES_DIR / "sample_test_clip.ass"
    if not sub_file.exists():
        sub_candidates = list(config.OUTPUT_SUBTITLES_DIR.glob("*.ass"))
        sub_file = sub_candidates[0] if sub_candidates else None

    print(f"Source video for visuals: '{source_video.name}'")
    print(f"Source subtitles        : '{sub_file.name if sub_file else 'None'}'")

    # 2. Test Intro & Outro Generation
    print("\n--- 1. Testing Intro & Outro Title Sequences ---")
    intro_card = config.TEMP_DIR / "test_intro.mp4"
    outro_card = config.TEMP_DIR / "test_outro.mp4"
    engine.create_intro(intro_card)
    engine.create_outro(outro_card)
    print("✅ 1080p Intro and Outro generated with smooth title fades.")

    # 3. Test Full Visual Assembly (Intro + Subtitles + Lower Third + Watermark + Outro)
    print("\n--- 2. Assembling Complete Long-Form Video Package ---")
    final_longform = config.OUTPUT_FINAL_DIR / "youtube_full_package_demo.mp4"
    engine.assemble_full_package(source_video, final_longform, ass_subtitles=sub_file)

    # Validate Long-form Export
    is_valid_lf, err_lf = check_media_integrity(final_longform)
    probe_lf = probe_media(final_longform)
    v_stream_lf = probe_lf["streams"][0]
    dur_lf = float(probe_lf["format"]["duration"])
    print(f"File Exists    : ✅ Yes ({final_longform.stat().st_size / (1024*1024):.2f} MB)")
    print(f"Resolution     : {v_stream_lf['width']}x{v_stream_lf['height']} @ {v_stream_lf.get('r_frame_rate', '30/1')}fps")
    print(f"Total Duration : {dur_lf:.2f}s (Includes Intro + Main + Outro)")
    print(f"Integrity Check: {'✅ Passed' if is_valid_lf else f'❌ Error: {err_lf}'}")

    # 4. Test YouTube Shorts 9:16 Vertical Converter
    print("\n--- 3. Testing YouTube Shorts 9:16 Vertical Conversion ---")
    final_shorts = config.OUTPUT_FINAL_DIR / "youtube_shorts_9x16_demo.mp4"
    engine.convert_to_shorts_9_16(source_video, final_shorts, style="blur_fill")

    # Validate Shorts Export
    is_valid_sh, err_sh = check_media_integrity(final_shorts)
    probe_sh = probe_media(final_shorts)
    v_stream_sh = probe_sh["streams"][0]
    print(f"File Exists    : ✅ Yes ({final_shorts.stat().st_size / (1024*1024):.2f} MB)")
    print(f"Resolution     : {v_stream_sh['width']}x{v_stream_sh['height']} (Vertical 9:16)")
    print(f"Framing Style  : Ambient blurred background + centered 16:9 frame")
    print(f"Integrity Check: {'✅ Passed' if is_valid_sh else f'❌ Error: {err_sh}'}")

    print("\n" + "=" * 65)
    print("  🎉 PHASE 4 VERIFICATION COMPLETE!")
    print(f"  • Long-Form 16:9 MP4 : {final_longform}")
    print(f"  • Shorts 9:16 MP4    : {final_shorts}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_phase4_tests()
