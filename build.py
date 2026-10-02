#!/usr/bin/env python3
"""
Builds the SVG assets for the stu-titor GitHub profile README.

GitHub strips CSS from READMEs, so custom fonts only survive inside SVG
images. Each SVG here carries its own tiny subset of IBM Plex (only the
glyphs it uses), so it renders the same for every visitor.

Edit the CONTENT section below, then run:
    pip install fonttools
    python3 build.py
"""
import base64
import io
import os
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
OUT = os.path.join(HERE, "assets")

# ---------------------------------------------------------------- CONTENT --

NAME = "Stu"
HANDLE = "@stu-titor"
BIO = ("Systems and machine learning. So far that has meant a pipelined CPU "
       "and cache simulator, a malloc with binned free lists, a Huffman "
       "compressor, and a CNN trained from scratch on Tiny ImageNet.")

# The 80-column card. Columns 1-72 hold the statement, 73-80 the sequence id.
CARD_STATEMENT = 'PRINT *, "HELLO, I\'M STU. I BUILD THINGS FROM THE BOTTOM UP."'
CARD_ID = "STU00010"
CARD_CAPTION = "The holes spell out the top line in IBM 029 card code."

PROJECTS = [
    ("Miru-Image-Classifier", "Python",
     "Convolutional neural network in PyTorch, trained from scratch on Tiny "
     "ImageNet to roughly 71% accuracy. Uses .NET and AWS."),
    ("Image-Collector", "Python",
     "Collects, deduplicates, and catalogs images from multiple providers "
     "into content-addressed storage and PostgreSQL."),
    ("chArm-v5-System-Emulator", "Assembly",
     "Pipeline and cache simulator for the chArm-v5 ISA, built in stages "
     "from PIPE- to PIPE to PCSIM. Runs on Linux."),
    ("Huffman-Encoding-System", "Java",
     "Lossless file compression and decompression using Huffman encoding."),
    ("Dynamic-Memory-Allocator", "C",
     "A custom malloc and free in C, built on binned free lists with "
     "deferred coalescing."),
    ("Stones-v2.0", "Java",
     "An updated version of Stones that adds new mobs and tools."),
]

TOOLKIT = [
    ("Languages", "Python, C, Java, assembly"),
    ("Machine learning", "PyTorch, convolutional neural networks"),
    ("Data", "PostgreSQL, content-addressed storage"),
    ("Platforms", "Linux, AWS, .NET"),
]

CONTACT_LABEL = "Connect on LinkedIn"
CONTACT_URL = "https://www.linkedin.com/in/simon-shrestha-ab98a2363"
GITHUB_USER = "stu-titor"

# ------------------------------------------------------------------ STYLE --
# Claude's palette: ivory, slate, cloud, and the clay orange.

THEMES = {
    "light": dict(panel="#faf9f5", stroke="#e8e6dc", ink="#141413",
                  ink2="#5e5d59", link="#c15f3c", stock="#e8e6dc",
                  stock_edge="#d6d3c7", printed="#a19e91", hole="#d97757"),
    "dark":  dict(panel="#1f1e1d", stroke="#34332f", ink="#faf9f5",
                  ink2="#b0aea5", link="#d97757", stock="#e8e6dc",
                  stock_edge="#e8e6dc", printed="#a19e91", hole="#d97757"),
}
LANG_COLOR = {"Python": "#6a9bcc", "C": "#d97757", "Java": "#788c5d",
              "Assembly": "#b0aea5"}
BUTTON = dict(fill="#d97757", ink="#141413")

FONTS = {
    "mono":   ("IBMPlexMono-Regular.ttf", "plex-mono",
               "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"),
    "monob":  ("IBMPlexMono-Bold.ttf", "plex-mono-bold",
               "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"),
    "serif":  ("IBMPlexSerif-Regular.ttf", "plex-serif",
               "Georgia, 'Times New Roman', serif"),
    "serifi": ("IBMPlexSerif-Italic.ttf", "plex-serif-italic",
               "Georgia, 'Times New Roman', serif"),
}
CAP = 0.698  # IBM Plex cap height, in em

# ------------------------------------------------------------ TYPE TOOLS --

_cache = {}


def tt(key):
    if key not in _cache:
        _cache[key] = TTFont(os.path.join(FONT_DIR, FONTS[key][0]))
    return _cache[key]


def measure(key, s, size):
    f = tt(key)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    units = sum(hmtx[cmap.get(ord(c), ".notdef")][0] for c in s)
    return units * size / f["head"].unitsPerEm


def wrap(key, s, size, width):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(key, trial, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


def font_face(key, chars):
    opts = subset.Options()
    opts.flavor = "woff"
    opts.drop_tables += ["DSIG", "meta"]
    font = subset.load_font(os.path.join(FONT_DIR, FONTS[key][0]), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)))
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    data = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{FONTS[key][1]}';"
            f"src:url(data:font/woff;base64,{data}) format('woff');}}")


class SVG:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.els, self.used, self.css = [], {}, []

    def add(self, s):
        self.els.append(s)

    def text(self, key, x, y, s, size, fill, anchor="start", extra=""):
        self.used.setdefault(key, set()).update(s)
        a = "" if anchor == "start" else f' text-anchor="{anchor}"'
        self.add(f'<text class="{key}" x="{x:.2f}" y="{y:.2f}" '
                 f'font-size="{size}" fill="{fill}"{a}{extra}>'
                 f'{escape(s)}</text>')

    def chars_at(self, key, xs, y, chars, size, fill, extra=""):
        """One glyph per x position, each centred on it (punch-card print)."""
        pairs = [(x, c) for x, c in zip(xs, chars) if c != " "]
        if not pairs:
            return
        self.used.setdefault(key, set()).update(c for _, c in pairs)
        xl = " ".join(f"{x:.2f}" for x, _ in pairs)
        s = "".join(c for _, c in pairs)
        self.add(f'<text class="{key}" x="{xl}" y="{y:.2f}" font-size="{size}"'
                 f' fill="{fill}" text-anchor="middle"{extra}>'
                 f'{escape(s)}</text>')

    def render(self):
        faces = "".join(font_face(k, v) for k, v in sorted(self.used.items()))
        classes = "".join(
            f".{k}{{font-family:'{FONTS[k][1]}',{FONTS[k][2]};}}"
            for k in sorted(self.used))
        style = faces + classes + "".join(self.css)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
                f'role="img" aria-labelledby="t"><title id="t">'
                f'{escape(self.title)}</title><style>{style}</style>'
                + "".join(self.els) + "</svg>")


def panel_path(x, y, w, h, cut=14, r=6):
    """A panel with the punch card's clipped top-left corner."""
    return (f"M{x + cut},{y} H{x + w - r} A{r},{r} 0 0 1 {x + w},{y + r} "
            f"V{y + h - r} A{r},{r} 0 0 1 {x + w - r},{y + h} "
            f"H{x + r} A{r},{r} 0 0 1 {x},{y + h - r} V{y + cut} Z")


def panel(svg, t, x, y, w, h, cut=14):
    svg.add(f'<path d="{panel_path(x + .5, y + .5, w - 1, h - 1, cut)}" '
            f'fill="{t["panel"]}" stroke="{t["stroke"]}"/>')


# -------------------------------------------------------- HOLLERITH CODE --
# IBM 029 keypunch code. Rows run 12, 11, 0, 1 ... 9 down the card.

ROWS = [12, 11, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
HOLLERITH = {" ": [], "&": [12], "-": [11], "/": [0, 1],
             ".": [12, 8, 3], "<": [12, 8, 4], "(": [12, 8, 5],
             "+": [12, 8, 6], "|": [12, 8, 7], "!": [11, 8, 2],
             "$": [11, 8, 3], "*": [11, 8, 4], ")": [11, 8, 5],
             ";": [11, 8, 6], ",": [0, 8, 3], "%": [0, 8, 4],
             "_": [0, 8, 5], ">": [0, 8, 6], "?": [0, 8, 7],
             ":": [8, 2], "#": [8, 3], "@": [8, 4], "'": [8, 5],
             "=": [8, 6], '"': [8, 7]}
for i in range(10):
    HOLLERITH[str(i)] = [i]
for i, c in enumerate("ABCDEFGHI"):
    HOLLERITH[c] = [12, i + 1]
for i, c in enumerate("JKLMNOPQR"):
    HOLLERITH[c] = [11, i + 1]
for i, c in enumerate("STUVWXYZ"):
    HOLLERITH[c] = [0, i + 2]


def card_line():
    body = (" " * 6 + CARD_STATEMENT).ljust(72)[:72]
    return (body + CARD_ID.ljust(8)[:8]).upper()


def punch_card(svg, t, x0, y0, width):
    """An 80-column FORTRAN card at true proportions (7 3/8 x 3 1/4 in)."""
    s = width / 7.375
    height = 3.25 * s
    col = [x0 + (0.2515 + i * 0.087) * s for i in range(80)]
    row = {r: y0 + (0.25 + i * 0.25) * s for i, r in enumerate(ROWS)}
    hw, hh = 0.055 * s, 0.125 * s
    line = card_line()

    edge = "" if t["stock_edge"] == t["stock"] else f' stroke="{t["stock_edge"]}"'
    svg.add(f'<path d="{panel_path(x0, y0, width, height, cut=0.24 * s, r=0.07 * s)}" '
            f'fill="{t["stock"]}"{edge}/>')

    # Field rules of the FORTRAN coding form: 1-5 | 6 | 7-72 | 73-80
    for c in (5, 6, 72):
        x = (col[c - 1] + col[c]) / 2
        svg.add(f'<line x1="{x:.2f}" y1="{y0 + 0.13 * s:.2f}" x2="{x:.2f}" '
                f'y2="{y0 + height - 0.06 * s:.2f}" stroke="{t["printed"]}" '
                f'stroke-width=".7"/>')
    label_y = (row[11] + row[0]) / 2 + 2.2
    for (a, b), lab in (((1, 5), "STATEMENT"), ((6, 6), "C"),
                        ((7, 72), "FORTRAN  STATEMENT"),
                        ((73, 80), "IDENTIFICATION")):
        svg.text("mono", (col[a - 1] + col[b - 1]) / 2, label_y, lab, 6.2,
                 t["printed"], "middle", ' letter-spacing=".6"')

    # Pre-printed digit rows and column numbers
    for d in range(10):
        svg.chars_at("mono", col, row[d] + 0.36 * 9.4, str(d) * 80, 9.4,
                     t["printed"])
    for r in (0, 9):
        y = row[r] + 0.115 * s
        for i, x in enumerate(col):
            svg.text("mono", x, y, str(i + 1), 4.6, t["printed"], "middle")

    # Holes and interpreted print, punched column by column on load
    for i, ch in enumerate(line):
        rows = HOLLERITH.get(ch, [])
        if not rows:
            continue
        g = [f'<g class="k" style="animation-delay:{0.5 + i * 0.028:.3f}s">']
        for r in rows:
            g.append(f'<rect x="{col[i] - hw / 2:.2f}" y="{row[r] - hh / 2:.2f}" '
                     f'width="{hw:.2f}" height="{hh:.2f}" rx=".9" '
                     f'fill="{t["hole"]}"/>')
        svg.els.extend(g)
        svg.text("mono", col[i], y0 + 0.148 * s, ch, 13.2, "#141413", "middle")
        svg.add("</g>")
    svg.css.append("@keyframes punch{from{opacity:0}to{opacity:1}}"
                   ".k{animation:punch .14s ease-out both}"
                   "@media (prefers-reduced-motion:reduce){.k{animation:none}}")
    return height


# ----------------------------------------------------------------- PIECES --

def hero(t):
    W, pad = 1000, 44
    name_size, bio_size, bio_lh = 84, 19.5, 30.5
    bio_x = 300
    bio_lines = wrap("serif", BIO, bio_size, W - pad - bio_x)
    name_base = pad + CAP * name_size + 6
    bio_first = name_base - CAP * name_size + CAP * bio_size
    bio_bottom = bio_first + (len(bio_lines) - 1) * bio_lh
    card_y = max(name_base + 40, bio_bottom + 12) + 34
    card_w = W - 2 * pad
    card_h = 3.25 * card_w / 7.375
    cap_y = card_y + card_h + 34
    H = round(cap_y + 34)

    svg = SVG(W, H, f"{NAME} ({HANDLE}). {BIO} A punched FORTRAN card "
                    f"reading: {CARD_STATEMENT}")
    panel(svg, t, 0, 0, W, H, cut=22)
    svg.text("monob", pad - 4, name_base, NAME, name_size, t["ink"],
             extra=' letter-spacing="-2"')
    svg.text("mono", pad, name_base + 36, HANDLE, 16, t["ink2"])
    for i, ln in enumerate(bio_lines):
        svg.text("serif", bio_x, bio_first + i * bio_lh, ln, bio_size, t["ink"])
    punch_card(svg, t, pad, card_y, card_w)
    svg.text("serifi", pad, cap_y, CARD_CAPTION, 15, t["ink2"])
    return svg


def heading(t, label):
    svg = SVG(1000, 58, label)
    svg.text("monob", 2, 42, label, 26, t["ink"], extra=' letter-spacing="-.4"')
    return svg


def project_cards(t):
    W_panel, gutter, pad = 476, 12, 26
    W = W_panel + gutter
    size, lh = 16, 24
    texts = [wrap("serif", d, size, W_panel - 2 * pad) for _, _, d in PROJECTS]
    most = max(len(x) for x in texts)
    first = 50 + 34
    foot = first + (most - 1) * lh + 44
    H = foot + pad
    out = []
    for i, ((name, lang, desc), lines) in enumerate(zip(PROJECTS, texts)):
        left = i % 2 == 0
        x = 0 if left else gutter
        svg = SVG(W, H, f"{name}: {desc} Written in {lang}.")
        panel(svg, t, x, 0, W_panel, H)
        svg.text("monob", x + pad, 50, name, 19, t["link"],
                 extra=' letter-spacing="-.3"')
        for j, ln in enumerate(lines):
            svg.text("serif", x + pad, first + j * lh, ln, size, t["ink"])
        svg.add(f'<rect x="{x + pad}" y="{foot - 9.5}" width="9" height="9" '
                f'rx="1" fill="{LANG_COLOR.get(lang, t["ink2"])}"/>')
        svg.text("mono", x + pad + 17, foot, lang, 13.5, t["ink2"])
        out.append((name, svg))
    return out


def toolkit(t):
    W, pad, row_h = 1000, 44, 54
    H = 2 * 22 + row_h * len(TOOLKIT)
    svg = SVG(W, H, "Toolkit. " + " ".join(f"{a}: {b}." for a, b in TOOLKIT))
    panel(svg, t, 0, 0, W, H)
    for i, (label, items) in enumerate(TOOLKIT):
        y = 22 + i * row_h
        if i:
            svg.add(f'<line x1="{pad}" y1="{y}" x2="{W - pad}" y2="{y}" '
                    f'stroke="{t["stroke"]}"/>')
        base = y + row_h / 2 + CAP * 18 / 2
        svg.text("serifi", pad, base, label, 17, t["ink2"])
        svg.text("serif", 300, base, items, 18, t["ink"])
    return svg


def contact(t):
    size = 16.5
    tw = measure("monob", CONTACT_LABEL, size)
    w, h = round(tw + 2 * 28), 54
    svg = SVG(w, h, CONTACT_LABEL)
    svg.add(f'<path d="{panel_path(0, 0, w, h, cut=12, r=6)}" '
            f'fill="{BUTTON["fill"]}"/>')
    svg.text("monob", w / 2, h / 2 + CAP * size / 2, CONTACT_LABEL, size,
             BUTTON["ink"], "middle")
    return svg


def slug(name):
    return name.lower().replace(".", "-")


def main():
    os.makedirs(OUT, exist_ok=True)
    for mode, t in THEMES.items():
        pieces = {"hero": hero(t),
                  "heading-projects": heading(t, "Projects"),
                  "heading-toolkit": heading(t, "Toolkit"),
                  "toolkit": toolkit(t),
                  "contact": contact(t)}
        for name, svg in project_cards(t):
            pieces["project-" + slug(name)] = svg
        for key, svg in pieces.items():
            path = os.path.join(OUT, f"{key}-{mode}.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg.render())
    write_readme(pieces["contact"].w)
    sizes = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f"wrote {len(os.listdir(OUT))} files to assets/ ({sizes / 1024:.0f} KB)"
          " and README.md")


def picture(key, alt, width):
    alt = escape(alt, {'"': "&quot;"})
    return (f'<picture><source media="(prefers-color-scheme: dark)" '
            f'srcset="assets/{key}-dark.svg"><img src="assets/{key}-light.svg" '
            f'width="{width}" alt="{alt}"></picture>')


def write_readme(contact_w):
    repo = f"https://github.com/{GITHUB_USER}"
    parts = [
        "<!-- Generated by build.py. Edit the CONTENT section there and "
        "rerun it rather than editing this file by hand. -->",
        "<p>" + picture("hero", f"{NAME} ({HANDLE}). {BIO}", "100%") + "</p>",
        "<p>" + picture("heading-projects", "Projects", "100%") + "</p>",
    ]
    cards = []
    for name, lang, desc in PROJECTS:
        cards.append(f'<a href="{repo}/{name}">'
                     + picture("project-" + slug(name),
                               f"{name}: {desc} Written in {lang}.", "50%")
                     + "</a>")
    for i in range(0, len(cards), 2):
        parts.append("<p>" + "".join(cards[i:i + 2]) + "</p>")
    parts += [
        "<p>" + picture("heading-toolkit", "Toolkit", "100%") + "</p>",
        "<p>" + picture("toolkit", "Toolkit. " + " ".join(
            f"{a}: {b}." for a, b in TOOLKIT), "100%") + "</p>",
        f'<p><a href="{CONTACT_URL}">'
        + picture("contact", CONTACT_LABEL, f"{contact_w / 10:.1f}%")
        + "</a></p>",
    ]
    with open(os.path.join(HERE, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts) + "\n")


if __name__ == "__main__":
    main()
