"""Laboratorio font 8x8 per Barbarian's Descent: 10 varianti in stile 'dark fantasy'.
Ogni glifo e' disegnato su una griglia 8x8 (bit 7 = pixel a sinistra)."""
import os
from PIL import Image, ImageDraw

C64 = [(0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189), (139, 63, 150), (85, 160, 73),
       (64, 49, 141), (191, 206, 114), (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80),
       (120, 120, 120), (148, 224, 137), (120, 105, 196), (159, 159, 159)]

# base 5x7 (colonne 0..4)
B = {
"A": ["01110","10001","10001","11111","10001","10001","10001"],
"B": ["11110","10001","10001","11110","10001","10001","11110"],
"C": ["01110","10001","10000","10000","10000","10001","01110"],
"D": ["11110","10001","10001","10001","10001","10001","11110"],
"E": ["11111","10000","10000","11110","10000","10000","11111"],
"F": ["11111","10000","10000","11110","10000","10000","10000"],
"G": ["01110","10001","10000","10111","10001","10001","01111"],
"H": ["10001","10001","10001","11111","10001","10001","10001"],
"I": ["01110","00100","00100","00100","00100","00100","01110"],
"J": ["00111","00010","00010","00010","00010","10010","01100"],
"K": ["10001","10010","10100","11000","10100","10010","10001"],
"L": ["10000","10000","10000","10000","10000","10000","11111"],
"M": ["10001","11011","10101","10101","10001","10001","10001"],
"N": ["10001","11001","10101","10011","10001","10001","10001"],
"O": ["01110","10001","10001","10001","10001","10001","01110"],
"P": ["11110","10001","10001","11110","10000","10000","10000"],
"Q": ["01110","10001","10001","10001","10101","10010","01101"],
"R": ["11110","10001","10001","11110","10100","10010","10001"],
"S": ["01111","10000","10000","01110","00001","00001","11110"],
"T": ["11111","00100","00100","00100","00100","00100","00100"],
"U": ["10001","10001","10001","10001","10001","10001","01110"],
"V": ["10001","10001","10001","10001","10001","01010","00100"],
"W": ["10001","10001","10001","10101","10101","10101","01010"],
"X": ["10001","10001","01010","00100","01010","10001","10001"],
"Y": ["10001","10001","01010","00100","00100","00100","00100"],
"Z": ["11111","00001","00010","00100","01000","10000","11111"],
"0": ["01110","10001","10011","10101","11001","10001","01110"],
"1": ["00100","01100","00100","00100","00100","00100","01110"],
"2": ["01110","10001","00001","00010","00100","01000","11111"],
"3": ["11111","00010","00100","00010","00001","10001","01110"],
"4": ["00010","00110","01010","10010","11111","00010","00010"],
"5": ["11111","10000","11110","00001","00001","10001","01110"],
"6": ["00110","01000","10000","11110","10001","10001","01110"],
"7": ["11111","00001","00010","00100","01000","01000","01000"],
"8": ["01110","10001","10001","01110","10001","10001","01110"],
"9": ["01110","10001","10001","01111","00001","00010","01100"],
".": ["00000","00000","00000","00000","00000","01100","01100"],
",": ["00000","00000","00000","00000","01100","00100","01000"],
":": ["00000","01100","01100","00000","01100","01100","00000"],
"!": ["00100","00100","00100","00100","00100","00000","00100"],
"?": ["01110","10001","00001","00010","00100","00000","00100"],
"-": ["00000","00000","00000","11111","00000","00000","00000"],
"/": ["00001","00001","00010","00100","01000","10000","10000"],
"'": ["00100","00100","01000","00000","00000","00000","00000"],
" ": ["00000"] * 7,
}


def grid(rows, w=5, x0=1, y0=0):
    g = [[0] * 8 for _ in range(8)]
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "1":
                g[y + y0][x + x0] = 1
    return g


def G(s):
    """glifo 8x8 da stringhe con '#'"""
    s = [r.ljust(8, ".")[:8] for r in s] + ["........"] * (8 - len(s))
    return [[1 if c == "#" else 0 for c in r] for r in s]


def copy(g):
    return [r[:] for r in g]


def bold(g):
    o = copy(g)
    for y in range(8):
        for x in range(7):
            if g[y][x]:
                o[y][x + 1] = 1
    return o


def serif(g, ch):
    o = copy(g)
    if ch in " .,:!'-/":
        return o
    # piedini/teste: estremi verticali dei tratti verticali
    for x in range(8):
        col = [g[y][x] for y in range(7)]
        if col[0] and col[1] and not any(g[0][max(0, x - 1):x] + g[0][x + 1:x + 2]):
            if x > 0: o[0][x - 1] = 1
            if x < 7: o[0][x + 1] = 1
        if col[6] and col[5] and not (x > 0 and g[6][x - 1]) and not (x < 7 and g[6][x + 1]):
            if x > 0: o[6][x - 1] = 1
            if x < 7: o[6][x + 1] = 1
    return o


def wedge(g, ch):
    """cuneo: pixel in alto a sinistra di ogni asta che parte dalla riga 0"""
    o = copy(g)
    if ch in " .,:!'-/":
        return o
    for x in range(1, 8):
        if g[0][x] and g[1][x] and not g[0][x - 1]:
            o[0][x - 1] = 1
    return o


def chisel(g):
    o = copy(g)
    for y in range(8):
        for x in range(8):
            if g[y][x]:
                n = sum(g[yy][xx] for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
                        if 0 <= yy < 8 and 0 <= xx < 8) - 1
                if n == 1 and (y in (0, 6)):
                    pass
    return o


def stretch(g):
    """7 righe -> 8: duplica la riga centrale"""
    rows = g[:7]
    return [r[:] for r in rows[:4]] + [rows[3][:]] + [r[:] for r in rows[4:7]]


def slant(g):
    o = [[0] * 8 for _ in range(8)]
    for y in range(8):
        sh = 1 if y < 3 else 0
        for x in range(8):
            if g[y][x] and x + sh < 8:
                o[y][x + sh] = 1
    return o


def spur(g, ch):
    o = copy(g)
    if ch in " .,:!'-/":
        return o
    # sperone a sinistra a meta' altezza delle aste
    for y in (3,):
        for x in range(1, 8):
            if g[y][x] and g[y - 1][x] and g[y + 1][x] and not g[y][x - 1]:
                o[y][x - 1] = 1
                break
    return o


def angular(rows):
    """sostituisce gli angoli arrotondati (01110 / 10001) con smussi a punta"""
    r = rows[:]
    return r


# varianti speciali di O / Q / 0 con croce
CROSS_O = ["01110", "10101", "10101", "11111", "10101", "10101", "01110"]
CROSS_O_DIAG = ["01110", "11011", "10101", "10101", "10101", "11011", "01110"]
CROSS_SQ = ["11111", "10101", "10101", "11111", "10101", "10101", "11111"]
DIAMOND_O = ["00100", "01010", "10001", "11111", "10001", "01010", "00100"]
RUNE_O = ["01110", "10101", "11111", "10101", "10101", "10001", "01110"]


def make_font(style):
    font = {}
    for ch, rows in B.items():
        rows = list(rows)
        name = style["name"]
        if ch in "OQ" and style.get("o"):
            rows = list(style["o"])
            if ch == "Q":
                rows = rows[:6] + ["01101"]
        if style.get("over") and ch in style["over"]:
            rows = list(style["over"][ch])
        g = grid(rows, x0=style.get("x0", 1))
        for t in style["fx"]:
            if t == "bold": g = bold(g)
            elif t == "serif": g = serif(g, ch)
            elif t == "wedge": g = wedge(g, ch)
            elif t == "stretch": g = stretch(g)
            elif t == "slant": g = slant(g)
            elif t == "spur": g = spur(g, ch)
        if ch in "O" and style.get("o8"):
            g = G(style["o8"])
        font[ch] = g
    return font


# ---- override "angolari" (punte invece di curve)
ANG = {
"A": ["00100","01010","10001","11111","10001","10001","10001"],
"C": ["01111","10000","10000","10000","10000","10000","01111"],
"D": ["11100","10010","10001","10001","10001","10010","11100"],
"G": ["01111","10000","10000","10011","10001","10001","01111"],
"S": ["01111","10000","01000","00110","00001","00001","11110"],
"U": ["10001","10001","10001","10001","10001","01010","00100"],
"V": ["10001","10001","10001","01010","01010","00100","00100"],
"B": ["11110","10001","10010","11100","10010","10001","11110"],
}
UNCIAL = {
"A": ["01110","10001","10001","10011","10101","11001","10001"],
"E": ["01110","10001","10000","11110","10000","10001","01110"],
"M": ["01010","10101","10101","10101","10101","10101","10001"],
"N": ["11110","10001","10001","10001","10001","10001","10001"],
"T": ["11111","10101","00100","00100","00100","00100","01110"],
"H": ["10000","10000","10110","11001","10001","10001","10001"],
}

BOLD_CROSS = [".######.", "##.##.##", "##.##.##", "########", "##.##.##", "##.##.##", ".######."]
STYLES = [
    {"name": "01 crocifero",  "fx": ["serif"], "o": CROSS_O},
    {"name": "02 ascia",      "fx": ["wedge", "stretch"], "o": CROSS_O, "over": ANG},
    {"name": "03 cripta",     "fx": ["bold"], "o": CROSS_SQ, "x0": 0, "o8": BOLD_CROSS},
    {"name": "04 runico",     "fx": [], "o": DIAMOND_O, "over": ANG},
    {"name": "05 sigillo",    "fx": ["serif", "stretch"], "o": CROSS_O_DIAG},
    {"name": "06 inferno",    "fx": ["slant"], "o": CROSS_O, "over": ANG},
    {"name": "07 monaco",     "fx": ["stretch"], "o": RUNE_O, "over": UNCIAL},
    {"name": "08 lama",       "fx": ["spur", "stretch"], "o": CROSS_O},
    {"name": "09 forgia",     "fx": ["bold", "wedge"], "o": CROSS_O, "x0": 0, "over": ANG, "o8": BOLD_CROSS},
    {"name": "10 reliquia",   "fx": ["serif"], "o": DIAMOND_O, "over": UNCIAL},
]

LOREM = ["LOREM IPSUM DOLOR SIT AMET,",
         "CONSECTETUR ADIPISCING ELIT.",
         "SED DO EIUSMOD TEMPOR 0123",
         "INCIDIDUNT UT LABORE: 456789!",
         "QUO VADIS, BARBARO? OBLIVION",
         "GOLD 2350  HP 99/117  DMG 41-61"]
WCOL = [7, 3, 10, 13, 15, 14, 8, 5, 1, 4, 12]


def render_screen(font, title, path, scale=2):
    # schermo C64: bordo 32 px + area 320x200
    W, H = 320 + 64, 200 + 64
    img = Image.new("RGB", (W, H), C64[0])
    def put(ch, cx, cy, col):
        g = font.get(ch, font[" "])
        for y in range(8):
            for x in range(8):
                if g[y][x]:
                    img.putpixel((32 + cx * 8 + x, 32 + cy * 8 + y), C64[col])
    def text(s, cx, cy, col):
        for i, ch in enumerate(s):
            put(ch, cx + i, cy, col)
    text("BARBARIAN'S DESCENT", 2, 1, 7)
    text("FONT " + title.upper(), 2, 2, 15)
    text("-" * 36, 2, 3, 11)
    wi = 0
    for li, line in enumerate(LOREM):
        x = 2
        for w in line.split(" "):
            if w:
                text(w, x, 5 + li * 2, WCOL[wi % len(WCOL)])
                wi += 1
            x += len(w) + 1
    text("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 2, 18, 1)
    text("0123456789 .,:!?'-/", 2, 20, 1)
    text("> NEW GAME   LOAD   QUIT", 2, 22, 13)
    img = img.resize((W * scale, H * scale), Image.NEAREST)
    img.save(path)
    return img


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "out", "work", "font")   # anteprime (13/11: in out/work/font/)
    os.makedirs(out, exist_ok=True)
    thumbs = []
    for st in STYLES:
        f = make_font(st)
        p = os.path.join(out, "font_" + st["name"].replace(" ", "_") + ".png")
        thumbs.append(render_screen(f, st["name"], p, scale=2))
    w, h = thumbs[0].size
    sheet = Image.new("RGB", (w * 2, h * 5), (20, 20, 20))
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % 2) * w, (i // 2) * h))
    sheet.save(os.path.join(out, "font_tutti.png"))
    print("ok", len(thumbs))


if __name__ == "__main__":
    main()
