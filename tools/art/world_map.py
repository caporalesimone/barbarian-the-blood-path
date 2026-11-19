#!/usr/bin/env python3
"""Fan art: la mappa del mondo di "Barbarian: The Blood Path" (v3, 19/11, approvata dal committente; prima: v2 del 15/11).
Non e' grafica del gioco (il C64 non la legge): e' un'illustrazione per il manuale, la wiki, la scatola.
Stile: pixel art "a 16 bit" ad alta risoluzione: tela logica 960x600 (salvata anche x2 = 1920x1200), rampe di colore con
retino ordinato (niente antialias, niente trasparenze), luce da nord-ovest, ombre a terra retinate, contorni scuri; tono
"crepuscolo" (ombre viola, luci calde) applicato alla mappa, non a targhe e cornice. Testo: font bitmap 5x7 definito qui.
Geografia: l'angolo sud-ovest di un continente, mare a ovest e a sud. Fascia innevata a nord (montagne, il campo), palude a
nord-ovest (Bad Water), valle a sud (Aldric's Hollow), terra di cenere a est in basso (Ruin's Gate, la cittadella, il
cratere di lava con l'Abisso al centro). Fra i biomi una fascia di passaggio con colori suoi (fango, gelo, terra bruciata).
Il percorso rosso tratteggiato segue l'ordine del gioco: 1 -> 2 -> 3 -> 4 -> cittadella -> Abisso.
Città con lo stesso grado di dettaglio (poche case, i segni riconoscibili): chiesa e cripta nel villaggio 1; palafitte,
casa degli spiriti con l'idolo, albero delle bottiglie e il pontile spezzato con le due barche del traghetto a Bad Water.
Geografia data esplicita (punti, poligoni) qui sotto; il caso (semi fissi: sempre la stessa immagine) sparge solo segni e alberi.
Uso: python3 tools/art/world_map.py -> out/work/art/world_map_1x.png (960x600) e world_map.png (1920x1200).
Serve numpy (container lab64-tools: lab64 run python3 tools/art/world_map.py; ./build.sh la genera prima del manuale)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
W, H, SCALE = 960, 600, 2
K = (16, 12, 18)
RS = np.random.RandomState(7)


def S2(pts):
    return [tuple(v * 2 for v in p) for p in pts]


# ------------------------------------------------------------------ geografia
COAST = S2([(74, -4), (74, 8), (72, 18), (68, 28), (66, 38), (62, 48), (58, 60), (54, 68), (46, 75), (38, 79), (33, 83), (36, 88),
            (44, 92), (52, 97), (60, 104), (68, 114), (76, 124), (84, 134), (90, 142), (96, 150),
            (90, 158), (80, 166), (68, 174), (58, 184), (50, 196), (54, 206), (60, 220), (70, 236),
            (84, 246), (98, 251), (108, 255), (116, 259), (124, 262), (134, 264), (150, 264), (164, 263), (176, 266),
            (190, 264), (200, 267), (240, 270), (280, 268), (300, 264), (322, 268), (346, 265), (364, 268),
            (384, 264), (404, 268), (428, 266), (452, 269), (484, 268)])
# (19/11, seconda stesura) neve = una fascia a nord; palude a ovest; capitolo finale a est, in basso; villaggio 1 a sud
MARSH = [(150, 214), (182, 186), (236, 172), (300, 168), (360, 176), (404, 200), (420, 244), (410, 292), (380, 330),
         (330, 350), (270, 354), (214, 344), (172, 318), (148, 270)]
LAKE = [(196, 236), (220, 208), (268, 198), (322, 198), (366, 212), (388, 246), (382, 286), (352, 312), (304, 322),
        (252, 320), (212, 302), (194, 270)]
SNOW = [(120, -8), (968, -8), (968, 196), (910, 206), (850, 190), (780, 180), (710, 186), (640, 180), (570, 166),
        (500, 158), (430, 150), (360, 140), (290, 136), (220, 128), (170, 112), (140, 60)]
ASH = [(968, 186), (968, 560), (776, 560), (744, 500), (716, 440), (696, 380), (684, 320), (694, 262), (726, 218),
       (790, 188), (860, 180), (920, 190)]
WOOD = [(430, 400), (500, 372), (580, 366), (640, 388), (660, 440), (640, 490), (570, 516), (490, 510), (440, 470)]
RIVER = [(598, 172), (590, 200), (572, 236), (548, 270), (520, 300), (486, 326), (452, 352), (424, 384), (404, 420),
         (392, 456), (384, 492), (378, 522), (374, 552)]
BRANCH = [(392, 456), (398, 478), (410, 500), (426, 520), (440, 536), (448, 554)]     # il ramo secondario della foce
FROZEN = (598, 166, 16, 7)                           # laghetto gelato: la sorgente del fiume
VILLAGE = (300, 452)
BRIDGE = (398, 438)
BW = (292, 260)                                      # Bad Water: centro del lago
ENTRY = (256, 334)
EXIT = (392, 258)
ROAD = [(300, 448), (296, 428), (286, 404), (274, 380), (262, 358), (256, 344), ENTRY]
ROAD2 = [EXIT, (412, 250), (440, 228), (470, 202), (500, 178), (522, 160), (540, 146)]
CAMP = (560, 128)
CAVE = (630, 114)
RING = (752, 286, 50, 36)
ROAD3 = [(598, 134), (640, 148), (676, 168), (700, 200), (710, 236), (716, 260), (736, 276)]
CITADEL = (850, 344)
CALD = (836, 464, 84, 44)                            # il cratere con l'Abisso al centro
ROAD4 = [(770, 296), (789, 311), (812, 328), (832, 340)]
ROAD5 = [(852, 352), (850, 372), (842, 392), (836, 410), (836, 424)]
# cime (x dell'apice, y della base, larghezza, altezza, esponente del profilo: < 1 = tonda)
PEAKS = [(250, 112, 92, 84, 0.9), (720, 128, 100, 90, 0.9), (886, 150, 96, 86, 0.85),
         (190, 96, 76, 40, 0.6), (320, 100, 88, 46, 0.6), (400, 112, 92, 48, 0.62), (470, 98, 84, 42, 0.6),
         (640, 92, 84, 46, 0.62), (800, 122, 90, 50, 0.6), (934, 112, 70, 40, 0.6),
         (540, 80, 92, 52, 0.65), (610, 68, 70, 38, 0.6),
         (150, 70, 60, 28, 0.55), (290, 60, 74, 34, 0.55), (360, 64, 64, 30, 0.55), (440, 56, 74, 34, 0.55),
         (700, 70, 74, 36, 0.55), (780, 64, 70, 34, 0.55), (860, 74, 74, 36, 0.55), (930, 60, 60, 30, 0.55),
         (210, 56, 64, 28, 0.55), (480, 138, 54, 24, 0.55), (350, 132, 58, 24, 0.55), (770, 166, 60, 26, 0.55),
         (846, 176, 54, 24, 0.55), (670, 150, 50, 22, 0.55), (940, 176, 50, 22, 0.55)]
PEAKS += [q for (ax, by, w, h, p) in PEAKS if h >= 80 for q in ((int(ax - w * 0.40), by - 2, int(w * 0.6), int(h * 0.5), 0.6),
                                                                  (int(ax + w * 0.42), by - 1, int(w * 0.55), int(h * 0.45), 0.6))]
HILLS = [(640, 262, 48, 22), (668, 300, 40, 18), (612, 334, 44, 20), (440, 250, 44, 20), (400, 290, 40, 18),
         (466, 300, 36, 16), (200, 412, 36, 16), (156, 444, 30, 14), (580, 250, 36, 16), (218, 506, 40, 18),
         (560, 542, 0, 0)][:-1]

# ------------------------------------------------------------------ colori
P = dict(
    SEA=[(14, 26, 82), (18, 40, 108), (26, 60, 138), (36, 86, 168), (54, 116, 196), (82, 152, 216), (124, 192, 230)],
    FOAM=(236, 250, 252),
    MEAD=[(44, 100, 42), (60, 124, 46), (82, 150, 52), (106, 174, 60), (134, 194, 72), (168, 214, 92)],
    WOOD=[(28, 74, 38), (38, 92, 42), (52, 110, 46), (68, 128, 52)],
    MARSH=[(42, 50, 28), (56, 66, 34), (74, 84, 40), (94, 102, 46), (118, 126, 56), (144, 148, 68)],
    LAKE=[(6, 10, 14), (9, 16, 20), (12, 24, 28), (16, 34, 36), (22, 46, 46)],
    SNOW=[(140, 160, 200), (170, 190, 222), (200, 214, 238), (224, 234, 247), (242, 247, 252), (255, 255, 255)],
    ASH=[(24, 20, 24), (36, 32, 36), (52, 48, 52), (70, 66, 70), (92, 86, 88), (116, 108, 108)],
    SAND=[(186, 154, 92), (212, 186, 114), (234, 214, 140), (246, 232, 170)],
    LAVA=[(64, 8, 8), (136, 22, 12), (204, 50, 16), (240, 104, 24), (252, 170, 40), (255, 230, 112)],
    ROCK=[(34, 36, 56), (56, 60, 86), (84, 92, 122), (120, 132, 166), (164, 180, 210), (206, 220, 240), (236, 242, 250),
          (255, 255, 255)],
    STONE=[(40, 36, 44), (64, 60, 68), (92, 88, 96), (124, 120, 126), (160, 156, 158), (196, 192, 190)],
    VOLC=[(18, 12, 16), (40, 26, 28), (66, 44, 42), (96, 66, 56), (130, 92, 72), (164, 122, 92), (196, 154, 116),
          (226, 190, 150)],
    TREE=[(18, 52, 30), (32, 88, 42), (54, 124, 50), (86, 160, 58), (128, 194, 74)],
    TREE2=[(24, 60, 24), (48, 98, 30), (82, 136, 36), (122, 168, 46), (166, 198, 66)],
    PINE=[(12, 40, 36), (22, 66, 52), (36, 96, 68), (60, 128, 86)],
    WOODB=[(52, 30, 18), (84, 52, 28), (120, 78, 40), (160, 110, 60), (196, 146, 86)],
    THATCH=[(74, 52, 22), (110, 80, 32), (150, 114, 46), (190, 152, 66), (222, 190, 96)],
    ROOF=[(88, 18, 22), (132, 28, 28), (180, 46, 36), (216, 78, 52), (238, 120, 82)],
    WALL=[(120, 104, 84), (168, 150, 120), (212, 196, 160), (238, 226, 196)],
    GOLD=[(110, 70, 22), (164, 112, 36), (214, 166, 64), (246, 216, 120), (255, 244, 190)],
    RED=(222, 36, 40), DRED=(96, 10, 22), BONE=(232, 226, 200), BONE2=(168, 158, 132),
    PURP=[(30, 8, 46), (64, 20, 96), (110, 44, 160), (160, 86, 214), (214, 160, 248), (246, 226, 255)],
    PARCH=(232, 214, 170), PARCH2=(190, 164, 116), GWIN=(150, 240, 96), WIN=(255, 224, 96),
)


# ------------------------------------------------------------------ campi
def fbm(seed, base=64, octaves=4):
    rs = np.random.RandomState(seed); out = np.zeros((H, W)); amp, tot, sc = 1.0, 0.0, base
    for _ in range(octaves):
        g = rs.rand(H // sc + 3, W // sc + 3)
        ys, xs = np.arange(H) / sc, np.arange(W) / sc
        y0, x0 = ys.astype(int), xs.astype(int)
        fy, fx = ys - y0, xs - x0
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        a, b, c, d = g[y0][:, x0], g[y0][:, x0 + 1], g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy)[:, None] + (c * (1 - fx) + d * fx) * fy[:, None])
        tot += amp; amp *= 0.5; sc = max(2, sc // 2)
    return out / tot


def pmask(poly):
    im = Image.new("L", (W, H), 0); ImageDraw.Draw(im).polygon(poly, fill=255)
    return np.array(im) > 0


def emask(cx, cy, rx, ry):
    yy, xx = np.mgrid[0:H, 0:W]
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1


def warp(m, amp, seed, base=24):
    dx = ((fbm(seed, base, 3) - 0.5) * 2 * amp).round().astype(int)
    dy = ((fbm(seed + 1, base, 3) - 0.5) * 2 * amp).round().astype(int)
    yy, xx = np.mgrid[0:H, 0:W]
    return m[np.clip(yy + dy, 0, H - 1), np.clip(xx + dx, 0, W - 1)]


def soft(m, r):
    return np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))) / 255.0


def grow(m, n=1):
    for _ in range(n):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    return m


BAY = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
bay = np.tile(BAY, (H // 4 + 1, W // 4 + 1))[:H, :W]
img = np.zeros((H, W, 3), np.uint8)


def ramp(m, v, cols, dith=1.0):
    n = len(cols)
    idx = np.clip(np.floor(np.clip(v, 0, 1) * (n - 1) + (bay - 0.5) * dith + 0.5), 0, n - 1).astype(int)
    img[m] = np.array(cols, np.uint8)[idx[m]]


def lit(e, d=2):
    return e - np.roll(np.roll(e, d, 0), d, 1)


def spline(pts, step=0.5):
    out = []
    p = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        n = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


# ------------------------------------------------------------------ 1. terreni
land = warp(pmask(COAST + [(W + 8, 540), (W + 8, -8)]), 5, 11, 20)
n1, n2, n3, n4 = fbm(1, 96, 5), fbm(2, 40, 4), fbm(3, 16, 3), fbm(4, 8, 2)
elev = 0.6 * n1 + 0.3 * n2 + 0.1 * n3
yy, xx = np.mgrid[0:H, 0:W]


def biome(poly, seed, r=13, k=0.55):
    """campo del bioma: 1 dentro, 0 fuori, con il bordo sfumato e rotto dal rumore (macchie da una parte e dall'altra)"""
    return soft(pmask(poly), r) + (fbm(seed, 18, 3) - 0.5) * k + (n4 - 0.5) * 0.14


bm, bs, ba = biome(MARSH, 21, 11, 0.5), biome(SNOW, 41, 15, 0.6), biome(ASH, 51, 15, 0.6)
ash = (ba > 0.5) & land
snow = (bs > 0.5) & land & ~ash
marsh = (bm > 0.5) & land & ~snow & ~ash
lake = warp(pmask(LAKE), 5, 31, 18) & land
wood = warp(pmask(WOOD), 8, 61) & land & ~ash & ~snow
frozen = warp(emask(*FROZEN), 2, 71, 10)
sea = ~land
# mare: fondale dalla distanza dalla costa + onde lunghe
dcoast = soft(land, 26)
swell = 0.5 + 0.5 * np.sin((yy * 0.33 + xx * 0.05) + n2 * 9)
ramp(sea, 0.06 + dcoast * 1.75 + (n1 - 0.5) * 0.30 + (swell - 0.5) * 0.07, P["SEA"])
img[sea & grow(land, 3) & (bay < 0.6)] = P["SEA"][6]
img[sea & grow(land, 1)] = P["FOAM"]
# terra: prato con luce da nord-ovest
ramp(land, 0.48 + lit(elev, 3) * 17 + (n2 - 0.5) * 0.42 + (n4 - 0.5) * 0.10, P["MEAD"])
ramp(wood, 0.4 + lit(elev, 3) * 22 + (n3 - 0.5) * 0.5, P["WOOD"])
ew = soft(wood, 7)
ramp(land & ~wood & (ew > 0.18 + bay * 0.5), 0.8 + (n3 - 0.5) * 0.4, P["WOOD"])
dsea = soft(sea, 4)
beach = land & (dsea > 0.16 + (n3 - 0.5) * 0.22) & ~snow & ~ash
# --- passaggi: ogni bioma ha una fascia di mezzo con colori suoi, larga e irregolare
MUDG = [(70, 84, 38), (86, 108, 44), (98, 130, 48), (110, 150, 54)]
FROST = [(96, 140, 92), (132, 170, 116), (172, 200, 150), (208, 224, 192), (232, 240, 226)]
SCORCH = [(52, 44, 40), (74, 62, 46), (98, 86, 52), (122, 112, 58), (140, 140, 66)]
SLATE = [(64, 60, 72), (96, 94, 110), (134, 134, 154), (174, 178, 200), (212, 218, 236)]
tm = land & ~marsh & ~snow & ~ash & (bm > 0.30)
ramp(tm, 1 - (bm - 0.30) / 0.20 + (n4 - 0.5) * 0.3, MUDG, 1.4)
ramp(marsh, 0.42 + lit(elev, 3) * 20 + (n2 - 0.5) * 0.6 + (n4 - 0.5) * 0.15, P["MARSH"])
ramp(marsh & (bm < 0.62), 0.78 + (n3 - 0.5) * 0.4, P["MARSH"], 1.4)
tf = land & ~snow & ~ash & (bs > 0.26)
ramp(tf, (bs - 0.26) / 0.24 + (n4 - 0.5) * 0.35, FROST, 1.5)
ramp(snow, 0.66 + lit(elev, 3) * 30 + (n2 - 0.5) * 0.35 + (n4 - 0.5) * 0.08, P["SNOW"])
ramp(snow & (bs < 0.64), 0.30 + (bs - 0.5) / 0.14 * 0.4 + (n3 - 0.5) * 0.3, P["SNOW"], 1.5)
tsn = snow & (bs < 0.58) & (n3 > 0.56)               # ciuffi d'erba che bucano la neve al margine
img[tsn & (bay < 0.5)] = FROST[1]
ts = land & ~ash & ~snow & (ba > 0.26)
ramp(ts, 1 - (ba - 0.26) / 0.24 + (n4 - 0.5) * 0.35, SCORCH, 1.5)
tsl = snow & (ba > 0.26)
ramp(tsl, 1 - (ba - 0.26) / 0.24 + (n4 - 0.5) * 0.3, SLATE, 1.5)
ramp(ash, 0.42 + lit(elev, 3) * 26 + (n2 - 0.5) * 0.45 + (n4 - 0.5) * 0.12, P["ASH"])
ramp(ash & (ba < 0.64), 0.72 + (n3 - 0.5) * 0.4, P["ASH"], 1.5)
ramp(beach, 0.25 + dsea * 1.6 + (n4 - 0.5) * 0.3, P["SAND"])
# scogliera: una fascia scura sotto la terra dove guarda a sud (rilievo)
cl = sea & (np.roll(land, 1, 0) | np.roll(land, 2, 0))
img[cl & np.roll(land, 1, 0)] = (70, 52, 44)
img[cl & ~np.roll(land, 1, 0)] = (34, 30, 52)
# crepe di brace nella cenere, piu' fitte verso il cratere
dc = np.hypot((xx - CALD[0]) / 1.4, yy - CALD[1])
crack = ash & (ba > 0.7) & (np.abs(fbm(81, 28, 3) - 0.5) < 0.006 + 0.016 * np.clip(1 - dc / 220, 0, 1))
ramp(crack, 0.35 + np.clip(1 - dc / 300, 0, 1) * 0.6 + (n4 - 0.5) * 0.3, P["LAVA"])
img[ash & grow(crack, 1) & ~crack & (bay < 0.5)] = (84, 30, 26)
# lago nero
water = lake & land
dl = soft(~water, 7)
ramp(water, 0.9 - dl * 1.5 + (n3 - 0.5) * 0.5, P["LAKE"])
img[grow(water, 1) & ~water & land] = (30, 34, 20)
img[grow(water, 3) & ~grow(water, 1) & land & (bay < 0.5)] = (44, 50, 26)
ramp(frozen & land, 0.5 + (n3 - 0.5) * 0.9, [(126, 190, 226), (160, 214, 240), (198, 234, 250), (230, 248, 255)])
img[grow(frozen, 1) & ~frozen & land] = (150, 170, 206)

occ = np.zeros((H, W), bool)                         # occupato: niente alberi qui


def block(x0, y0, x1, y1):
    occ[max(0, int(y0)):int(y1) + 1, max(0, int(x0)):int(x1) + 1] = True


# segni delle trame
def marks(mask, n, shapes, seed):
    rs = np.random.RandomState(seed)
    ys, xs = np.nonzero(mask[2:-2, 2:-4])
    if not len(ys):
        return
    for k in rs.choice(len(ys), min(n, len(ys)), replace=False):
        y, x = ys[k] + 2, xs[k] + 2
        sh = shapes[rs.randint(len(shapes))]
        if all(mask[y + dy, x + dx] for dx, dy, _ in sh):
            for dx, dy, c in sh:
                img[y + dy, x + dx] = c


mead = land & ~marsh & ~snow & ~ash & ~beach & ~water & ~tf & ~ts
G = P["MEAD"]
marks(mead, 5200, [[(0, 0, G[1]), (2, 0, G[1]), (1, 1, G[1])], [(0, 0, G[5]), (1, -1, G[5]), (2, 0, G[5])],
                   [(0, 0, G[0]), (1, 0, G[0])], [(0, 0, G[5]), (1, 0, G[5])]], 5)
marks(mead, 420, [[(0, 0, (250, 230, 90))], [(0, 0, (250, 250, 250))], [(0, 0, (240, 120, 150))],
                  [(0, 0, (250, 230, 90)), (2, 1, (250, 230, 90))]], 6)
M = P["MARSH"]
marks(marsh & ~water, 2600, [[(0, 0, M[5]), (0, 1, M[5]), (2, -1, (176, 184, 76)), (2, 0, (176, 184, 76))],
                             [(0, 0, M[0]), (1, 0, M[0]), (2, 0, M[0])], [(0, 0, (176, 184, 76)), (0, 1, M[4])],
                             [(0, 0, (10, 16, 18)), (1, 0, (10, 16, 18)), (2, 0, (10, 16, 18)), (1, 1, (10, 16, 18))]], 7)
marks(water, 700, [[(0, 0, (30, 78, 48)), (1, 1, (30, 78, 48)), (2, 1, (30, 78, 48)), (3, 0, (30, 78, 48))],
                   [(0, 0, (60, 70, 76)), (1, 0, (60, 70, 76))], [(0, 0, (44, 110, 60)), (1, 0, (44, 110, 60))]], 8)
SN = P["SNOW"]
marks(snow, 2600, [[(0, 0, SN[1]), (1, 0, SN[1]), (2, 0, SN[1])], [(0, 0, SN[0]), (1, 0, SN[0])],
                   [(0, 0, SN[5]), (1, 0, SN[5]), (1, -1, SN[5])], [(0, 0, SN[1]), (1, 0, SN[1]), (1, -1, SN[1])]], 9)
A_ = P["ASH"]
marks(ash, 3200, [[(0, 0, A_[5])], [(0, 0, A_[0]), (1, 0, A_[0])], [(0, 0, A_[4]), (1, 0, A_[4]), (0, 1, A_[1])],
                  [(0, 0, (150, 60, 30))]], 10)
marks(beach, 500, [[(0, 0, P["SAND"][0])], [(0, 0, (250, 244, 210))]], 11)
SE = P["SEA"]
marks(sea & ~grow(land, 3), 2100, [[(0, 0, SE[5]), (1, 0, SE[5]), (2, 0, SE[5]), (3, 0, SE[5]), (1, 1, SE[1]), (2, 1, SE[1])],
                                   [(0, 0, SE[6]), (1, 0, SE[6]), (2, 0, SE[6])],
                                   [(0, 0, SE[5]), (1, -1, SE[5]), (2, -1, SE[5]), (3, 0, SE[5])],
                                   [(0, 0, SE[4]), (1, 0, SE[4])]], 12)

im = Image.fromarray(img)
dr = ImageDraw.Draw(im)
objs = []


def obj(y, fn):
    objs.append((y, len(objs), fn))


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        im.putpixel((int(x), int(y)), c)


# ------------------------------------------------------------------ 2. fiume e strade
def rivers(parts):
    """parts: [(punti, larghezza, allarga alla foce)]: tutti i rami insieme, un colore alla volta, cosi' si saldano"""
    sps = [(spline(p, 0.5), w_, fl) for p, w_, fl in parts]
    for d_, col in ((2, (24, 60, 120)), (0, (60, 130, 208)), (-2, (116, 186, 236))):
        for sp, w_, fl in sps:
            for i, (x, y) in enumerate(sp):
                t = i / len(sp)
                r = max(0.6, (w_ * (0.5 + 0.5 * t) * (1 + fl * max(0, t - 0.86) * 5) + d_) / 2)
                dr.ellipse((x - r, y - r, x + r, y + r), fill=col)
    for sp, w_, fl in sps:
        for i, (x, y) in enumerate(sp[::9]):
            if i % 2:
                px(x, y, (220, 244, 252)); px(x + 1, y, (220, 244, 252))
        for x, y in sp[::2]:
            block(x - 5, y - 5, x + 5, y + 5)


rivers([(RIVER, 7, 0.5), (BRANCH, 4.5, 0.6)])
_a = np.array(im)                                    # il fiume finisce alla costa: il mare torna com'era, con la schiuma alla foce
_m = (_a != img).any(2) & sea
_a[sea] = img[sea]
_a[_m & grow(land, 2)] = P["FOAM"]
_a[_m & ~grow(land, 2) & grow(land, 7) & (bay < 0.5)] = P["SEA"][6]
im = Image.fromarray(_a)
dr = ImageDraw.Draw(im)


def road_block(pts):
    for x, y in spline(pts, 1.0):
        block(x - 5, y - 6, x + 5, y + 4)


def road(pts):
    sp = spline(pts, 1.0)
    for i, (x, y) in enumerate(sp):
        if i % 11 < 6:
            dr.rectangle((x - 1, y - 1, x + 2, y + 2), fill=P["DRED"])
    for i, (x, y) in enumerate(sp):
        if i % 11 < 6:
            dr.rectangle((x - 1, y - 1, x + 1, y + 1), fill=P["RED"])
            px(x - 1, y - 1, (255, 120, 110))


# ------------------------------------------------------------------ 3. oggetti: figure base
def sprite(rows, key):
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.uint8)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != "." and ch != " ":
                a[j, i] = tuple(key[ch]) + (255,)
    return Image.fromarray(a)


def paste(sp, x, y):
    im.paste(sp, (int(x), int(y)), sp)


def paste_cb(sp, cx, by):
    paste(sp, cx - sp.size[0] // 2, by - sp.size[1] + 1)


def outline(a, col=K):
    m = a[:, :, 3] > 0
    o = grow(np.pad(m, 1), 1)[1:-1, 1:-1] & ~m
    a[o] = tuple(col) + (255,)
    return a


def blob(r, cols, seed, squash=0.92):
    s = 2 * r + 5
    rs = np.random.RandomState(seed)
    a = np.zeros((s, s, 4), np.uint8)
    yy_, xx_ = np.mgrid[0:s, 0:s]
    c = s // 2
    dx, dy = (xx_ - c) / r, (yy_ - c) / (r * squash)
    wob = 1 + 0.16 * np.sin(np.arctan2(dy, dx) * 5 + rs.rand() * 6) + 0.08 * np.sin(np.arctan2(dy, dx) * 9 + rs.rand() * 6)
    ins = dx * dx + dy * dy <= wob
    v = 0.55 - 0.42 * dx - 0.55 * dy + (rs.rand(s, s) - 0.5) * 0.35
    n = len(cols)
    idx = np.clip(np.floor(v * (n - 1) + (np.tile(BAY, (s // 4 + 1, s // 4 + 1))[:s, :s] - 0.5) * 0.9 + 0.5), 1, n - 1).astype(int)
    a[ins, :3] = np.array(cols, np.uint8)[idx[ins]]
    a[ins, 3] = 255
    return outline(a, cols[0])


TREES = [Image.fromarray(blob(r, P[c], s)) for s, (r, c) in enumerate(((6, "TREE"), (7, "TREE"), (5, "TREE2"), (6, "TREE2"), (5, "TREE"), (7, "TREE2")))]
BUSH = [Image.fromarray(blob(3, P["TREE"], 30 + s)) for s in range(3)]


def shadow(cx, by, rx, ry, col):
    """ombra a terra: un'ellisse retinata piu' scura"""
    for y in range(int(by - ry), int(by + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if 0 <= x < W and 0 <= y < H and ((x - cx) / rx) ** 2 + ((y - by) / ry) ** 2 <= 1 and (x + y) % 2 == 0:
                r_, g_, b_ = im.getpixel((x, y))
                im.putpixel((x, y), (int(r_ * col), int(g_ * col), int(b_ * col)))


def tree(cx, by, k):
    sp = TREES[k % len(TREES)]
    shadow(cx + 3, by, sp.size[0] // 2 - 1, 2, 0.6)
    dr.rectangle((cx - 1, by - 4, cx, by), fill=P["WOODB"][1]); px(cx - 1, by - 3, P["WOODB"][3])
    paste_cb(sp, cx, by - 3)


def pine_sprite(h, snowy, seed):
    w = h * 2 // 3 | 1
    a = np.zeros((h + 3, w + 2, 4), np.uint8)
    c = w // 2 + 1
    cols = P["PINE"]
    for y in range(h):
        tier = (y % (h // 3 + 1)) / (h // 3 + 1)
        base = (y / h) * 0.55 + 0.25
        hw = max(0, int(round((0.35 + 0.65 * tier) * base * w / 1.1)))
        for x in range(c - hw, c + hw + 1):
            dxx = (x - c) / max(1, hw)
            col = cols[3] if dxx < -0.45 else cols[2] if dxx < 0.1 else cols[1]
            if snowy and (dxx < -0.2 and tier < 0.5 or y < 2):
                col = (240, 246, 252) if dxx < -0.5 or y < 2 else (190, 208, 232)
            a[y, x] = col + (255,)
    a[h:h + 3, c - 1:c + 1] = P["WOODB"][1] + (255,)
    return Image.fromarray(outline(a, cols[0]))


PINES = [pine_sprite(h, s, i) for i, (h, s) in enumerate(((17, True), (14, True), (19, True), (15, False), (18, False)))]


def pine(cx, by, k, snowy=True):
    sp = PINES[k % 3] if snowy else PINES[3 + k % 2]
    shadow(cx + 3, by, 5, 2, 0.72 if snowy else 0.6)
    paste_cb(sp, cx, by)


DEAD = sprite(["k...k..k.", ".k.k..k..", "..kk.k...", "...kkk...", "k...k....", ".kkkk....", "...kk....", "...kk....",
               "..kkkk..."], {"k": (20, 14, 16)})
MANG = sprite(["..ggg....", ".gGGgg...", "gGGGGGg..", ".gGGGg.g.", "..gbg.gGg", "...b...b.", "..b.b.b..", ".b...b..."],
              {"g": (20, 52, 34), "G": (40, 88, 50), "b": (58, 40, 24)})
MANG2 = sprite([".gg..", "gGGg.", "gGGGg", ".gbg.", ".b.b."], {"g": (20, 52, 34), "G": (46, 96, 54), "b": (58, 40, 24)})


def dome(cx, by, w, h, cols, edge):
    a = np.zeros((h + 2, w + 2, 4), np.uint8)
    yy_, xx_ = np.mgrid[0:h + 2, 0:w + 2]
    dx, dy = (xx_ - w / 2 - 1) / (w / 2), (yy_ - h - 1) / h
    ins = (dx * dx + dy * dy <= 1) & (yy_ <= h)
    v = 0.62 - 0.5 * dx - 0.75 * (dy + 0.5)
    n = len(cols)
    idx = np.clip(np.floor(v * (n - 1) + (np.tile(BAY, (h // 4 + 2, w // 4 + 2))[:h + 2, :w + 2] - 0.5) + 0.5), 0, n - 1).astype(int)
    a[ins, :3] = np.array(cols, np.uint8)[idx[ins]]; a[ins, 3] = 255
    return Image.fromarray(outline(a, edge))


def hill(cx, by, w, h):
    shadow(cx + w // 4, by + 1, w // 2, 3, 0.7)
    paste_cb(dome(cx, by, w, h, P["MEAD"], P["MEAD"][0]), cx, by)
    block(cx - w // 2, by - h, cx + w // 2, by + 2)


def peak(ax, by, w, h, seed, kind="snow", p=0.9):
    """cima: faccia in luce a sinistra della cresta, in ombra a destra, neve in alto, roccia a strisce in basso"""
    rs = np.random.RandomState(seed)
    pw, ph = w + 12, h + 2
    a = np.zeros((ph, pw, 4), np.uint8)
    yy_, xx_ = np.mgrid[0:ph, 0:pw]
    x0 = 6 + w * 0.46
    t = np.clip((yy_ + 1) / h, 0, 1)
    jl = np.cumsum(rs.randint(-1, 2, ph)) * 0.7; jr = np.cumsum(rs.randint(-1, 2, ph)) * 0.7
    tp = t[:, 0] ** p                                # p < 1: spalle larghe, cima tonda
    jl -= jl[0]; jr -= jr[0]
    zig = np.cumsum(rs.choice([-1, 0, 1, 1], ph)) * 0.9
    bow = np.sin(t[:, 0] * math.pi) * w * (rs.rand() * 0.10 - 0.02)          # fianchi un po' concavi o convessi
    xl = (x0 - tp * (w * 0.46) + np.clip(jl, -4, 4) * t[:, 0] + bow)[:, None]
    xr = (x0 + tp * (w * 0.54) + np.clip(jr, -4, 4) * t[:, 0] - bow * 0.6)[:, None]
    xm = (x0 + np.clip(zig, -3, w * 0.16) * t[:, 0] ** 0.7)[:, None]
    ins = (xx_ >= xl) & (xx_ <= xr) & (yy_ < h)
    nz = rs.rand(ph // 3 + 2, pw // 3 + 2).repeat(3, 0).repeat(3, 1)[:ph, :pw]
    isl = xx_ < xm
    per = 9 + rs.randint(0, 8)
    spur = ((xx_ - xm) * (np.where(isl, -1, 1)) + yy_ * (0.4 + rs.rand() * 0.4) + nz * 6) % per < 1.5      # costoni
    v = np.where(isl, 0.98 - 0.42 * t - 0.12 * nz, 0.52 - 0.30 * t - 0.10 * nz)
    v = np.where(spur & (t > 0.22), v - np.where(isl, 0.22, 0.14), v)
    v = np.where(np.abs(xx_ - xm) < 1, v - 0.1, v)
    if kind == "snow":
        cols = np.array(P["ROCK"], np.uint8)
        rock = (t > 0.5 + nz * 0.3) & spur | (t > 0.82 + nz * 0.12)
        v = np.where(rock, v - 0.2, v)
    else:
        cols = np.array(P["VOLC"], np.uint8)
        v = v * 0.92 + 0.06
    n = len(cols)
    b_ = np.tile(BAY, (ph // 4 + 1, pw // 4 + 1))[:ph, :pw]
    idx = np.clip(np.floor(np.clip(v, 0, 1) * (n - 1) + (b_ - 0.5) * 0.6 + 0.5), 0, n - 1).astype(int)
    a[ins, :3] = cols[idx[ins]]; a[ins, 3] = 255
    if kind == "volc":
        gl = ins & (np.abs((xx_ - xm) + (yy_ * 0.2)) % 17 < 1) & (t > 0.55) & ~isl
        a[gl, :3] = (214, 70, 20)
    sp = Image.fromarray(outline(a, tuple(int(c) for c in cols[0])))
    # ombra portata a destra
    for y in range(by - h // 3, by + 3):
        ext = int((y - (by - h // 3)) * 0.9)
        for x in range(ax + w // 2 - 2, ax + w // 2 + 4 + ext // 2):
            if 0 <= x < W and 0 <= y < H and (x + y) % 2 == 0:
                r_, g_, b2 = im.getpixel((x, y)); im.putpixel((x, y), (int(r_ * 0.72), int(g_ * 0.76), int(b2 * 0.86)))
    paste(sp, ax - int(x0), by - h)
    block(ax - w // 2 - 2, by - h * 0.55, ax + w // 2 + 4, by + 3)


def house(x, by, w=14, h=8, roof="ROOF", wall="WALL", win=True):
    R, Wc = P[roof], P[wall]
    shadow(x + w // 2 + 3, by + 1, w // 2 + 1, 2, 0.62)
    dr.rectangle((x - 1, by - h - 1, x + w, by + 1), fill=K)
    dr.rectangle((x, by - h, x + w - 1, by), fill=Wc[2])
    dr.rectangle((x + w - 4, by - h, x + w - 1, by), fill=Wc[1])
    dr.line((x, by, x + w - 1, by), fill=Wc[0])
    rh = h - 1
    dr.polygon([(x - 2, by - h), (x + w + 1, by - h), (x + w - 3, by - h - rh), (x + 2, by - h - rh)], fill=K)
    for j in range(rh):
        y = by - h - 1 - j
        xa = x - 1 + j * 3 // rh; xb = x + w - j * 3 // rh
        dr.line((xa, y, xb, y), fill=R[2 if j % 2 else 1])
        dr.line((xa, y, xa + (xb - xa) // 3, y), fill=R[3 if j % 2 else 2])
    dr.line((x + 3, by - h - rh, x + w - 4, by - h - rh), fill=R[4])
    dr.rectangle((x + w // 2 - 1, by - 4, x + w // 2, by), fill=P["WOODB"][0])
    if win:
        dr.rectangle((x + 2, by - 5, x + 3, by - 4), fill=P["WIN"]); dr.rectangle((x + w - 4, by - 5, x + w - 3, by - 4), fill=P["WIN"])
    block(x - 3, by - h - rh - 2, x + w + 3, by + 3)


def tower(x, by, w, h, cols, spire=None, win=None):
    dr.rectangle((x - 1, by - h - 1, x + w, by + 1), fill=K)
    dr.rectangle((x, by - h, x + w - 1, by), fill=cols[2])
    dr.rectangle((x, by - h, x + max(0, w // 4 - 1), by), fill=cols[3])
    dr.rectangle((x + w - max(1, w // 3), by - h, x + w - 1, by), fill=cols[1])
    for i in range(x - 1, x + w + 1, 2):
        dr.rectangle((i, by - h - 3, i, by - h - 1), fill=cols[2] if i < x + w - 2 else cols[1]); px(i, by - h - 4, K)
    if spire:
        dr.polygon([(x - 2, by - h - 2), (x + w + 1, by - h - 2), (x + w // 2, by - h - 4 - w)], fill=K)
        dr.polygon([(x - 1, by - h - 3), (x + w // 2, by - h - 3), (x + w // 2, by - h - 2 - w)], fill=spire[1])
        dr.polygon([(x + w // 2, by - h - 3), (x + w, by - h - 3), (x + w // 2, by - h - 2 - w)], fill=spire[0])
    if win:
        for yy_ in range(by - h + 4, by - 3, 7):
            dr.rectangle((x + w // 2 - 1, yy_, x + w // 2 - 1, yy_ + 2), fill=win)


# ------------------------------------------------------------------ 4. Bad Water (dettaglio come il villaggio 1)
IDOL = sprite(["w.....w", "ww...ww", ".wWWWw.", ".WkWkW.", ".WWWWW.", "..WkW..", "..kbk..", "...b...", "...b...", "..gbg..",
               "...b...", "..kbk.."], {"w": (240, 236, 214), "W": (214, 206, 176), "k": K, "b": (96, 62, 30), "g": (150, 240, 96)})
BTREE = sprite(["k...k...k", ".k..k..k.", "g.k.k.k.g", "g..kkk..g", ".g.kbk.g.", "g..kbk..g", "g...b...g", "....b....",
                "...kbk..."], {"k": (26, 18, 14), "b": (70, 44, 24), "g": (120, 240, 110)})
FERRY = sprite(["......g......", ".....kkk.....", "....kTTTk....", "...kTTTTTk...", "....k...k....", "k...k...k...k",
                "kbk.k...k.kbk", ".kbbbbbbbbbk.", "..kBBBBBBBk..", "...kkkkkkk..."],
               {"k": K, "g": (150, 240, 96), "T": (190, 152, 66), "b": (160, 110, 60), "B": (104, 66, 34)})
PLK = [(196, 146, 86), (160, 110, 60), (120, 78, 40), (70, 44, 24)]


def planks(x0, y0, x1, y1):
    """passerella o assito: assi chiare, bordo scuro, pali nell'acqua"""
    dr.rectangle((x0 - 1, y0 - 1, x1 + 1, y1 + 2), fill=K)
    dr.rectangle((x0, y0, x1, y1), fill=PLK[1]); dr.line((x0, y0, x1, y0), fill=PLK[0]); dr.line((x0, y1 + 1, x1, y1 + 1), fill=PLK[3])
    if x1 - x0 >= y1 - y0:
        for x in range(x0 + 2, x1, 4):
            dr.line((x, y0 + 1, x, y1), fill=PLK[2])
        for x in range(x0 + 1, x1, 7):
            dr.line((x, y1 + 2, x, y1 + 4), fill=PLK[3])
    else:
        for y in range(y0 + 2, y1, 3):
            dr.line((x0 + 1, y, x1 - 1, y), fill=PLK[2])


def stilt_hut(x, by, w=14, spirit=False):
    T = [(30, 60, 30), (48, 92, 40), (74, 126, 50), (110, 158, 64), (150, 190, 86)] if spirit else P["THATCH"]
    h = 7 if not spirit else 9
    for sx in (x + 1, x + w // 2, x + w - 2):          # i pali e il riflesso
        dr.line((sx, by, sx, by + 5), fill=PLK[3]); px(sx, by + 6, (30, 44, 44))
    dr.rectangle((x - 2, by - 1, x + w + 1, by + 1), fill=K); dr.line((x - 1, by, x + w, by), fill=PLK[0])
    dr.rectangle((x - 1, by - h - 1, x + w, by - 1), fill=K)
    dr.rectangle((x, by - h, x + w - 1, by - 1), fill=P["WOODB"][2]); dr.rectangle((x + w - 4, by - h, x + w - 1, by - 1), fill=P["WOODB"][1])
    rh = h
    dr.polygon([(x - 3, by - h), (x + w + 2, by - h), (x + w - 3, by - h - rh - 1), (x + 2, by - h - rh - 1)], fill=K)
    for j in range(rh):
        y = by - h - 1 - j
        xa = x - 2 + j * 4 // rh; xb = x + w + 1 - j * 4 // rh
        dr.line((xa, y, xb, y), fill=T[2 if j % 2 else 1]); dr.line((xa, y, xa + (xb - xa) * 2 // 5, y), fill=T[3 if j % 2 else 2])
    dr.line((x + 3, by - h - rh, x + w - 4, by - h - rh), fill=T[4])
    cx = x + w // 2
    dr.rectangle((cx - 1, by - 4, cx, by - 1), fill=(14, 10, 10))
    wl = P["GWIN"] if spirit else P["WIN"]
    dr.rectangle((x + 2, by - 5, x + 3, by - 4), fill=wl); dr.rectangle((x + w - 4, by - 5, x + w - 3, by - 4), fill=wl)
    if spirit:                                         # la maschera-teschio cornuta sopra la porta
        dr.rectangle((cx - 2, by - h - 3, cx + 2, by - h), fill=P["BONE"]); px(cx - 1, by - h - 2, K); px(cx + 1, by - h - 2, K)
        for d_ in (-1, 1):
            px(cx + d_ * 3, by - h - 4, P["BONE"]); px(cx + d_ * 4, by - h - 5, P["BONE"])


def bad_water():
    cx, cy = BW
    # passerelle (prima: stanno sotto le capanne)
    def walk():
        planks(254, 314, 258, 336)                     # il pontile dalla riva, spezzato
        planks(254, 268, 258, 278)
        planks(240, 256, 286, 267)                     # l'assito di mezzo, con l'albero delle bottiglie
        planks(228, 240, 231, 262); planks(228, 259, 240, 262)          # verso la capanna a nord-ovest
        planks(218, 284, 221, 290); planks(218, 264, 240, 267); planks(218, 264, 221, 284)   # verso ovest
        planks(286, 258, 392, 261)                     # la passerella est, fino all'uscita
        planks(300, 236, 303, 258)                     # capanna a nord
        planks(322, 261, 325, 286)                     # locanda
        planks(350, 244, 353, 258)                     # casa degli spiriti
    obj(200, walk)
    obj(240, lambda: stilt_hut(220, 240, 16))
    obj(236, lambda: stilt_hut(294, 236, 14))
    obj(292, lambda: stilt_hut(208, 292, 14))
    obj(294, lambda: stilt_hut(314, 294, 22))
    obj(246, lambda: stilt_hut(340, 246, 26, True))
    obj(252, lambda: paste_cb(IDOL, 332, 250))
    obj(258, lambda: paste_cb(BTREE, 264, 258))
    obj(312, lambda: paste_cb(FERRY, 256, 312))
    obj(290, lambda: paste_cb(FERRY, 256, 290))
    for x, y in ((246, 300), (268, 284), (300, 270), (372, 252), (238, 250)):          # pali con i teschi
        obj(y, lambda x=x, y=y: (dr.line((x, y - 4, x, y + 2), fill=PLK[3]), dr.rectangle((x - 1, y - 6, x + 1, y - 5), fill=P["BONE"]),
                                  px(x, y - 5, K)))
    for x, y in ((242, 254), (284, 254), (330, 256)):  # lanterne verdi
        obj(y, lambda x=x, y=y: (dr.line((x, y - 4, x, y), fill=K), px(x, y - 5, P["GWIN"]), px(x - 1, y - 5, (60, 140, 60)),
                                  px(x + 1, y - 5, (60, 140, 60))))
    block(cx - 104, cy - 70, cx + 104, cy + 78)


bad_water()


# ------------------------------------------------------------------ 5. zona 1: Aldric's Hollow
def village1():
    vx, vy = VILLAGE
    # piazza di ciottoli e fontana
    for y in range(vy + 2, vy + 14):
        for x in range(vx - 12, vx + 14):
            if ((x - vx) / 13) ** 2 + ((y - vy - 8) / 6) ** 2 <= 1:
                px(x, y, P["STONE"][4 if (x + y * 2) % 5 else 3])
    obj(vy + 12, lambda: (dr.ellipse((vx - 4, vy + 5, vx + 4, vy + 11), fill=P["STONE"][2], outline=K),
                          dr.ellipse((vx - 2, vy + 6, vx + 2, vy + 9), fill=(96, 178, 236)), px(vx, vy + 5, (236, 250, 252)),
                          px(vx, vy + 4, (236, 250, 252))))
    # chiesa con il campanile
    cx, cy = vx - 14, vy - 6

    def church():
        S = P["STONE"]
        shadow(cx + 22, cy + 1, 16, 3, 0.62)
        house(cx + 6, cy, 22, 12, "ROOF", "WALL")
        for x in (cx + 10, cx + 16, cx + 22):
            dr.rectangle((x, cy - 9, x + 1, cy - 5), fill=P["WIN"]); px(x, cy - 10, (255, 240, 170))
        tower(cx - 4, cy, 9, 30, [S[1], S[2], S[4], S[5]], spire=(P["ROOF"][1], P["ROOF"][3]), win=P["WIN"])
        dr.line((cx, cy - 47, cx, cy - 52), fill=P["GOLD"][3]); dr.line((cx - 2, cy - 50, cx + 2, cy - 50), fill=P["GOLD"][3])
        dr.rectangle((cx - 1, cy - 5, cx + 1, cy), fill=P["WOODB"][0])
    obj(cy, church)
    block(cx - 8, cy - 54, cx + 34, cy + 4)
    # cimitero con la cripta
    gx, gy = vx - 58, vy - 22

    def grave():
        dr.rectangle((gx, gy, gx + 34, gy + 22), fill=(60, 110, 50))
        for x in range(gx, gx + 35, 2):
            px(x, gy, P["STONE"][1]); px(x, gy + 22, P["STONE"][1]); px(x, gy - 1, P["STONE"][3]); px(x, gy + 21, P["STONE"][3])
        for y in range(gy, gy + 23, 2):
            px(gx, y, P["STONE"][2]); px(gx + 34, y, P["STONE"][2])
        for i, (ox, oy) in enumerate(((5, 5), (12, 4), (19, 6), (6, 13), (13, 14), (26, 5), (27, 14), (20, 15))):
            x, y = gx + ox, gy + oy
            dr.rectangle((x, y, x + 2, y + 3), fill=P["STONE"][4]); px(x + 1, y - 1, P["STONE"][5]); px(x + 2, y + 3, P["STONE"][2])
            px(x + 4, y + 3, (40, 80, 40))
    obj(gy + 22, grave)
    block(gx - 2, gy - 3, gx + 36, gy + 24)

    def crypt():
        x, y = gx - 22, gy + 20
        S = P["STONE"]
        shadow(x + 12, y + 1, 9, 2, 0.62)
        dr.rectangle((x - 1, y - 11, x + 15, y + 1), fill=K)
        dr.rectangle((x, y - 10, x + 14, y), fill=S[3]); dr.rectangle((x + 10, y - 10, x + 14, y), fill=S[2])
        dr.polygon([(x - 2, y - 10), (x + 16, y - 10), (x + 7, y - 18)], fill=K)
        dr.polygon([(x, y - 11), (x + 7, y - 11), (x + 7, y - 16)], fill=S[5]); dr.polygon([(x + 7, y - 11), (x + 14, y - 11), (x + 7, y - 16)], fill=S[4])
        dr.rectangle((x + 5, y - 6, x + 9, y), fill=(10, 8, 12)); dr.line((x + 7, y - 21, x + 7, y - 17), fill=S[5]); dr.line((x + 6, y - 20, x + 8, y - 20), fill=S[5])
        block(x - 3, y - 22, x + 18, y + 3)
    obj(gy + 20, crypt)
    for i, (ox, oy, rf) in enumerate(((-30, 16, "ROOF"), (20, 2, "ROOF"), (24, 22, "ROOF"), (-22, 34, "ROOF"), (-48, 22, "ROOF"),
                                      (2, 32, "ROOF"), (40, 10, "ROOF"))):
        obj(vy + oy, lambda ox=ox, oy=oy, rf=rf: house(vx + ox, vy + oy, 14 + (ox % 3) * 2, 8, rf))
        block(vx + ox - 4, vy + oy - 18, vx + ox + 22, vy + oy + 4)
    # ponte di pietra
    bx, by = BRIDGE

    def bridge():
        S = P["STONE"]
        dr.rectangle((bx - 14, by - 5, bx + 14, by + 3), fill=K)
        dr.rectangle((bx - 13, by - 4, bx + 13, by - 1), fill=S[4]); dr.line((bx - 13, by - 4, bx + 13, by - 4), fill=S[5])
        dr.rectangle((bx - 13, by, bx + 13, by + 2), fill=S[2])
        for x in (bx - 7, bx + 1):
            dr.rectangle((x, by, x + 5, by + 2), fill=(30, 70, 140)); dr.line((x, by, x + 5, by), fill=K)
        for x in range(bx - 12, bx + 13, 4):
            px(x, by - 5, S[5]); px(x, by - 6, K)
    obj(by + 3, bridge)
    block(bx - 16, by - 8, bx + 16, by + 5)


village1()


# ------------------------------------------------------------------ 6. zona 3: montagne e campo
def camp():
    cx, cy = CAMP

    def palisade(front):
        for a in range(0, 360, 5):
            if (a > 180) != front or 60 < a < 100:
                continue
            x = cx + int(40 * math.cos(math.radians(a))); y = cy + int(20 * math.sin(math.radians(a)))
            dr.rectangle((x - 1, y - 7, x + 1, y), fill=K); dr.line((x, y - 6, x, y), fill=P["WOODB"][2]); px(x, y - 7, (240, 246, 252))
    obj(cy - 21, lambda: palisade(True))
    obj(cy + 21, lambda: palisade(False))

    def tent(x, y, col):
        dr.polygon([(x - 8, y), (x + 8, y), (x, y - 11)], fill=K)
        dr.polygon([(x - 6, y - 1), (x, y - 1), (x, y - 9)], fill=col[3]); dr.polygon([(x, y - 1), (x + 6, y - 1), (x, y - 9)], fill=col[1])
        dr.polygon([(x - 1, y - 1), (x + 1, y - 1), (x, y - 5)], fill=(20, 14, 12)); dr.line((x, y - 14, x, y - 10), fill=K)
        px(x + 1, y - 14, P["RED"]); px(x + 2, y - 14, P["RED"]); px(x + 1, y - 13, P["RED"])
    for i, (ox, oy) in enumerate(((-18, -6), (16, -8), (-20, 10), (18, 10), (0, -12))):
        obj(cy + oy, lambda ox=ox, oy=oy, i=i: tent(cx + ox, cy + oy, P["WOODB"] if i % 2 else P["THATCH"]))

    def fire():
        dr.ellipse((cx - 4, cy + 2, cx + 4, cy + 6), fill=(70, 60, 60))
        dr.polygon([(cx - 2, cy + 4), (cx + 2, cy + 4), (cx, cy - 3)], fill=(244, 132, 32)); px(cx, cy + 2, (255, 230, 112)); px(cx, cy + 1, (255, 230, 112))
        px(cx - 1, cy - 5, (200, 200, 210)); px(cx + 1, cy - 8, (220, 220, 230))
    obj(cy + 6, fire)

    def watch():
        x, y = cx - 34, cy + 6
        dr.line((x - 3, y, x - 2, y - 16), fill=K); dr.line((x + 3, y, x + 2, y - 16), fill=K)
        dr.rectangle((x - 5, y - 22, x + 5, y - 16), fill=K); dr.rectangle((x - 4, y - 21, x + 4, y - 17), fill=P["WOODB"][3])
        dr.polygon([(x - 6, y - 22), (x + 6, y - 22), (x, y - 28)], fill=P["WOODB"][1])
    obj(cy + 7, watch)
    block(cx - 46, cy - 34, cx + 46, cy + 24)

    def cave():
        x, y = CAVE
        R = P["ROCK"]
        dr.ellipse((x - 13, y - 14, x + 13, y + 8), fill=K)
        dr.ellipse((x - 12, y - 13, x + 12, y + 7), fill=R[3]); dr.pieslice((x - 12, y - 13, x + 12, y + 7), 180, 300, fill=R[5])
        dr.ellipse((x - 7, y - 8, x + 7, y + 8), fill=(8, 8, 14))
        dr.rectangle((x - 14, y + 1, x + 14, y + 9), fill=None)
        for i in (-5, 0, 4):
            dr.line((x + i, y - 7, x + i, y - 5 + abs(i) % 3), fill=R[6])
    obj(CAVE[1] + 2, cave)
    block(CAVE[0] - 16, CAVE[1] - 16, CAVE[0] + 16, CAVE[1] + 8)


camp()
for i, (ax, by, w, h, pp) in enumerate(PEAKS):
    obj(by, lambda ax=ax, by=by, w=w, h=h, i=i, pp=pp: peak(ax, by, w, h, 100 + i, "snow", pp))
    block(ax - w // 2 - 2, by - h * 0.5, ax + w // 2 + 4, by + 3)
for hx, hy, hw, hh in HILLS:
    obj(hy, lambda a=(hx, hy, hw, hh): hill(*a))
    block(hx - hw // 2, hy - hh, hx + hw // 2, hy + 2)


# ------------------------------------------------------------------ 7. zona 4: Ruin's Gate, l'Abisso, la caldera con la cittadella
def ruins_gate():
    cx, cy, rx, ry = RING
    S = P["STONE"]

    def wall(front):
        for a in range(0, 360, 1):
            if (0 < a < 180) != front:
                continue
            if a % 90 in range(34, 52) and a < 300 or 255 < a < 285:
                continue                               # brecce e la porta a nord
            x = cx + int(rx * math.cos(math.radians(a))); y = cy + int(ry * math.sin(math.radians(a)))
            hgt = 7 if a % 14 > 2 else 9
            dr.rectangle((x - 2, y - hgt - 1, x + 2, y + 1), fill=K)
            dr.rectangle((x - 1, y - hgt, x + 1, y), fill=S[4] if a > 120 and a < 300 else S[3]); px(x, y - hgt, S[5])
            if a % 6 == 0:
                px(x, y - hgt // 2, S[1])
        for a in (20, 70, 115, 160, 205, 250, 290, 335):
            if (0 < a < 180) != front:
                continue
            x = cx + int(rx * math.cos(math.radians(a))); y = cy + int(ry * math.sin(math.radians(a)))
            tower(x - 3, y + 1, 7, 13 + a % 5, [S[0], S[1], S[3], S[5]])
    obj(cy - ry, lambda: wall(False))
    obj(cy + ry + 2, lambda: wall(True))

    def houses():
        for ox, oy in ((-32, -12), (22, -18), (-24, 18), (26, 14), (-6, -26), (-4, 4)):
            x, y = cx + ox, cy + oy
            dr.rectangle((x - 1, y - 9, x + 11, y + 1), fill=K); dr.rectangle((x, y - 8, x + 10, y), fill=S[2])
            dr.polygon([(x, y - 8), (x + 4, y - 8), (x, y - 13)], fill=S[3]); dr.rectangle((x + 4, y - 4, x + 6, y), fill=(10, 8, 12))
            px(x + 8, y - 6, (240, 120, 40))
        tower(cx + 6, cy + 4, 7, 22, [S[0], S[1], S[3], S[5]])          # la torre spezzata al centro
    obj(cy + 1, houses)
    block(cx - rx - 6, cy - ry - 16, cx + rx + 6, cy + ry + 6)


ruins_gate()


def citadel():
    """la cittadella su uno sperone, fra Ruin's Gate e il cratere"""
    x, y = CITADEL
    V = P["VOLC"]

    def draw():
        shadow(x + 18, y + 6, 40, 5, 0.6)
        dr.polygon([(x - 40, y + 8), (x - 30, y - 8), (x - 8, y - 14), (x + 16, y - 12), (x + 34, y - 4), (x + 42, y + 8),
                    (x + 22, y + 14), (x - 18, y + 14)], fill=K)
        dr.polygon([(x - 37, y + 7), (x - 28, y - 6), (x - 8, y - 12), (x + 15, y - 10), (x + 32, y - 3), (x + 39, y + 7),
                    (x + 21, y + 12), (x - 17, y + 12)], fill=V[2])
        dr.polygon([(x - 37, y + 7), (x - 28, y - 6), (x - 8, y - 12), (x - 2, y + 2), (x - 17, y + 12)], fill=V[4])
        dr.line((x - 28, y - 6, x - 8, y - 12), fill=V[6])
        y0 = y - 6
        C = [(10, 8, 14), (26, 20, 34), (44, 36, 56), (72, 62, 88)]
        sp = ((120, 20, 30), (180, 40, 40))
        win = (255, 120, 40)
        tower(x - 24, y0 - 2, 8, 30, C, spire=sp, win=win)
        tower(x + 18, y0, 8, 34, C, spire=sp, win=win)
        dr.rectangle((x - 17, y0 - 21, x + 19, y0 + 3), fill=K)
        dr.rectangle((x - 16, y0 - 20, x + 18, y0 + 2), fill=C[2]); dr.rectangle((x - 16, y0 - 20, x - 12, y0 + 2), fill=C[3])
        dr.rectangle((x + 10, y0 - 20, x + 18, y0 + 2), fill=C[1])
        for i in range(x - 16, x + 19, 3):
            dr.rectangle((i, y0 - 23, i + 1, y0 - 21), fill=C[2]); px(i, y0 - 24, K); px(i + 1, y0 - 24, K)
        tower(x - 6, y0 - 14, 13, 40, C, spire=sp, win=win)
        tower(x - 13, y0 - 6, 6, 22, C, spire=sp, win=win); tower(x + 9, y0 - 6, 6, 24, C, spire=sp, win=win)
        dr.rectangle((x - 2, y0 - 6, x + 3, y0 + 2), fill=(255, 150, 40)); dr.rectangle((x - 1, y0 - 7, x + 2, y0 - 6), fill=(255, 150, 40))
        dr.rectangle((x - 1, y0 - 4, x + 2, y0 + 2), fill=(120, 20, 10))
        for wx, wy in ((-12, -12), (-9, -6), (12, -13), (14, -5), (-3, -18), (4, -16)):
            px(x + wx, y0 + wy, win); px(x + wx, y0 + wy + 1, (200, 50, 20))
        for i in range(9):
            px(x + 1 + (i * 5) % 7 - 3, y0 - 72 - i * 3, (90, 80, 90) if i % 2 else (120, 110, 118))
    obj(y + 14, draw)
    block(x - 44, y - 84, x + 46, y + 18)


citadel()


def caldera():
    """il cratere di lava; al centro, su uno scoglio, l'Abisso (ci si arriva dopo la cittadella)"""
    cx, cy, rx, ry = CALD
    V = P["VOLC"]
    rs = np.random.RandomState(3)

    def rim(front):
        n = 22
        for i in (range(n) if not front else sorted(range(n), key=lambda q: abs(q - n / 2 + 0.5), reverse=True)):
            a = math.pi + math.pi * (i + 0.5) / n if not front else math.pi * (i + 0.5) / n
            x = cx + int((rx + 6) * math.cos(a)); y = cy + int((ry + 4) * math.sin(a))
            w = 30 + rs.randint(0, 14); h = (26 if not front else 15) + rs.randint(0, 12)
            if not front and abs(x - cx) < 14:
                continue                               # il varco del ponte, a nord
            peak(x, y + (8 if front else 4), w, h, 300 + i + (50 if front else 0), "volc")

    def lava():
        arr = np.array(im)
        m = emask(cx, cy, rx, ry)
        d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        veins = np.abs(fbm(91, 20, 3) - 0.5)
        v = 0.95 - veins * 9 + (n4 - 0.5) * 0.25 - d * 0.18
        n = len(P["LAVA"])
        idx = np.clip(np.floor(np.clip(v, 0, 1) * (n - 1) + (bay - 0.5) + 0.5), 0, n - 1).astype(int)
        arr[m] = np.array(P["LAVA"], np.uint8)[idx[m]]
        gl = grow(m, 3) & ~m & (bay < 0.45)
        arr[gl] = (120, 34, 20)
        im.paste(Image.fromarray(arr))

    def abyss():
        x, y, a, b = cx, cy + 4, 30, 15
        C = P["PURP"]
        dr.ellipse((x - a - 9, y - b - 5, x + a + 9, y + b + 7), fill=K)                     # lo scoglio
        dr.ellipse((x - a - 8, y - b - 4, x + a + 8, y + b + 5), fill=V[2])
        dr.pieslice((x - a - 8, y - b - 4, x + a + 8, y + b + 5), 150, 290, fill=V[4])
        dr.arc((x - a - 8, y - b - 4, x + a + 8, y + b + 5), 20, 160, fill=(255, 170, 40))
        for k, (s_, col) in enumerate(((1.0, K), (0.92, C[0]), (0.78, C[1]), (0.62, C[2]), (0.46, C[3]), (0.3, C[4]), (0.14, C[5]))):
            dr.ellipse((x - a * s_, y - b * s_, x + a * s_, y + b * s_), fill=col)
        for i in range(34):                            # il vortice
            an = i * 0.55; r_ = 0.18 + (i % 9) / 11
            px(x + a * r_ * math.cos(an), y + b * r_ * math.sin(an), C[5 if i % 3 else 3])
        for i in range(-4, 5):                         # scintille che salgono
            px(x + i * 6, y - b - 5 - (i * i) % 9, C[4]); px(x + i * 5 + 2, y - b - 12 - (i * 3) % 7, C[3])
            px(x + i * 4 - 1, y - b - 20 - (i * 5) % 9, C[2])

    def bridge():
        x0, y0, x1, y1 = cx, cy - ry - 4, cx, cy - 14
        S = P["STONE"]
        dr.rectangle((x0 - 3, y0, x0 + 3, y1), fill=K)
        dr.rectangle((x0 - 2, y0, x0 + 2, y1), fill=S[3]); dr.line((x0 - 2, y0, x0 - 2, y1), fill=S[5]); dr.line((x0 + 2, y0, x0 + 2, y1), fill=S[1])
        for yb in range(y0 + 2, y1, 4):
            dr.line((x0 - 1, yb, x0 + 1, yb), fill=S[2])
    obj(cy - ry - 2, lambda: rim(False))
    obj(cy - ry - 1, lambda: lava())
    obj(cy - ry, bridge)
    obj(cy + 20, abyss)
    obj(cy + ry + 12, lambda: rim(True))
    block(cx - rx - 22, cy - ry - 40, cx + rx + 22, cy + ry + 26)


caldera()
ROADS = (ROAD, ROAD2, ROAD3, ROAD4, ROAD5)
for r_ in ROADS:
    road_block(r_)

# ------------------------------------------------------------------ 8. alberi
def scatter_trees(mask, n, fn, seed, mind=9):
    rs = np.random.RandomState(seed)
    ys, xs = np.nonzero(mask & ~occ)
    pts = []
    grid = {}
    for k in rs.permutation(len(ys))[:n * 6]:
        y, x = int(ys[k]), int(xs[k])
        if y < 14 or y > H - 10 or x < 10 or x > W - 10 or occ[y, x]:
            continue
        g = (x // mind, y // mind)
        if any((g[0] + i, g[1] + j) in grid for i in (-1, 0, 1) for j in (-1, 0, 1)
               if (g[0] + i, g[1] + j) in grid and math.hypot(grid[(g[0] + i, g[1] + j)][0] - x, grid[(g[0] + i, g[1] + j)][1] - y) < mind):
            continue
        grid[g] = (x, y); pts.append((x, y))
        if len(pts) >= n:
            break
    for i, (x, y) in enumerate(pts):
        obj(y, lambda x=x, y=y, i=i: fn(x, y, i))


scatter_trees(wood & mead, 380, tree, 71, 10)
scatter_trees(mead & ~wood & (n2 > 0.52), 240, tree, 72, 13)
scatter_trees(mead & ~wood, 160, lambda x, y, i: paste_cb(BUSH[i % 3], x, y), 73, 12)
scatter_trees(snow & ((bs < 0.86) | (n2 > 0.60)), 260, pine, 74, 9)
scatter_trees(tf, 110, lambda x, y, i: pine(x, y, i, i % 3 == 0), 75, 10)                  # fascia del gelo: abeti misti
scatter_trees(mead & (bs > 0.12), 60, lambda x, y, i: pine(x, y, i, False), 79, 11)
scatter_trees((marsh | tm) & ~water, 150, lambda x, y, i: paste_cb(MANG if i % 3 else DEAD, x, y), 76, 13)
scatter_trees(ash, 140, lambda x, y, i: paste_cb(DEAD, x, y), 77, 14)
scatter_trees(ts | tsl, 60, lambda x, y, i: paste_cb(DEAD if i % 2 else BUSH[i % 3], x, y), 80, 11)   # terra bruciata
scatter_trees(ash & (n3 > 0.55), 60, lambda x, y, i: (dr.ellipse((x - 3, y - 2, x + 3, y + 1), fill=P["ASH"][1], outline=K),
                                                  px(x - 1, y - 1, P["ASH"][4])), 78, 16)


# ------------------------------------------------------------------ 9. mostri e navi
def ship(cx, cy, flag=(222, 36, 40)):
    Wd = P["WOODB"]
    for i in range(-11, 12, 3):
        px(cx + i, cy + 4, P["FOAM"]); px(cx + i + 1, cy + 5, P["SEA"][5])
    dr.polygon([(cx - 10, cy - 2), (cx + 11, cy - 2), (cx + 7, cy + 3), (cx - 7, cy + 3)], fill=K)
    dr.polygon([(cx - 8, cy - 1), (cx + 9, cy - 1), (cx + 6, cy + 2), (cx - 6, cy + 2)], fill=Wd[2]); dr.line((cx - 8, cy - 1, cx + 9, cy - 1), fill=Wd[4])
    dr.line((cx, cy - 18, cx, cy - 2), fill=K)
    dr.polygon([(cx - 8, cy - 5), (cx - 1, cy - 5), (cx - 1, cy - 16), (cx - 6, cy - 12)], fill=K)
    dr.polygon([(cx - 6, cy - 6), (cx - 2, cy - 6), (cx - 2, cy - 14), (cx - 5, cy - 11)], fill=(240, 236, 220))
    dr.polygon([(cx + 1, cy - 4), (cx + 9, cy - 4), (cx + 1, cy - 17)], fill=K); dr.polygon([(cx + 2, cy - 5), (cx + 7, cy - 5), (cx + 2, cy - 14)], fill=(250, 248, 236))
    dr.line((cx + 2, cy - 9, cx + 4, cy - 9), fill=flag); dr.rectangle((cx + 1, cy - 20, cx + 3, cy - 19), fill=flag)


def serpent(cx, cy):
    C = [(10, 50, 44), (22, 96, 70), (44, 148, 92), (104, 200, 110), (190, 236, 140)]
    for k, (ox, r) in enumerate(((0, 15), (34, 13), (64, 10), (88, 7))):
        x = cx + ox
        th = max(3, r // 2)
        box = lambda d: (x - r - d, cy - (r + d) * 0.95, x + r + d, cy + (r + d) * 0.95)
        dr.arc(box(1), 180, 360, fill=K, width=th + 2)
        dr.arc(box(0), 180, 360, fill=C[2], width=th)
        dr.arc(box(0), 180, 275, fill=C[3], width=max(2, th // 2))
        dr.arc(box(-th + 1), 180, 360, fill=(214, 208, 120), width=1)
        dr.arc(box(0), 300, 360, fill=C[1], width=th)
        for a_ in range(196, 350, 22):                 # cresta dorsale
            sx = x + (r + 2) * math.cos(math.radians(a_)); sy = cy + (r + 2) * 0.95 * math.sin(math.radians(a_))
            dr.polygon([(sx - 2, sy + 1), (sx + 2, sy + 1), (sx, sy - 3)], fill=(236, 120, 60), outline=K)
        for i in range(-r - 4, r + 5, 2):
            px(x + i, cy + 1, P["FOAM"]); px(x + i + 1, cy + 2, P["SEA"][5])
    head = sprite(["......kkkk......", "....kkGGGGkk....", "..kkGGGLGGGGkk..", ".kGGLLGGGGGwkGGk", "kGGGGGGGGGGkyGGk",
                   "kGGgggGGGGGGGGGk", ".kkkwkwkgGGGGGk.", "...k.k.kggGGGGk.", "........kggGGGk.", "........kggGGGk.",
                   ".......kgggGGGk.", ".......kgggGGk..", ".......kgggGGk.."],
                  {"k": K, "G": C[2], "g": C[1], "L": C[3], "w": (250, 250, 240), "y": (255, 220, 60)})
    paste(head, cx - 40, cy - 24)
    for i in range(-36, -20, 2):
        px(cx + i, cy + 1, P["FOAM"]); px(cx + i + 1, cy + 2, P["SEA"][5])
    dr.polygon([(cx - 42, cy - 17), (cx - 47, cy - 19), (cx - 44, cy - 15), (cx - 48, cy - 13)], fill=P["RED"])


def kraken(cx, cy):
    C = [(60, 10, 40), (120, 24, 60), (176, 46, 78), (224, 96, 110), (250, 170, 160)]
    for i, (ox, lean, hgt) in enumerate(((-26, -1.0, 26), (-12, 0.6, 34), (4, -0.5, 30), (18, 0.9, 24), (30, -0.3, 16))):
        pts = []
        for s in range(hgt):
            t = s / hgt
            pts.append((cx + ox + lean * 9 * math.sin(t * 3.0 + i), cy - s, 4.2 * (1 - t) + 1.0))
        for x, y, r in pts:
            dr.ellipse((x - r - 1, y - r - 1, x + r + 1, y + r + 1), fill=K)
        for x, y, r in pts:
            dr.ellipse((x - r, y - r, x + r, y + r), fill=C[2])
        for k, (x, y, r) in enumerate(pts):
            dr.ellipse((x - r, y - r, x, y + r), fill=C[3]) if r > 2 else px(x - 1, y, C[3])
            if k % 4 == 1:
                px(x + r * 0.5, y, C[4])
        for j in range(-6, 7, 2):
            px(cx + ox + j, cy + 1, P["FOAM"]); px(cx + ox + j + 1, cy + 2, P["SEA"][5])
    dr.ellipse((cx - 8, cy - 9, cx + 12, cy + 3), fill=K); dr.ellipse((cx - 7, cy - 8, cx + 11, cy + 2), fill=C[2])
    dr.ellipse((cx - 6, cy - 8, cx + 4, cy - 2), fill=C[3]); dr.rectangle((cx - 2, cy - 4, cx, cy - 3), fill=(255, 230, 90)); px(cx - 1, cy - 4, K)
    dr.rectangle((cx + 5, cy - 4, cx + 7, cy - 3), fill=(255, 230, 90)); px(cx + 6, cy - 4, K)
    for j in range(-10, 14, 2):
        px(cx + j, cy + 3, P["FOAM"])


def dragon(cx, cy):
    """drago in volo visto dall'alto, muso a sinistra: corpo sinuoso, due ali di pipistrello, coda a freccia, fiammata"""
    R = [(96, 10, 22), (150, 22, 30), (206, 44, 36), (238, 96, 60)]
    MB = [(170, 70, 30), (226, 120, 44), (250, 170, 70)]
    shadow(cx + 14, cy + 52, 34, 7, 0.66)
    body = [(cx - 30 + s, cy + 3 * math.sin(s / 9.0)) for s in range(0, 66)]
    for sign, sc in ((-1, 1.0), (1, 0.86)):            # le ali: sopra piu' grande, sotto in scorcio
        ax_, ay_ = cx - 6, cy + sign * 2
        tips = [(-16, 30), (-2, 22), (8, 32), (16, 20), (26, 24), (20, 6)]
        pts = [(ax_, ay_)] + [(ax_ + tx, ay_ + sign * ty * sc) for tx, ty in tips] + [(ax_ + 12, ay_)]
        dr.polygon(pts, fill=K)
        inner = [(ax_, ay_)] + [(ax_ + tx * 0.92, ay_ + sign * (ty * sc - 2)) for tx, ty in tips] + [(ax_ + 11, ay_)]
        dr.polygon(inner, fill=MB[1] if sign < 0 else MB[0])
        for tx, ty in tips[::2]:                       # le stecche
            dr.line((ax_ + 2, ay_, ax_ + tx * 0.92, ay_ + sign * (ty * sc - 2)), fill=R[1])
        dr.line((ax_, ay_, ax_ + tips[0][0], ay_ + sign * tips[0][1] * sc), fill=R[2], width=2)
    for i, (x, y) in enumerate(body):                  # corpo: dal collo alla coda
        r = 2.0 + 3.2 * math.sin(min(1.0, i / 40.0) * math.pi) if i < 40 else max(0.8, 3.0 * (1 - (i - 40) / 26.0))
        dr.ellipse((x - r - 1, y - r - 1, x + r + 1, y + r + 1), fill=K)
    for i, (x, y) in enumerate(body):
        r = 2.0 + 3.2 * math.sin(min(1.0, i / 40.0) * math.pi) if i < 40 else max(0.8, 3.0 * (1 - (i - 40) / 26.0))
        dr.ellipse((x - r, y - r, x + r, y + r), fill=R[2])
    for i, (x, y) in enumerate(body):
        if i % 4 == 0 and 4 < i < 58:
            px(x, y - 1, R[3]); px(x, y + 2, R[1])
    hx, hy = body[0]
    dr.polygon([(hx + 3, hy - 5), (hx - 12, hy - 1), (hx - 12, hy + 2), (hx + 3, hy + 5)], fill=K)
    dr.polygon([(hx + 2, hy - 3), (hx - 10, hy), (hx - 10, hy + 1), (hx + 2, hy + 4)], fill=R[2])
    dr.line((hx + 1, hy - 4, hx + 6, hy - 8), fill=P["BONE"]); dr.line((hx + 1, hy + 5, hx + 6, hy + 9), fill=P["BONE"])
    px(hx - 3, hy - 1, (255, 230, 90)); px(hx - 3, hy + 2, (255, 230, 90))
    tx, ty = body[-1]
    dr.polygon([(tx, ty), (tx + 7, ty - 5), (tx + 5, ty), (tx + 7, ty + 5)], fill=R[1], outline=K)
    for i in range(1, 12):                             # la fiammata
        fx, fy = hx - 12 - i * 2, hy + (i % 3 - 1) * (i // 3)
        dr.rectangle((fx - 1, fy - (12 - i) // 4, fx, fy + (12 - i) // 4), fill=(255, 230, 112) if i < 5 else (244, 132, 32) if i < 9 else (204, 50, 16))


def bones(cx, cy):
    B, B2 = P["BONE"], P["BONE2"]
    dr.line((cx - 2, cy + 1, cx + 62, cy + 1), fill=K, width=3); dr.line((cx - 2, cy, cx + 62, cy), fill=B2)
    for i in range(7):
        x = cx + 4 + i * 9
        r = 17 - abs(i - 3) * 2.2
        dr.arc((x - 6, cy - r, x + 6, cy + r * 0.3), 180, 350, fill=K, width=3)
        dr.arc((x - 5, cy - r + 1, x + 5, cy + r * 0.3), 180, 350, fill=B, width=1)
    sk = sprite(["..kkkkkkk..", ".kWWWWWWWk.", "kWWWWWWWWWk", "kWkkWWWkkWk", "kWkkWWWkkWk", "kWWWWkWWWWk", ".kWWWWWWWk.",
                 "..kWkWkWk..", "..kkkkkkk.."], {"k": K, "W": B})
    paste(sk, cx - 18, cy - 8)


def wisps():
    for x, y in ((236, 224), (352, 226), (372, 290), (226, 306), (290, 300), (180, 250), (396, 320)):
        obj(y, lambda x=x, y=y: (px(x, y, (220, 255, 200)), px(x - 1, y, P["GWIN"]), px(x + 1, y, P["GWIN"]), px(x, y - 1, P["GWIN"]),
                                 px(x, y + 1, (60, 150, 70))))


obj(580, lambda: serpent(720, 566))
obj(330, lambda: kraken(60, 330))
obj(300, lambda: ship(96, 300))
obj(566, lambda: ship(430, 566))
obj(120, lambda: ship(40, 120, (40, 40, 40)))
obj(398, lambda: bones(704, 396))
wisps()
for fx_, fy_ in ((250, 572), (262, 578), (150, 470)):
    obj(fy_, lambda fx_=fx_, fy_=fy_: (dr.polygon([(fx_ - 3, fy_), (fx_ + 3, fy_), (fx_ + 1, fy_ - 6)], fill=(70, 80, 100)),
                                     dr.line((fx_ - 3, fy_, fx_ + 1, fy_ - 6), fill=K), px(fx_ - 4, fy_ + 1, P["FOAM"]), px(fx_ + 4, fy_ + 1, P["FOAM"])))

for _, _, fn in sorted(objs, key=lambda o: (o[0], o[1])):
    fn()
for r_ in ROADS:
    road(r_)
dragon(600, 420)

# ------------------------------------------------------------------ 9b. tono della variante (solo la mappa: targhe e cornice restano uguali)
def grade(a):
    """tono crepuscolo: ombre viola, luci calde, colori ridotti a passi di 8"""
    f = a.astype(float)
    lum = (f[..., 0] * 0.3 + f[..., 1] * 0.59 + f[..., 2] * 0.11)[..., None] / 255
    f = f * np.array([1.04, 0.80, 0.86]) + np.array([26, 2, 30]) * (1 - lum) + np.array([18, 6, -14]) * lum
    f = f * 0.94
    q = 8
    return (np.clip(f, 0, 255) // q * q + q // 2).astype(np.uint8)


im = Image.fromarray(grade(np.array(im)))
dr = ImageDraw.Draw(im)

# ------------------------------------------------------------------ 10. targhe, titolo, cornice
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
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "'": ["#", "#", "#", ".", ".", ".", "."],
    "-": ["....", "....", "....", "####", "....", "....", "...."],
    " ": ["..", "..", "..", "..", "..", "..", ".."],
}


def text_w(s, k=2):
    return (sum(len(FONT[c][0]) + 1 for c in s) - 1) * k


def text(x, y, s, cols, k=2, sh=K):
    """testo con il font 5x7 ingrandito k volte: ombra scura, due toni (alto chiaro, basso scuro)"""
    for pas in (0, 1):
        cx = x
        for c in s:
            g = FONT[c]
            for j, r in enumerate(g):
                for i, v in enumerate(r):
                    if v == "#":
                        X, Y = cx + i * k, y + j * k
                        if pas == 0:
                            dr.rectangle((X + 1, Y + 1, X + k, Y + k), fill=sh)
                        else:
                            dr.rectangle((X, Y, X + k - 1, Y + k - 1), fill=cols[0] if j < 3 else cols[1])
                            if j == 0 or g[j - 1][i] != "#":
                                dr.line((X, Y, X + k - 1, Y), fill=cols[2])
            cx += (len(g[0]) + 1) * k


def badge(x, y, n, s=17):
    dr.rectangle((x, y, x + s, y + s), fill=K); dr.rectangle((x + 1, y + 1, x + s - 1, y + s - 1), fill=P["GOLD"][3])
    dr.rectangle((x + 2, y + 2, x + s - 2, y + s - 2), fill=P["RED"]); dr.rectangle((x + 2, y + s - 4, x + s - 2, y + s - 2), fill=P["DRED"])
    text(x + (s - text_w(str(n))) // 2 + 1, y + 2, str(n), [(255, 255, 255), (250, 232, 200), (255, 255, 255)], 2, P["DRED"])


def label(x, y, num, s, style, point=None):
    tw = text_w(s)
    bw = tw + (40 if num else 20)
    if point:
        dr.line((x + bw // 2, y + 12, point[0], point[1]), fill=K, width=3); dr.line((x + bw // 2, y + 12, point[0], point[1]), fill=P["GOLD"][3])
        dr.ellipse((point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3), fill=P["RED"], outline=K)
    if True:                                         # nastro rosso con le code
        Rr = [(70, 6, 16), (112, 12, 24), (156, 22, 32), (204, 52, 52)]
        for sx, d_ in ((x - 12, -1), (x + bw + 12, 1)):
            dr.polygon([(sx, y + 5), (sx + d_ * 16, y + 5), (sx + d_ * 9, y + 17), (sx + d_ * 16, y + 30), (sx, y + 30)], fill=K)
            dr.polygon([(sx, y + 6), (sx + d_ * 14, y + 6), (sx + d_ * 8, y + 17), (sx + d_ * 14, y + 29), (sx, y + 29)], fill=Rr[0])
        dr.rectangle((x - 13, y - 2, x + bw + 13, y + 26), fill=K)
        dr.rectangle((x - 12, y - 1, x + bw + 12, y + 25), fill=Rr[2]); dr.rectangle((x - 12, y - 1, x + bw + 12, y + 2), fill=Rr[3])
        dr.rectangle((x - 12, y + 21, x + bw + 12, y + 25), fill=Rr[1]); dr.line((x - 12, y + 4, x + bw + 12, y + 4), fill=P["GOLD"][3])
        dr.line((x - 12, y + 19, x + bw + 12, y + 19), fill=P["GOLD"][3])
        cols = [(255, 252, 240), (255, 232, 160), (255, 255, 255)]
    if num:
        badge(x + 4, y + 3, num)
    text(x + (30 if num else 10), y + 5, s, cols, 2, K)


STYLE = "ribbon"
label(170, 562, 1, "ALDRIC'S HOLLOW", STYLE, (300, 476))
label(60, 150, 2, "BAD WATER", STYLE, (236, 214))
label(640, 40, 3, "THE LAST CAMP", STYLE, (574, 110))
label(548, 332, 4, "RUIN'S GATE", STYLE, (718, 306))
label(770, 222, None, "THE CITADEL", STYLE, (848, 286))
label(560, 478, 5, "THE ABYSS", STYLE, (752, 470))
# titolo
T = "BARBARIAN - THE BLOOD PATH"
tw = text_w(T, 3)
tx, ty = 250 - tw // 2 + 60, 12
dr.rectangle((tx - 14, ty - 5, tx + tw + 14, ty + 30), fill=K)
dr.rectangle((tx - 13, ty - 4, tx + tw + 13, ty + 29), fill=P["GOLD"][2]); dr.line((tx - 13, ty - 4, tx + tw + 13, ty - 4), fill=P["GOLD"][4])
dr.rectangle((tx - 11, ty - 2, tx + tw + 11, ty + 27), fill=(60, 8, 16)); dr.rectangle((tx - 10, ty - 1, tx + tw + 10, ty + 26), outline=P["GOLD"][1])
text(tx, ty + 3, T, [P["GOLD"][4], P["GOLD"][3], (255, 255, 255)], 3)
# rosa dei venti
cx, cy = 76, 486
for r, col in ((30, K), (29, P["GOLD"][1]), (27, (20, 40, 100))):
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col)
for a, ln, c1, c2 in ((0, 34, P["GOLD"][4], P["GOLD"][2]), (90, 34, P["GOLD"][4], P["GOLD"][2]), (45, 20, P["PARCH"], P["PARCH2"])):
    for k in range(4):
        an = math.radians(a + k * 90)
        tip = (cx + ln * math.sin(an), cy - ln * math.cos(an))
        l_ = (cx + 5 * math.sin(an - 1.57), cy - 5 * math.cos(an - 1.57)); r_ = (cx + 5 * math.sin(an + 1.57), cy - 5 * math.cos(an + 1.57))
        dr.polygon([tip, l_, (cx, cy)], fill=c1, outline=K); dr.polygon([tip, r_, (cx, cy)], fill=c2, outline=K)
dr.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=P["RED"], outline=K)
text(cx - 5, cy - 54, "N", [P["GOLD"][4], P["GOLD"][3], (255, 255, 255)], 2)
# cornice
for i, col in enumerate((K, P["GOLD"][1], P["GOLD"][3], P["GOLD"][4], P["GOLD"][2], P["GOLD"][0], K)):
    dr.rectangle((i, i, W - 1 - i, H - 1 - i), outline=col)
for x, y in ((0, 0), (W - 13, 0), (0, H - 13), (W - 13, H - 13)):
    dr.rectangle((x, y, x + 12, y + 12), fill=K); dr.rectangle((x + 1, y + 1, x + 11, y + 11), fill=P["GOLD"][3])
    dr.rectangle((x + 3, y + 3, x + 9, y + 9), fill=P["RED"], outline=K); px(x + 4, y + 4, (255, 180, 170))


out = np.array(im)
res = Image.fromarray(out).resize((W * SCALE, H * SCALE), Image.NEAREST)
dst = os.path.join(ROOT, "out", "work", "art")
os.makedirs(dst, exist_ok=True)
Image.fromarray(out).save(os.path.join(dst, "world_map_1x.png"))
res.save(os.path.join(dst, "world_map.png"))
print("world map: out/work/art/world_map.png (%dx%d, %d colori)" % (res.size[0], res.size[1], len(set(map(tuple, out.reshape(-1, 3))))))
