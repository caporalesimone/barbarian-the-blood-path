#!/usr/bin/env python3
"""Fan art: la mappa del mondo di "Barbarian: The Blood Path" in pixel art a 32 bit (15/11, TODO Z2).
Non e' grafica del gioco (il C64 non la legge): e' un'illustrazione per il manuale, la wiki, la scatola. Disegnata dal
codice (rumore per il terreno, tavolozze per zona, icone a mano), sempre uguale (seme fisso).
Zone: 1 Aldric's Crossing (valle verde, sud-ovest), 2 Blackwater Mill (lago nero e palude, nord-ovest), 3 The Last Camp
(montagne innevate, est), 4 Ruin's Gate (terra di cenere, il cratere, la cittadella, nord-est); sotto il cratere l'Abisso.
La strada segue il gioco: dal villaggio 1 si esce a nord, dal 2 a est, dal 3 a nord, nel 4 si scende nel cratere.
Uso: python3 tools/art/world_map.py   ->  out/work/art/world_map.png (1440x900) e world_map_1x.png (480x300)
Serve Pillow (container lab64-tools)."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
W, H, SCALE = 480, 300, 3
R = random.Random(1987)


def noise_grid(n, seed):
    r = random.Random(seed)
    return [[r.random() for _ in range(n + 2)] for _ in range(n + 2)]


def fbm_maker(seed, octaves=5, base=5):
    grids = [(noise_grid(base * 2 ** o, seed + o), base * 2 ** o) for o in range(octaves)]

    def f(x, y):
        v, amp, tot = 0.0, 1.0, 0.0
        for g, n in grids:
            fx, fy = x / W * n, y / H * n * H / W
            ix, iy = int(fx), int(fy)
            tx, ty = fx - ix, fy - iy
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            iy = min(iy, n)
            a = g[iy][ix] * (1 - tx) + g[iy][ix + 1] * tx
            b = g[iy + 1][ix] * (1 - tx) + g[iy + 1][ix + 1] * tx
            v += (a * (1 - ty) + b * ty) * amp
            tot += amp; amp *= 0.5
        return v / tot
    return f


elev, moist, detail = fbm_maker(11), fbm_maker(47, 4, 4), fbm_maker(93, 3, 24)
ZONES = {1: (118, 222), 2: (128, 118), 3: (312, 150), 4: (352, 62)}     # centri delle zone (x, y)


def zone_w(x, y):
    """peso di ogni zona nel punto (1 al centro, 0 lontano)"""
    out = {}
    for k, (cx, cy) in ZONES.items():
        d = math.hypot((x - cx) / (1.2 if k in (1, 3) else 1.0), y - cy)
        out[k] = max(0.0, 1 - d / 66.0)
    return out


def land(x, y):
    """altezza: > 0.42 terra. Un continente con le coste frastagliate"""
    dx, dy = (x - W * 0.5) / (W * 0.5), (y - H * 0.5) / (H * 0.5)
    fall = 1 - (abs(dx) ** 2.6 + abs(dy) ** 2.6) ** 0.5 * 0.95
    z = zone_w(x, y)
    h = elev(x, y) * 0.62 + fall * 0.52 + 0.10 * max(z.values())
    h += 0.20 * z[3] + 0.06 * z[4] - 0.05 * z[2]
    return h


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ramp(cols, t):
    t = max(0.0, min(0.999, t)) * (len(cols) - 1)
    return lerp(cols[int(t)], cols[int(t) + 1], t - int(t))


SEA = [(14, 22, 52), (20, 38, 84), (28, 62, 118), (44, 96, 150), (84, 148, 180)]
GRASS = [(58, 110, 48), (74, 134, 54), (104, 158, 62), (150, 184, 84)]
FOREST = [(26, 66, 40), (36, 88, 46), (52, 108, 52)]
SWAMP = [(22, 26, 22), (38, 46, 30), (60, 66, 36), (84, 86, 44)]
SNOW = [(96, 104, 128), (150, 160, 184), (206, 214, 230), (246, 248, 252)]
ROCK = [(62, 56, 60), (92, 84, 84), (128, 118, 112)]
ASH = [(34, 30, 32), (58, 52, 54), (86, 78, 78), (112, 102, 98)]
SAND = [(196, 178, 122), (222, 206, 150)]


def colour(x, y):
    h = land(x, y)
    if h < 0.42:                                          # mare: piu' chiaro verso la costa
        t = (h - 0.10) / 0.32
        c = ramp(SEA, t)
        if h > 0.405 and (x + y) % 2 == 0:
            c = (150, 196, 210)                           # risacca
        elif (y + int(detail(x, y) * 9)) % 7 == 0 and (x // 3 + y) % 5 == 0 and h < 0.38:
            c = lerp(c, (120, 170, 200), 0.5)             # onde
        return c
    z = zone_w(x, y)
    e = (h - 0.42) / 0.5
    d = detail(x, y)
    m = moist(x, y)
    if h < 0.435:
        base = ramp(SAND, d)
    else:
        base = ramp(FOREST, d) if m > 0.52 else ramp(GRASS, 0.25 + e * 1.3 + (d - 0.5) * 0.5)
        if e > 0.55:
            base = ramp(ROCK, (e - 0.55) * 3 + (d - 0.5) * 0.4)
        if e > 0.74:
            base = ramp(SNOW, (e - 0.74) * 5 + d * 0.3)
    k = max(z, key=z.get)
    w = min(1.0, z[k] * 1.9)
    if w > 0 and h >= 0.435:
        if k == 1:
            zc = ramp(GRASS, 0.35 + d * 0.6)
        elif k == 2:
            zc = ramp(SWAMP, 0.15 + d * 0.9)
        elif k == 3:
            zc = ramp(SNOW, 0.25 + e * 0.9 + d * 0.35) if e > 0.18 else ramp(SNOW, 0.5 + d * 0.5)
        else:
            zc = ramp(ASH, 0.1 + d * 0.9)
        # bordo delle zone a retino (dither), non sfumato: e' pixel art
        if w > 0.75 or (w > 0.45 and (x + y) % 2 == 0) or (w > 0.25 and x % 2 == 0 and y % 2 == 0):
            base = zc
    # luce da nord-ovest
    sh = (land(x - 1, y - 1) - land(x + 1, y + 1)) * 26
    sh = max(-0.45, min(0.45, sh))
    return lerp(base, (255, 250, 230), sh) if sh > 0 else lerp(base, (10, 8, 24), -sh)


def quant(c, n=20):
    return tuple(min(255, (v // n) * n + n // 2) for v in c)


img = Image.new("RGB", (W, H))
px = img.load()
for y in range(H):
    for x in range(W):
        px[x, y] = quant(colour(x, y))


def P(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        px[x, y] = c


def sprite(x, y, rows, pal, k=2):
    """icona da righe di caratteri (pal: carattere -> colore, ' ' trasparente), con il centro in basso a (x, y);
    k = pixel della mappa per pixel dell'icona; un filo d'ombra sotto"""
    h, w = len(rows), max(len(r) for r in rows)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != " ":
                for a in range(k):
                    for b in range(k):
                        P(x - w * k // 2 + i * k + a, y - h * k + 1 + j * k + b, pal[ch])
    for i in range(1, w * k - 1):
        xx, yy = x - w * k // 2 + i, y + 1
        if 0 <= xx < W and 0 <= yy < H:
            px[xx, yy] = lerp(px[xx, yy], (0, 0, 0), 0.35)


K = (16, 12, 20)
TREE = ([" gg ", "gGGg", "gGGg", " kk "], {"g": (40, 110, 50), "G": (70, 150, 62), "k": (70, 44, 26)})
FIR = (["  w  ", " wGw ", " GGG ", "wGGGw", "GGGGG", "  k  "], {"w": (240, 244, 250), "G": (36, 84, 66), "k": (64, 40, 28)})
DEAD = (["k k ", " kk ", "kk k", " k  ", " k  "], {"k": (24, 18, 20)})
HUT = (["  rr  ", " rrrr ", "rrrrrr", "wwwwww", "wwkwyw"], {"r": (150, 62, 40), "w": (214, 196, 160), "k": K, "y": (250, 210, 90)})
CHURCH = (["  y   ", "  y   ", " yyy  ", "  s   ", " sss  ", "sssrrr", "swsrrr", "sksww "],
          {"y": (240, 214, 110), "s": (190, 188, 196), "r": (140, 60, 44), "w": (220, 214, 200), "k": K})
STILT = (["  tt  ", " tttt ", "tttttt", "wwwwww", "wgwwkw", "p    p", "p    p"],
         {"t": (96, 74, 40), "w": (150, 110, 64), "g": (130, 230, 110), "k": K, "p": (60, 44, 28)})
MILL = (["   tttt  ", "  tttttt ", " tttttttt", " wwwwwwww", "ooowgwwgw", "o+owwwwww", "ooowwkwww", " p      p"],
        {"t": (70, 80, 50), "w": (150, 110, 64), "g": (130, 230, 110), "k": K, "o": (96, 70, 40), "+": (200, 160, 90), "p": (60, 44, 28)})
TENT = (["  rp  ", "  b   ", " bBb  ", " bBBb ", "bBkBBb"], {"r": (200, 40, 40), "p": (200, 40, 40), "b": (92, 64, 40), "B": (134, 98, 60), "k": K})
FIRE = ([" y ", "yoy", "ror", "kkk"], {"y": (255, 236, 130), "o": (255, 150, 40), "r": (210, 50, 30), "k": (50, 36, 30)})
RUIN = (["s   s", "ss  s", "sks s", "sssss"], {"s": (150, 144, 140), "k": K})
TOWER = ([" s s s ", " sssss ", "  sks  ", "  sss  ", "  sks  ", "  sss  ", " sssss ", " ssrss "],
         {"s": (70, 62, 70), "k": (220, 60, 40), "r": (250, 120, 50)})
CITADEL = (["   s       s   ", "   s   s   s   ", "  sss  s  sss  ", "  sks sss sks  ", "  sss sks sss  ", " sssssssssssss ",
            " sksssskssssks ", " ssssssrssssss ", "sssssssrsssssss"],
           {"s": (48, 42, 52), "k": (230, 70, 40), "r": (255, 150, 60)})
BOAT = (["  m  ", " mm  ", "bbbbb", " bbb "], {"m": (230, 226, 210), "b": (110, 72, 40)})
ROCKS = (["    w    ", "   wWs   ", "  wWWss  ", " wWWsSss ", "wWWssSSss"],
         {"w": (250, 250, 255), "W": (214, 220, 236), "s": (120, 116, 132), "S": (84, 80, 98)})


def spread(n, spr, cx, cy, rx, ry, ok, keep=()):
    k = 0
    for _ in range(n * 30):
        if k >= n:
            break
        x, y = int(R.gauss(cx, rx / 2)), int(R.gauss(cy, ry / 2))
        if not (4 < x < W - 4 and 8 < y < H - 2) or not ok(x, y):
            continue
        if any(abs(x - a) < w and abs(y - b) < h for a, b, w, h in keep):
            continue
        sprite(x, y, *spr); k += 1


is_land = lambda x, y: land(x, y) > 0.445
KEEP = []
# ---- 2: il lago nero di Blackwater (prima delle icone)
lx, ly = ZONES[2]
for y in range(ly - 30, ly + 30):
    for x in range(lx - 46, lx + 46):
        d = ((x - lx) / 40.0) ** 2 + ((y - ly) / 22.0) ** 2 + (detail(x, y) - 0.5) * 0.5
        if d < 1 and land(x, y) > 0.43:
            c = (10, 12, 16) if d < 0.8 else (30, 44, 30)
            if d < 0.8 and (x * 3 + y * 5) % 23 == 0:
                c = (60, 120, 60)                         # alghe
            if d < 0.8 and (x + y * 2) % 31 == 0:
                c = (40, 50, 70)                          # riflessi
            px[x, y] = c
# ---- 4: il cratere con il bagliore dell'Abisso
cx4, cy4 = ZONES[4][0] - 8, ZONES[4][1] + 22
for y in range(cy4 - 16, cy4 + 16):
    for x in range(cx4 - 24, cx4 + 24):
        d = ((x - cx4) / 17.0) ** 2 + ((y - cy4) / 9.0) ** 2
        if d < 1.25:
            if d > 1.0:
                c = (120, 108, 104) if y < cy4 else (40, 34, 36)       # orlo: chiaro sopra, in ombra sotto
            elif d > 0.62:
                c = (20, 14, 18) if (x + y) % 2 else (46, 16, 26)
            elif d > 0.3:
                c = (90, 24, 70) if (x + y) % 2 else (50, 14, 50)
            else:
                c = (176, 70, 200) if (x + y) % 2 else (120, 40, 160)
            if d < 0.1:
                c = (240, 190, 255)
            px[x, y] = c
# ---- fiume di Aldric's Crossing: dalle colline al mare
rx_, ry_ = ZONES[1][0] + 26, ZONES[1][1] - 34
for i in range(120):
    for dx in (0, 1):
        if land(rx_ + dx, ry_) > 0.42:
            P(rx_ + dx, ry_, (70, 140, 190) if i % 5 else (150, 200, 226))
    ry_ += 1
    rx_ += (-1 if detail(rx_, ry_ * 3) > 0.52 else 0) + (1 if i % 9 == 0 else 0)
    if land(rx_, ry_) < 0.40:
        break
# ---- la strada: 1 -> 2 -> 3 -> 4 -> cratere
ROAD = [(ZONES[1][0], ZONES[1][1] - 8), (ZONES[1][0] - 6, 170), (ZONES[2][0] - 2, ZONES[2][1] + 28), (ZONES[2][0] + 44, ZONES[2][1] + 6),
        (236, 136), (ZONES[3][0] - 26, ZONES[3][1] + 4), (ZONES[3][0], ZONES[3][1] - 6), (ZONES[3][0] + 22, 112),
        (ZONES[4][0] - 6, ZONES[4][1] + 34), (cx4 + 2, cy4 + 10)]
step = 0
for (xa, ya), (xb, yb) in zip(ROAD, ROAD[1:]):
    n = int(math.hypot(xb - xa, yb - ya))
    for i in range(n):
        t = i / n
        x = int(xa + (xb - xa) * t + math.sin((step + i) / 7.0) * 2.5)
        y = int(ya + (yb - ya) * t + math.cos((step + i) / 9.0) * 1.5)
        if (step + i) % 5 < 3:
            P(x, y, (226, 196, 120)); P(x, y + 1, (120, 84, 40))
    step += n
# ---- icone: zona 1
x1, y1 = ZONES[1]
sprite(x1 - 2, y1, *CHURCH); sprite(x1 - 24, y1 + 8, *HUT); sprite(x1 + 20, y1 + 6, *HUT); sprite(x1 + 2, y1 + 18, *HUT); sprite(x1 - 30, y1 - 8, *HUT)
KEEP.append((x1 - 4, y1 + 2, 44, 28))
spread(34, TREE, x1, y1, 70, 50, lambda x, y: is_land(x, y) and zone_w(x, y)[1] > 0.15, KEEP)
# ---- zona 2
x2, y2 = ZONES[2]
sprite(x2 - 24, y2 + 6, *STILT); sprite(x2 - 6, y2 - 2, *STILT); sprite(x2 + 2, y2 + 17, *STILT); sprite(x2 + 24, y2 + 2, *MILL)
for a, b, n in ((x2 - 18, y2 + 1, 8), (x2, y2 - 3, 14), (x2 - 4, y2 + 9, 4)):
    for i in range(n):
        P(a + i, b, (150, 110, 60)); P(a + i, b + 1, (70, 50, 30))     # passerelle
KEEP.append((x2, y2, 50, 26))
spread(24, ([" gg ", "gGGg", " gg ", " kk "], {"g": (30, 60, 34), "G": (54, 96, 48), "k": (40, 30, 22)}), x2, y2, 86, 60,
       lambda x, y: is_land(x, y) and zone_w(x, y)[2] > 0.12, KEEP)
sprite(x2 + 34, y2 + 12, *BOAT)
# ---- zona 3
x3, y3 = ZONES[3]
sprite(x3 - 18, y3 + 4, *TENT); sprite(x3 + 16, y3 + 6, *TENT); sprite(x3, y3 - 8, *TENT); sprite(x3 - 1, y3 + 8, *FIRE)
for i in range(-30, 32, 2):                               # palizzata
    P(x3 + i, y3 + 14, (96, 64, 36)); P(x3 + i, y3 + 13, (150, 108, 64)); P(x3 + i, y3 + 12, (150, 108, 64) if i % 4 == 0 else px[x3 + i, y3 + 12])
KEEP.append((x3, y3, 40, 26))
spread(12, ROCKS, x3 + 10, y3 - 34, 110, 30, lambda x, y: is_land(x, y) and zone_w(x, y)[3] > 0.12, KEEP)
spread(30, FIR, x3, y3 + 6, 120, 70, lambda x, y: is_land(x, y) and zone_w(x, y)[3] > 0.1, KEEP)
# ---- zona 4
x4, y4 = ZONES[4]
sprite(x4 + 6, y4 - 4, *CITADEL)
sprite(x4 - 38, y4 + 6, *RUIN); sprite(x4 + 34, y4 + 22, *RUIN); sprite(x4 + 18, y4 + 44, *RUIN); sprite(x4 - 44, y4 + 38, *RUIN); sprite(x4 + 44, y4 + 2, *TOWER)
KEEP += [(x4 + 6, y4 - 10, 34, 24), (cx4, cy4, 30, 16)]
for _ in range(26):                                       # crepe di lava nella cenere
    x, y = int(R.gauss(x4, 30)), int(R.gauss(y4 + 16, 22))
    if is_land(x, y) and zone_w(x, y)[4] > 0.3 and not any(abs(x - a) < w and abs(y - b) < h for a, b, w, h in KEEP):
        for i in range(R.randint(3, 7)):
            P(x, y, (230, 80, 30) if i % 2 else (255, 170, 60)); x += R.choice((1, 1, 0)); y += R.choice((-1, 0, 1))
spread(18, DEAD, x4, y4 + 10, 100, 60, lambda x, y: is_land(x, y) and zone_w(x, y)[4] > 0.12, KEEP)
# ---- mare: navi e mostro
sprite(60, 60, *BOAT); sprite(430, 236, *BOAT)
for i, (dx, dy) in enumerate(((0, 0), (5, -2), (10, 0), (15, -2), (20, 0))):
    for k in range(3):
        P(404 + dx + k, 270 + dy - (1 if k == 1 else 0), (40, 110, 90))
P(426, 267, (40, 110, 90)); P(427, 266, (40, 110, 90)); P(428, 267, (230, 60, 40))

# ---- cornice, cartigli, scritte
d = ImageDraw.Draw(img)
d.fontmode = "1"                                          # niente antialias: pixel netti
font = ImageFont.load_default()
GOLD, DARK, PARCH = (214, 172, 84), (30, 20, 16), (232, 214, 170)
for i, c in enumerate((DARK, GOLD, (150, 108, 44), DARK)):
    d.rectangle([i, i, W - 1 - i, H - 1 - i], outline=c)
for cx_, cy_ in ((6, 6), (W - 7, 6), (6, H - 7), (W - 7, H - 7)):
    d.rectangle([cx_ - 3, cy_ - 3, cx_ + 3, cy_ + 3], fill=GOLD, outline=DARK)
    d.point((cx_, cy_), fill=(200, 40, 40))


def label(x, y, text, num=None, col=PARCH):
    w = int(d.textbbox((0, 0), text, font=font)[2] * 1.1) + 12 + (11 if num else 0)
    d.rectangle([x - w // 2, y, x + w // 2, y + 12], fill=DARK, outline=GOLD)
    tx = x - w // 2 + 4
    if num:
        d.rectangle([tx - 2, y + 2, tx + 7, y + 10], fill=(170, 30, 30))
        d.text((tx, y + 1), str(num), font=font, fill=(255, 240, 200)); tx += 11
    d.text((tx, y + 1), text, font=font, fill=col)


label(x1 + 4, y1 + 30, "ALDRIC'S CROSSING", 1)
label(x2 - 8, y2 - 46, "BLACKWATER MILL", 2)
label(x3 + 30, y3 + 24, "THE LAST CAMP", 3)
label(x4 - 70, y4 - 24, "RUIN'S GATE", 4)
label(cx4 - 66, cy4 + 14, "THE ABYSS", None, (220, 160, 255))
d.line([cx4 - 38, cy4 + 18, cx4 - 14, cy4 + 6], fill=(220, 160, 255))
# titolo
tw = d.textbbox((0, 0), "BARBARIAN  -  THE BLOOD PATH", font=font)[2] + 20
d.rectangle([W // 2 - tw // 2, 8, W // 2 + tw // 2, 24], fill=(120, 20, 20), outline=GOLD)
d.rectangle([W // 2 - tw // 2 + 2, 10, W // 2 + tw // 2 - 2, 22], outline=(60, 8, 8))
d.text((W // 2 - tw // 2 + 8, 11), "BARBARIAN  -  THE BLOOD PATH", font=font, fill=(255, 226, 150))
# rosa dei venti
rx0, ry0 = 40, H - 44
for a in range(0, 360, 45):
    L = 15 if a % 90 == 0 else 8
    d.line([rx0, ry0, rx0 + int(math.sin(math.radians(a)) * L), ry0 - int(math.cos(math.radians(a)) * L)], fill=GOLD if a % 90 == 0 else PARCH)
d.ellipse([rx0 - 3, ry0 - 3, rx0 + 3, ry0 + 3], fill=(170, 30, 30), outline=DARK)
d.text((rx0 - 3, ry0 - 29), "N", font=font, fill=PARCH)

out = os.path.join(ROOT, "out", "work", "art")
os.makedirs(out, exist_ok=True)
img.save(os.path.join(out, "world_map_1x.png"))
img.resize((W * SCALE, H * SCALE), Image.NEAREST).save(os.path.join(out, "world_map.png"))
print("world map: out/work/art/world_map.png (%dx%d)" % (W * SCALE, H * SCALE))
