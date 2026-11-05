#!/usr/bin/env python3
"""
Render the DeadRecon logo: card XIII, a pixel skull with its identity censored.

The art is drawn on a pixel grid, so it stays sharp at whole-number scales. The favicon
has its own 16 px grid, because the full skull's detail is lost at that size.

Outputs:
  docs/assets/deadrecon-card.svg|png            full card (landing page, README, social image)
  docs/assets/deadrecon-mark.svg                the card's skull at nav size
  docs/assets/deadrecon-favicon.svg             simplified skull for 16 px
  docs/assets/deadrecon-avatar.png              square avatar, 528 px
  deadrecon/web/static/img/                     the same card, mark and favicon SVGs

Usage: python scripts/render_logo.py   (requires Pillow for the PNGs)
"""
import math
from pathlib import Path

ROOT = Path(__file__).parent.parent
RED, WHITE, BLACK = "#ff3b1f", "#ffffff", "#000000"
BONE, BAR, RAY, HOLE = 1, 2, 4, 3  # HOLE is black that hides whatever is behind it
PALETTE = {BONE: WHITE, BAR: RED, RAY: RED}

FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "C": "01111 10000 10000 10000 10000 10000 01111",
    "D": "11110 10001 10001 10001 10001 10001 11110", "E": "11111 10000 10000 11110 10000 10000 11111",
    "I": "111 010 010 010 010 010 111", "N": "10001 11001 10101 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "R": "11110 10001 10001 11110 10100 10010 10001",
    "X": "10001 10001 01010 00100 01010 10001 10001", " ": "000 000 000 000 000 000 000",
}


class Grid:
    def __init__(self, w, h, fill=0):
        self.w, self.h = w, h
        self.cells = [[fill] * w for _ in range(h)]

    def set(self, x, y, value):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.cells[y][x] = value

    def get(self, x, y):
        return self.cells[y][x] if 0 <= x < self.w and 0 <= y < self.h else None

    def rect(self, x0, y0, x1, y1, value):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, value)

    def blit(self, other, dx, dy):
        for y in range(other.h):
            for x in range(other.w):
                if other.cells[y][x] is not None:
                    self.set(dx + x, dy + y, other.cells[y][x])


def skull(w, h, detail=True, pitch=None, nose=.42):
    """A symmetric skull with a short jaw, small sockets and shading on its far side."""
    g = Grid(w, h, None)
    pitch = pitch or max(3, round(w / 11))
    for y in range(h):
        for x in range(w):
            u, v = (x + .5 - w / 2) / (w / 2), (y + .5 - h / 2) / (h / 2)
            a = abs(u)
            head = (u / .98) ** 2 + ((v + .26) / .72) ** 2 <= 1
            cheek = -.2 <= v <= .42 and a <= .80 - .28 * max(0, v - .05) / .37
            jaw = .40 <= v <= .72 and a <= .58
            if not (head or cheek or jaw):
                continue
            g.cells[y][x] = BONE
            if ((a - .42) / .25) ** 2 + ((v - .03) / .17) ** 2 <= 1:
                g.cells[y][x] = HOLE
            if .24 <= v <= .46 and a <= (v - .21) * nose:
                g.cells[y][x] = HOLE
            offset = abs(x - (w - 1) / 2)
            if jaw and v >= .56 and int(offset - .5) % pitch == 0 and offset < w * .3:
                g.cells[y][x] = HOLE
            shaded = (u > .62 and v < .25) or (u > .36 and v < -.62 and u * 1.1 - v * .25 > .7)
            if detail and shaded and g.cells[y][x] == BONE and (x + y) % 2 == 0:
                g.cells[y][x] = HOLE
    last = max(y for y in range(h) if any(c is not None for c in g.cells[y]))
    g.cells, g.h = g.cells[:last + 1], last + 1
    for dx, dy in ((0, 0), (1, 1), (1, 2), (0, 3), (-1, 4), (0, 5)):  # crack
        if detail and g.get(int(w * .36) + dx, int(h * .05) + dy + 1) == BONE:
            g.set(int(w * .36) + dx, int(h * .05) + dy + 1, HOLE)
    return g


def halo(g, p=2):
    """Clear a black gap around the skull, so it separates from the rays."""
    out = Grid(g.w + 2 * p, g.h + 2 * p, None)
    for y in range(g.h):
        for x in range(g.w):
            if g.cells[y][x] is not None:
                for dy in range(-p, p + 1):
                    for dx in range(-p, p + 1):
                        if abs(dx) + abs(dy) <= p + 1:
                            out.set(x + p + dx, y + p + dy, HOLE)
    out.blit(g, p, p)
    return out


def rays(g, cx, cy, x0, y0, x1, y1, count=12, base=.2):
    """Sharp star points over a checkerboard field that thins out with distance."""
    reach = min(x1 - x0, y1 - y0) / 2
    step = 2 * math.pi / count
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx, dy = x + .5 - cx, y + .5 - cy
            r = math.hypot(dx, dy) or .01
            turn = (math.atan2(dy, dx) + math.pi / 2) / step
            index = round(turn)
            delta = (turn - index) * step
            along, off = r * math.cos(delta), abs(r * math.sin(delta))
            length = reach * (1.28 if index % 2 == 0 else .92)
            half = reach * base * max(0, 1 - along / length) * (1 if index % 2 == 0 else .8)
            q = r / reach
            if off < half:
                g.set(x, y, RAY)
            elif half > 0 and off < half + 1.6 and (x + y) % 2 == 0:
                g.set(x, y, RAY)
            elif q < .62 and (x + y) % 2 == 0:
                g.set(x, y, RAY)
            elif .62 <= q < .9 and x % 2 == 0 and y % 2 == 0:
                g.set(x, y, RAY)
            elif .9 <= q < 1.3 and x % 4 == 0 and y % 4 == 0:
                g.set(x, y, RAY)


def notched(g, x0, y0, x1, y1, notch=2, clear=True):
    if clear:
        g.rect(x0, y0, x1, y1, 0)
    for x in range(x0 + notch, x1 - notch + 1):
        g.set(x, y0, BONE)
        g.set(x, y1, BONE)
    for y in range(y0 + notch, y1 - notch + 1):
        g.set(x0, y, BONE)
        g.set(x1, y, BONE)
    for k in range(1, notch):
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            g.set(cx + sx * k, cy + sy * (notch - k), BONE)


def text_width(text):
    return sum(len(FONT[c].split()[0]) + 1 for c in text) - 1


def plate(g, text, cy, pad=3):
    x0 = (g.w - text_width(text)) // 2 - pad
    x1 = x0 + text_width(text) + 2 * pad - 1
    notched(g, x0 - 1, cy - 5, x1 + 1, cy + 5)
    x = x0 + pad
    for char in text:
        rows = FONT[char].split()
        for j, row in enumerate(rows):
            for i, c in enumerate(row):
                if c == "1":
                    g.set(x + i, cy - 3 + j, BONE)
        x += len(rows[0]) + 1


def card():
    w, h = 92, 112
    g = Grid(w, h)
    left, top, right, bottom = 5, 2, w - 6, h - 3
    cx, cy = w // 2, 54
    rays(g, cx, cy, left + 3, top + 3, right - 3, bottom - 3)
    head = halo(skull(44, 50))
    ox, oy = cx - head.w // 2, cy - 23
    g.blit(head, ox, oy)
    notched(g, left, top, right, bottom, notch=3, clear=False)
    for x in range(left + 3, right - 2):  # dotted inner rule
        if x % 2 == 0:
            g.set(x, top + 2, BONE)
            g.set(x, bottom - 2, BONE)
    for y in range(top + 3, bottom - 2):
        if y % 2 == 0:
            g.set(left + 2, y, BONE)
            g.set(right - 2, y, BONE)
    g.rect(cx - 14, top + 3, cx + 14, top + 6, 0)  # nothing pokes past the plates
    g.rect(cx - 37, bottom - 6, cx + 37, bottom - 3, 0)
    plate(g, "XIII", top + 11)
    plate(g, "DEAD RECON", bottom - 10)
    bar_top = oy + 2 + 21
    g.rect(0, bar_top, w - 1, bar_top + 8, BAR)  # breaks the frame on purpose
    return g


MARK_16 = """
....########....
..############..
.##############.
.##############.
.##############.
rrrrrrrrrrrrrrrr
rrrrrrrrrrrrrrrr
.######..######.
..#####..#####..
...##########...
....########....
....##.##.##....
....##.##.##....
"""


def favicon():
    rows = MARK_16.strip().split("\n")
    g = Grid(16, 16)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != ".":
                g.set(x, y + 1, BAR if c == "r" else BONE)
    return g


def mark():
    """The card's skull at nav size: same proportions, same bar across the eyes."""
    g = Grid(40, 34)
    head = skull(32, 36, pitch=4, nose=.62)
    g.blit(head, 4, 2)
    g.rect(0, 2 + 15, 39, 2 + 20, BAR)
    return g


def svg(g, background=None):
    parts = [f'<rect width="{g.w}" height="{g.h}" fill="{background}"/>'] if background else []
    runs = {}
    for y in range(g.h):
        x = 0
        while x < g.w:
            value = g.cells[y][x]
            if value not in PALETTE:
                x += 1
                continue
            end = x
            while end + 1 < g.w and g.cells[y][end + 1] == value:
                end += 1
            runs.setdefault(PALETTE[value], []).append(f"M{x} {y}h{end - x + 1}v1h-{end - x + 1}z")
            x = end + 1
    parts += [f'<path fill="{color}" d="{"".join(d)}"/>' for color, d in runs.items()]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {g.w} {g.h}" shape-rendering="crispEdges" '
            f'role="img" aria-label="DeadRecon">{"".join(parts)}</svg>\n')


def png(g, path, scale, background=(0, 0, 0)):
    from PIL import Image
    colors = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in PALETTE.items()}
    image = Image.new("RGB", (g.w, g.h), background)
    for y in range(g.h):
        for x in range(g.w):
            if g.cells[y][x] in colors:
                image.putpixel((x, y), colors[g.cells[y][x]])
    image.resize((g.w * scale, g.h * scale), Image.NEAREST).save(path, optimize=True)


def main():
    assets, static = ROOT / "docs/assets", ROOT / "deadrecon/web/static/img"
    the_card, skull_mark = card(), mark()
    for folder in (assets, static):
        (folder / "deadrecon-card.svg").write_text(svg(the_card, BLACK))
        (folder / "deadrecon-mark.svg").write_text(svg(skull_mark))
        (folder / "deadrecon-favicon.svg").write_text(svg(favicon()))
    png(the_card, assets / "deadrecon-card.png", 8)
    avatar = Grid(44, 44)
    avatar.blit(skull_mark, 2, 5)
    png(avatar, assets / "deadrecon-avatar.png", 12)


if __name__ == "__main__":
    main()
