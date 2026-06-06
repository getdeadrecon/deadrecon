#!/usr/bin/env python3
"""
Render the PhantomSignal wordmark avatar to PNG assets.

Outputs:
  docs/assets/phantomsignal-avatar.png              — dark background (docs/README)
  docs/assets/phantomsignal-avatar-transparent.png  — transparent background
  phantomsignal/web/static/img/phantom-ascii.png             — dark bg (UI)
  phantomsignal/web/static/img/phantom-ascii-transparent.png — transparent (UI)

Requirements:
  pip install Pillow pyfiglet

Usage:
  python scripts/render_avatar.py
"""

from pathlib import Path
import pyfiglet
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/hack/Hack-Regular.ttf"
FONT_SZ   = 13
LINE_H    = FONT_SZ + 2
PAD       = 24

FG        = (0, 255, 65, 255)       # neon green
DARK_BG   = (10, 10, 15, 255)
GLOW_COL  = (0, 255, 65)
GLOW_R    = 6                       # glow blur radius

ROOT    = Path(__file__).parent.parent
DOCS    = ROOT / "docs" / "assets"
STATIC  = ROOT / "phantomsignal" / "web" / "static" / "img"


def slant_lines(word: str) -> list[str]:
    raw = pyfiglet.figlet_format(word, font="slant")
    lines = raw.rstrip("\n").splitlines()
    # strip trailing whitespace but keep leading (shapes the slant)
    return [l.rstrip() for l in lines]


def render(bg: tuple, path: Path) -> None:
    phantom_lines = slant_lines("PHANTOM")
    signal_lines  = slant_lines("SIGNAL")

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SZ)
    except OSError:
        font = ImageFont.load_default()

    # Measure each block with a dummy image
    dummy = Image.new("RGBA", (1, 1))
    dc    = ImageDraw.Draw(dummy)

    def block_width(lines):
        return max((dc.textlength(l, font=font) for l in lines), default=0)

    pw = block_width(phantom_lines)
    sw = block_width(signal_lines)

    canvas_w = int(max(pw, sw) + PAD * 2)
    total_lines = len(phantom_lines) + 1 + len(signal_lines)  # 1 blank gap
    canvas_h = int(PAD + total_lines * LINE_H + PAD)

    # Render text layer (transparent base, then composite glow)
    text_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    td = ImageDraw.Draw(text_layer)

    def draw_block(lines, y_start):
        w = block_width(lines)
        x = (canvas_w - w) / 2          # centre each block independently
        y = y_start
        for line in lines:
            td.text((x, y), line, font=font, fill=FG)
            y += LINE_H
        return y

    y = PAD
    y = draw_block(phantom_lines, y)
    y += LINE_H                          # blank gap between words
    draw_block(signal_lines, y)

    # Build glow: blur a copy of the text layer, composite under sharp text
    glow = text_layer.filter(ImageFilter.GaussianBlur(radius=GLOW_R))
    glow2 = text_layer.filter(ImageFilter.GaussianBlur(radius=GLOW_R * 2))

    img = Image.new("RGBA", (canvas_w, canvas_h), bg)
    img = Image.alpha_composite(img, glow2)
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, text_layer)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    print(f"  ✓  {path}  ({canvas_w}×{canvas_h})")


if __name__ == "__main__":
    print("Rendering PhantomSignal avatar assets...")
    render(DARK_BG,      DOCS   / "phantomsignal-avatar.png")
    render((0, 0, 0, 0), DOCS   / "phantomsignal-avatar-transparent.png")
    render(DARK_BG,      STATIC / "phantom-ascii.png")
    render((0, 0, 0, 0), STATIC / "phantom-ascii-transparent.png")
    print("Done.")
