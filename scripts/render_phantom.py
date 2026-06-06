#!/usr/bin/env python3
"""
Render the PhantomSignal phantom mascot art to PNG assets.

Outputs two files:
  phantomsignal/web/static/img/phantom-ascii.png             — dark background version
  phantomsignal/web/static/img/phantom-ascii-transparent.png — transparent background (used in UI)

Requirements:
  pip install Pillow
  apt-get install fonts-hack  (or equivalent — needs Hack-Regular.ttf)

Usage:
  python scripts/render_phantom.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Phantom mascot art (38 cols × 20 rows) ───────────────────────────────────
_PHANTOM = [
    r"            ▄▄████████████▄▄            ",
    r"          ▄██████████████████▄          ",
    r"         ████████████████████████         ",
    r"        ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓████        ",
    r"        ████▓                ▓████        ",
    r"        ████▓  ╰──────────╯  ▓████        ",
    r"         ████████████████████████         ",
    r"     ▄▄███████████████████████████▄▄     ",
    r"     ████████████████████████████████     ",
    r"   ▐██╲▓▓████████████████████▓▓╱██▌   ",
    r"  ╱███╲╲ ▓████████████████████ ╱╱███╲  ",
    r" ╱╱╱ ╲╲  ████████████████████  ╱╱ ╲╲╲ ",
    r"          ██████████████████████          ",
    r"          ▓████████████████████▓          ",
    r"          ██████████████████████          ",
    r"         ▐▌▌  ▌██▌  ▌██▌  ▌██▌▐         ",
    r"          ▌▌  ▐▌ ▐▌  ▌ ▐▌  ▌▌           ",
    r"          ▌    ▌   ▌  ▌   ▌  ▌           ",
    r"           ▌    ▌   ▌▌   ▌    ▌          ",
    r"            ▌         ▌         ▌         ",
]

# Signal halo chars per row (left side — mirrored right)
_HALO = [
    " · ░", "· ░░", "  ░░", " ─░░", " ─░░",
    " ─░░", " ─░░", "  ░░", "  ░░", "  ░░",
    "   ░", "   ░", "    ", "    ", "    ",
    "    ", "    ", "    ", "    ", "    ",
]

# Compose art lines: mirrored halo + phantom row + halo
ART_LINES = [
    f"{_HALO[i][::-1]}{row}{_HALO[i]}"
    for i, row in enumerate(_PHANTOM)
] + [
    "",
    "     ·  ·  P H A N T O M   S I G N A L  ·  ·",
    "     OSINT Intelligence Framework",
]

# ── Config ───────────────────────────────────────────────────────────────────
FONT_SZ = 14                        # px — Hack Regular for block art
LINE_H  = FONT_SZ + 2               # line spacing
PAD     = 16                        # canvas padding (px)
FG      = (0, 255, 65, 255)         # neon green
DARK_BG = (10, 10, 15, 255)         # near-black

FONT_PATH = "/usr/share/fonts/truetype/hack/Hack-Regular.ttf"

OUT_DIR = Path(__file__).parent.parent / "phantomsignal" / "web" / "static" / "img"

# ── Render ───────────────────────────────────────────────────────────────────
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SZ)
    except OSError:
        raise SystemExit(
            f"Font not found: {FONT_PATH}\n"
            "Install with: sudo apt-get install fonts-hack\n"
            "or update FONT_PATH in this script."
        )

    # Measure canvas
    dummy = Image.new("RGBA", (1, 1))
    dc    = ImageDraw.Draw(dummy)
    max_w = max(dc.textlength(l, font=font) for l in ART_LINES)
    art_h = LINE_H * len(ART_LINES)

    total_w = int(max_w + PAD * 2)
    total_h = int(PAD + art_h + PAD)
    art_x   = (total_w - max_w) / 2   # centre art horizontally

    def render(bg: tuple, fg: tuple, path: Path) -> None:
        img = Image.new("RGBA", (total_w, total_h), bg)
        d   = ImageDraw.Draw(img)
        y   = PAD
        for line in ART_LINES:
            d.text((art_x, y), line, font=font, fill=fg)
            y += LINE_H
        img.save(path)
        print(f"  ✓  {path}  ({total_w}×{total_h})")

    print("Rendering PhantomSignal phantom assets...")
    render(DARK_BG, FG, OUT_DIR / "phantom-ascii.png")
    render((0, 0, 0, 0), FG, OUT_DIR / "phantom-ascii-transparent.png")
    print("Done.")


if __name__ == "__main__":
    main()
