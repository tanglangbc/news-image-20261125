#!/usr/bin/env python3
"""THE WORLD TODAY — Wednesday 25 November 2026.

A one-day newspaper front page summing up 25 November 2026 world news,
drawn as a single 1024x1024 PNG.

Standard library only (no PIL): the program keeps its own pixel buffer and
its own PNG encoder. Deterministic — no clock, no randomness, fixed
compression — so two runs write byte-identical files.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   -> out/entry.png
"""
import os
import struct
import zlib

SIZE = 1024

# ink and paper
PAPER = (245, 241, 232)
NAVY = (20, 33, 61)
INK = (24, 24, 24)
GREY = (90, 90, 90)
FAINT = (180, 172, 155)
WHITE = (255, 255, 255)
TEAL = (14, 116, 110)
LEAF = (34, 139, 60)
EMBER = (214, 92, 20)
ROYAL = (30, 90, 168)
CRIMSON = (178, 34, 34)
PLUM = (106, 76, 147)
BRASS = (201, 162, 39)
SMOKE = (200, 200, 200)
AMBER = (255, 200, 40)

buf = bytearray(PAPER * SIZE * SIZE)


def put(x, y, colour):
    """Paint one pixel of the buffer, clipping to the page."""
    if 0 <= x < SIZE and 0 <= y < SIZE:
        off = (y * SIZE + x) * 3
        buf[off], buf[off + 1], buf[off + 2] = colour


def fill(x, y, w, h, colour):
    """Paint a solid rectangle."""
    for yy in range(y, y + h):
        base = (yy * SIZE + x) * 3
        for xx in range(w):
            o = base + xx * 3
            buf[o], buf[o + 1], buf[o + 2] = colour


def hbar(x0, x1, y, colour, thick=1):
    for yy in range(y, y + thick):
        for xx in range(x0, x1 + 1):
            put(xx, yy, colour)


def vbar(x, y0, y1, colour, thick=1):
    for xx in range(x, x + thick):
        for yy in range(y0, y1 + 1):
            put(xx, yy, colour)


def seg(x0, y0, x1, y1, colour, thick=1):
    """Bresenham segment between two points."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        for a in range(thick):
            for b in range(thick):
                put(x + a, y + b, colour)
        if x == x1 and y == y1:
            return
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def ring(cx, cy, r, colour):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d = (xx - cx) ** 2 + (yy - cy) ** 2
            if r * r - 2 * r <= d <= r * r:
                put(xx, yy, colour)


def dot(cx, cy, r, colour):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                put(xx, yy, colour)


def wedge(x0, y0, x1, y1, x2, y2, colour):
    """Filled triangle, painted scanline by scanline."""
    pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = pts

    def at(p, q, y):
        if q[1] == p[1]:
            return p[0]
        return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])

    for y in range(ay, cy + 1):
        if y <= by:
            lo, hi = at((ax, ay), (bx, by), y), at((ax, ay), (cx, cy), y)
        else:
            lo, hi = at((bx, by), (cx, cy), y), at((ax, ay), (cx, cy), y)
        for x in range(int(min(lo, hi)), int(max(lo, hi)) + 1):
            put(x, y, colour)


# ------------------------------------------------------------------ lettering
# A 5x7 bitmap face. Each glyph is seven rows; each row is a 5-bit number,
# most significant bit on the left (e.g. A opens 01110 = 14).
FACE = {
    'A': (14, 17, 17, 31, 17, 17, 17),
    'B': (30, 17, 17, 30, 17, 17, 30),
    'C': (14, 17, 16, 16, 16, 17, 14),
    'D': (30, 17, 17, 17, 17, 17, 30),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'F': (31, 16, 16, 30, 16, 16, 16),
    'G': (14, 17, 16, 23, 17, 17, 15),
    'H': (17, 17, 17, 31, 17, 17, 17),
    'I': (14, 4, 4, 4, 4, 4, 14),
    'J': (7, 2, 2, 2, 2, 18, 12),
    'K': (17, 18, 20, 24, 20, 18, 17),
    'L': (16, 16, 16, 16, 16, 16, 31),
    'M': (17, 27, 21, 21, 17, 17, 17),
    'N': (17, 25, 21, 19, 17, 17, 17),
    'O': (14, 17, 17, 17, 17, 17, 14),
    'P': (30, 17, 17, 30, 16, 16, 16),
    'Q': (14, 17, 17, 17, 21, 18, 13),
    'R': (30, 17, 17, 30, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'U': (17, 17, 17, 17, 17, 17, 14),
    'V': (17, 17, 17, 17, 17, 10, 4),
    'W': (17, 17, 17, 21, 21, 27, 17),
    'X': (17, 17, 10, 4, 10, 17, 17),
    'Y': (17, 17, 10, 4, 4, 4, 4),
    'Z': (31, 1, 2, 4, 8, 16, 31),
    '0': (14, 17, 19, 21, 25, 17, 14),
    '1': (4, 12, 4, 4, 4, 4, 14),
    '2': (14, 17, 1, 6, 8, 16, 31),
    '3': (31, 2, 4, 2, 1, 17, 14),
    '4': (2, 6, 10, 18, 31, 2, 2),
    '5': (31, 16, 30, 1, 1, 17, 14),
    '6': (6, 8, 16, 30, 17, 17, 14),
    '7': (31, 1, 2, 4, 8, 8, 8),
    '8': (14, 17, 17, 14, 17, 17, 14),
    '9': (14, 17, 17, 15, 1, 2, 12),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '-': (0, 0, 0, 14, 0, 0, 0),
    ',': (0, 0, 0, 0, 4, 4, 8),
    '.': (0, 0, 0, 0, 0, 12, 12),
    "'": (4, 4, 8, 0, 0, 0, 0),
    ':': (0, 12, 12, 0, 12, 12, 0),
    '/': (1, 2, 2, 4, 8, 8, 16),
    '(': (2, 4, 8, 8, 8, 4, 2),
    ')': (8, 4, 2, 2, 2, 4, 8),
    '&': (12, 18, 20, 8, 21, 18, 13),
    '%': (25, 26, 2, 4, 8, 11, 19),
    '+': (0, 4, 4, 31, 4, 4, 0),
    '!': (4, 4, 4, 4, 4, 0, 4),
    '?': (14, 17, 1, 6, 4, 0, 4),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def put_text(x, y, s, scale, colour):
    """Paint a string left-aligned at (x, y)."""
    cx = x
    for ch in s:
        rows = FACE.get(ch, FACE[' '])
        for r, bits in enumerate(rows):
            for col in range(5):
                if bits >> (4 - col) & 1:
                    fill(cx + col * scale, y + r * scale, scale, scale, colour)
        cx += 6 * scale
    return cx


def put_centred(y, s, scale, colour):
    put_text(SIZE // 2 - text_width(s, scale) // 2, y, s, scale, colour)


def wrap_text(s, scale, max_w):
    """Greedy word wrap into lines no wider than max_w."""
    lines, cur = [], ''
    for w in s.split(' '):
        trial = (cur + ' ' + w).strip()
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ pictures
# Each pictogram fills a 160x160 box whose top-left corner is (x, y).

def pic_tower(x, y):
    """Riyadh's tallest tower, struck a second time in a week."""
    cx, cy = x + 80, y + 80
    fill(cx - 26, cy - 52, 52, 112, NAVY)
    for k in range(5):
        fill(cx - 18, cy - 42 + k * 20, 36, 8, BRASS)
    wedge(cx - 26, cy - 52, cx + 26, cy - 52, cx, cy - 72, NAVY)
    dot(cx + 8, cy - 62, 17, EMBER)
    dot(cx - 13, cy - 50, 11, AMBER)
    dot(cx + 24, cy - 42, 9, SMOKE)
    dot(cx - 30, cy - 66, 8, SMOKE)
    hbar(cx - 46, cx + 46, cy + 60, GREY, 6)


def pic_stamp(x, y):
    """A file under investigation: paper, lines of text, a red seal."""
    cx, cy = x + 80, y + 80
    fill(cx - 52, cy - 56, 104, 116, WHITE)
    vbar(cx - 52, cy - 56, cy + 60, INK, 3)
    vbar(cx + 52, cy - 56, cy + 60, INK, 3)
    hbar(cx - 52, cx + 52, cy - 56, INK, 3)
    hbar(cx - 52, cx + 52, cy + 60, INK, 3)
    for k in range(4):
        hbar(cx - 40, cx + 40, cy - 34 + k * 16, GREY, 3)
    ring(cx + 16, cy + 14, 26, CRIMSON)
    ring(cx + 16, cy + 14, 18, CRIMSON)
    fill(cx + 8, cy + 6, 16, 16, CRIMSON)


def pic_chipdown(x, y):
    """A chip with a falling arrow: the comeback rally fades."""
    cx, cy = x + 80, y + 80
    fill(cx - 42, cy - 42, 84, 84, NAVY)
    fill(cx - 26, cy - 26, 52, 52, LEAF)
    fill(cx - 14, cy - 14, 28, 28, WHITE)
    for k in range(4):
        fill(cx - 42 + k * 22, cy - 54, 10, 12, NAVY)
        fill(cx - 42 + k * 22, cy + 42, 10, 12, NAVY)
        fill(cx - 54, cy - 42 + k * 22, 12, 10, NAVY)
        fill(cx + 42, cy - 42 + k * 22, 12, 10, NAVY)
    fill(cx + 29, cy - 58, 10, 34, CRIMSON)
    wedge(cx + 22, cy - 24, cx + 46, cy - 24, cx + 34, cy - 2, CRIMSON)


def pic_jet(x, y):
    """A jet crossing into an air defence zone, seen from above."""
    cx, cy = x + 80, y + 80
    wedge(cx, cy - 58, cx - 14, cy + 10, cx + 14, cy + 10, GREY)
    wedge(cx - 12, cy - 10, cx - 58, cy + 34, cx - 12, cy + 18, GREY)
    wedge(cx + 12, cy - 10, cx + 58, cy + 34, cx + 12, cy + 18, GREY)
    wedge(cx - 10, cy + 10, cx - 22, cy + 44, cx - 2, cy + 30, GREY)
    wedge(cx + 10, cy + 10, cx + 22, cy + 44, cx + 2, cy + 30, GREY)
    dot(cx, cy - 30, 6, CRIMSON)
    for k in range(6):
        hbar(cx - 66 + k * 24, cx - 48 + k * 24, cy + 58, ROYAL, 3)


def pic_store(x, y):
    """A supermarket front with a striped awning and three figures."""
    cx, cy = x + 80, y + 80
    fill(cx - 58, cy - 30, 116, 76, TEAL)
    for k in range(6):
        fill(cx - 58 + k * 20, cy - 46, 20, 16, CRIMSON if k % 2 == 0 else WHITE)
    hbar(cx - 58, cx + 58, cy - 46, INK, 4)
    fill(cx - 40, cy - 8, 26, 54, WHITE)
    fill(cx + 14, cy - 8, 26, 54, WHITE)
    for k in range(3):
        dot(cx - 34 + k * 34, cy + 18, 9, NAVY)
    hbar(cx - 58, cx + 58, cy + 46, INK, 6)


def pic_medal(x, y):
    """The Medal of Freedom: a ribbon and a gold disc with a star."""
    cx, cy = x + 80, y + 80
    wedge(cx - 26, cy - 58, cx - 2, cy - 58, cx - 14, cy - 6, CRIMSON)
    wedge(cx + 2, cy - 58, cx + 26, cy - 58, cx + 14, cy - 6, ROYAL)
    dot(cx, cy + 22, 34, BRASS)
    ring(cx, cy + 22, 26, (150, 110, 10))
    wedge(cx, cy - 2, cx + 7, cy + 16, cx - 7, cy + 16, WHITE)
    wedge(cx, cy + 46, cx + 7, cy + 28, cx - 7, cy + 28, WHITE)


# ------------------------------------------------------------------ the day
# (kicker, accent, pictogram, headline, sub-headline)
STORIES = [
    ("MIDDLE EAST", EMBER, pic_tower,
     "HOUTHIS HIT RIYADH TOWER AGAIN", "SECOND STRIKE IN A WEEK, 11 HURT"),
    ("CHINA", CRIMSON, pic_stamp,
     "CHINA PROBES TOP OFFICIAL", "SHANGHAI CHIEF CHEN JINING HELD"),
    ("TECH", LEAF, pic_chipdown,
     "HUANG IN THERAPY", "NVIDIA COMEBACK RALLY FADES"),
    ("SECURITY", ROYAL, pic_jet,
     "RUSSIAN JETS IN KOREA ZONE", "SEOUL: PLANES IN DEFENCE ZONE"),
    ("COLOMBIA", TEAL, pic_store,
     "HOSTAGE STANDOFF IN CARTAGENA", "25 HELD AFTER FAILED RAID"),
    ("USA", BRASS, pic_medal,
     "TRUMP HONOURS GIULIANI", "MEDAL OF FREEDOM AWARDED"),
]


def draw_page():
    """Paint the masthead, six story panels and the footer."""
    fill(0, 0, SIZE, 128, NAVY)
    put_centred(18, "THE WORLD TODAY", 8, WHITE)
    hbar(0, SIZE - 1, 96, BRASS, 3)
    put_centred(106, "WEDNESDAY, 25 NOVEMBER 2026", 3, BRASS)

    margin, gap = 16, 16
    panel_w = (SIZE - 2 * margin - gap) // 2
    panel_h = (968 - 144 - 2 * gap) // 3
    for i, (kicker, accent, pic, head, sub) in enumerate(STORIES):
        col, row = i % 2, i // 2
        x0 = margin + col * (panel_w + gap)
        y0 = 144 + row * (panel_h + gap)
        fill(x0, y0, panel_w, panel_h, WHITE)
        fill(x0, y0, panel_w, 8, accent)
        hbar(x0, x0 + panel_w - 1, y0 + panel_h - 1, FAINT, 2)
        vbar(x0, y0, y0 + panel_h - 1, FAINT, 2)
        vbar(x0 + panel_w - 1, y0, y0 + panel_h - 1, FAINT, 2)
        put_text(x0 + 18, y0 + 20, kicker, 2, accent)
        pic(x0 + 14, y0 + 66)
        tx = x0 + 184
        max_w = panel_w - 184 - 14
        y = y0 + 76
        for ln in wrap_text(head, 4, max_w):
            put_text(tx, y, ln, 4, INK)
            y += 34
        y += 8
        for ln in wrap_text(sub, 3, max_w):
            put_text(tx, y, ln, 3, GREY)
            y += 26

    hbar(16, SIZE - 17, 984, FAINT, 2)
    put_centred(996, "SIX STORIES . ONE DAY . 25 NOVEMBER 2026", 2, GREY)


# ------------------------------------------------------------------ PNG out
def png_chunk(kind, data):
    body = struct.pack(">I", len(data)) + kind + data
    return body + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def render_png():
    """Encode the buffer as a 1024x1024 RGB PNG (filter: none)."""
    rows = bytearray()
    for y in range(SIZE):
        rows.append(0)
        rows += buf[y * SIZE * 3:(y + 1) * SIZE * 3]
    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", header)
            + png_chunk(b"IDAT", zlib.compress(bytes(rows), 9))
            + png_chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "./out")
    os.makedirs(out_dir, exist_ok=True)
    draw_page()
    data = render_png()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
