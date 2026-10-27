"""
Procedural High-Retention B-Roll Graphic Asset Generator for AI-Editor.
Generates broadcast-grade visual metaphor cards (Blueprint House, Web Browser, Mobile App, Cloud DB, Neural AI, Code Terminal).
100% offline, local-first. Uses PIL/Pillow if available, with robust pure-Python/FFmpeg fallbacks.
"""

import os
import shutil
import struct
import subprocess
import zlib
from pathlib import Path
from typing import Tuple, Dict

import config

ARTIFACT_GRAPHICS_DIR = Path(r"C:\Users\LENOVO T480\.gemini\antigravity-ide\brain\b3102ea1-db82-4ad6-a03b-b9b517cb163a")
ARTIFACT_MAP = {
    "blueprint_house": ARTIFACT_GRAPHICS_DIR / "blueprint_house_1792984115950.jpg",
    "browser_website": ARTIFACT_GRAPHICS_DIR / "browser_website_1792984139636.jpg",
    "mobile_app": ARTIFACT_GRAPHICS_DIR / "mobile_app_1792984168506.jpg",
    "cloud_database": ARTIFACT_GRAPHICS_DIR / "cloud_database_1792984189760.jpg",
    "neural_brain": ARTIFACT_GRAPHICS_DIR / "neural_brain_1792984212524.jpg",
    "code_terminal": ARTIFACT_GRAPHICS_DIR / "code_terminal_1792984240941.jpg",
}

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    """Draws a smooth rounded rectangle on a PIL ImageDraw context."""
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    else:
        draw.rectangle(xy, fill=fill, outline=outline, width=width)


def _get_font(size: int, bold: bool = False, mono: bool = False):
    """Loads a high-quality scalable TrueType font with graceful multi-tier fallbacks."""
    if not HAS_PIL:
        return None
    if mono:
        candidates = ["consola.ttf", "consolab.ttf", "cour.ttf", "courbd.ttf"]
    elif bold:
        candidates = ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "tahomabd.ttf"]
    else:
        candidates = ["segoeui.ttf", "arial.ttf", "calibri.ttf", "tahoma.ttf"]

    for fname in candidates:
        try:
            return ImageFont.truetype(fname, size)
        except Exception:
            try:
                win_path = Path("C:/Windows/Fonts") / fname
                if win_path.exists():
                    return ImageFont.truetype(str(win_path), size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def create_broll_card_pil(
    output_path: Path,
    title: str,
    subtitle: str,
    accent_hex: str,
    card_type: str,
    width: int = 520,
    height: int = 320
) -> Path:
    """Generates a sleek glassmorphic B-roll metaphor card using PIL with 3D drop shadow and crisp typography."""
    # Convert hex to RGB
    hex_clean = accent_hex.lstrip("#").replace("0x", "")
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    accent_rgb = (r, g, b)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 0. Smooth Ambient Drop Shadow for 3D floating glass depth
    for offset, alpha in [(6, 16), (4, 32), (2, 55)]:
        _draw_rounded_rect(
            draw,
            [6 - offset, 6 - offset, width - 6 + offset, height - 6 + offset],
            radius=16 + offset,
            fill=(0, 0, 0, alpha)
        )

    # 1. Frosted Glass Container with dark slate fill & subtle glow border
    bg_color = (15, 23, 42, 240)  # Dark slate with 94% opacity
    border_color = (r, g, b, 210)
    _draw_rounded_rect(draw, [6, 6, width - 6, height - 6], radius=16, fill=bg_color, outline=border_color, width=2)

    # 2. Glowing Top Accent Strip
    draw.rectangle([18, 6, width - 18, 10], fill=accent_rgb + (255,))

    font_badge = _get_font(12, bold=True)
    font_title = _get_font(21, bold=True)

    # 3. Card Header Tag (pill badge)
    tag_bg = (r, g, b, 45)
    _draw_rounded_rect(draw, [24, 20, 190, 48], radius=7, fill=tag_bg, outline=accent_rgb + (180,), width=1)
    draw.text((34, 26), f"● {subtitle.upper()}", fill=accent_rgb + (255,), font=font_badge)

    # 4. Main Card Title
    draw.text((24, 58), title.upper(), fill=(255, 255, 255, 255), font=font_title)

    # Subtle horizontal divider
    draw.line([(24, 92), (width - 24, 92)], fill=(51, 65, 85, 140), width=1)

    # 5. Type-Specific Procedural Vector Graphic in lower area
    icon_box = [24, 100, width - 24, height - 20]
    _draw_card_graphic(draw, card_type, icon_box, accent_rgb)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


def _draw_card_graphic(draw, card_type: str, box: list, accent_rgb: Tuple[int, int, int]):
    """Draws custom rich procedural vector illustration inside the card graphic box."""
    x1, y1, x2, y2 = box
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    acc_fill = accent_rgb + (255,)
    acc_soft = accent_rgb + (180,)
    dim_fill = (148, 163, 184, 210)  # Slate 400
    dark_glass = (15, 23, 42, 220)

    font_xs = _get_font(10, bold=True)
    font_sm = _get_font(11, bold=True)
    font_med = _get_font(15, bold=True)
    font_mono = _get_font(12, mono=True)

    if card_type == "blueprint_house":
        # 1. Blueprint Architecture: Precision CAD blueprint with dimension lines & truss structure
        # Fine technical coordinate grid
        for gx in range(x1 + 15, x2 - 15, 24):
            draw.line([(gx, y1 + 5), (gx, y2 - 5)], fill=(30, 41, 59, 140), width=1)
        for gy in range(y1 + 5, y2 - 5, 20):
            draw.line([(x1 + 15, gy), (x2 - 15, gy)], fill=(30, 41, 59, 140), width=1)

        # House foundation slab & walls
        draw.rectangle([cx - 100, cy + 65, cx + 100, cy + 74], fill=dim_fill, outline=acc_fill, width=1)
        draw.rectangle([cx - 90, cy - 15, cx + 90, cy + 65], outline=acc_fill, fill=dark_glass, width=2)

        # Roof truss & apex with rafters
        draw.polygon([(cx - 108, cy - 15), (cx, cy - 78), (cx + 108, cy - 15)], outline=acc_fill, fill=(15, 23, 42, 130), width=2)
        draw.line([(cx, cy - 78), (cx, cy - 15)], fill=acc_soft, width=1)
        draw.line([(cx - 54, cy - 46), (cx, cy - 15)], fill=(30, 41, 59, 200), width=1)
        draw.line([(cx + 54, cy - 46), (cx, cy - 15)], fill=(30, 41, 59, 200), width=1)

        # Architectural Windows & Door
        draw.rectangle([cx - 22, cy + 18, cx + 22, cy + 65], outline=acc_fill, fill=(30, 41, 59, 240), width=1)
        draw.ellipse([cx + 12, cy + 42, cx + 16, cy + 46], fill=acc_fill)  # Doorknob
        draw.rectangle([cx - 72, cy - 2, cx - 38, cy + 30], outline=dim_fill, width=1)
        draw.line([(cx - 55, cy - 2), (cx - 55, cy + 30)], fill=dim_fill, width=1)
        draw.line([(cx - 72, cy + 14), (cx - 38, cy + 14)], fill=dim_fill, width=1)
        draw.rectangle([cx + 38, cy - 2, cx + 72, cy + 30], outline=dim_fill, width=1)
        draw.line([(cx + 55, cy - 2), (cx + 55, cy + 30)], fill=dim_fill, width=1)
        draw.line([(cx + 38, cy + 14), (cx + 72, cy + 14)], fill=dim_fill, width=1)

        # CAD Dimension Markers with arrows
        draw.line([(cx - 90, cy + 82), (cx + 90, cy + 82)], fill=acc_fill, width=1)
        draw.line([(cx - 90, cy + 78), (cx - 90, cy + 86)], fill=acc_fill, width=2)
        draw.line([(cx + 90, cy + 78), (cx + 90, cy + 86)], fill=acc_fill, width=2)
        draw.text((cx - 36, cy + 86), "14.8m SPAN", fill=acc_soft, font=font_sm)

    elif card_type == "browser_website":
        # 2. Modern Web Platform: Glassmorphic browser with status pills, sidebar, and dashboard chart
        _draw_rounded_rect(draw, [x1 + 6, y1 + 4, x2 - 6, y2 - 6], radius=10, fill=dark_glass, outline=dim_fill, width=1)
        # Chrome header bar
        draw.rectangle([x1 + 6, y1 + 4, x2 - 6, y1 + 32], fill=(30, 41, 59, 230))
        # Traffic light buttons (glowing)
        draw.ellipse([x1 + 18, y1 + 14, x1 + 28, y1 + 24], fill=(239, 68, 68, 255))
        draw.ellipse([x1 + 34, y1 + 14, x1 + 44, y1 + 24], fill=(245, 158, 11, 255))
        draw.ellipse([x1 + 50, y1 + 14, x1 + 60, y1 + 24], fill=(16, 185, 129, 255))
        # SSL URL Bar with green status dot
        _draw_rounded_rect(draw, [x1 + 75, y1 + 10, x2 - 95, y1 + 28], radius=6, fill=(15, 23, 42, 255), outline=None)
        draw.ellipse([x1 + 84, y1 + 16, x1 + 90, y1 + 22], fill=(16, 185, 129, 255))
        draw.text((x1 + 96, y1 + 12), "https://production-app.io/v2", fill=acc_fill, font=_get_font(11))
        # Ping pill badge
        _draw_rounded_rect(draw, [x2 - 85, y1 + 10, x2 - 16, y1 + 28], radius=4, fill=(16, 185, 129, 40), outline=(16, 185, 129, 180), width=1)
        draw.text((x2 - 76, y1 + 12), "24ms", fill=(16, 185, 129, 255), font=font_sm)

        # Dashboard layout: Left sidebar + Metric Cards + Vector Chart
        draw.rectangle([x1 + 14, y1 + 40, x1 + 60, y2 - 14], fill=(30, 41, 59, 180))
        _draw_rounded_rect(draw, [x1 + 22, y1 + 48, x1 + 52, y1 + 56], radius=3, fill=acc_fill, outline=None)
        _draw_rounded_rect(draw, [x1 + 22, y1 + 66, x1 + 52, y1 + 72], radius=3, fill=dim_fill, outline=None)
        _draw_rounded_rect(draw, [x1 + 22, y1 + 82, x1 + 52, y1 + 88], radius=3, fill=dim_fill, outline=None)

        # Main chart & stat card
        _draw_rounded_rect(draw, [x1 + 72, y1 + 40, x2 - 14, y2 - 14], radius=6, fill=(15, 23, 42, 190), outline=dim_fill, width=1)
        # Vector line chart showing strong upward momentum
        chart_pts = [
            (x1 + 86, cy + 42), (x1 + 125, cy + 28), (x1 + 165, cy + 34),
            (x1 + 205, cy + 8), (x1 + 245, cy + 14), (x2 - 28, cy - 20)
        ]
        for idx in range(len(chart_pts) - 1):
            draw.line([chart_pts[idx], chart_pts[idx + 1]], fill=acc_fill, width=2)
            draw.ellipse([chart_pts[idx][0] - 3, chart_pts[idx][1] - 3, chart_pts[idx][0] + 3, chart_pts[idx][1] + 3], fill=acc_fill)
        draw.ellipse([chart_pts[-1][0] - 4, chart_pts[-1][1] - 4, chart_pts[-1][0] + 4, chart_pts[-1][1] + 4], fill=(255, 255, 255, 255), outline=acc_fill, width=2)

    elif card_type == "mobile_app":
        # 3. Mobile Ecosystem: AMOLED curved smartphone chassis with dynamic island & metric widgets
        phone_w, phone_h = 135, 180
        px1 = cx - phone_w // 2
        py1 = cy - phone_h // 2
        px2 = cx + phone_w // 2
        py2 = cy + phone_h // 2
        # Smartphone chassis with dual-layer border
        _draw_rounded_rect(draw, [px1, py1, px2, py2], radius=20, fill=(10, 15, 28, 245), outline=acc_fill, width=2)
        # Dynamic Island pill
        _draw_rounded_rect(draw, [cx - 20, py1 + 6, cx + 20, py1 + 17], radius=5, fill=(0, 0, 0, 255), outline=None)
        # Status indicators (WiFi & Battery)
        draw.line([(px1 + 16, py1 + 12), (px1 + 24, py1 + 12)], fill=dim_fill, width=1)
        draw.rectangle([px2 - 28, py1 + 9, px2 - 16, py1 + 15], outline=dim_fill, width=1)

        # Screen UI Widget 1: Revenue / Performance card
        _draw_rounded_rect(draw, [px1 + 10, py1 + 26, px2 - 10, py1 + 72], radius=8, fill=acc_fill, outline=None)
        draw.text((px1 + 18, py1 + 32), "PERFORMANCE", fill=(15, 23, 42, 220), font=font_xs)
        draw.text((px1 + 18, py1 + 46), "+94.6%", fill=(15, 23, 42, 255), font=font_med)

        # Screen UI Widget 2: Activity metric pills
        _draw_rounded_rect(draw, [px1 + 10, py1 + 80, px2 - 10, py1 + 118], radius=8, fill=(30, 41, 59, 210), outline=dim_fill, width=1)
        draw.text((px1 + 18, py1 + 88), "ACTIVE USERS", fill=acc_soft, font=font_xs)
        draw.text((px1 + 18, py1 + 100), "128,400", fill=(255, 255, 255, 255), font=font_med)

        # Screen UI Widget 3: Action bar
        _draw_rounded_rect(draw, [px1 + 10, py1 + 126, px2 - 10, py1 + 150], radius=8, fill=(30, 41, 59, 180), outline=None)
        # Bottom home indicator
        draw.line([(cx - 24, py2 - 8), (cx + 24, py2 - 8)], fill=dim_fill, width=2)

    elif card_type == "cloud_database":
        # 4. Cloud Infrastructure: Metallic stacked cylinder array with glowing network fiber nodes
        db_w, db_h = 160, 36
        dx1 = cx - db_w // 2
        dx2 = cx + db_w // 2
        # Stacked database cylinders with metallic bevel
        for idx, dy in enumerate([cy - 44, cy + 2, cy + 48]):
            is_top = (idx == 0)
            draw.ellipse([dx1, dy, dx2, dy + db_h], outline=acc_fill if is_top else dim_fill, fill=(15, 23, 42, 230), width=2)
            draw.line([(dx1, dy + db_h // 2), (dx1, dy + db_h)], fill=acc_fill if is_top else dim_fill, width=2)
            draw.line([(dx2, dy + db_h // 2), (dx2, dy + db_h)], fill=acc_fill if is_top else dim_fill, width=2)
            # Glowing server activity LEDs
            led_col = acc_fill if idx == 0 else (16, 185, 129, 255)
            draw.ellipse([dx2 - 32, dy + db_h // 2 - 4, dx2 - 24, dy + db_h // 2 + 4], fill=led_col)
            draw.ellipse([dx2 - 18, dy + db_h // 2 - 4, dx2 - 10, dy + db_h // 2 + 4], fill=(255, 255, 255, 200))

        # Cloud sync node line with upward data pulses
        draw.line([(cx, y1 + 10), (cx, cy - 44)], fill=acc_fill, width=2)
        draw.ellipse([cx - 8, y1 + 4, cx + 8, y1 + 20], fill=dark_glass, outline=acc_fill, width=2)
        draw.polygon([(cx, y1 + 8), (cx - 4, y1 + 15), (cx + 4, y1 + 15)], fill=acc_fill)
        # Uptime pill
        _draw_rounded_rect(draw, [cx - 50, y2 - 22, cx + 50, y2 - 4], radius=4, fill=(16, 185, 129, 40), outline=(16, 185, 129, 180), width=1)
        draw.text((cx - 44, y2 - 20), "99.99% UPTIME", fill=(16, 185, 129, 255), font=font_sm)

    elif card_type == "neural_brain":
        # 5. Neural AI Engine: Multi-layer synaptic network with glowing vector connections & pulse nodes
        layers = [
            [(x1 + 60, cy - 54), (x1 + 60, cy), (x1 + 60, cy + 54)],
            [(cx - 42, cy - 68), (cx - 42, cy - 22), (cx - 42, cy + 22), (cx - 42, cy + 68)],
            [(cx + 42, cy - 68), (cx + 42, cy - 22), (cx + 42, cy + 22), (cx + 42, cy + 68)],
            [(x2 - 60, cy - 36), (x2 - 60, cy + 36)]
        ]
        # Synaptic connection lines with layered alpha glow
        for l1 in layers[0]:
            for l2 in layers[1]:
                draw.line([l1, l2], fill=accent_rgb + (65,), width=1)
        for l2 in layers[1]:
            for l3 in layers[2]:
                draw.line([l2, l3], fill=accent_rgb + (85,), width=1)
        for l3 in layers[2]:
            for l4 in layers[3]:
                draw.line([l3, l4], fill=accent_rgb + (95,), width=1)

        # Synaptic Nodes with halo borders
        for l_idx, lyr in enumerate(layers):
            is_accent_layer = (l_idx in (1, 2))
            for pt in lyr:
                node_halo = acc_fill if is_accent_layer else (255, 255, 255, 230)
                draw.ellipse([pt[0] - 8, pt[1] - 8, pt[0] + 8, pt[1] + 8], fill=(15, 23, 42, 255), outline=node_halo, width=2)
                draw.ellipse([pt[0] - 3, pt[1] - 3, pt[0] + 3, pt[1] + 3], fill=node_halo)

        # Neural Tensor equation tag at bottom
        _draw_rounded_rect(draw, [cx - 60, y2 - 22, cx + 60, y2 - 4], radius=4, fill=(15, 23, 42, 200), outline=acc_soft, width=1)
        draw.text((cx - 48, y2 - 19), "y = σ(W·x + b)", fill=acc_fill, font=_get_font(12, bold=True))

    else:
        # 6. Software Development Engine: macOS-style code terminal with syntax color highlighting
        _draw_rounded_rect(draw, [x1 + 6, y1 + 4, x2 - 6, y2 - 6], radius=10, fill=(10, 14, 23, 245), outline=acc_fill, width=1)
        # Window title bar with dots
        draw.rectangle([x1 + 6, y1 + 4, x2 - 6, y1 + 30], fill=(22, 29, 47, 240))
        draw.ellipse([x1 + 18, y1 + 13, x1 + 26, y1 + 21], fill=(239, 68, 68, 255))
        draw.ellipse([x1 + 32, y1 + 13, x1 + 40, y1 + 21], fill=(245, 158, 11, 255))
        draw.ellipse([x1 + 46, y1 + 13, x1 + 54, y1 + 21], fill=(16, 185, 129, 255))
        draw.text((x1 + 68, y1 + 10), "core/engine.py — bash (80x24)", fill=dim_fill, font=_get_font(11, mono=True))

        # Code syntax lines with line numbers
        code_lines = [
            ("01", "import", " torch, numpy as np", (245, 158, 11, 255), (255, 255, 255, 230)),
            ("02", "def", " build_pipeline(data):", acc_fill, (255, 255, 255, 240)),
            ("03", "    model =", " load_whisper('int8')", (148, 163, 184, 255), (16, 185, 129, 255)),
            ("04", "    return", " model.optimize()", acc_fill, (255, 255, 255, 240)),
            ("05", ">>>", " [STATUS: PRODUCTION READY]", (16, 185, 129, 255), (16, 185, 129, 255)),
        ]
        curr_y = y1 + 42
        for line_num, kw_txt, rest_txt, kw_col, rest_col in code_lines:
            draw.text((x1 + 18, curr_y), line_num, fill=(71, 85, 105, 255), font=font_mono)
            draw.text((x1 + 46, curr_y), kw_txt, fill=kw_col, font=font_mono)
            kw_w = len(kw_txt) * 7 + 6
            draw.text((x1 + 46 + kw_w, curr_y), rest_txt, fill=rest_col, font=font_mono)
            curr_y += 24
        # Blinking cursor block
        draw.rectangle([x1 + 48, curr_y + 2, x1 + 56, curr_y + 16], fill=acc_fill)


def create_pure_png_fallback(output_path: Path, width: int = 520, height: int = 320) -> Path:
    """
    Guaranteed pure-Python fallback using standard library zlib & struct.
    Generates a dark slate glass card PNG without needing PIL or FFmpeg.
    """
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)  # Filter byte None
        for x in range(width):
            # Border test (outer 3px)
            is_border = (x < 3 or x >= width - 3 or y < 3 or y >= height - 3 or y == 8)
            if is_border:
                raw_data.extend([0, 240, 255, 220])  # Cyan border
            else:
                raw_data.extend([15, 23, 42, 230])   # Dark slate glass

    compressed = zlib.compress(bytes(raw_data), level=6)

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        return length + chunk_type + data + crc

    png_bytes = bytearray(b"\x89PNG\r\n\x1a\n")
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png_bytes.extend(make_chunk(b"IHDR", ihdr_data))
    png_bytes.extend(make_chunk(b"IDAT", compressed))
    png_bytes.extend(make_chunk(b"IEND", b""))

    with open(output_path, "wb") as f:
        f.write(png_bytes)
    return output_path


def ensure_graphic_assets(force: bool = False) -> Dict[str, Path]:
    """
    Generates and verifies all 6 high-retention metaphor graphic cards in assets/graphics/.
    Returns a dictionary mapping card keys to their generated file paths.
    """
    graphics_dir = getattr(config, "GRAPHICS_DIR", config.ASSETS_DIR / "graphics")
    graphics_dir.mkdir(parents=True, exist_ok=True)

    cards_manifest = {
        "blueprint_house": {
            "title": "System Architecture",
            "subtitle": "Metaphor",
            "accent": "0x00F0FF",
            "filename": "blueprint_house.png"
        },
        "browser_website": {
            "title": "Web Application",
            "subtitle": "Platform",
            "accent": "0xC084FC",
            "filename": "browser_website.png"
        },
        "mobile_app": {
            "title": "Mobile Ecosystem",
            "subtitle": "Interface",
            "accent": "0x00FF9D",
            "filename": "mobile_app.png"
        },
        "cloud_database": {
            "title": "Cloud Infrastructure",
            "subtitle": "Data Layer",
            "accent": "0x00F0FF",
            "filename": "cloud_database.png"
        },
        "neural_brain": {
            "title": "Neural Intelligence",
            "subtitle": "AI Core",
            "accent": "0xFFD700",
            "filename": "neural_brain.png"
        },
        "code_terminal": {
            "title": "Software Engine",
            "subtitle": "Development",
            "accent": "0x00FF9D",
            "filename": "code_terminal.png"
        }
    }

    generated_paths: Dict[str, Path] = {}

    # Clean up corrupted/empty <= 1024-byte .mov files in animated/
    anim_dir = getattr(config, "ANIMATED_GRAPHICS_DIR", config.ASSETS_DIR / "graphics" / "animated")
    if anim_dir.exists():
        for mov_f in anim_dir.glob("*.mov"):
            try:
                if mov_f.stat().st_size <= 1024:
                    mov_f.unlink()
            except Exception:
                pass

    for key, info in cards_manifest.items():
        target_path = graphics_dir / info["filename"]
        # Replace if forcing, missing, or if it is the old 1356-byte rectangle box
        if force or not target_path.exists() or target_path.stat().st_size <= 2048:
            deployed = False
            src_art = ARTIFACT_MAP.get(key)

            # 1. First priority: Deploy broadcast-tier 4K master illustration from artifacts
            if src_art and src_art.exists() and src_art.stat().st_size > 10000:
                # High-res 1280x720 PNG conversion via FFmpeg
                try:
                    res = subprocess.run(
                        ["ffmpeg", "-y", "-i", str(src_art), "-vf", "scale=1280:720", str(target_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=15
                    )
                    if res.returncode == 0 and target_path.exists() and target_path.stat().st_size > 2048:
                        deployed = True
                except Exception:
                    pass

                # PIL fallback
                if not deployed and HAS_PIL:
                    try:
                        with Image.open(src_art) as im:
                            im.convert("RGBA").resize((1280, 720), Image.Resampling.LANCZOS).save(str(target_path), "PNG")
                            deployed = True
                    except Exception:
                        pass

                # Direct copy fallback (FFmpeg natively decodes JPEGs under any extension)
                if not deployed:
                    try:
                        shutil.copyfile(src_art, target_path)
                        deployed = True
                    except Exception:
                        pass

            # 2. Second priority: Procedural card if source art not found
            if not deployed:
                if HAS_PIL:
                    try:
                        create_broll_card_pil(
                            target_path,
                            title=info["title"],
                            subtitle=info["subtitle"],
                            accent_hex=info["accent"],
                            card_type=key
                        )
                    except Exception:
                        create_pure_png_fallback(target_path)
                else:
                    create_pure_png_fallback(target_path)

        generated_paths[key] = target_path

    return generated_paths


# Auto-deploy broadcast art on module import so all 6 assets are instantly active
try:
    ensure_graphic_assets()
except Exception:
    pass

