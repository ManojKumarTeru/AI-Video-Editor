"""
Kinetic 5+ YOE Motion Graphics Engine for AI-Editor.
Generates broadcast-grade procedural animated motion graphics (Vox, Johnny Harris, Ali Abdaal tier).
Features:
- Damped harmonic spring physics (overshoot bounce on entry, floating breathing drift, velocity slide exit)
- Live procedural micro-animations (stroke-drawing charts, live typewriter terminal, traveling synaptic pulses)
- 45° specular light sheen sweep across frosted glass
- 100% offline, local-first QuickTime PNG transparent video (.mov) alpha compilation.
"""

import math
import struct
import subprocess
from pathlib import Path
from typing import Tuple, Dict, List, Optional

import config
from utils.graphics_generator import _get_font, _draw_rounded_rect

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def spring_overshoot_scale(p: float, entry_duration: float = 0.22) -> float:
    """
    Damped harmonic oscillator physics curve for natural Apple/After Effects spring pop.
    Scale starts at 0.78, peaks at 1.06 (overshoot), and settles smoothly to 1.00.
    """
    if p >= entry_duration:
        return 1.00
    t_norm = p / entry_duration
    # Damped sine wave: 1 - exp(-gamma * t) * cos(omega * t)
    gamma = 6.5
    omega = 14.0
    scale = 1.0 - math.exp(-gamma * t_norm) * math.cos(omega * t_norm)
    return max(0.70, min(1.08, 0.78 + scale * 0.22))


def breathing_drift_y(p: float, amplitude: float = 2.5, frequency: float = 1.6) -> float:
    """Subtle floating sine wave drift to keep graphics visually alive and breathing."""
    return amplitude * math.sin(2.0 * math.pi * frequency * p)


def exit_glide_alpha_y(p: float, exit_start: float = 0.88) -> Tuple[float, float]:
    """Smooth velocity acceleration downwards and alpha decay during card exit."""
    if p < exit_start:
        return 1.0, 0.0
    t_exit = (p - exit_start) / (1.0 - exit_start)
    # Quadratic acceleration downwards
    alpha = max(0.0, 1.0 - (t_exit ** 1.5))
    dy = (t_exit ** 2.0) * 24.0
    return alpha, dy


def draw_specular_sheen(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    p: float,
    sheen_start: float = 0.08,
    sheen_end: float = 0.42
):
    """
    Draws an angled 45-degree specular light sheen wipe across the glass container.
    Gives the visual asset an ultra-premium physical reflection seen in high-end 3D motion design.
    """
    if p < sheen_start or p > sheen_end:
        return
    progress = (p - sheen_start) / (sheen_end - sheen_start)
    sheen_x = int(-140 + progress * (width + 280))
    sheen_w = 48

    # Multi-pass soft gradient streak
    for i in range(sheen_w):
        frac = i / sheen_w
        # Bell curve alpha profile
        alpha = int(48.0 * math.sin(frac * math.pi))
        col = (255, 255, 255, alpha)
        x_top = sheen_x + i
        x_bottom = x_top - 65
        draw.line([(x_top, 8), (x_bottom, height - 8)], fill=col, width=1)


def draw_animated_broll_frame(
    card_type: str,
    title: str,
    subtitle: str,
    accent_rgb: Tuple[int, int, int],
    frame_idx: int,
    total_frames: int,
    width: int = 520,
    height: int = 320
) -> Image.Image:
    """
    Renders a single frame of the 5+ YOE motion graphic at normalized progress p in [0.0, 1.0].
    Applies spring physics, breathing hover drift, animated internal elements, and specular light wipe.
    """
    p = frame_idx / max(1, total_frames - 1)
    scale = spring_overshoot_scale(p, entry_duration=0.20)
    drift_y = breathing_drift_y(p)
    exit_alpha, exit_dy = exit_glide_alpha_y(p, exit_start=0.88)

    # Base high-res canvas
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # 1. 3D Floating Ambient Drop Shadow
    shadow_alpha_base = int(55 * exit_alpha)
    for offset, alpha_mult in [(6, 0.30), (4, 0.55), (2, 1.0)]:
        _draw_rounded_rect(
            draw,
            [6 - offset, 6 - offset, width - 6 + offset, height - 6 + offset],
            radius=16 + offset,
            fill=(0, 0, 0, int(shadow_alpha_base * alpha_mult))
        )

    # 2. Obsidian Frosted Glass Body & Glowing Border
    bg_alpha = int(242 * exit_alpha)
    bg_color = (15, 23, 42, bg_alpha)
    border_alpha = int(210 * exit_alpha)
    border_color = accent_rgb + (border_alpha,)
    _draw_rounded_rect(draw, [6, 6, width - 6, height - 6], radius=16, fill=bg_color, outline=border_color, width=2)

    # 3. Glowing Neon Top Accent Strip
    draw.rectangle([18, 6, width - 18, 10], fill=accent_rgb + (int(255 * exit_alpha),))

    # Fonts
    font_badge = _get_font(12, bold=True)
    font_title = _get_font(21, bold=True)
    font_sm = _get_font(11, bold=True)
    font_med = _get_font(15, bold=True)
    font_mono = _get_font(12, mono=True)
    font_xs = _get_font(10, bold=True)

    # 4. Header Pill Badge
    tag_bg = accent_rgb + (int(45 * exit_alpha),)
    _draw_rounded_rect(draw, [24, 20, 190, 48], radius=7, fill=tag_bg, outline=accent_rgb + (int(180 * exit_alpha),), width=1)
    draw.text((34, 26), f"● {subtitle.upper()}", fill=accent_rgb + (int(255 * exit_alpha),), font=font_badge)

    # 5. Card Title
    draw.text((24, 58), title.upper(), fill=(255, 255, 255, int(255 * exit_alpha)), font=font_title)

    # Subtle horizontal divider
    draw.line([(24, 92), (width - 24, 92)], fill=(51, 65, 85, int(140 * exit_alpha)), width=1)

    # 6. Type-Specific Live Animated Vector Graphic
    box = [24, 100, width - 24, height - 20]
    _draw_animated_vector(draw, card_type, box, accent_rgb, p, exit_alpha, font_sm, font_med, font_mono, font_xs)

    # 7. Specular 45° Light Sheen Wipe across glass
    draw_specular_sheen(draw, width, height, p)

    # 8. Apply kinetic spring scaling & drift displacement
    if abs(scale - 1.0) > 0.005 or abs(drift_y) > 0.1 or exit_dy > 0.1:
        eff_dy = int(drift_y + exit_dy)
        if scale != 1.0:
            sw = max(10, int(width * scale))
            sh = max(10, int(height * scale))
            scaled_img = canvas.resize((sw, sh), Image.Resampling.BICUBIC)
            final_canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            paste_x = (width - sw) // 2
            paste_y = (height - sh) // 2 + eff_dy
            final_canvas.paste(scaled_img, (paste_x, paste_y), scaled_img)
            return final_canvas
        elif eff_dy != 0:
            final_canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            final_canvas.paste(canvas, (0, eff_dy), canvas)
            return final_canvas

    return canvas


def _draw_animated_vector(
    draw: ImageDraw.ImageDraw,
    card_type: str,
    box: List[int],
    accent_rgb: Tuple[int, int, int],
    p: float,
    alpha_mul: float,
    font_sm,
    font_med,
    font_mono,
    font_xs
):
    """Renders frame-interpolated internal micro-animations for each metaphor card."""
    x1, y1, x2, y2 = box
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    acc_fill = accent_rgb + (int(255 * alpha_mul),)
    acc_soft = accent_rgb + (int(180 * alpha_mul),)
    dim_fill = (148, 163, 184, int(210 * alpha_mul))
    dark_glass = (15, 23, 42, int(220 * alpha_mul))

    if card_type == "blueprint_house":
        # 1. Blueprint Architecture CAD: coordinate grid + dynamic dimension snap
        grid_alpha = int(140 * min(1.0, p / 0.25) * alpha_mul)
        for gx in range(x1 + 15, x2 - 15, 24):
            draw.line([(gx, y1 + 5), (gx, y2 - 5)], fill=(30, 41, 59, grid_alpha), width=1)
        for gy in range(y1 + 5, y2 - 5, 20):
            draw.line([(x1 + 15, gy), (x2 - 15, gy)], fill=(30, 41, 59, grid_alpha), width=1)

        # House slab & walls
        draw.rectangle([cx - 100, cy + 65, cx + 100, cy + 74], fill=dim_fill, outline=acc_fill, width=1)
        draw.rectangle([cx - 90, cy - 15, cx + 90, cy + 65], outline=acc_fill, fill=dark_glass, width=2)

        # Roof truss rafters
        draw.polygon([(cx - 108, cy - 15), (cx, cy - 78), (cx + 108, cy - 15)], outline=acc_fill, fill=(15, 23, 42, int(130 * alpha_mul)), width=2)
        draw.line([(cx, cy - 78), (cx, cy - 15)], fill=acc_soft, width=1)
        draw.line([(cx - 54, cy - 46), (cx, cy - 15)], fill=(30, 41, 59, int(200 * alpha_mul)), width=1)
        draw.line([(cx + 54, cy - 46), (cx, cy - 15)], fill=(30, 41, 59, int(200 * alpha_mul)), width=1)

        # Architectural Windows & Door
        draw.rectangle([cx - 22, cy + 18, cx + 22, cy + 65], outline=acc_fill, fill=(30, 41, 59, int(240 * alpha_mul)), width=1)
        draw.ellipse([cx + 12, cy + 42, cx + 16, cy + 46], fill=acc_fill)
        draw.rectangle([cx - 72, cy - 2, cx - 38, cy + 30], outline=dim_fill, width=1)
        draw.line([(cx - 55, cy - 2), (cx - 55, cy + 30)], fill=dim_fill, width=1)
        draw.line([(cx - 72, cy + 14), (cx - 38, cy + 14)], fill=dim_fill, width=1)
        draw.rectangle([cx + 38, cy - 2, cx + 72, cy + 30], outline=dim_fill, width=1)
        draw.line([(cx + 55, cy - 2), (cx + 55, cy + 30)], fill=dim_fill, width=1)
        draw.line([(cx + 38, cy + 14), (cx + 72, cy + 14)], fill=dim_fill, width=1)

        # Dynamic dimension arrows expand into place
        dim_progress = min(1.0, max(0.0, (p - 0.15) / 0.35))
        curr_span = int(90 * dim_progress)
        draw.line([(cx - curr_span, cy + 82), (cx + curr_span, cy + 82)], fill=acc_fill, width=1)
        draw.line([(cx - curr_span, cy + 78), (cx - curr_span, cy + 86)], fill=acc_fill, width=2)
        draw.line([(cx + curr_span, cy + 78), (cx + curr_span, cy + 86)], fill=acc_fill, width=2)
        if dim_progress > 0.6:
            draw.text((cx - 36, cy + 86), "14.8m SPAN", fill=acc_soft, font=font_sm)

    elif card_type == "browser_website":
        # 2. Modern Web Platform: Draw-on Vector Line Chart + Live URL Ping
        _draw_rounded_rect(draw, [x1 + 6, y1 + 4, x2 - 6, y2 - 6], radius=10, fill=dark_glass, outline=dim_fill, width=1)
        draw.rectangle([x1 + 6, y1 + 4, x2 - 6, y1 + 32], fill=(30, 41, 59, int(230 * alpha_mul)))

        # Traffic light buttons with sequential fade
        draw.ellipse([x1 + 18, y1 + 14, x1 + 28, y1 + 24], fill=(239, 68, 68, int(255 * alpha_mul)))
        draw.ellipse([x1 + 34, y1 + 14, x1 + 44, y1 + 24], fill=(245, 158, 11, int(255 * alpha_mul)))
        draw.ellipse([x1 + 50, y1 + 14, x1 + 60, y1 + 24], fill=(16, 185, 129, int(255 * alpha_mul)))

        # URL Bar
        _draw_rounded_rect(draw, [x1 + 75, y1 + 10, x2 - 95, y1 + 28], radius=6, fill=(15, 23, 42, int(255 * alpha_mul)), outline=None)
        draw.ellipse([x1 + 84, y1 + 16, x1 + 90, y1 + 22], fill=(16, 185, 129, int(255 * alpha_mul)))
        draw.text((x1 + 96, y1 + 12), "https://production-app.io/v2", fill=acc_fill, font=font_xs)

        # Ping pill badge (pulsing green glow)
        ping_pulse = int(180 + 75 * math.sin(p * 12.0))
        _draw_rounded_rect(draw, [x2 - 85, y1 + 10, x2 - 16, y1 + 28], radius=4, fill=(16, 185, 129, int(40 * alpha_mul)), outline=(16, 185, 129, int(ping_pulse * alpha_mul)), width=1)
        draw.text((x2 - 76, y1 + 12), "24ms", fill=(16, 185, 129, int(255 * alpha_mul)), font=font_sm)

        # Left sidebar
        draw.rectangle([x1 + 14, y1 + 40, x1 + 60, y2 - 14], fill=(30, 41, 59, int(180 * alpha_mul)))
        _draw_rounded_rect(draw, [x1 + 22, y1 + 48, x1 + 52, y1 + 56], radius=3, fill=acc_fill, outline=None)
        _draw_rounded_rect(draw, [x1 + 22, y1 + 66, x1 + 52, y1 + 72], radius=3, fill=dim_fill, outline=None)
        _draw_rounded_rect(draw, [x1 + 22, y1 + 82, x1 + 52, y1 + 88], radius=3, fill=dim_fill, outline=None)

        # Main chart container
        _draw_rounded_rect(draw, [x1 + 72, y1 + 40, x2 - 14, y2 - 14], radius=6, fill=(15, 23, 42, int(190 * alpha_mul)), outline=dim_fill, width=1)

        # 5+ YOE Kinetic Stroke Draw-On Chart
        full_pts = [
            (x1 + 86, cy + 42), (x1 + 125, cy + 28), (x1 + 165, cy + 34),
            (x1 + 205, cy + 8), (x1 + 245, cy + 14), (x2 - 28, cy - 20)
        ]
        # Progress along chart path
        chart_p = min(1.0, max(0.0, (p - 0.10) / 0.50))
        num_segments = len(full_pts) - 1
        visible_segs = chart_p * num_segments

        for idx in range(num_segments):
            if visible_segs <= idx:
                break
            seg_frac = min(1.0, visible_segs - idx)
            pt_a = full_pts[idx]
            pt_b = full_pts[idx + 1]
            interp_x = int(pt_a[0] + (pt_b[0] - pt_a[0]) * seg_frac)
            interp_y = int(pt_a[1] + (pt_b[1] - pt_a[1]) * seg_frac)
            draw.line([pt_a, (interp_x, interp_y)], fill=acc_fill, width=2)
            draw.ellipse([pt_a[0] - 3, pt_a[1] - 3, pt_a[0] + 3, pt_a[1] + 3], fill=acc_fill)

            # Glowing Tracer Circle at head of line
            if seg_frac < 1.0 or idx == num_segments - 1:
                draw.ellipse([interp_x - 5, interp_y - 5, interp_x + 5, interp_y + 5], fill=(255, 255, 255, int(255 * alpha_mul)), outline=acc_fill, width=2)

    elif card_type == "mobile_app":
        # 3. Mobile Ecosystem: Dynamic Island Notch + Roll-Up Metrics
        phone_w, phone_h = 135, 180
        px1, py1 = cx - phone_w // 2, cy - phone_h // 2
        px2, py2 = cx + phone_w // 2, cy + phone_h // 2
        _draw_rounded_rect(draw, [px1, py1, px2, py2], radius=20, fill=(10, 15, 28, int(245 * alpha_mul)), outline=acc_fill, width=2)

        # Dynamic Island with animated expansion
        island_w = int(24 + 16 * min(1.0, p / 0.20))
        _draw_rounded_rect(draw, [cx - island_w, py1 + 6, cx + island_w, py1 + 17], radius=5, fill=(0, 0, 0, int(255 * alpha_mul)), outline=None)
        draw.line([(px1 + 16, py1 + 12), (px1 + 24, py1 + 12)], fill=dim_fill, width=1)
        draw.rectangle([px2 - 28, py1 + 9, px2 - 16, py1 + 15], outline=dim_fill, width=1)

        # Performance metric rolling up (+0% -> +94.6%)
        counter_p = min(1.0, max(0.0, (p - 0.12) / 0.45))
        perf_val = 94.6 * counter_p
        _draw_rounded_rect(draw, [px1 + 10, py1 + 26, px2 - 10, py1 + 72], radius=8, fill=acc_fill, outline=None)
        draw.text((px1 + 18, py1 + 32), "PERFORMANCE", fill=(15, 23, 42, int(220 * alpha_mul)), font=font_xs)
        draw.text((px1 + 18, py1 + 46), f"+{perf_val:.1f}%", fill=(15, 23, 42, int(255 * alpha_mul)), font=font_med)

        # Active users metric rolling up
        users_val = int(128400 * counter_p)
        _draw_rounded_rect(draw, [px1 + 10, py1 + 80, px2 - 10, py1 + 118], radius=8, fill=(30, 41, 59, int(210 * alpha_mul)), outline=dim_fill, width=1)
        draw.text((px1 + 18, py1 + 88), "ACTIVE USERS", fill=acc_soft, font=font_xs)
        draw.text((px1 + 18, py1 + 100), f"{users_val:,}", fill=(255, 255, 255, int(255 * alpha_mul)), font=font_med)

        _draw_rounded_rect(draw, [px1 + 10, py1 + 126, px2 - 10, py1 + 150], radius=8, fill=(30, 41, 59, int(180 * alpha_mul)), outline=None)
        draw.line([(cx - 24, py2 - 8), (cx + 24, py2 - 8)], fill=dim_fill, width=2)

    elif card_type == "cloud_database":
        # 4. Cloud Infrastructure: Stacked metallic cylinders + Ascending Data Packets
        db_w, db_h = 160, 36
        dx1, dx2 = cx - db_w // 2, cx + db_w // 2
        for idx, dy in enumerate([cy - 44, cy + 2, cy + 48]):
            is_top = (idx == 0)
            draw.ellipse([dx1, dy, dx2, dy + db_h], outline=acc_fill if is_top else dim_fill, fill=(15, 23, 42, int(230 * alpha_mul)), width=2)
            draw.line([(dx1, dy + db_h // 2), (dx1, dy + db_h)], fill=acc_fill if is_top else dim_fill, width=2)
            draw.line([(dx2, dy + db_h // 2), (dx2, dy + db_h)], fill=acc_fill if is_top else dim_fill, width=2)

            # Flashing LEDs (alternating at 3Hz)
            led_state = int((p * 10.0 + idx) % 2)
            led_col = acc_fill if led_state == 0 else (16, 185, 129, int(255 * alpha_mul))
            draw.ellipse([dx2 - 32, dy + db_h // 2 - 4, dx2 - 24, dy + db_h // 2 + 4], fill=led_col)
            draw.ellipse([dx2 - 18, dy + db_h // 2 - 4, dx2 - 10, dy + db_h // 2 + 4], fill=(255, 255, 255, int(200 * alpha_mul)))

        # Cloud upload conduit with ascending pulse particles
        draw.line([(cx, y1 + 10), (cx, cy - 44)], fill=acc_fill, width=2)
        draw.ellipse([cx - 8, y1 + 4, cx + 8, y1 + 20], fill=dark_glass, outline=acc_fill, width=2)
        draw.polygon([(cx, y1 + 8), (cx - 4, y1 + 15), (cx + 4, y1 + 15)], fill=acc_fill)

        # Ascending particle
        particle_y = int((cy - 44) - ((p * 3.0) % 1.0) * (cy - 44 - (y1 + 12)))
        draw.ellipse([cx - 3, particle_y - 3, cx + 3, particle_y + 3], fill=(255, 255, 255, int(255 * alpha_mul)))

        _draw_rounded_rect(draw, [cx - 50, y2 - 22, cx + 50, y2 - 4], radius=4, fill=(16, 185, 129, int(40 * alpha_mul)), outline=(16, 185, 129, int(180 * alpha_mul)), width=1)
        draw.text((cx - 44, y2 - 20), "99.99% UPTIME", fill=(16, 185, 129, int(255 * alpha_mul)), font=font_sm)

    elif card_type == "neural_brain":
        # 5. Neural AI Engine: Synaptic Nodes with Traveling Energy Pulses
        layers = [
            [(x1 + 60, cy - 54), (x1 + 60, cy), (x1 + 60, cy + 54)],
            [(cx - 42, cy - 68), (cx - 42, cy - 22), (cx - 42, cy + 22), (cx - 42, cy + 68)],
            [(cx + 42, cy - 68), (cx + 42, cy - 22), (cx + 42, cy + 22), (cx + 42, cy + 68)],
            [(x2 - 60, cy - 36), (x2 - 60, cy + 36)]
        ]

        # Synaptic pathways
        for l1 in layers[0]:
            for l2 in layers[1]:
                draw.line([l1, l2], fill=accent_rgb + (int(65 * alpha_mul),), width=1)
        for l2 in layers[1]:
            for l3 in layers[2]:
                draw.line([l2, l3], fill=accent_rgb + (int(85 * alpha_mul),), width=1)
        for l3 in layers[2]:
            for l4 in layers[3]:
                draw.line([l3, l4], fill=accent_rgb + (int(95 * alpha_mul),), width=1)

        # Traveling Synaptic Energy Pulses
        pulse_t = (p * 2.5) % 1.0
        # Energy moving layer 1 -> layer 2
        for l1 in layers[0]:
            l2 = layers[1][1]
            px = int(l1[0] + (l2[0] - l1[0]) * pulse_t)
            py = int(l1[1] + (l2[1] - l1[1]) * pulse_t)
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 255, 255, int(240 * alpha_mul)))

        # Breathing Nodes
        node_halo_scale = 1.0 + 0.15 * math.sin(p * 8.0)
        for l_idx, lyr in enumerate(layers):
            is_accent_layer = (l_idx in (1, 2))
            for pt in lyr:
                halo_r = int(8 * (node_halo_scale if is_accent_layer else 1.0))
                node_halo = acc_fill if is_accent_layer else (255, 255, 255, int(230 * alpha_mul))
                draw.ellipse([pt[0] - halo_r, pt[1] - halo_r, pt[0] + halo_r, pt[1] + halo_r], fill=(15, 23, 42, int(255 * alpha_mul)), outline=node_halo, width=2)
                draw.ellipse([pt[0] - 3, pt[1] - 3, pt[0] + 3, pt[1] + 3], fill=node_halo)

        _draw_rounded_rect(draw, [cx - 60, y2 - 22, cx + 60, y2 - 4], radius=4, fill=(15, 23, 42, int(200 * alpha_mul)), outline=acc_soft, width=1)
        draw.text((cx - 48, y2 - 19), "y = σ(W·x + b)", fill=acc_fill, font=font_mono)

    else:
        # 6. Software Development Engine: Live Typewriter Code Terminal with Blinking Cursor
        _draw_rounded_rect(draw, [x1 + 6, y1 + 4, x2 - 6, y2 - 6], radius=10, fill=(10, 14, 23, int(245 * alpha_mul)), outline=acc_fill, width=1)
        draw.rectangle([x1 + 6, y1 + 4, x2 - 6, y1 + 30], fill=(22, 29, 47, int(240 * alpha_mul)))
        draw.ellipse([x1 + 18, y1 + 13, x1 + 26, y1 + 21], fill=(239, 68, 68, int(255 * alpha_mul)))
        draw.ellipse([x1 + 32, y1 + 13, x1 + 40, y1 + 21], fill=(245, 158, 11, int(255 * alpha_mul)))
        draw.ellipse([x1 + 46, y1 + 13, x1 + 54, y1 + 21], fill=(16, 185, 129, int(255 * alpha_mul)))
        draw.text((x1 + 68, y1 + 10), "core/engine.py — bash (80x24)", fill=dim_fill, font=font_mono)

        code_lines = [
            ("01", "import", " torch, numpy as np", (245, 158, 11, int(255 * alpha_mul)), (255, 255, 255, int(230 * alpha_mul))),
            ("02", "def", " build_pipeline(data):", acc_fill, (255, 255, 255, int(240 * alpha_mul))),
            ("03", "    model =", " load_whisper('int8')", (148, 163, 184, int(255 * alpha_mul)), (16, 185, 129, int(255 * alpha_mul))),
            ("04", "    return", " model.optimize()", acc_fill, (255, 255, 255, int(240 * alpha_mul))),
            ("05", ">>>", " [STATUS: PRODUCTION READY]", (16, 185, 129, int(255 * alpha_mul)), (16, 185, 129, int(255 * alpha_mul))),
        ]

        # Progressive Typewriter effect across lines
        type_progress = min(1.0, max(0.0, (p - 0.08) / 0.55))
        active_line_float = type_progress * len(code_lines)
        curr_y = y1 + 42

        for l_idx, (line_num, kw_txt, rest_txt, kw_col, rest_col) in enumerate(code_lines):
            if active_line_float < l_idx:
                break
            line_completion = min(1.0, active_line_float - l_idx)
            draw.text((x1 + 18, curr_y), line_num, fill=(71, 85, 105, int(255 * alpha_mul)), font=font_mono)

            # Character typing slice
            full_line_text = kw_txt + rest_txt
            chars_to_show = int(len(full_line_text) * line_completion)
            kw_len = len(kw_txt)

            if chars_to_show <= kw_len:
                draw.text((x1 + 46, curr_y), kw_txt[:chars_to_show], fill=kw_col, font=font_mono)
                cx_cursor = x1 + 46 + len(kw_txt[:chars_to_show]) * 7
            else:
                draw.text((x1 + 46, curr_y), kw_txt, fill=kw_col, font=font_mono)
                rest_chars = chars_to_show - kw_len
                kw_w = kw_len * 7 + 6
                draw.text((x1 + 46 + kw_w, curr_y), rest_txt[:rest_chars], fill=rest_col, font=font_mono)
                cx_cursor = x1 + 46 + kw_w + rest_chars * 7

            # Blinking cursor block on active line
            is_active_typing_line = (int(active_line_float) == l_idx)
            blink_state = int(p * 5.0) % 2
            if is_active_typing_line and blink_state == 0:
                draw.rectangle([cx_cursor + 2, curr_y + 2, cx_cursor + 10, curr_y + 16], fill=acc_fill)

            curr_y += 24


def generate_animated_card_clip(
    card_type: str,
    title: str,
    subtitle: str,
    accent_hex: str,
    output_mov_path: Path,
    duration: float = 2.2,
    fps: int = 30,
    force: bool = False
) -> Path:
    """
    Renders 60fps/30fps procedural motion frames and encodes them into a transparent QuickTime MOV (png codec).
    100% offline, local-first. Produces frame-accurate alpha transparency for broadcast video compositing.
    """
    output_mov_path = Path(output_mov_path).resolve()
    if not HAS_PIL:
        return output_mov_path
    if not force and output_mov_path.exists() and output_mov_path.stat().st_size > 1024:
        return output_mov_path

    output_mov_path.parent.mkdir(parents=True, exist_ok=True)

    hex_clean = accent_hex.lstrip("#").replace("0x", "")
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    accent_rgb = (r, g, b)

    width, height = 520, 320
    total_frames = int(duration * fps)

    # Launch FFmpeg pipe to write transparent QuickTime PNG video stream directly
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgba",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "png",
        "-pix_fmt", "rgba",
        str(output_mov_path)
    ]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for f_idx in range(total_frames):
            frame_img = draw_animated_broll_frame(
                card_type=card_type,
                title=title,
                subtitle=subtitle,
                accent_rgb=accent_rgb,
                frame_idx=f_idx,
                total_frames=total_frames,
                width=width,
                height=height
            )
            raw_bytes = frame_img.tobytes("raw", "RGBA")
            if proc.stdin:
                proc.stdin.write(raw_bytes)

        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=25)
    except Exception:
        pass

    return output_mov_path


def ensure_animated_graphic_assets(force: bool = False) -> Dict[str, Path]:
    """
    Generates and caches all 6 animated 5+ YOE motion graphics in assets/graphics/animated/.
    Returns a dictionary mapping card keys to their generated transparent .mov file paths.
    """
    anim_dir = getattr(config, "ANIMATED_GRAPHICS_DIR", config.ASSETS_DIR / "graphics" / "animated")
    anim_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "blueprint_house": ("System Architecture", "Metaphor", "0x00F0FF", "anim_blueprint_house.mov"),
        "browser_website": ("Web Application", "Platform", "0xC084FC", "anim_browser_website.mov"),
        "mobile_app": ("Mobile Ecosystem", "Interface", "0x00FF9D", "anim_mobile_app.mov"),
        "cloud_database": ("Cloud Infrastructure", "Data Layer", "0x00F0FF", "anim_cloud_database.mov"),
        "neural_brain": ("Neural Intelligence", "AI Core", "0xFFD700", "anim_neural_brain.mov"),
        "code_terminal": ("Software Engine", "Development", "0x00FF9D", "anim_code_terminal.mov"),
    }

    results: Dict[str, Path] = {}
    for key, (title, subtitle, accent, filename) in manifest.items():
        mov_p = anim_dir / filename
        generate_animated_card_clip(
            card_type=key,
            title=title,
            subtitle=subtitle,
            accent_hex=accent,
            output_mov_path=mov_p,
            duration=2.2,
            fps=30,
            force=force
        )
        results[key] = mov_p

    return results
