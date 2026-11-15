#!/usr/bin/env python3
"""Fan art: la mappa del mondo di "Barbarian: The Blood Path" in pixel art (15/11, TODO Z2; v2 rifatta a mano il 15/11).
Non e' grafica del gioco (il C64 non la legge): e' un'illustrazione per il manuale, la wiki, la scatola.
Stile: mappa del mondo di un gioco di ruolo a 16/32 bit disegnata a mano. Colori PIENI, bordi netti, contorni di 1 pixel,
ogni trama fatta di piccoli segni ripetuti definiti qui (ciuffi d'erba, onde, canne, ombre sulla neve). Niente rumore,
sfumature, ombreggiature, interpolazioni di colore, trasparenze, antialias (anche il testo: font bitmap 5x7 definito qui).
Geografia: l'angolo sud-ovest di un continente. Il mare sta a ovest e a sud, la terra esce dal quadro in alto e a destra.
Zone: 1 Aldric's Crossing (valle verde e fiume, sud-ovest), 2 Blackwater Mill (lago nero e palude, nord-ovest), 3 The Last
Camp (montagne innevate, centro-est), 4 Ruin's Gate (terra di cenere, mura, cratere dell'Abisso, cittadella, nord-est).
La strada segue il gioco: dal villaggio 1 a nord fino alla palude, lungo la riva sud del lago, a est fino al campo, a nord dal passo,
nel 4 si scende nel cratere.
Tutta la geografia e' data esplicita (punti, poligoni, linee) in cima al file; il caso (seme fisso, sempre la stessa
immagine) serve solo a spargere segni e alberi dentro le aree definite.
Uso: python3 tools/art/world_map.py   ->  out/work/art/world_map.png (1440x900) e world_map_1x.png (480x300)
Serve Pillow (container lab64-tools)."""
import math, os, random
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
W, H, SCALE = 480, 300, 3
SEED = 1987

# ============================================================================ tavolozza (colori pieni, ~55)
PAL = {
    "K": (16, 12, 16), "WHITE": (248, 248, 240),
    "GOLD": (214, 172, 84), "DGOLD": (132, 92, 36), "PGOLD": (246, 226, 160), "RED": (196, 36, 36),
    "DRED": (104, 20, 24), "PLAQ": (40, 28, 32), "PARCH": (232, 214, 170),
    # mare
    "DEEP": (28, 56, 128), "SEA": (52, 100, 176), "WAVE": (110, 156, 220), "FOAM": (224, 246, 250),
    "STEP1": (24, 30, 50),
    # costa
    "SAND": (234, 214, 140), "SAND2": (200, 170, 96),
    # prato e bosco
    "MEAD": (116, 180, 66), "MEAD2": (84, 146, 50), "MEADL": (160, 208, 86),
    "TREE1": (66, 140, 54), "TREE2": (38, 98, 44), "TREEO": (22, 54, 30),
    "YEL": (232, 200, 72), "OCH": (186, 132, 48),
    "BRN": (112, 72, 38), "DBRN": (68, 42, 24), "LBRN": (176, 126, 72),
    # acqua dolce
    "RIV": (104, 176, 234), "RIVB": (40, 92, 172), "CYAN": (110, 226, 236),
    # pietra e case
    "GRY1": (204, 204, 200), "GRY2": (150, 150, 152), "GRY3": (102, 100, 110), "GRY4": (50, 48, 60),
    "ROOF": (186, 52, 40), "ROOFD": (126, 30, 30), "WIN": (252, 222, 92),
    # palude
    "OL1": (86, 96, 46), "OL2": (58, 66, 34), "OL3": (132, 142, 62), "YG": (170, 178, 72),
    "BLK": (12, 16, 16), "ALG": (40, 92, 52), "GWIN": (140, 236, 92),
    # montagne
    "SNOW": (242, 246, 250), "SNSH": (172, 198, 228), "FIR": (36, 84, 60), "FIR2": (22, 54, 40),
    "ORG": (244, 132, 32),
    # cenere e Abisso
    "ASH": (80, 76, 78), "ASH2": (118, 112, 112), "PURD": (64, 20, 84), "VIO": (138, 64, 196),
    "PVIO": (226, 196, 252),
}

# ============================================================================ geografia (pixel logici, x 0..479, y 0..299)
# Costa da nord a est: la terra sta a destra della linea (verso nord-est), il mare a sinistra e sotto.
COAST = [(74, -4), (74, 8), (72, 18), (68, 28), (66, 38), (62, 48), (58, 60), (54, 68), (46, 75), (38, 79), (33, 83), (36, 88),
         (44, 92), (52, 97), (60, 104), (68, 114), (76, 124), (84, 134), (90, 142), (96, 150),
         (90, 158), (80, 166), (68, 174), (58, 184), (50, 196), (54, 206), (60, 220), (70, 236),
         (84, 246), (98, 251), (108, 255), (116, 259), (124, 262), (134, 264), (150, 264), (164, 263), (176, 266),
         (190, 264), (200, 267), (240, 270), (280, 268), (300, 264), (322, 268), (346, 265), (364, 268),
         (384, 264), (404, 268), (428, 266), (452, 269), (484, 268)]
ISLETS = [[(27, 204), (32, 203), (34, 207), (29, 209)], [(36, 213), (40, 212), (41, 216), (37, 216)]]
CAPES = [(40, 84), (50, 196)]                       # coste rocciose (niente sabbia)
BEACH = (200, 280)                                  # spiaggia larga sulla costa sud
CLIFF_X = 300                                       # da qui a est la costa sud e' scogliera

LAKE = [(88, 108), (92, 98), (102, 90), (116, 86), (132, 84), (146, 84), (152, 86), (157, 93), (161, 103),
        (174, 104), (186, 107), (186, 114), (178, 122), (162, 127), (144, 130), (124, 130), (106, 127),
        (98, 124), (92, 118)]
CHANNEL = [(95, 120), (106, 123), (103, 134), (101, 146), (101, 156), (89, 156), (92, 146), (93, 132)]
MARSH = [(68, 72), (90, 60), (116, 56), (150, 56), (176, 62), (196, 74), (208, 94), (208, 116), (198, 132),
         (178, 146), (152, 152), (128, 154), (108, 150), (92, 144), (70, 128), (58, 104)]
SNOW = [(262, 58), (278, 54), (300, 70), (322, 82), (344, 92), (360, 104), (378, 112), (400, 118), (426, 132),
        (452, 146), (484, 150), (484, 304), (396, 304), (380, 254), (354, 226), (330, 204), (300, 186), (282, 172),
        (270, 146), (262, 112), (258, 84)]
ASH = [(290, -4), (484, -4), (484, 146), (452, 142), (430, 130), (410, 118), (390, 112), (370, 106), (352, 98),
       (336, 88), (318, 78), (300, 66), (284, 52), (282, 30)]
WOOD = [(178, 210), (200, 202), (226, 192), (252, 198), (258, 222), (250, 246), (214, 252), (186, 242), (176, 226)]

# (15/11) il fiume nasce ai piedi di una cima a sud del campo, nella neve, e scende a sud-ovest verso la valle
RIVER = [(357, 171), (352, 174), (340, 180), (326, 186), (310, 190), (294, 190), (278, 186), (264, 178),
         (252, 172), (236, 176), (220, 186), (200, 196), (184, 202), (174, 207), (169, 216), (167, 230),
         (160, 242), (146, 249), (132, 251)]
DELTA = [[(132, 251), (126, 255), (119, 263), (116, 268)], [(132, 251), (135, 257), (137, 268)]]

# zona 1
VILLAGE = (150, 218)
CHURCH = (146, 213)                  # centro in basso
CRYPT = (126, 212)
GRAVEYARD = (131, 203, 142, 213)     # recinto x0, y0, x1, y1
HOUSES = [(137, 223), (161, 219), (158, 229), (140, 233), (127, 226)]
SQUARE = (150, 224)
FIELDS = [(102, 232), (118, 232), (102, 242), (118, 242)]   # 14x8, angolo in alto a sinistra
FENCE = ((100, 229), (134, 229))
BRIDGE = (171, 209)
HILLS = [(262, 200, 22, 10), (284, 208, 26, 12), (300, 214, 20, 9), (252, 214, 16, 7),
         (296, 230, 16, 7),
         (228, 160, 18, 8), (246, 150, 16, 7), (212, 40, 18, 8), (232, 50, 20, 9), (196, 26, 14, 6),
         (250, 24, 16, 7), (110, 26, 16, 7)]
# zona 2
HUTS = [(112, 104), (128, 96), (140, 114), (120, 118)]
BELL = (126, 108)
MILL = (167, 99)                     # centro in basso dell'edificio
PIER_E = ((187, 110), (197, 110))
PIER_S = ((138, 131), (138, 126))
# zona 3: cime (x apice, y base, larghezza); fila nord-est, fila sud-ovest e cime di mezzo
PEAKS = [(272, 68, 16), (288, 78, 20), (306, 86, 18), (323, 94, 22), (339, 99, 18),
         (370, 122, 18), (384, 134, 22), (395, 150, 20), (404, 168, 22), (411, 188, 18), (417, 208, 20),
         (423, 228, 16),
         (282, 96, 18), (300, 122, 26), (317, 120, 18), (358, 142, 16), (364, 162, 18), (372, 188, 26),
         (386, 206, 20), (398, 226, 18),
         (295, 90, 14), (312, 102, 14), (330, 108, 14), (390, 180, 16), (404, 212, 14)]
CAMP = (330, 150)
TENTS = [(321, 145), (340, 146), (322, 160), (341, 161)]
CAVE = (338, 128)
PASS = (354, 104)
# zona 4
RING = (392, 74, 35, 30)             # centro, semiassi delle mura
CRATER = (392, 80, 17, 9)
COLUMNS = [(372, 64), (376, 94), (416, 72)]
ANGEL = (414, 92)
CITADEL = (446, 22)
GATEHOUSE = (410, 50)

ROAD = [(152, 221), (156, 214), (158, 200), (154, 186), (148, 172), (143, 160), (140, 148), (139, 138),
        (146, 136), (160, 134), (176, 130), (188, 122), (194, 114), (197, 110)]   # (15/11) lungo la riva sud del lago
ROAD2 = [(197, 110), (214, 116), (234, 124), (254, 133), (274, 141), (294, 148), (312, 152), (322, 152),
         (330, 147), (334, 138), (343, 130), (348, 118), (352, 108), (356, 100), (364, 98), (374, 102),
         (386, 106), (392, 108), (392, 98), (392, 90)]
TRACK = [(157, 210), (164, 209), (178, 209), (188, 213), (198, 214)]   # sentiero di terra verso il bosco

SHIPS = [(30, 150), (214, 284)]
SERPENT = (360, 286)
COMPASS = (40, 256)

# targhe: (x, y in alto a sinistra, numero o None, testo)
LABELS = [(66, 276, 1, "ALDRIC'S CROSSING"), (84, 36, 2, "BLACKWATER MILL"), (300, 222, 3, "THE LAST CAMP"),
          (264, 30, 4, "RUIN'S GATE")]
ABYSS_LABEL = (404, 104)
ABYSS_POINT = ((410, 104), (402, 87))
NUMBERS = [(1, 114, 205), (2, 178, 78), (3, 300, 136), (4, 348, 60)]      # quadratini rossi accanto ai luoghi
LEGEND = (408, 244)

# ============================================================================ tela
C = [["SEA"] * W for _ in range(H)]          # colore (nome della tavolozza) di ogni pixel
T = [["sea"] * W for _ in range(H)]          # terreno di ogni pixel
BLOCK = [[False] * W for _ in range(H)]      # pixel gia' occupati da strade, fiumi, edifici, targhe


def rng(name):
    return random.Random("%d-%s" % (SEED, name))


def inside(x, y):
    return 0 <= x < W and 0 <= y < H


def put(x, y, c):
    if inside(x, y):
        C[y][x] = c


def block_rect(x0, y0, x1, y1):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            BLOCK[y][x] = True


def poly_pixels(pts):
    """pixel col centro dentro il poligono (pari-dispari, nessun antialias)"""
    out, n = [], len(pts)
    ys = [p[1] for p in pts]
    for y in range(max(0, int(min(ys)) - 1), min(H, int(max(ys)) + 2)):
        yc, xs = y + 0.5, []
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
            if (ay <= yc) != (by <= yc):
                xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for x in range(max(0, math.ceil(a - 0.5)), min(W - 1, math.floor(b - 0.5)) + 1):
                out.append((x, y))
    return out


def rough(pts, name, seg=4, amp=1, closed=True):
    """contorno irregolare a gradini: lati spezzati ogni `seg` px, punti spostati di +-amp px interi"""
    r, out = rng(name), []
    n = len(pts) if closed else len(pts) - 1
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
        L = math.hypot(bx - ax, by - ay)
        k = max(1, int(L / seg))
        nx, ny = (-(by - ay) / L, (bx - ax) / L) if L else (0, 0)
        for j in range(k):
            t = j / k
            o = r.randint(-amp, amp) if j else 0
            out.append((round(ax + (bx - ax) * t + nx * o), round(ay + (by - ay) * t + ny * o)))
    if not closed:
        out.append(pts[-1])
    return out


def line(a, b):
    """Bresenham: pixel da a a b compresi"""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, out = dx + dy, []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy


def spline(pts, step=0.25):
    """Catmull-Rom tra i punti dati -> lista di pixel in ordine, 8-connessi, senza doppioni"""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        n = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for j in range(n + 1):
            t = j / n
            q = [0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                        + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in (0, 1)]
            pt = (round(q[0]), round(q[1]))
            if not out:
                out.append(pt)
            elif pt != out[-1]:
                for s in line(out[-1], pt)[1:]:
                    out.append(s)
    # toglie gli angoli a L (scala pulita da pixel art)
    clean = [out[0]]
    for i in range(1, len(out) - 1):
        a, b = clean[-1], out[i + 1]
        if abs(a[0] - b[0]) == 1 and abs(a[1] - b[1]) == 1:
            continue
        clean.append(out[i])
    clean.append(out[-1])
    return clean


def polyline(pts):
    out = []
    for a, b in zip(pts, pts[1:]):
        for s in line(a, b):
            if not out or s != out[-1]:
                out.append(s)
    return out


def distance(src):
    """distanza (chamfer 3-4, circa euclidea) dal pixel True piu' vicino"""
    INF = 10 ** 9
    d = [[0 if src[y][x] else INF for x in range(W)] for y in range(H)]
    for y in range(H):
        row, up = d[y], (d[y - 1] if y else None)
        for x in range(W):
            v = row[x]
            if v:
                if x: v = min(v, row[x - 1] + 3)
                if up:
                    v = min(v, up[x] + 3)
                    if x: v = min(v, up[x - 1] + 4)
                    if x < W - 1: v = min(v, up[x + 1] + 4)
                row[x] = v
    for y in range(H - 1, -1, -1):
        row, dn = d[y], (d[y + 1] if y < H - 1 else None)
        for x in range(W - 1, -1, -1):
            v = row[x]
            if v:
                if x < W - 1: v = min(v, row[x + 1] + 3)
                if dn:
                    v = min(v, dn[x] + 3)
                    if x: v = min(v, dn[x - 1] + 4)
                    if x < W - 1: v = min(v, dn[x + 1] + 4)
                row[x] = v
    return [[v / 3 for v in row] for row in d]


def nb4(x, y):
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


# ============================================================================ disegnini (sprite) e segni
KEY = {"k": "K", "W": "WHITE", "w": "SNOW", "y": "WIN", "r": "ROOF", "R": "ROOFD", "s": "GRY1", "S": "GRY2",
       "d": "GRY3", "D": "GRY4", "b": "BRN", "B": "DBRN", "l": "LBRN", "q": "TREE1", "Q": "TREE2", "z": "TREEO",
       "f": "FIR", "F": "FIR2", "o": "ORG", "e": "RED", "Y": "YEL", "c": "CYAN", "p": "PARCH", "m": "TREE1",
       "M": "TREE2", "t": "BRN", "T": "LBRN", "n": "GWIN", "a": "GOLD", "A": "DGOLD", "g": "FIR2",
       "h": "SNSH", "v": "VIO", "V": "PVIO", "x": "TREE1", "X": "TREE2", "u": "BLK"}


def stamp(x, y, rows, key=None, outline=None):
    """disegna le righe con il loro angolo in alto a sinistra in (x, y); '.' = trasparente; outline: contorno di 1 px"""
    key = key or KEY
    wd = max(len(r) for r in rows)
    if outline:
        for j in range(-1, len(rows) + 1):
            for i in range(-1, wd + 1):
                if 0 <= j < len(rows) and i < len(rows[j]) and i >= 0 and rows[j][i] != ".":
                    continue
                if any(0 <= jj < len(rows) and 0 <= ii < len(rows[jj]) and rows[jj][ii] != "."
                       for ii, jj in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1))):
                    put(x + i, y + j, outline)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != ".":
                put(x + i, y + j, key[ch])


def stamp_cb(cx, by, rows, key=None, outline=None):
    """come stamp, ma (cx, by) e' il centro della riga di base"""
    wd = max(len(r) for r in rows)
    stamp(cx - wd // 2, by - len(rows) + 1, rows, key, outline)


def size(rows):
    return max(len(r) for r in rows), len(rows)


TREE = ["..zzz..", ".zqqqz.", "zqqqqQz", "zqqqQQz", "zQqQQQz", ".zQQQz.", "..zbz..", "...b..."]
TREE_S = [".zzz.", "zqqQz", "zqQQz", ".zzz.", "..b..", "..b.."]
FIRT = ["..w..", ".wwf.", ".ffF.", "wfffF", ".fFF.", "wffFF", "ffFFF", "..b.."]
FIR_S = [".w.", "wfF", ".F.", "fFF", ".b."]
MANGROVE = [".ggg..", "ggggg.", "..gBg.", "...B..", "..B...", ".B.B..", "B...B."]
BURNT = ["k.k..", ".kk.k", "..kk.", "k.k..", ".kk..", "..k..", ".kkk."]
HOUSE = ["...kk...", "..krrk..", ".krrrRk.", "krrrrRRk", "kkkkkkkk", ".kpypBk.", ".kpppBk.", ".kkkkkk."]
CHURCH_S = ["..a..........", ".aaa.........", "..a..........", "..k..........", ".kSk.........",
          ".kSk.........", "kSSDk........", "kSSDk.kkkkk..", "kSSDkkrrrrRk.", "kSySkrrrrrRRk",
          "kSSDkkkkkkkkk", "kSSDkSySySySk", "kSBDkSSSBSSSk", "kkkkkkkkkkkkk"]
CRYPT_S = ["....k....", "...kSk...", "..kSSSk..", ".kkkkkkk.", ".kSDSDSk.", ".kSkkkSk.", ".kSkkkSk.",
         "kkkkkkkkk"]
GCROSS = [".s.", "sSs", ".S.", ".S."]
FOUNTAIN = [".SSS.", "SScSS", ".SSS."]
BRIDGE_S = ["kkkkkkkkkkkkk", "sssssssssssss", "SSSSSSSSSSSSS", "SDDSSDDSSSDDS", "D..DD..DSD..D"]
HUT = ["...kkk...", "..kTTtk..", ".kTTTttk.", "kTTTTtttk", "kkkkkkkkk", ".klBlnlk.", ".klBlnlk.",
       ".kkkkkkk.", "..B...B..", "..B...B.."]
BELLF = ["BBBBB", "B.a.B", "BaaaB", "B...B", "B...B"]
MILL_S = ["....kkkkkkkk...", "...kmmmmmmMMk..", "..kmmMmmmmmMMk.", ".kmmmmmmMmmmMMk", "kmmmmmmmmmmmmMk",
          "kkkkkkkkkkkkkkk", ".kpppBpppBpppk.", ".kpyyBpppBpyyk.", ".kpppBpppBpppk.", ".kpppBpBBBpppk.",
          ".kpppBpBkBpppk.", ".kkkkkkkkkkkkk."]
WHEEL = ["..BBBBB..", ".B..b..B.", "B.b.b.b.B", "B..bbb..B", "Bbbbbbbb.", "B..bbb..B", "B.b.b.b.B",
         ".B..b..B.", "..BBBBB.."]
BOAT = ["...B....", "...B....", "lllllll.", "kbbbbbbk", ".kkkkkk."]
SHIP = [".....e.....", ".....k.....", "...WWkW....", "..WWWkWW...", "..WWWkWWW..", ".WWWWkWWWh.",
        ".hhhhkhhhh.", ".....k.....", "bbbbbbbbbbb", ".bBBBBBBBk.", "..kkkkkkk.."]
TENT = ["....kee..", "....k....", "...klk...", "..kllbk..", ".klllbbk.", "kllBlbbbk", "kkkkkkkkk"]
FIRE = ["..Y..", ".YoY.", ".oYo.", "oeYeo", ".eoe.", "BbBbB"]
TOWER = ["kbkbkbk", "kbbbbbk", ".kbebk.", ".kbbbk.", ".kB.Bk.", ".kBbBk.", ".kB.Bk.", ".kBbBk.", ".kB.Bk.",
         ".kBbBk.", "kkkkkkk"]
BANNER = ["keee", "keee", "kee.", "ke..", "k...", "k...", "k...", "k...", "k..."]
COLUMN = [".s.", "sss", "sSs", "sSs", "sSs", "sSs", "sSs", "SSS"]
ANGEL_S = ["S.....S", "Ss.s.sS", ".sssss.", "..sSs..", "..sSs..", ".sSSSs.", ".sSSSs.", "ddddddd"]
DIG3 = {1: [".#.", "##.", ".#.", ".#.", "###"], 2: ["##.", "..#", ".#.", "#..", "###"],
        3: ["##.", "..#", ".#.", "..#", "##."], 4: ["#.#", "#.#", "###", "..#", "..#"]}

# segni delle trame: (dx, dy, colore)
TUFT = [(0, 0, "MEAD2"), (2, 0, "MEAD2"), (1, 1, "MEAD2")]
TUFT_L = [(0, 0, "MEADL"), (1, -1, "MEADL"), (2, 0, "MEADL")]
WAVE_M = [(0, 0, "WAVE"), (1, 0, "WAVE"), (2, 0, "WAVE")]
REED = [(0, 0, "OL3"), (0, 1, "OL3"), (2, -1, "YG"), (2, 0, "YG")]
REED2 = [(0, 0, "YG"), (0, 1, "YG"), (1, 1, "OL2")]
MIST_M = [(0, 0, "GRY1"), (1, 0, "GRY1"), (2, 0, "GRY1"), (4, 0, "GRY1")]
ALGAE = [(0, 0, "ALG"), (1, 1, "ALG"), (2, 1, "ALG"), (3, 0, "ALG")]
GLINT_M = [(0, 0, "GRY3"), (1, 0, "GRY3")]
SNOW_M = [(0, 0, "SNSH"), (1, 0, "SNSH"), (2, 0, "SNSH")]
SNOW_M2 = [(0, 0, "SNSH"), (1, 0, "SNSH"), (1, -1, "SNSH")]
ASH_M = [(0, 0, "ASH2")]
ASH_K = [(0, 0, "K"), (1, 0, "K")]
SAND_M = [(0, 0, "SAND2")]

# font bitmap 5x7 (larghezza variabile), solo maiuscole
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "J": ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "'": ["#", "#", "#", ".", ".", ".", "."],
    "-": ["....", "....", "....", "####", "....", "....", "...."],
    " ": ["..", "..", "..", "..", "..", "..", ".."],
}


def text_w(s):
    return sum(len(FONT[ch][0]) + 1 for ch in s) - 1


def text(x, y, s, col):
    for ch in s:
        g = FONT[ch]
        for j, r in enumerate(g):
            for i, v in enumerate(r):
                if v == "#":
                    put(x + i, y + j, col)
        x += len(g[0]) + 1


def scatter(name, cell, marks, ok, prob=1.0, bleed=0):
    """un segno per cella di una griglia, in un punto a caso della cella (semina regolare, aria fatta a mano).
    ok(x, y): il pixel puo' ricevere il segno. bleed: quanti pixel del segno possono uscire dall'area (frangia)."""
    r = rng(name)
    for gy in range(0, H, cell):
        for gx in range(0, W, cell):
            x, y = gx + r.randrange(cell), gy + r.randrange(cell)
            m = marks[r.randrange(len(marks))] if isinstance(marks[0], list) else marks
            if r.random() > prob:
                continue
            bad = sum(1 for dx, dy, _ in m if not (inside(x + dx, y + dy) and ok(x + dx, y + dy)))
            if bad > bleed or not ok(x, y):
                continue
            for dx, dy, c in m:
                if inside(x + dx, y + dy) and not BLOCK[y + dy][x + dx]:
                    put(x + dx, y + dy, c)


# ============================================================================ 1. terra, mare, terreni
land = [[False] * W for _ in range(H)]
for x, y in poly_pixels(rough(COAST + [(484, 268), (484, -4)], "coast", seg=4, amp=1)):
    land[y][x] = True
for isl in ISLETS:
    for x, y in poly_pixels(isl):
        land[y][x] = True
channel = set(poly_pixels(rough(CHANNEL, "chan", 3, 1)))
for x, y in channel:
    land[y][x] = False

water = [[not land[y][x] for x in range(W)] for y in range(H)]
d_sea = distance(land)          # nel mare: distanza dalla terra
d_land = distance(water)        # in terra: distanza dal mare

for y in range(H):
    for x in range(W):
        if land[y][x]:
            T[y][x] = "meadow"
for name, poly, ter in (("marsh", MARSH, "marsh"), ("snow", SNOW, "snow"), ("ash", ASH, "ash"),
                        ("lake", LAKE, "lake")):
    for x, y in poly_pixels(rough(poly, name, seg=4, amp=1)):
        if land[y][x]:
            T[y][x] = ter
for x, y in channel:
    T[y][x] = "chan"
for isl in ISLETS:
    for x, y in poly_pixels(isl):
        T[y][x] = "rock"

BASE = {"meadow": "MEAD", "marsh": "OL1", "snow": "SNOW", "ash": "ASH", "lake": "BLK", "rock": "GRY2"}


def coast_kind(x, y):
    """che costa c'e' qui: 'cliff', 'rock' o 'sand'"""
    if x >= CLIFF_X and y > 220:
        return "cliff"
    if any(math.hypot(x - cx, y - cy) < 13 for cx, cy in CAPES) or T[y][x] == "rock":
        return "rock"
    return "sand"


for y in range(H):
    for x in range(W):
        t = T[y][x]
        if t == "sea":
            d = d_sea[y][x]
            C[y][x] = "SEA" if d <= 10 else "DEEP"
        elif t == "chan":
            C[y][x] = "BLK" if y < 136 else ("STEP1" if y < 144 else ("DEEP" if y < 150 else "SEA"))
        else:
            C[y][x] = BASE[t]
            d = d_land[y][x]
            if d <= 3.4 and t in ("meadow", "snow", "marsh"):
                k = coast_kind(x, y)
                wide = 5.4 if BEACH[0] <= x <= BEACH[1] and y > 240 else 2.4
                if k == "cliff":
                    C[y][x] = "GRY4" if d <= 1 else ("GRY3" if d <= 2.4 else C[y][x])
                elif k == "rock":
                    C[y][x] = "GRY3" if d <= 1 else ("GRY2" if d <= 2.4 else C[y][x])
                elif d <= wide and t != "marsh":
                    C[y][x] = "SAND"
            if d > 3.4 and BEACH[0] <= x <= BEACH[1] and y > 240 and d <= 5.4:
                C[y][x] = "SAND"
# isolotti: roccia con un ciuffo verde
for isl in ISLETS:
    px = poly_pixels(isl)
    for x, y in px:
        if any(not land[yy][xx] for xx, yy in nb4(x, y)):
            C[y][x] = "GRY3"
    x, y = px[len(px) // 2]
    put(x, y - 1, "MEAD2"); put(x + 1, y - 1, "MEAD2")

# schiuma: 1 px spezzato contro la terra (non nel canale)
for y in range(H):
    for x in range(W):
        if T[y][x] == "sea" and d_sea[y][x] <= 1.01 and (x * 7 + y * 13) % 9 not in (0, 1):
            C[y][x] = "FOAM"
# contorni netti di 1 px fra i terreni
EDGE = {("lake", "marsh"): "OL2", ("lake", "meadow"): "OL2", ("snow", "meadow"): "SNSH", ("ash", "meadow"): "K",
        ("ash", "snow"): "K", ("marsh", "meadow"): "OL2"}
edge_px = []
for y in range(H):
    for x in range(W):
        t = T[y][x]
        for xx, yy in nb4(x, y):
            if inside(xx, yy) and (T[yy][xx], t) in EDGE and C[y][x] not in ("SAND", "GRY3", "GRY4"):
                edge_px.append((x, y, EDGE[(T[yy][xx], t)]))
                break
for x, y, c in edge_px:
    C[y][x] = c


def is_t(*ters):
    return lambda x, y: T[y][x] in ters and C[y][x] == BASE.get(T[y][x], C[y][x])


# ============================================================================ 2. fiume, strade (prima, cosi' gli alberi le evitano)
river = []
for pts in [RIVER] + DELTA:
    river += spline(pts)
riv_px = set()
for i, (x, y) in enumerate(river):
    if not (inside(x, y) and land[y][x]):
        continue
    for px, py in ((x, y), (x + 1, y)):
        if inside(px, py) and land[py][px]:
            riv_px.add((px, py))
for x, y in riv_px:
    for xx, yy in nb4(x, y):
        if inside(xx, yy) and land[yy][xx] and (xx, yy) not in riv_px and C[yy][xx] != "FOAM":
            C[yy][xx] = "RIVB"
            BLOCK[yy][xx] = True
for x, y in riv_px:
    C[y][x] = "RIV"
    BLOCK[y][x] = True
for i, (x, y) in enumerate(spline(RIVER)):
    if i % 6 == 3 and (x, y) in riv_px:
        C[y][x] = "WHITE"
# sorgente: una pozza di disgelo ai piedi della cima (364, 162), nella neve
stamp(356, 169, [".cccc.", "cRRRRc", ".cRRc."], {"c": "RIVB", "R": "RIV"})

road = polyline(ROAD) + polyline(ROAD2)
for x, y in road:
    block_rect(x - 1, y - 1, x + 1, y + 1)

# ============================================================================ 3. trame (segni ripetuti)
scatter("tuft", 6, [TUFT, TUFT, TUFT_L], is_t("meadow"), bleed=1)
scatter("flower", 13, [[(0, 0, "YEL")], [(0, 0, "WHITE")]], is_t("meadow"), prob=0.5)
scatter("wave", 11, WAVE_M, lambda x, y: T[y][x] == "sea" and d_sea[y][x] > 13 and C[y][x] == "DEEP")
scatter("wave2", 9, [[(0, 0, "FOAM"), (1, 0, "FOAM")]],
        lambda x, y: T[y][x] == "sea" and 4 < d_sea[y][x] < 9 and C[y][x] == "SEA", prob=0.35)
scatter("reed", 5, [REED, REED2], is_t("marsh"), bleed=1)
scatter("mist", 21, MIST_M, is_t("marsh"))
scatter("algae", 9, ALGAE, is_t("lake"))
scatter("glint", 12, GLINT_M, is_t("lake"))
scatter("snow", 8, [SNOW_M, SNOW_M2], is_t("snow"))
scatter("ashs", 6, ASH_M, is_t("ash"), bleed=0)
scatter("ashk", 11, ASH_K, is_t("ash"))
scatter("sand", 5, SAND_M, lambda x, y: C[y][x] == "SAND")
# pozze nere nella palude
r = rng("pools")
for _ in range(140):
    x, y = r.randrange(60, 210), r.randrange(56, 156)
    w = r.choice((3, 4, 5))
    cells = [(x + i, y) for i in range(w)] + [(x + i, y + 1) for i in range(1, w - 1)]
    ring = [(x + i, y - 1) for i in range(1, w - 1)] + [(x - 1, y), (x + w, y), (x, y + 1), (x + w - 1, y + 1)]
    if all(inside(a, b) and T[b][a] == "marsh" and not BLOCK[b][a] for a, b in cells + ring) and r.random() < 0.3:
        for a, b in ring:
            C[b][a] = "OL2"
        for a, b in cells:
            C[b][a] = "BLK"
        block_rect(x - 1, y - 1, x + w, y + 1)
# crepe di lava nella cenere, soprattutto vicino al cratere
r = rng("lava")
cx, cy = CRATER[0], CRATER[1]
for k in range(46):
    ang, rad = r.random() * 6.283, (r.random() ** 1.8) * 80 + 20
    x, y = round(cx + math.cos(ang) * rad * 1.3), round(cy + math.sin(ang) * rad * 0.9)
    n = r.randint(6, 14)
    dx = r.choice((-1, 1))
    for i in range(n):
        if not inside(x, y) or T[y][x] != "ash" or BLOCK[y][x]:
            break
        if i % 5 != 4:
            C[y][x] = "RED" if i % 3 == 2 else "ORG"
        x += dx if r.random() < 0.7 else 0
        y += r.choice((-1, 0, 0, 1))

# ============================================================================ 4. oggetti (ordinati per y di base)
objs = []          # (y base, funzione)


def fits(x0, y0, w, h, ter, margin=0):
    for y in range(y0 - margin, y0 + h + margin):
        for x in range(x0 - margin, x0 + w + margin):
            if not inside(x, y) or BLOCK[y][x] or T[y][x] not in ter:
                return False
    return True


def place(name, sprite, n, area, ter, prob=None, outline=None, margin=0, tries=4000):
    """spargi `sprite` in `area` (poligono), sul terreno `ter`; prob(x, y) = probabilita' di tenere il punto"""
    r = rng(name)
    pts = poly_pixels(area)
    w, h = size(sprite)
    got = 0
    for _ in range(tries):
        if got >= n:
            break
        x, y = pts[r.randrange(len(pts))]
        x0, y0 = x - w // 2, y - h + 1
        if prob and r.random() > prob(x, y):
            continue
        if fits(x0, y0, w, h, ter, margin):
            block_rect(x0, y0, x0 + w - 1, y0 + h - 1)
            objs.append((y, lambda x0=x0, y0=y0: stamp(x0, y0, sprite, outline=outline)))
            got += 1


def obj(by, fn):
    objs.append((by, fn))


# --- zona 2: lago, palafitte, mulino, pontili
def walkways():
    for a, b in zip(HUTS, HUTS[1:] + HUTS[:1]):
        for x, y in line((a[0], a[1] + 1), (b[0], b[1] + 1)):
            if T[y][x] == "lake":
                put(x, y, "LBRN"); put(x, y + 1, "DBRN")


obj(0, walkways)
for hx, hy in HUTS:
    obj(hy, lambda hx=hx, hy=hy: stamp_cb(hx, hy + 3, HUT))
    block_rect(hx - 5, hy - 7, hx + 5, hy + 4)
obj(BELL[1], lambda: stamp_cb(BELL[0], BELL[1] + 2, BELLF))
mx, my = MILL
obj(my, lambda: stamp_cb(mx, my, MILL_S))
obj(my + 1, lambda: stamp_cb(mx - 10, my - 1, WHEEL))
block_rect(mx - 15, my - 12, mx + 8, my + 1)


def piers():
    for (a, b) in (PIER_E, PIER_S):
        for x, y in line(a, b):
            put(x, y, "LBRN")
            if a[1] == b[1]:
                put(x, y + 1, "DBRN")
            else:
                put(x + 1, y, "DBRN")


obj(1, piers)
obj(113, lambda: stamp(PIER_E[0][0] + 1, 110, BOAT))

# --- zona 1: villaggio
gx0, gy0, gx1, gy1 = GRAVEYARD


def graveyard():
    for x in range(gx0, gx1 + 1):
        put(x, gy0, "GRY2"); put(x, gy1, "GRY2")
    for y in range(gy0, gy1 + 1):
        put(gx0, y, "GRY2"); put(gx1, y, "GRY2")
    put(gx0 + 5, gy1, "MEAD")                                    # cancello
    for i, (x, y) in enumerate(((gx0 + 2, gy0 + 2), (gx0 + 6, gy0 + 2), (gx0 + 2, gy0 + 6), (gx0 + 6, gy0 + 6),
                                (gx0 + 9, gy0 + 4))):
        stamp(x, y, GCROSS)


obj(gy1, graveyard)
block_rect(gx0, gy0, gx1, gy1)
obj(CRYPT[1], lambda: stamp_cb(CRYPT[0], CRYPT[1], CRYPT_S))
block_rect(CRYPT[0] - 5, CRYPT[1] - 8, CRYPT[0] + 5, CRYPT[1])
obj(CHURCH[1], lambda: stamp(CHURCH[0] - 2, CHURCH[1] - 13, CHURCH_S))
block_rect(CHURCH[0] - 3, CHURCH[1] - 14, CHURCH[0] + 11, CHURCH[1])


def square():
    sx, sy = SQUARE
    for y in range(sy - 3, sy + 4):
        for x in range(sx - 6, sx + 7):
            if abs(x - sx) + abs(y - sy) * 2 <= 10:
                put(x, y, "GRY1" if (x + y) % 2 else "GRY2")
    stamp_cb(sx, sy + 1, FOUNTAIN)


obj(SQUARE[1] - 4, square)
block_rect(SQUARE[0] - 6, SQUARE[1] - 3, SQUARE[0] + 6, SQUARE[1] + 3)
for hx, hy in HOUSES:
    obj(hy, lambda hx=hx, hy=hy: stamp_cb(hx, hy, HOUSE))
    block_rect(hx - 5, hy - 8, hx + 4, hy)


def fields():
    for fx, fy in FIELDS:
        for y in range(fy, fy + 8):
            for x in range(fx, fx + 14):
                edge = x in (fx, fx + 13) or y in (fy, fy + 7)
                put(x, y, "DBRN" if edge else ("YEL" if (y - fy) % 2 else "OCH"))
    (x0, y0), (x1, _) = FENCE
    for x in range(x0, x1 + 1):
        put(x, y0, "LBRN")
        if (x - x0) % 3 == 0:
            put(x, y0 - 1, "DBRN"); put(x, y0, "DBRN")


obj(0, fields)
block_rect(FIELDS[0][0] - 1, FENCE[0][1] - 1, FIELDS[1][0] + 15, FIELDS[2][1] + 8)


def track():
    for i, (x, y) in enumerate(polyline(TRACK)):
        if i % 3 != 2 and T[y][x] != "sea" and (x, y) not in riv_px:
            put(x, y, "LBRN")
    stamp_cb(BRIDGE[0], BRIDGE[1] + 2, BRIDGE_S)


obj(BRIDGE[1] + 2, track)
for x, y in polyline(TRACK):
    block_rect(x, y, x, y + 1)
block_rect(BRIDGE[0] - 7, BRIDGE[1] - 3, BRIDGE[0] + 7, BRIDGE[1] + 3)


def hill(cx, by, w, h):
    def fn():
        a, pts = w / 2, []
        for x in range(cx - w // 2, cx + w // 2 + 1):
            t = (x - cx) / a
            top = by - round(h * math.sqrt(max(0, 1 - t * t)))
            for y in range(top, by + 1):
                put(x, y, "MEADL")
            pts.append((x, top))
        for x, top in pts:
            put(x, top - 1 if abs(x - cx) < w // 2 else top, "TREEO")
        for i in range(len(pts) - 1):           # chiude i gradini del contorno
            (x0, t0), (x1, t1) = pts[i], pts[i + 1]
            for y in range(min(t0, t1), max(t0, t1)):
                put(x0 if t0 > t1 else x1, y, "TREEO")
        # un segno a mano: piccolo arco interno a destra e due ciuffi
        for k in range(3):
            put(cx + w // 4 + k, by - h // 2 + k // 2, "MEAD2")
        put(cx - w // 4, by - 2, "MEAD2"); put(cx - w // 4 + 2, by - 2, "MEAD2"); put(cx - w // 4 + 1, by - 1, "MEAD2")
    return fn


for hx, hy, hw, hh in HILLS:
    obj(hy - 30, hill(hx, hy, hw, hh))
    block_rect(hx - hw // 2 - 1, hy - hh - 1, hx + hw // 2 + 1, hy)

# --- zona 3: montagne, campo, grotta


def peak(ax, by, w):
    h = round(w * 0.95)
    ay = by - h

    def fn():
        r = rng("peak%d_%d" % (ax, by))
        px = {}
        for y in range(ay, by + 1):
            span = round((y - ay) * (w / 2) / h)
            for x in range(ax - span, ax + span + 1):
                px[(x, y)] = "GRY2" if x <= ax else "GRY3"
        snow_h = round(h * 0.42)
        jag = [r.choice((0, 1, 2, 3)) for _ in range(w + 3)]
        for (x, y) in list(px):
            col = x - (ax - w // 2)
            lim = ay + snow_h + (jag[col // 2 * 2 % len(jag)] if 0 <= col else 0)
            if y <= lim:
                px[(x, y)] = "SNOW" if x <= ax else "SNSH"
        for (x, y), c in px.items():
            put(x, y, c)
        for (x, y) in px:
            if any(q not in px for q in nb4(x, y)) and y < by:
                put(x, y, "GRY4")
        put(ax, ay - 1, "GRY4")
    return fn


for ax, by, w in sorted(PEAKS, key=lambda p: p[1]):
    obj(by, peak(ax, by, w))
    h = round(w * 0.95)
    block_rect(ax - w // 2, by - h, ax + w // 2, by)

cvx, cvy = CAVE


def cave():
    face = ["....dddddd....", "..dddSSddddd..", ".ddSSSddddddd.", "dddSSkkkkdddDd", "ddSSkkkkkkddDD",
            "ddSkkkkkkkkdDD", "dddkkkkkkkkdDD", "DDDkkkkkkkkDDD"]
    stamp_cb(cvx, cvy + 3, face, outline="GRY4")


obj(cvy + 3, cave)
block_rect(cvx - 8, cvy - 5, cvx + 8, cvy + 4)

cx, cy = CAMP


def palisade():
    for k in range(0, 34):
        ang = math.radians(15 + k * 6)              # da sud-est a nord-ovest, passando per sud e ovest
        if 168 <= 15 + k * 6 <= 192:                # porta ovest
            continue
        x, y = round(cx + math.cos(ang) * 20), round(cy + 2 + math.sin(ang) * 15)
        put(x, y - 2, "K"); put(x, y - 1, "BRN"); put(x, y, "DBRN")


obj(cy + 17, palisade)
obj(cy + 3, lambda: stamp_cb(cx, cy + 3, FIRE))
for tx, ty in TENTS:
    obj(ty, lambda tx=tx, ty=ty: stamp_cb(tx, ty, TENT))
obj(cy + 3, lambda: stamp_cb(cx - 22, cy + 6, TOWER))
obj(cy - 6, lambda: stamp(cx + 13, cy - 16, BANNER))
block_rect(cx - 26, cy - 18, cx + 22, cy + 18)

# --- zona 4: mura, cratere, rovine, cittadella
rx0, ry0, ra, rb = RING


def walls():
    gaps = [(80, 100), (200, 214), (300, 312), (20, 28), (140, 146)]
    for k in range(720):
        deg = k / 2
        if any(a <= deg <= b for a, b in gaps):
            continue
        ang = math.radians(deg)
        x, y = round(rx0 + math.cos(ang) * ra), round(ry0 + math.sin(ang) * rb)
        put(x, y + 1, "K"); put(x, y, "GRY1"); put(x, y - 1, "GRY1")
        if y < ry0:
            put(x, y - 2, "K")
    r = rng("blocks")
    for a, b in gaps:
        for _ in range(3):
            ang = math.radians(r.uniform(a, b))
            x = round(rx0 + math.cos(ang) * (ra + r.randint(-3, 4)))
            y = round(ry0 + math.sin(ang) * (rb + r.randint(-3, 4)))
            if abs(x - 392) > 3 or y < 100:
                stamp(x, y, ["ss", "SD"])


obj(ry0 + rb, walls)
crx, cry, ca, cb = CRATER


def crater():
    bands = [(ca, cb, None), (ca - 2, cb - 1, "K"), (ca - 5, cb - 3, "PURD"), (ca - 9, cb - 5, "VIO"),
             (ca - 13, cb - 7, "PVIO")]
    for a, b, col in bands:
        for y in range(cry - b, cry + b + 1):
            for x in range(crx - a, crx + a + 1):
                if ((x - crx) / (a + 0.5)) ** 2 + ((y - cry) / (b + 0.5)) ** 2 <= 1:
                    put(x, y, col if col else ("GRY1" if y < cry else "K"))


obj(cry, crater)
block_rect(crx - ca, cry - cb, crx + ca, cry + cb)
for x, y in COLUMNS:
    obj(y, lambda x=x, y=y: stamp_cb(x, y, COLUMN, outline="K"))
    block_rect(x - 2, y - 9, x + 2, y + 1)
obj(ANGEL[1], lambda: stamp_cb(ANGEL[0], ANGEL[1], ANGEL_S, outline="K"))
block_rect(ANGEL[0] - 5, ANGEL[1] - 9, ANGEL[0] + 5, ANGEL[1] + 1)


def ruins():
    for x, y, w in ((370, 82, 6), (410, 64, 5), (380, 56, 5), (402, 96, 4)):
        for i in range(w):
            put(x + i, y, "GRY2"); put(x + i, y + 1, "K")
        put(x, y - 1, "GRY2"); put(x, y - 2, "GRY2")


obj(60, ruins)
gtx, gty = GATEHOUSE


def gatehouse():
    # due torri spezzate (cima a gradini) e l'arco nero della porta in mezzo
    stamp(gtx - 7, gty - 12, [".d.....", "dSd....", "sSd.d..", "sSddSd.", "sSSSSd.", "sSkkSd.", "sSkkSdd",
                              "sSSSSSd", "sSSSSSd", "sSddSSd", "sSddSSd", "sSddSSd"], outline="K")
    stamp(gtx + 3, gty - 9, ["..d.d", ".dSdd", "sSSSd", "sSkSd", "sSSSd", "sSSSd", "sSSSd", "sSSSd", "sSSSd"],
          outline="K")
    for y in range(gty - 6, gty + 3):
        for x in range(gtx - 1, gtx + 3):
            put(x, y, "GRY3" if y == gty - 6 or x in (gtx - 1, gtx + 2) else ("RED" if y > gty - 2 else "K"))


obj(gty, gatehouse)
block_rect(gtx - 7, gty - 13, gtx + 8, gty + 1)
ctx, cty = CITADEL


def citadel():
    towers = [(-26, 6, 6), (-18, -4, 7), (-8, -16, 8), (2, -8, 7), (12, -24, 8), (22, -2, 7), (30, -18, 8)]
    # muro di base
    for y in range(cty + 2, cty + 14):
        for x in range(ctx - 30, ctx + 40):
            put(x, y, "K")
    for x in range(ctx - 30, ctx + 40, 3):
        put(x, cty + 1, "K")
    for ox, top, w in towers:
        for y in range(cty + top, cty + 14):
            for x in range(ctx + ox, ctx + ox + w):
                put(x, y, "GRY4" if x == ctx + ox else "K")
        for x in range(ctx + ox, ctx + ox + w, 2):
            put(x, cty + top - 1, "K")
        for wy in range(cty + top + 3, cty + 10, 5):
            put(ctx + ox + w // 2, wy, "RED")
    # porta rossa
    for y in range(cty + 6, cty + 14):
        for x in range(ctx - 2, ctx + 3):
            if y > cty + 6 or abs(x - ctx) < 2:
                put(x, y, "RED" if abs(x - ctx) < 2 else "ORG")
    put(ctx, cty + 13, "YEL")


obj(cty + 14, citadel)
block_rect(ctx - 32, 0, W - 1, cty + 15)
place("burnt", BURNT, 26, ASH, ("ash",), margin=1)

# --- alberi, abeti, mangrovie
wx0 = 176
place("wood", TREE, 60, WOOD, ("meadow",), prob=lambda x, y: 1.0 - (x - wx0) / 95)
place("wood_s", TREE_S, 30, WOOD + [(232, 186)], ("meadow",), prob=lambda x, y: 1.0 - (x - wx0) / 110)
place("ne_trees", TREE_S, 10, [(176, 196), (196, 184), (226, 176), (226, 186), (196, 194)], ("meadow",))
place("north_trees", TREE, 22, [(80, 4), (290, 4), (282, 50), (210, 84), (200, 66), (70, 60)], ("meadow",))
place("north_trees_s", TREE_S, 18, [(80, 4), (290, 4), (282, 50), (210, 84), (200, 66), (70, 60)], ("meadow",))
place("se_trees", TREE_S, 14, [(300, 196), (390, 250), (300, 258), (250, 250)], ("meadow",))
place("west_trees", TREE_S, 10, [(60, 150), (110, 160), (130, 196), (100, 230), (60, 222)], ("meadow",))
place("fir_w", FIRT, 40, [(258, 120), (300, 150), (300, 196), (270, 196), (256, 160)], ("snow", "meadow"),
      prob=lambda x, y: 1.0 - abs(x - 280) / 40)
place("fir", FIRT, 40, SNOW, ("snow",))
place("fir_s", FIR_S, 40, SNOW, ("snow",))
place("mangrove", MANGROVE, 22, MARSH, ("marsh",))

# ============================================================================ 5. disegno degli oggetti
for _, fn in sorted(objs, key=lambda o: o[0]):
    fn()

# strada a puntini d'oro: 2 px oro, 1 px scuro sotto, 2 px di vuoto
gold = set()
for path in (polyline(ROAD), polyline(ROAD2)):
    for i, p in enumerate(path):
        if i % 4 in (0, 1):
            gold.add(p)
for x, y in gold:
    put(x, y, "GOLD")
for x, y in gold:
    if (x, y + 1) not in gold:
        put(x, y + 1, "DBRN")

# mare: navi e serpente
for sx, sy in SHIPS:
    stamp_cb(sx, sy + 5, SHIP)
    put(sx - 6, sy + 6, "FOAM"); put(sx + 6, sy + 5, "FOAM"); put(sx + 7, sy + 5, "FOAM")
sx, sy = SERPENT
for i in range(3):
    stamp(sx - 22 + i * 10, sy - 3, ["..kkk..", ".kxxXk.", "kxxXXXk", "kX...Xk"])
    for fx in (-1, 3, 7):
        put(sx - 22 + i * 10 + fx, sy + 1, "FOAM")
stamp(sx + 8, sy - 9, ["..kkkk.", ".kxxxek", "kxxxkk.", "kxXk...", ".kXk...", ".kXk...", ".kXk...", ".kXk...",
                       ".kXXk.."])
put(sx + 7, sy + 1, "FOAM"); put(sx + 13, sy + 1, "FOAM")


# ============================================================================ 6. cornice, targhe, rosa dei venti
def plaque(x0, y0, x1, y1, field="PLAQ"):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x in (x0, x1) or y in (y0, y1):
                c = "K"
            elif x in (x0 + 1, x1 - 1) or y in (y0 + 1, y1 - 1):
                c = "GOLD"
            else:
                c = field
            put(x, y, c)


def num_box(x, y, n, outline=False):
    """quadratino rosso 5x5 (7x7 col contorno) con la cifra bianca"""
    if outline:
        for j in range(7):
            for i in range(7):
                put(x + i - 1, y + j - 1, "K")
    for j in range(5):
        for i in range(5):
            put(x + i, y + j, "RED")
    for j, r in enumerate(DIG3[n]):
        for i, v in enumerate(r):
            if v == "#":
                put(x + 1 + i, y + j, "WHITE")


placed = []


def label(x, y, num, s, col="PARCH"):
    tw = text_w(s)
    w = 2 + 3 + (7 + 3 if num else 0) + tw + 3 + 2
    h = 2 + 3 + 7 + 3 + 2
    plaque(x, y, x + w - 1, y + h - 1)
    tx = x + 5
    if num:
        for j in range(7):
            for i in range(7):
                put(tx + i, y + 5 + j, "RED")
        for j, r in enumerate(DIG3[num]):
            for i, v in enumerate(r):
                if v == "#":
                    put(tx + 2 + i, y + 6 + j, "WHITE")
        tx += 10
    text(tx, y + 5, s, col)
    placed.append((s, x, y, x + w - 1, y + h - 1, tx, tx + tw - 1))
    return x + w - 1, y + h - 1


for n, x, y in NUMBERS:
    num_box(x, y, n, outline=True)
for x, y, n, s in LABELS:
    label(x, y, n, s)
(a, b) = ABYSS_POINT
for x, y in line(a, b):
    put(x, y, "VIO")
label(ABYSS_LABEL[0], ABYSS_LABEL[1], None, "THE ABYSS", "PVIO")

# legenda
lx, ly = LEGEND
plaque(lx, ly, lx + 60, ly + 16)
for i in range(12):
    if i % 4 in (0, 1):
        put(lx + 6 + i, ly + 8, "GOLD"); put(lx + 6 + i, ly + 9, "DBRN")
text(lx + 24, ly + 5, "ROAD", "PARCH")
placed.append(("LEGEND", lx, ly, lx + 60, ly + 16, lx + 24, lx + 24 + text_w("ROAD") - 1))

# titolo
title = "BARBARIAN  -  THE BLOOD PATH"
tw = text_w(title)
tx0 = W // 2 - (tw + 10) // 2
plaque(tx0, 8, tx0 + tw + 9, 24, "DRED")
text(tx0 + 5, 13, title, "PGOLD")
placed.append(("TITLE", tx0, 8, tx0 + tw + 9, 24, tx0 + 5, tx0 + 4 + tw))

# rosa dei venti
ox, oy = COMPASS
for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
    for k in range(2, 13):
        put(ox + dx * k, oy + dy * k, "GOLD")
        if k < 9:
            put(ox + dx * k + dy, oy + dy * k - dx, "DGOLD")
for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
    for k in range(2, 7):
        put(ox + dx * k, oy + dy * k, "PARCH")
for j in range(-2, 3):
    for i in range(-2, 3):
        put(ox + i, oy + j, "K" if max(abs(i), abs(j)) == 2 else "RED")
text(ox - 2, oy - 22, "N", "PARCH")

# cornice doppia
for i, c in enumerate(("K", "GOLD", "DGOLD", "K")):
    for x in range(i, W - i):
        put(x, i, c); put(x, H - 1 - i, c)
    for y in range(i, H - i):
        put(i, y, c); put(W - 1 - i, y, c)
for x0, y0 in ((0, 0), (W - 7, 0), (0, H - 7), (W - 7, H - 7)):
    for j in range(7):
        for i in range(7):
            edge = i in (0, 6) or j in (0, 6)
            put(x0 + i, y0 + j, "K" if edge else ("RED" if 2 <= i <= 4 and 2 <= j <= 4 else "GOLD"))

# ============================================================================ 7. controlli e salvataggio
for s, x0, y0, x1, y1, t0, t1 in placed:
    assert 4 <= x0 and x1 <= W - 5 and 4 <= y0 and y1 <= H - 5, "targa fuori dalla cornice: " + s
    assert t0 - x0 >= 5 and x1 - t1 >= 5, "testo senza margine: " + s
for i, a in enumerate(placed):
    for b in placed[i + 1:]:
        assert a[3] < b[1] or b[3] < a[1] or a[4] < b[2] or b[4] < a[2], "targhe sovrapposte: %s / %s" % (a[0], b[0])

img = Image.new("RGB", (W, H))
img.putdata([PAL[C[y][x]] for y in range(H) for x in range(W)])
out = os.path.join(ROOT, "out", "work", "art")
os.makedirs(out, exist_ok=True)
img.save(os.path.join(out, "world_map_1x.png"))
img.resize((W * SCALE, H * SCALE), Image.NEAREST).save(os.path.join(out, "world_map.png"))
print("world map: out/work/art/world_map.png (%dx%d, %d colori)" % (W * SCALE, H * SCALE,
                                                                    len(img.getcolors(4096))))
