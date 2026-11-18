"""Tile delle grotte (18/11, TODO M11, docs/wiki/dungeon.md): muro, parete e pavimenti di roccia per i temi dei capitoli con
`map: {style: caves}` (data/chapters.yaml); li usa tools/build/gen_gfx.py al posto dei mattoni nel file del tema dei piani.

Classi dei pixel multicolor (palette in src/game.asm): 0 sfondo (nero), 1 roccia (pal_c1), 2 neve sulle creste o roccia
chiara (pal_c2: bianco nella palette 9 del piano 11, grigio chiaro nella 10), 3 ombre (colore della RAM: blu nella 9, nero
nella 10). Le crepe degli strati sono buchi neri (classe 0): stanno bene con tutte e due le palette. Generatore casuale proprio: gli altri tile e file non cambiano."""
import random

W, H = 8, 16


def _grid(c):
    return [[c] * W for _ in range(H)]


def _noise(g, r, c, dens, only=None):
    for y in range(H):
        for x in range(W):
            if r.random() < dens and (only is None or g[y][x] in only):
                g[y][x] = c


def tiles():
    """{nome del tile: griglia 8x16 di classi 0..3}: WALL, WALLFACE, FLOOR, FLOORB, FLOORC"""
    r = random.Random(1311)
    out = {}
    # massa di roccia vista dall'alto: roccia con crepe e granelli chiari (neve al piano 11)
    g = _grid(1)
    _noise(g, r, 3, 0.08)
    _noise(g, r, 0, 0.10)
    _noise(g, r, 2, 0.06, only=[1])
    out["WALL"] = g
    # parete di roccia sopra un pavimento: cresta chiara irregolare in alto (neve), strati con crepe, ombra in basso.
    # Gli strati hanno la stessa riga ai bordi sinistro e destro: le pareti vicine si saldano.
    g = _grid(1)
    for x in range(W):
        cap = 2 + (r.random() < 0.5) + (r.random() < 0.25)
        for y in range(cap):
            g[y][x] = 2
        g[cap][x] = 3 if r.random() < 0.6 else 1
    for y0 in (6, 10, 13):
        y = y0
        for x in range(W):
            if 0 < x < W - 1 and r.random() < 0.35:
                y = max(y0 - 1, min(y0 + 1, y + r.choice((-1, 1))))
            elif x == W - 1:
                y = y0
            if r.random() < 0.85:
                g[y][x] = 0
    for _ in range(2):                                   # crepe verticali corte
        x, y = r.randrange(1, W - 1), r.randrange(5, 12)
        for k in range(r.randrange(2, 4)):
            g[min(H - 2, y + k)][x] = 0
    _noise(g, r, 2, 0.04, only=[1])
    for x in range(W):
        g[H - 1][x] = 3 if x % 2 else 0
    out["WALLFACE"] = g
    # pavimento: terra scura con ghiaia (1) e qualche granello chiaro (2)
    base = _grid(0)
    _noise(base, r, 1, 0.09)
    _noise(base, r, 2, 0.02, only=[0])
    out["FLOOR"] = [row[:] for row in base]
    g = [row[:] for row in base]                          # sasso
    for (x, y, c) in ((2, 6, 2), (3, 6, 2), (1, 7, 1), (2, 7, 1), (3, 7, 1), (4, 7, 1), (1, 8, 3), (2, 8, 1), (3, 8, 1),
                      (4, 8, 3), (2, 9, 3), (3, 9, 3), (5, 12, 1), (6, 12, 2)):
        g[y][x] = c
    out["FLOORB"] = g
    g = [row[:] for row in base]                          # ciottoli sparsi
    for (x, y, c) in ((1, 3, 1), (2, 3, 2), (5, 6, 1), (4, 10, 1), (5, 10, 1), (5, 9, 2), (2, 13, 1)):
        g[y][x] = c
    out["FLOORC"] = g
    return out
