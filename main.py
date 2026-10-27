"""
🎬 AI-Editor: Main CLI Entry Point & Master 1-Click Orchestrator
Local-first, AI-powered video editing pipeline for 20-60 min YouTube videos and Shorts.
"""

import sys
import argparse
from pathlib import Path

import config
from core.inspector import MediaInspector
from core.transcriber import Transcriber
from core.editor import SmartEditor
from core.audio import AudioPipeline
from core.visuals import VisualEngine, extract_highlight_callouts
from core.zooms import plan_zooms, ZoomInterval
from core.exporter import Exporter, ProductionReport
from utils.ffmpeg_utils import probe_media


def cmd_process(args):
    """
    Executes the complete 1-Click AI Video Editing Pipeline:
    1. Inspects raw input files
    2. Creates a safe backup of untouched originals
    3. Transcribes speech and formats word-level subtitles
    4. Removes dead air conservatively (preserves natural breathing)
    5. Syncs external microphone and masters audio to -14 LUFS with music ducking
    6. Applies styled captions, branding lower thirds, and intro/outro (or Shorts 9:16)
    7. Renders YouTube-optimized master MP4 with automated QA validation!
    """
    config.ensure_directories()
    from utils.graphics_generator import ensure_graphic_assets
    ensure_graphic_assets()
    print("=" * 65)
    print("  🎬 AI-Editor: Starting 1-Click Master Pipeline")
    print(f"  Format: {args.format.upper()} | Model: {args.model}")
    print("=" * 65)

    # --- STEP 1: Inspect Inputs ---
    inspector = MediaInspector()
    inputs = inspector.scan_all_inputs()

    if getattr(args, "file", None):
        raw_video = Path(args.file).resolve()
        if not raw_video.exists():
            print(f"❌ Specified video file not found: {raw_video}")
            return
        meta = inspector.inspect_file(raw_video, "video")
        orig_duration = meta.duration_seconds
    else:
        if not inputs["video"]:
            print("❌ No video files found in 'input/video/'.")
            print("Please place your raw video recordings into: input/video/")
            return
        raw_video = inputs["video"][0].path
        orig_duration = inputs["video"][0].duration_seconds

    ext_mic = Path(args.mic).resolve() if getattr(args, "mic", None) else (inputs["audio"][0].path if inputs["audio"] else None)
    bg_music = Path(args.music).resolve() if getattr(args, "music", None) else (inputs["music"][0].path if inputs["music"] else None)

    print(f"\n[1/7] 🔍 Selected Video: '{raw_video.name}' ({orig_duration:.1f}s)")
    if ext_mic:
        print(f"      🎙️ External Mic: '{ext_mic.name}'")
    if bg_music:
        print(f"      🎵 Background Music: '{bg_music.name}'")

    # --- STEP 1.5: Load Production Style & Sound Kit ---
    from core.kits import get_production_kit
    selected_kit = get_production_kit(getattr(args, "kit", "creator_elite"))
    print(f"      🎛️ Production Kit: {selected_kit.display_name}")

    # --- STEP 2: Backup Originals ---
    exporter = Exporter()
    backup_path = exporter.backup_originals()

    current_video = raw_video
    audio_pipe = AudioPipeline(config.AudioConfig(
        sfx_pop_volume=selected_kit.audio.pop_volume,
        sfx_flash_volume=getattr(selected_kit.audio, "flash_volume", 0.45),
        sfx_whoosh_volume=selected_kit.audio.whoosh_volume,
        sfx_thump_volume=selected_kit.audio.thump_volume
    ))

    # --- STEP 3: Auto-Synchronize External Microphone (if present) ---
    if ext_mic:
        print("\n[2/7] 🎙️ Auto-synchronizing external microphone with camera video...")
        synced_video = config.WORKSPACE_DIR / "temp" / f"{raw_video.stem}_synced_mic.mp4"
        audio_pipe.sync_external_audio(raw_video, ext_mic, synced_video)
        current_video = synced_video
    else:
        print("\n[2/7] 🎙️ Camera audio selected (no external mic provided).")

    # --- STEP 4: Conservative Silence Cutting ---
    time_saved = 0.0
    percent_saved = 0.0

    if not args.no_cut:
        print("\n[3/7] ✂️ Analyzing audio waveform for dead air...")
        editor = SmartEditor()
        cut_plan = editor.build_cut_plan(current_video)
        time_saved = cut_plan.time_saved
        percent_saved = cut_plan.percent_saved

        if len(cut_plan.cuts) > 0:
            trimmed_file = config.WORKSPACE_DIR / "temp" / f"{raw_video.stem}_trimmed.mp4"
            editor.apply_cuts(cut_plan, trimmed_file)
            current_video = trimmed_file
        else:
            print("  No dead air exceeded threshold. Keeping original pacing.")
    else:
        print("\n[3/7] ✂️ Silence cutting skipped by user flag.")

    # --- STEP 5: Transcribe Speech & Format Subtitles ---
    # Transcribing the cut timeline guarantees 100% frame-perfect subtitle alignment!
    print("\n[4/7] 📝 Transcribing speech with word-level timestamps...")
    trans_lang = getattr(args, "language", "te")
    trans_task = getattr(args, "task", "translate")
    trans_force = getattr(args, "force", False)
    transcriber = Transcriber(config.TranscriptionConfig(
        model_size=args.model,
        language=trans_lang,
        task=trans_task
    ))
    segments = transcriber.transcribe(current_video, force_recompute=trans_force)

    srt_path = config.OUTPUT_SUBTITLES_DIR / f"{raw_video.stem}.srt"
    ass_path = config.OUTPUT_SUBTITLES_DIR / f"{raw_video.stem}.ass"
    transcriber.export_srt(segments, srt_path)
    sub_cfg = config.SubtitleConfig(
        font_name=selected_kit.subtitles.font_name,
        font_size=selected_kit.subtitles.font_size,
        primary_color=selected_kit.subtitles.primary_color,
        secondary_color=selected_kit.subtitles.secondary_color,
        outline_width=selected_kit.subtitles.outline_width,
        shadow_width=selected_kit.subtitles.shadow_width,
        margin_bottom=selected_kit.subtitles.margin_bottom,
        background_box=selected_kit.subtitles.background_pill,
        kinetic_bounce_enabled=not getattr(args, "no_kinetic", False)
    )
    transcriber.export_ass(segments, ass_path, style_cfg=sub_cfg)

    # Extract right-side highlight callouts from speech segments if enabled
    callouts = []
    if not getattr(args, "no_callouts", False) and segments:
        custom_kw = [w.strip() for w in args.highlights.split(",")] if getattr(args, "highlights", None) else None
        callouts = extract_highlight_callouts(
            segments,
            custom_keywords=custom_kw,
            duration=getattr(args, "callout_duration", 1.3),
            min_interval=getattr(args, "callout_interval", 3.5),
            blackout_start=0.0,
            blackout_end=1.5
        )
        if callouts:
            callout_names = [f"'{c.text}' ({c.start_time}s)" for c in callouts]
            print(f"✨ Extracted {len(callouts)} right-side attention callout(s): {', '.join(callout_names)}")

    # Plan dynamic virtual multi-cam punch-in cuts from speech segments
    zoom_intervals = []
    if not getattr(args, "no_zooms", False) and segments:
        is_shorts = (args.format == "shorts")
        z_wide_dur = 1.8 if is_shorts else getattr(args, "zoom_interval", 4.0)
        z_zoom_dur = 3.0 if is_shorts else getattr(args, "zoom_duration", 3.8)
        z_blackout_start = 1.0 if is_shorts else 2.5
        z_blackout_end = 1.0 if is_shorts else 2.5

        zoom_intervals = plan_zooms(
            segments,
            total_duration=orig_duration,
            scale=getattr(args, "zoom_scale", 1.15),
            zoom_duration=z_zoom_dur,
            min_wide_duration=z_wide_dur,
            blackout_start=z_blackout_start,
            blackout_end=z_blackout_end
        )
        if zoom_intervals:
            print(f"🎬 Directed {len(zoom_intervals)} semantic attention punch-in shot(s):")
            for z in zoom_intervals:
                print(f"   🎥 [{z.start_time:.2f}s - {z.end_time:.2f}s]: {z.reason}")

    # Detect spoken analogies & visual metaphor B-roll cards
    broll_overlays = []
    if not getattr(args, "no_broll", False) and segments:
        from core.broll import detect_metaphor_overlays
        broll_overlays = detect_metaphor_overlays(
            segments,
            duration=2.2,
            min_interval=6.5,
            blackout_start=0.0,
            blackout_end=7.5
        )
        if broll_overlays:
            broll_names = [f"'{b.title}' ({b.start_time}s)" for b in broll_overlays]
            print(f"🖼️ Scheduled {len(broll_overlays)} visual metaphor cutaway(s): {', '.join(broll_names)}")

    # Select Cold Open hook teaser quote
    cold_open_clip = None
    if not getattr(args, "no_cold_open", False) and segments and args.format != "shorts":
        from core.hooks import select_cold_open_clip
        cold_open_clip = select_cold_open_clip(segments, video_duration=orig_duration, target_duration=4.0)
        if cold_open_clip and cold_open_clip[1] > cold_open_clip[0]:
            print(f"🪝 Curated Cold Open Hook Teaser: {cold_open_clip[0]:.2f}s - {cold_open_clip[1]:.2f}s")

    # Prepare tactile micro-sound effect triggers (pops on badges, whooshes on camera zooms, thumps on key takeaways)
    sfx_events = []
    if not getattr(args, "no_sfx", False):
        for c in callouts:
            if not getattr(args, "no_impact", False) and getattr(c, "category", "") in ("TECH", "KEY"):
                sfx_events.append((c.start_time, "thump"))
            else:
                sfx_events.append((c.start_time, "pop"))
        for b in broll_overlays:
            sfx_events.append((b.start_time, "pop"))
        for z in zoom_intervals:
            # Camera Flash & Shutter hits right on the punch-in cut (18ms pre-roll for mirror flip)
            sfx_events.append((max(0.0, z.start_time - 0.018), "camera_flash"))
            # Smooth pull-back airy whoosh for zoom out
            sfx_events.append((max(0.0, z.end_time - 0.05), "whoosh_out"))
        sfx_events.sort(key=lambda x: x[0])

    # --- STEP 6: Audio Pipeline & Mastering ---
    print("\n[5/7] 🎚️ Mastering audio to -14 LUFS with vocal de-esser & micro-SFX...")
    mastered_audio_video = config.WORKSPACE_DIR / "temp" / f"{raw_video.stem}_mastered_audio.mp4"
    audio_pipe.process_video_audio(
        current_video,
        mastered_audio_video,
        external_audio=None,  # Already synced in step 3
        music_file=bg_music,
        sfx_events=sfx_events
    )
    current_video = mastered_audio_video

    # --- STEP 6: Visual Polish, Branding & Formatting ---
    print(f"\n[6/7] 🎨 Applying visual polish (format={args.format})...")
    visual_engine = VisualEngine(config.VisualsConfig(
        intro_enabled=(not args.no_intro and args.format != "shorts"),
        outro_enabled=(not args.no_outro and args.format != "shorts"),
        lower_third_enabled=not args.no_branding,
        speaker_name=args.speaker,
        speaker_title=args.title,
        watermark_enabled=not args.no_branding,
        callouts_enabled=not getattr(args, "no_callouts", False),
        callout_duration=getattr(args, "callout_duration", 1.3),
        callout_min_interval=getattr(args, "callout_interval", 3.5),
        zooms_enabled=not getattr(args, "no_zooms", False),
        zoom_scale=getattr(args, "zoom_scale", 1.15),
        zoom_duration=getattr(args, "zoom_duration", 3.8),
        zoom_min_interval=getattr(args, "zoom_interval", 5.5),
        color_grade_enabled=not getattr(args, "no_grade", False),
        grade_contrast=selected_kit.grading.contrast,
        grade_saturation=selected_kit.grading.saturation,
        grade_gamma=selected_kit.grading.gamma,
        grade_s_curve=selected_kit.grading.s_curve_str,
        grade_vignette=selected_kit.grading.vignette_angle,
        vignette_enabled=not getattr(args, "no_grade", False),
        retention_bar_enabled=getattr(args, "retention_bar", False),
        retention_bar_color=selected_kit.grading.retention_bar_color,
        kit_name=selected_kit.name,
        broll_enabled=not getattr(args, "no_broll", False),
        motion_graphics_enabled=not getattr(args, "no_motion", False),
        background_defocus_enabled=not getattr(args, "no_defocus", False),
        cold_open_enabled=not getattr(args, "no_cold_open", False),
        impact_enabled=not getattr(args, "no_impact", False)
    ))

    sub_to_burn = ass_path if not args.no_subs else None
    polished_video = config.WORKSPACE_DIR / "temp" / f"{raw_video.stem}_visual_assembled.mp4"

    if args.format == "shorts":
        # Shorts mode: Dynamic zooms + burn captions + branding + convert to 9:16
        branded_16x9 = config.WORKSPACE_DIR / "temp" / f"{raw_video.stem}_temp_branded.mp4"
        temp_zoomed = None
        source_vid = current_video
        if zoom_intervals and not getattr(args, "no_zooms", False):
            temp_zoomed = config.WORKSPACE_DIR / "temp" / f"{raw_video.stem}_temp_zoomed.mp4"
            visual_engine.apply_dynamic_zooms(current_video, temp_zoomed, zoom_intervals=zoom_intervals)
            source_vid = temp_zoomed

        if sub_to_burn:
            temp_sub = config.WORKSPACE_DIR / "temp" / f"{raw_video.stem}_subbed.mp4"
            visual_engine.burn_subtitles(source_vid, sub_to_burn, temp_sub)
            visual_engine.add_branding_overlays(temp_sub, branded_16x9, callouts=callouts, broll_overlays=broll_overlays)
            if temp_sub.exists():
                try:
                    temp_sub.unlink()
                except Exception:
                    pass
        else:
            visual_engine.add_branding_overlays(source_vid, branded_16x9, callouts=callouts, broll_overlays=broll_overlays)

        if temp_zoomed and temp_zoomed.exists():
            try:
                temp_zoomed.unlink()
            except Exception:
                pass
        visual_engine.convert_to_shorts_9_16(branded_16x9, polished_video, style="blur_fill")
    else:
        # Long-form mode: Assemble Cold Open -> Intro -> Main (Zooms + Subs + Overlays + B-roll) -> Outro
        visual_engine.assemble_full_package(
            current_video,
            polished_video,
            ass_subtitles=sub_to_burn,
            callouts=callouts,
            zoom_intervals=zoom_intervals,
            broll_overlays=broll_overlays,
            cold_open_clip=cold_open_clip
        )

    current_video = polished_video

    # --- STEP 7: Final YouTube Master Export & QA Validation ---
    print("\n[7/7] 📦 Encoding YouTube delivery master MP4 & validating QA...")
    suffix = "_Shorts_Master.mp4" if args.format == "shorts" else "_YouTube_Master.mp4"
    final_output_path = config.OUTPUT_FINAL_DIR / f"{raw_video.stem}{suffix}"

    exporter.render_youtube_optimized(
        current_video,
        final_output_path,
        crf=args.crf,
        preset="fast",
        is_shorts=(args.format == "shorts")
    )

    qa_passed, qa_issues = exporter.validate_export(final_output_path)
    probe_final = probe_media(final_output_path)
    v_st = next((s for s in probe_final.get("streams", []) if s.get("codec_type") == "video"), {})
    a_st = next((s for s in probe_final.get("streams", []) if s.get("codec_type") == "audio"), {})
    final_dur = float(probe_final.get("format", {}).get("duration", 0.0))
    file_size_mb = round(final_output_path.stat().st_size / (1024 * 1024), 2)

    report_fps = "30"
    for f_field in ["avg_frame_rate", "r_frame_rate"]:
        f_raw = str(v_st.get(f_field, "") or "")
        if "/" in f_raw:
            num, den = f_raw.split("/")
            if float(den) > 0:
                calc_f = round(float(num) / float(den), 2)
                if 12.0 <= calc_f <= 65.0:
                    report_fps = str(calc_f)
                    break

    # Generate upload-ready YouTube package (.txt) with chapters, titles & description
    metadata_pkg = None
    if not getattr(args, "no_package", False) and segments:
        metadata_pkg = exporter.generate_youtube_release_package(
            project_name=raw_video.stem,
            segments=segments,
            duration=final_dur,
            output_dir=config.OUTPUT_FINAL_DIR,
            callouts=callouts
        )

    # --- Executive Production Summary ---
    report = ProductionReport(
        project_name=raw_video.stem,
        export_format=args.format,
        original_duration=orig_duration,
        final_duration=final_dur,
        time_saved=time_saved,
        percent_saved=percent_saved,
        output_path=final_output_path,
        output_size_mb=file_size_mb,
        resolution=f"{v_st.get('width', 1920)}x{v_st.get('height', 1080)}",
        fps=report_fps,
        video_codec=str(v_st.get("codec_name") or "h264"),
        audio_codec=str(a_st.get("codec_name") or "aac"),
        subtitles_path=ass_path if not args.no_subs else None,
        backup_path=backup_path,
        callouts_count=len(callouts),
        zooms_count=len(zoom_intervals),
        metadata_path=metadata_pkg,
        qa_passed=qa_passed,
        qa_issues=qa_issues
    )
    exporter.print_production_report(report)


def cmd_inspect(args):
    """Inspect all media files in input directories."""
    print("\n🔍 Scanning input folders for media files...")
    inspector = MediaInspector()
    results = inspector.scan_all_inputs()
    inspector.print_report(results)


def cmd_transcribe(args):
    """Transcribe a specific media file or all files in input/video."""
    config.ensure_directories()
    trans_lang = getattr(args, "language", "te")
    trans_task = getattr(args, "task", "translate")
    transcriber = Transcriber(config.TranscriptionConfig(
        model_size=args.model,
        language=trans_lang,
        task=trans_task
    ))

    if args.file:
        target_files = [Path(args.file)]
    else:
        target_files = list(config.INPUT_VIDEO_DIR.glob("*.mp4")) + \
                       list(config.INPUT_VIDEO_DIR.glob("*.mov")) + \
                       list(config.INPUT_VIDEO_DIR.glob("*.mkv"))

    if not target_files:
        print("❌ No media files found to transcribe.")
        print(f"Please place video files into: {config.INPUT_VIDEO_DIR}")
        return

    print(f"\n🎙️ Starting transcription for {len(target_files)} file(s) using model '{args.model}'...")
    for f in target_files:
        print(f"\nProcessing '{f.name}'...")
        segments = transcriber.transcribe(f, force_recompute=args.force)
        
        # Export subtitles
        srt_path = config.OUTPUT_SUBTITLES_DIR / f"{f.stem}.srt"
        ass_path = config.OUTPUT_SUBTITLES_DIR / f"{f.stem}.ass"
        
        transcriber.export_srt(segments, srt_path)
        transcriber.export_ass(segments, ass_path)

    print("\n✅ All transcriptions completed!")
    print(f"Subtitles exported to: {config.OUTPUT_SUBTITLES_DIR}")


def cmd_edit(args):
    """Detect and conservatively cut silence from video files."""
    config.ensure_directories()
    editor = SmartEditor(config.EditingConfig(
        silence_threshold_db=args.threshold,
        min_silence_duration=args.min_pause
    ))

    if args.file:
        target_files = [Path(args.file)]
    else:
        target_files = [
            p for p in config.INPUT_VIDEO_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".mkv"}
        ]

    if not target_files:
        print("❌ No video files found to edit.")
        print(f"Please place video files into: {config.INPUT_VIDEO_DIR}")
        return

    for f in target_files:
        print(f"\nAnalyzing '{f.name}' for dead air...")
        plan = editor.build_cut_plan(f)
        editor.print_cut_report(plan)

        if not args.preview:
            out_file = config.OUTPUT_FINAL_DIR / f"{f.stem}_trimmed.mp4"
            editor.apply_cuts(plan, out_file)


def cmd_audio(args):
    """Master audio track, sync external mic, and mix background music with ducking."""
    config.ensure_directories()
    pipeline = AudioPipeline()

    if args.file:
        target_video = Path(args.file)
    else:
        videos = [
            p for p in config.INPUT_VIDEO_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".mkv"}
        ]
        if not videos:
            print("❌ No video files found in input/video/.")
            return
        target_video = videos[0]

    # Discover mic audio if any
    ext_audio = Path(args.mic) if args.mic else None
    if not ext_audio and config.INPUT_AUDIO_DIR.exists():
        audios = list(config.INPUT_AUDIO_DIR.glob("*.wav")) + list(config.INPUT_AUDIO_DIR.glob("*.mp3"))
        if audios:
            ext_audio = audios[0]

    # Discover music if any
    bg_music = Path(args.music) if args.music else None
    if not bg_music and config.INPUT_MUSIC_DIR.exists():
        tracks = list(config.INPUT_MUSIC_DIR.glob("*.mp3")) + list(config.INPUT_MUSIC_DIR.glob("*.wav"))
        if tracks:
            bg_music = tracks[0]

    out_video = config.OUTPUT_FINAL_DIR / f"{target_video.stem}_mastered_audio.mp4"
    pipeline.process_video_audio(target_video, out_video, external_audio=ext_audio, music_file=bg_music)


def cmd_polish(args):
    """Burn subtitles, add branding lower thirds/watermark, attention callouts, and attach intro/outro."""
    config.ensure_directories()
    from core.kits import get_production_kit
    selected_kit = get_production_kit(getattr(args, "kit", "creator_elite"))

    engine = VisualEngine(config.VisualsConfig(
        intro_enabled=not args.no_intro,
        outro_enabled=not args.no_outro,
        lower_third_enabled=not args.no_branding,
        speaker_name=args.speaker,
        speaker_title=args.title,
        watermark_enabled=not args.no_branding,
        callouts_enabled=not getattr(args, "no_callouts", False),
        callout_duration=getattr(args, "callout_duration", 1.3),
        callout_min_interval=getattr(args, "callout_interval", 3.5),
        zooms_enabled=not getattr(args, "no_zooms", False),
        zoom_scale=getattr(args, "zoom_scale", 1.15),
        zoom_duration=getattr(args, "zoom_duration", 3.8),
        zoom_min_interval=getattr(args, "zoom_interval", 5.5),
        color_grade_enabled=not getattr(args, "no_grade", False),
        grade_contrast=selected_kit.grading.contrast,
        grade_saturation=selected_kit.grading.saturation,
        grade_gamma=selected_kit.grading.gamma,
        grade_s_curve=selected_kit.grading.s_curve_str,
        grade_vignette=selected_kit.grading.vignette_angle,
        vignette_enabled=not getattr(args, "no_grade", False),
        retention_bar_enabled=getattr(args, "retention_bar", False),
        retention_bar_color=selected_kit.grading.retention_bar_color,
        kit_name=selected_kit.name,
        broll_enabled=not getattr(args, "no_broll", False),
        motion_graphics_enabled=not getattr(args, "no_motion", False),
        background_defocus_enabled=not getattr(args, "no_defocus", False),
        cold_open_enabled=not getattr(args, "no_cold_open", False)
    ))

    target_video = Path(args.file) if args.file else None
    if not target_video:
        videos = list(config.OUTPUT_FINAL_DIR.glob("*.mp4")) or list(config.INPUT_VIDEO_DIR.glob("*.mp4"))
        if not videos:
            print("❌ No video files found.")
            return
        target_video = videos[0]

    sub_file = Path(args.subtitles) if args.subtitles else None
    if not sub_file:
        ass_files = list(config.OUTPUT_SUBTITLES_DIR.glob("*.ass"))
        if ass_files:
            sub_file = ass_files[0]

    callouts = []
    zoom_intervals = []
    broll_overlays = []
    cold_open_clip = None

    cache_files = list((config.WORKSPACE_DIR / "cache").glob("*.json"))
    if cache_files:
        import json
        from core.transcriber import SubtitleSegment, WordTimestamp
        try:
            with open(cache_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                seg_list = [
                    SubtitleSegment(
                        start=s["start"], end=s["end"], text=s["text"],
                        words=[WordTimestamp(**w) for w in s.get("words", [])]
                    )
                    for s in data
                ]
                if not getattr(args, "no_callouts", False):
                    custom_kw = [w.strip() for w in args.highlights.split(",")] if getattr(args, "highlights", None) else None
                    callouts = extract_highlight_callouts(
                        seg_list,
                        custom_keywords=custom_kw,
                        duration=getattr(args, "callout_duration", 1.3),
                        min_interval=getattr(args, "callout_interval", 3.5),
                        blackout_start=0.0,
                        blackout_end=1.5
                    )
                    if callouts:
                        print(f"✨ Extracted {len(callouts)} right-side attention callout(s)")
                if not getattr(args, "no_zooms", False):
                    v_dur = float(probe_media(target_video).get("format", {}).get("duration", 60.0))
                    zoom_intervals = plan_zooms(
                        seg_list,
                        total_duration=v_dur,
                        scale=getattr(args, "zoom_scale", 1.15),
                        zoom_duration=getattr(args, "zoom_duration", 3.8),
                        min_wide_duration=getattr(args, "zoom_interval", 5.5)
                    )
                    if zoom_intervals:
                        print(f"🎬 Directed {len(zoom_intervals)} virtual multi-cam punch-in shot(s)")
                if not getattr(args, "no_broll", False):
                    from core.broll import detect_metaphor_overlays
                    broll_overlays = detect_metaphor_overlays(seg_list)
                    if broll_overlays:
                        print(f"🖼️ Scheduled {len(broll_overlays)} visual metaphor cutaway(s)")
                if not getattr(args, "no_cold_open", False):
                    from core.hooks import select_cold_open_clip
                    v_dur = float(probe_media(target_video).get("format", {}).get("duration", 60.0))
                    cold_open_clip = select_cold_open_clip(seg_list, video_duration=v_dur)
        except Exception:
            pass

    out_file = config.OUTPUT_FINAL_DIR / f"{target_video.stem}_fully_polished.mp4"
    engine.assemble_full_package(
        target_video,
        out_file,
        ass_subtitles=sub_file,
        callouts=callouts,
        zoom_intervals=zoom_intervals,
        broll_overlays=broll_overlays,
        cold_open_clip=cold_open_clip
    )


def cmd_shorts(args):
    """Convert 16:9 video into YouTube Shorts 9:16 vertical format."""
    config.ensure_directories()
    engine = VisualEngine()

    target_video = Path(args.file) if args.file else None
    if not target_video:
        videos = list(config.OUTPUT_FINAL_DIR.glob("*.mp4")) or list(config.INPUT_VIDEO_DIR.glob("*.mp4"))
        if not videos:
            print("❌ No video files found.")
            return
        target_video = videos[0]

    out_file = config.OUTPUT_FINAL_DIR / f"{target_video.stem}_shorts_9x16.mp4"
    engine.convert_to_shorts_9_16(target_video, out_file, style=args.style)


def cmd_test(args):
    """Run validation test suites."""
    if args.phase == 1:
        import test_phase1
        test_phase1.run_phase1_tests()
    elif args.phase == 2:
        import test_phase2
        test_phase2.run_phase2_tests()
    elif args.phase == 3:
        import test_phase3
        test_phase3.run_phase3_tests()
    elif args.phase == 4:
        import test_phase4
        test_phase4.run_phase4_tests()
    elif args.phase == 5:
        import test_end_to_end
        test_end_to_end.run_end_to_end_test()
    else:
        import test_phase1, test_phase2, test_phase3, test_phase4, test_end_to_end
        test_phase1.run_phase1_tests()
        test_phase2.run_phase2_tests()
        test_phase3.run_phase3_tests()
        test_phase4.run_phase4_tests()
        test_end_to_end.run_end_to_end_test()


def cmd_doctor(args):
    """Run environment and hardware health check."""
    import check_environment
    check_environment.check_python()
    check_environment.check_hardware()
    check_environment.check_ffmpeg()
    check_environment.test_pip_and_ai_packages()


def main():
    parser = argparse.ArgumentParser(
        description="🎬 AI-Editor: Local AI-Powered Video Editing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: process (1-Click Pipeline)
    p_process = subparsers.add_parser("process", help="Run 1-Click Master Editing Pipeline")
    p_process.add_argument("--file", "-f", type=str, default=None, help="Specific raw video file (defaults to first in input/video/)")
    p_process.add_argument("--mic", "-a", type=str, default=None, help="External microphone audio file")
    p_process.add_argument("--music", "-m", type=str, default=None, help="Background music audio file")
    p_process.add_argument("--format", default="youtube", choices=["youtube", "shorts"], help="Output format: youtube (16:9) or shorts (9:16)")
    p_process.add_argument("--speaker", default="Content Creator", help="Speaker name for lower third")
    p_process.add_argument("--title", default="Video Host", help="Speaker title for lower third")
    p_process.add_argument("--model", default="large-v3-turbo", choices=["tiny", "base", "small", "medium", "large-v3-turbo", "large-v3"], help="Whisper model size (default: large-v3-turbo)")
    p_process.add_argument("--language", "-l", default="te", help="Input speech language (default: te for Telugu, en for English, auto for auto-detect)")
    p_process.add_argument("--task", default="translate", choices=["translate", "transcribe"], help="Subtitle task: translate to English script or transcribe")
    p_process.add_argument("--force", action="store_true", help="Force recomputation of transcription, bypassing cache")
    p_process.add_argument("--crf", type=int, default=18, help="Quality factor (default: 18, visually lossless)")
    p_process.add_argument("--no-cut", action="store_true", help="Skip dead-air removal")
    p_process.add_argument("--no-subs", action="store_true", help="Skip caption burning")
    p_process.add_argument("--no-intro", action="store_true", help="Skip intro sequence")
    p_process.add_argument("--no-outro", action="store_true", help="Skip outro sequence")
    p_process.add_argument("--no-branding", action="store_true", help="Skip lower thirds & watermark")
    p_process.add_argument("--highlights", default=None, help="Comma-separated custom keywords to display as right-side attention callouts")
    p_process.add_argument("--callout-interval", type=float, default=3.5, help="Minimum seconds between attention callout badges (default: 3.5)")
    p_process.add_argument("--callout-duration", type=float, default=1.3, help="Duration in seconds each callout badge stays on screen (default: 1.3)")
    p_process.add_argument("--no-callouts", action="store_true", help="Disable right-side attention callout badges")
    p_process.add_argument("--no-zooms", action="store_true", help="Disable dynamic virtual multi-cam punch-in zoom cuts")
    p_process.add_argument("--zoom-scale", type=float, default=1.15, help="Punch-in zoom scale factor (default: 1.15)")
    p_process.add_argument("--zoom-duration", type=float, default=3.8, help="Hold duration for punch-in close-ups in seconds (default: 3.8)")
    p_process.add_argument("--zoom-interval", type=float, default=5.5, help="Minimum wide shot duration between zooms in seconds (default: 5.5)")
    p_process.add_argument("--no-grade", action="store_true", help="Disable studio cinematic color grading & vignette")
    p_process.add_argument("--no-sfx", action="store_true", help="Disable tactile micro-sound effects (pops & whooshes)")
    p_process.add_argument("--no-package", action="store_true", help="Skip generating YouTube upload release package")
    p_process.add_argument("--no-cold-open", action="store_true", help="Disable cold open hook teaser")
    p_process.add_argument("--no-broll", action="store_true", help="Disable auto B-roll visual metaphor cutaway cards")
    p_process.add_argument("--no-kinetic", action="store_true", help="Disable kinetic word-by-word spring bounce subtitles")
    p_process.add_argument("--retention-bar", action="store_true", help="Enable top retention progress bar (disabled by default)")
    p_process.add_argument("--no-impact", action="store_true", help="Disable sub-bass impact thumps on key takeaways")
    p_process.add_argument("--no-motion", action="store_true", help="Disable 5+ YOE animated motion graphics (fallback to static cards)")
    p_process.add_argument("--no-defocus", action="store_true", help="Disable cinematic background lens blur during active graphics")
    p_process.add_argument("--kit", default="creator_elite", choices=["creator_elite", "neon_cyber", "minimal_studio"], help="Production style & sound kit preset")
    p_process.set_defaults(func=cmd_process)

    # Command: inspect
    p_inspect = subparsers.add_parser("inspect", help="Scan and inspect all media files in input/")
    p_inspect.set_defaults(func=cmd_inspect)

    # Command: transcribe
    p_transcribe = subparsers.add_parser("transcribe", help="Transcribe speech and generate SRT/ASS subtitles")
    p_transcribe.add_argument("--file", "-f", type=str, default=None, help="Path to specific video/audio file")
    p_transcribe.add_argument("--model", "-m", type=str, default="large-v3-turbo", choices=["tiny", "base", "small", "medium", "large-v3-turbo", "large-v3"], help="Whisper model size")
    p_transcribe.add_argument("--language", "-l", default="te", help="Input speech language (default: te for Telugu)")
    p_transcribe.add_argument("--task", default="translate", choices=["translate", "transcribe"], help="Subtitle task: translate to English script or transcribe")
    p_transcribe.add_argument("--force", action="store_true", help="Force recomputation bypassing cache")
    p_transcribe.set_defaults(func=cmd_transcribe)

    # Command: edit
    p_edit = subparsers.add_parser("edit", help="Remove dead air conservatively with pro padding")
    p_edit.add_argument("--file", "-f", type=str, default=None, help="Specific video to edit")
    p_edit.add_argument("--threshold", "-t", type=float, default=-38.0, help="Silence threshold in dB (default: -38.0)")
    p_edit.add_argument("--min-pause", "-p", type=float, default=0.8, help="Min pause duration to cut in seconds (default: 0.8)")
    p_edit.add_argument("--preview", action="store_true", help="Only preview the cut plan without rendering")
    p_edit.set_defaults(func=cmd_edit)

    # Command: audio
    p_audio = subparsers.add_parser("audio", help="Master audio track, sync external mic, and mix background music with ducking")
    p_audio.add_argument("--file", "-f", type=str, default=None, help="Video file to process")
    p_audio.add_argument("--mic", "-a", type=str, default=None, help="External microphone audio file")
    p_audio.add_argument("--music", "-m", type=str, default=None, help="Background music audio file")
    p_audio.set_defaults(func=cmd_audio)

    # Command: polish
    p_polish = subparsers.add_parser("polish", help="Burn subtitles, add branding overlays, and attach intro/outro")
    p_polish.add_argument("--file", "-f", type=str, default=None, help="Video file to polish")
    p_polish.add_argument("--subtitles", "-s", type=str, default=None, help="ASS subtitle file to burn")
    p_polish.add_argument("--speaker", default="Content Creator", help="Speaker name for lower third")
    p_polish.add_argument("--title", default="Video Host", help="Speaker title for lower third")
    p_polish.add_argument("--no-intro", action="store_true", help="Disable intro sequence")
    p_polish.add_argument("--no-outro", action="store_true", help="Disable outro sequence")
    p_polish.add_argument("--no-branding", action="store_true", help="Disable lower third branding")
    p_polish.add_argument("--highlights", default=None, help="Comma-separated custom keywords for right-side callout badges")
    p_polish.add_argument("--callout-interval", type=float, default=3.5, help="Minimum seconds between attention callouts (default: 3.5)")
    p_polish.add_argument("--callout-duration", type=float, default=1.3, help="Duration in seconds each callout stays on screen (default: 1.3)")
    p_polish.add_argument("--no-callouts", action="store_true", help="Disable right-side attention callouts")
    p_polish.add_argument("--no-zooms", action="store_true", help="Disable virtual multi-cam zoom cuts")
    p_polish.add_argument("--zoom-scale", type=float, default=1.15, help="Punch-in zoom scale factor (default: 1.15)")
    p_polish.add_argument("--zoom-duration", type=float, default=3.8, help="Hold duration for punch-in close-ups in seconds (default: 3.8)")
    p_polish.add_argument("--zoom-interval", type=float, default=5.5, help="Minimum wide shot duration between zooms in seconds (default: 5.5)")
    p_polish.add_argument("--no-grade", action="store_true", help="Disable studio cinematic color grading & vignette")
    p_polish.add_argument("--no-sfx", action="store_true", help="Disable tactile micro-sound effects (pops & whooshes)")
    p_polish.add_argument("--no-package", action="store_true", help="Skip generating YouTube release package")
    p_polish.add_argument("--no-cold-open", action="store_true", help="Disable cold open hook teaser")
    p_polish.add_argument("--no-broll", action="store_true", help="Disable auto B-roll visual metaphor cutaway cards")
    p_polish.add_argument("--no-kinetic", action="store_true", help="Disable kinetic word-by-word spring bounce subtitles")
    p_polish.add_argument("--retention-bar", action="store_true", help="Enable top retention progress bar (disabled by default)")
    p_polish.add_argument("--no-impact", action="store_true", help="Disable sub-bass impact thumps on key takeaways")
    p_polish.add_argument("--no-motion", action="store_true", help="Disable 5+ YOE animated motion graphics (fallback to static cards)")
    p_polish.add_argument("--no-defocus", action="store_true", help="Disable cinematic background lens blur during active graphics")
    p_polish.add_argument("--kit", default="creator_elite", choices=["creator_elite", "neon_cyber", "minimal_studio"], help="Production style & sound kit preset")
    p_polish.set_defaults(func=cmd_polish)

    # Command: shorts
    p_shorts = subparsers.add_parser("shorts", help="Convert 16:9 video into 9:16 vertical YouTube Shorts format")
    p_shorts.add_argument("--file", "-f", type=str, default=None, help="Video file to convert")
    p_shorts.add_argument("--style", default="blur_fill", choices=["blur_fill", "center_crop"], help="Vertical framing style")
    p_shorts.set_defaults(func=cmd_shorts)

    # Command: test
    p_test = subparsers.add_parser("test", help="Run validation tests")
    p_test.add_argument("--phase", type=int, default=5, choices=[1, 2, 3, 4, 5], help="Which phase test suite to run (default: 5)")
    p_test.set_defaults(func=cmd_test)

    # Command: doctor
    p_doctor = subparsers.add_parser("doctor", help="Check system environment, FFmpeg, and dependencies")
    p_doctor.set_defaults(func=cmd_doctor)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
