#!/usr/bin/env python3
"""Attrezzi di disegno dei tile dei villaggi (15/11, TODO Z2): griglie 8x16 di valori 0..3 (pixel multicolor larghi il
doppio), come make_tile di tools/build/gen_gfx.py. Usati da tools/build/vil*.py (un modulo per villaggio)."""
import random

W, H = 8, 16


def A(*rows):
    """tile da 16 righe di 8 cifre 0..3 ('.' = 0)"""
    assert len(rows) == H and all(len(r) == W for r in rows), rows
    return [[0 if c == "." else int(c) for c in r] for r in rows]


def grid(c=0):
    return [[c] * W for _ in range(H)]


def put(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c


def hline(g, y, x0, x1, c):
    for x in range(x0, x1 + 1):
        put(g, x, y, c)


def vline(g, x, y0, y1, c):
    for y in range(y0, y1 + 1):
        put(g, x, y, c)


def noise(g, c, dens, r, only=None):
    for y in range(H):
        for x in range(W):
            if r.random() < dens and (only is None or g[y][x] in only):
                g[y][x] = c


def bricks(base, joint, offs_a=(3, 7), offs_b=(1, 5)):
    g = grid(base)
    for by in range(4):
        hline(g, by * 4 + 3, 0, 7, joint)
        for x in (offs_a if by % 2 == 0 else offs_b):
            vline(g, x, by * 4, by * 4 + 2, joint)
    return g




def ell(g, cx, cy, rx, ry, c):
    for y in range(H):
        for x in range(W):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                g[y][x] = c


def rnd(key):
    """generatore casuale proprio di un tile (non tocca quello di gen_gfx: gli altri file non cambiano)"""
    return random.Random(key)


def over(base, *rows):
    """copia di base con sopra le righe date (' ' = lascia la base, '.' = 0)"""
    assert len(rows) == H and all(len(r) == W for r in rows), rows
    return [[base[y][x] if c == " " else (0 if c == "." else int(c)) for x, c in enumerate(r)] for y, r in enumerate(rows)]


def canvas(*rows):
    """disegno grande (multipli di 8x16) da righe di cifre; ' ' non ammesso"""
    return [[0 if c == "." else int(c) for c in r] for r in rows]


def cut(cv, tx, ty, base=None):
    """tile (tx, ty) di un disegno grande; con base, i pixel '9' del disegno prendono la base"""
    g = [row[tx * W:tx * W + W] for row in cv[ty * H:ty * H + H]]
    assert len(g) == H and all(len(r) == W for r in g), (tx, ty)
    if base is not None:
        g = [[base[y][x] if v == 9 else v for x, v in enumerate(r)] for y, r in enumerate(g)]
    return g


def tile_rows(g):
    return ["".join(str(v) for v in r) for r in g]
