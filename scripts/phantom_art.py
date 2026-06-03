#!/usr/bin/env python3
"""
PhantomSignal ANSI Art Pack
BBS / Blocktronics / Demoscene aesthetic — 80-col EGA palette
Phantom character: hooded void-face, outstretched clawed arms, jagged tendrils
Generates:
  docs/assets/phantom_scene.ans   — full 80-col scene
  docs/assets/phantom_ghost.ans   — standalone ghost figure
  docs/assets/phantom_splash.ans  — 80x24 CLI splash
"""
from pathlib import Path

E   = "\033"
RST = f"{E}[0m"
_   = RST

# ── colour primitives ────────────────────────────────────────────────────────
def f(n):      return f"{E}[{30+n if n<8 else 90+n-8}m"
def b(n):      return f"{E}[{40+n if n<8 else 100+n-8}m"
def fb(fg,bg): return f"{E}[{30+fg if fg<8 else 90+fg-8};{40+bg if bg<8 else 100+bg-8}m"

K,R,G,Y,B,M,C,W         = 0,1,2,3,4,5,6,7
bK,bR,bG,bY,bB,bM,bC,bW = 8,9,10,11,12,13,14,15

# palette shortcuts
PH  = f(bM)        # bright magenta  — phantom body highlight
PM  = f(M)         # dark magenta    — phantom body mid
PD  = f(R)         # dark red        — phantom deep shadow / outline
GN  = f(G)         # dark green      — signal dim
BGN = f(bG)        # bright green    — signal bright
CY  = f(C)         # dark cyan
BCY = f(bC)        # bright cyan
DM  = f(W)         # dim grey
WH  = f(bW)        # white
VO  = fb(K, bM)    # black fg on bright-mag bg — void face interior
GR  = fb(bM, K)    # bright-mag fg on black bg — grin edge

# half-block helpers
def HT(fg,bg): return fb(fg,bg)+"▀"+RST   # upper=fg  lower=bg
def HB(fg,bg): return fb(fg,bg)+"▄"+RST   # upper=bg  lower=fg

DOCS = Path(__file__).parent.parent / "docs" / "assets"
DOCS.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
#  THE PHANTOM  — 38 printable chars wide, 20 rows
#  Hooded void-face · arms outstretched · clawed hands · jagged tendrils
#  Inspired by classic BBS/blocktronics character art, EGA 16-colour palette
# ─────────────────────────────────────────────────────────────────────────────
def ghost_lines():
    rows = [
        # ── hood dome ─────────────────────────────────────────────────────────
        f"          {HB(bM,K)}{PH}████████████{_}{HB(bM,K)}          ",
        f"        {HB(bM,K)}{PH}████████████████{_}{HB(bM,K)}        ",
        f"       {PH}██████████████████████{_}       ",
        # ── void face ─────────────────────────────────────────────────────────
        f"      {PH}███{VO}              {GR}█{VO} {_}{PH}███{_}      ",
        f"      {PH}███{VO}              {VO}  {_}{PH}███{_}      ",
        f"      {PH}███{VO}  {GR}╰──────────╯{VO}  {_}{PH}███{_}      ",
        # ── chin / neck ───────────────────────────────────────────────────────
        f"       {PH}██████████████████████{_}       ",
        # ── wide shoulders ────────────────────────────────────────────────────
        f"  {HB(bM,K)}{PH}████████████████████████████{_}{HB(bM,K)}  ",
        f"  {PH}████████████████████████████████{_}  ",
        # ── arms extending with shadow ────────────────────────────────────────
        f"{PM}▐{_}{PH}██{PM}╲{_}   {PH}████████████████████{_}   {PM}╱{PH}██{PM}▌{_}",
        f"{PM}╱{PH}█{PM}╲{PH}╲{_}  {PM}▐{PH}██████████████████{PM}▌{_}  {PM}╱{PH}╱{PM}╲{PH}█{PM}╲{_}",
        # ── clawed hands ──────────────────────────────────────────────────────
        f"{PD}╱{PM}╱{PD}╱{_}   {PH}████████████████████{_}   {PD}╲{PM}╲{PD}╲{_}",
        # ── solid body ────────────────────────────────────────────────────────
        f"      {PH}████████████████████████{_}      ",
        f"      {PM}▓{PH}██████████████████████{PM}▓{_}      ",
        f"       {PH}████████████████████████{_}       ",
        # ── tendril base — body starts breaking into points ───────────────────
        f"      {HT(bM,K)}{PH}▌▌{_}{HT(bM,K)}{_}  {HT(bM,K)}{PH}▌▌{_}{HT(bM,K)}{_}  {HT(bM,K)}{PH}▌▌{_}{HT(bM,K)}{_}      ",
        # ── tendrils ──────────────────────────────────────────────────────────
        f"      {PH}▌{_}  {PM}▐▌{_}   {PH}▌{_}{PM}▌{_}   {PM}▌▐{_}  {PH}▌{_}      ",
        f"       {PM}▌{_}   {PH}▌{_}   {PM}▌{_}   {PH}▌{_}   {PM}▌{_}       ",
        f"        {PH}▌{_}   {PM}▌{_}   {PH}▌{_}   {PM}▌{_}        ",
        f"         {PM}▌{_}       {PH}▌{_}         ",
    ]
    return rows


# ─────────────────────────────────────────────────────────────────────────────
#  SIGNAL HALOS — flanking the phantom, one per ghost row
#  (inner, outer) — rendered mirrored left / normal right
# ─────────────────────────────────────────────────────────────────────────────
HALO = [
    (f"{CY}░{_}",  f"{GN} · {_}"),
    (f"{CY}░{_}",  f"{GN}·  {_}"),
    (f"{CY}░{_}",  f"{GN}   {_}"),
    (f"{CY}░{_}",  f"{GN}─  {_}"),
    (f"{CY}░{_}",  f"{GN}─  {_}"),
    (f"{CY}░{_}",  f"{GN}─  {_}"),
    (f"{CY}░{_}",  f"{GN}─  {_}"),
    (f"{CY}░{_}",  f"{GN}   {_}"),
    (f"{CY}░{_}",  f"{GN}   {_}"),
    (f"{CY}░{_}",  f"{GN}   {_}"),
    (f"{CY}░{_}",  f"{GN}   {_}"),
    (f"{CY}░{_}",  f"{GN}   {_}"),
    ("  ",          "    "),
    ("  ",          "    "),
    ("  ",          "    "),
    ("  ",          "    "),
    ("  ",          "    "),
    ("  ",          "    "),
    ("  ",          "    "),
    ("  ",          "    "),
]


# ─────────────────────────────────────────────────────────────────────────────
#  FULL SCENE  (80 cols)
# ─────────────────────────────────────────────────────────────────────────────
def scene() -> str:
    lines = []

    def ln(s=""): lines.append(s)

    bdr = f"{PM}║{_}"
    top = f"{PM}╔{'═'*78}╗{_}"
    bot = f"{PM}╚{'═'*78}╝{_}"

    ln(top)
    ln(f"{bdr}{'':^80}{bdr}")

    # Slant-font header — cyan gradient
    def hln(s): ln(f"{bdr}  {s:<76}{_}{bdr}")
    hln(f"{BCY}    ____  __  _____    _   ____________  __  ___")
    hln(f"{BCY}   / __ \\/ / / /   |  / | / /_  __/ __ \\/  |/  /")
    hln(f"{CY}  / /_/ / /_/ / /| | /  |/ / / / / / / / /|_/ /")
    hln(f"{CY} / ____/ __  / ___ |/ /|  / / / / /_/ / /  / /")
    hln(f"{f(bK)}/_/   /_/ /_/_/  |_/_/ |_/ /_/  \\____/_/  /_/{_}")
    ln(f"{bdr}{'':^80}{bdr}")
    hln(f"{PH}   _____ ___________   _____    __")
    hln(f"{PH}  / ___//  _/ ____/ | / /   |  / /")
    hln(f"{PM}  \\__ \\ / // / __/  |/ / /| | / /")
    hln(f"{PM} ___/ // // /_/ / /|  / ___ |/ /___")
    hln(f"{f(bK)}/____/___/\\____/_/ |_/_/  |_/_____/{_}")
    ln(f"{bdr}{'':^80}{bdr}")

    # Signal divider
    sdiv = f"{GN}·{_}  {GN}·{_}  {GN}─{_}{BGN}{'─'*52}{_}{GN}─{_}  {GN}·{_}  {GN}·{_}"
    ln(f"{bdr}  {sdiv}  {bdr}")
    ln(f"{bdr}{'':^80}{bdr}")

    # Ghost + halo
    ghost = ghost_lines()
    PAD = 15
    for i, grow in enumerate(ghost):
        hl, hr = HALO[i] if i < len(HALO) else ("  ", "    ")
        ln(f"{bdr}{'':>{PAD}}{GN}{hr[::-1]}{_}{CY}{hl[::-1]}{_}{grow}{CY}{hl}{_}{GN}{hr}{_}{'':>{PAD}}{bdr}")

    ln(f"{bdr}{'':^80}{bdr}")
    ln(f"{bdr}  {sdiv}  {bdr}")
    ln(f"{bdr}{'':^80}{bdr}")

    # Footer
    ln(f"{bdr}  {PH}>> OPEN-SOURCE OSINT INTELLIGENCE FRAMEWORK <<{_:<29}{bdr}")
    ln(f"{bdr}  {DM}\"See everything. Leave no trace.\"{_:<44}{bdr}")
    ln(f"{bdr}{'':^80}{bdr}")
    ln(f"{bdr}  {BGN}pip install phantomsignal{_}   {DM}github.com/getphantomsignal/phantomsignal{_}{'':>5}{bdr}")
    ln(f"{bdr}  {DM}phantomsignal.sh{_}{'':>56}v1.3.0{bdr}")
    ln(f"{bdr}{'':^80}{bdr}")
    ln(bot)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  STANDALONE GHOST
# ─────────────────────────────────────────────────────────────────────────────
def standalone_ghost() -> str:
    lines = []

    lines += [
        f"  {PH}P H A N T O M   S I G N A L{_}",
        f"  {PM}{'─'*28}{_}",
        f"  {DM}OSINT Intelligence Framework{_}",
        f"  {PM}{'─'*28}{_}",
        "",
        f"  {GN}·  ·  ·  {'─'*16}  ·  ·  ·{_}",
        f"  {CY}    ░░{'░'*22}░░{_}",
    ]

    for row in ghost_lines():
        lines.append(f"  {CY}░{_}{row}{CY}░{_}")

    lines += [
        f"  {CY}    ░░{'░'*22}░░{_}",
        f"  {GN}·  ·  ·  {'─'*16}  ·  ·  ·{_}",
        "",
        f'  {DM}"See everything. Leave no trace."{_}',
        f"  {BGN}pip install phantomsignal{_}",
        "",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  SPLASH SCREEN  80×24
# ─────────────────────────────────────────────────────────────────────────────
def splash() -> str:
    lines = []

    def ln(s=""): lines.append(s)

    bdr = f"{PM}║{_}"
    top = f"{PM}╔{'═'*78}╗{_}"
    bot = f"{PM}╚{'═'*78}╝{_}"

    ln(top)
    ln(f"{bdr}  {PH}{'PHANTOM SIGNAL':^76}{_}{bdr}")
    ln(f"{bdr}  {BGN}{'OPEN-SOURCE OSINT INTELLIGENCE FRAMEWORK':^76}{_}{bdr}")
    ln(f"{bdr}  {PM}{'─'*76}{_}{bdr}")

    ghost = ghost_lines()
    for i, row in enumerate(ghost[:10]):
        side = f"{GN}·{_}" if i % 3 == 0 else "  "
        pad = " " * 18
        ln(f"{bdr}{pad}{CY}░{_}{side}{row}{side}{CY}░{_}{pad}{bdr}")

    ln(f"{bdr}  {BGN}{'· ' * 18}·{_:>5}{bdr}")
    ln(f"{bdr}{'':^80}{bdr}")
    ln(f"{bdr}  {PH}{'DNS':^12}{_}{GN}│{_}{PH}{'PORT SCAN':^12}{_}{GN}│{_}{PH}{'TECH DETECT':^12}{_}{GN}│{_}{PH}{'INTEL APIS':^12}{_}{GN}│{_}{PH}{'SHADOW SCORE':^12}{_}  {bdr}")
    ln(f"{bdr}  {BGN}{'A/MX/NS/TXT':^12}{_}{GN}│{_}{BGN}{'99 ports':^12}{_}{GN}│{_}{BGN}{'50+ stacks':^12}{_}{GN}│{_}{BGN}{'30+ sources':^12}{_}{GN}│{_}{BGN}{'0–100':^12}{_}  {bdr}")
    ln(f"{bdr}  {PM}{'─'*76}{_}{bdr}")
    ln(f"{bdr}  {BGN}$ pip install phantomsignal{_}{'':>52}{bdr}")
    ln(f"{bdr}  {DM}phantomsignal.sh  ·  github.com/getphantomsignal/phantomsignal  ·  v1.3.0{_}  {bdr}")
    ln(f"{bdr}  {DM}\"See everything. Leave no trace.\"{_}{'':>44}{bdr}")
    ln(bot)

    while len(lines) < 24:
        lines.append("")

    return "\n".join(lines[:24])


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pieces = {
        "phantom_scene.ans":  scene,
        "phantom_ghost.ans":  standalone_ghost,
        "phantom_splash.ans": splash,
    }
    for fname, fn in pieces.items():
        art = fn()
        print(f"\n{'─'*80}\n  {fname}\n{'─'*80}")
        print(art)
        (DOCS / fname).write_text(art + "\n", encoding="utf-8")
        print(f"\n{RST}✓  {DOCS / fname}")
