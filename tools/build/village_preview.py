#!/usr/bin/env python3
"""Anteprime dei villaggi dei capitoli (15/11): out/work/villages/twnN_tiles.png (i 45 tile) e twnN_map.png (la mappa
intera 48x48 con i colori del villaggio), dai file che legge il C64 (out/work/gfx/gfx0.prg, twnN.prg) e dalle mappe di
testo. Uso: python3 tools/build/village_preview.py [capitolo ...]   (dopo tools/build/gen_gfx.py)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import gen_gfx as G, gen_maps as M, villages as V
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
NT = len(G.TOWN_TILES)


def tiles(c):
    f = "twn%d.prg" % c if V.VILLAGES[c]["tiles"] else "gfx0.prg"
    d = open(os.path.join(ROOT, "out", "work", "gfx", f), "rb").read()[2:]
    out = []
    for i in range(NT):
        g = [[0] * 8 for _ in range(16)]
        for q, (y0, x0) in enumerate(((0, 0), (0, 4), (8, 0), (8, 4))):
            for y in range(8):
                b = d[(q * NT + i) * 8 + y]
                for x in range(4):
                    g[y0 + y][x0 + x] = (b >> (6 - 2 * x)) & 3
        out.append(g)
    return out


def draw(img, g, pal, ox, oy, sc):
    for y in range(16):
        for x in range(8):
            col = G.C64[pal[g[y][x]]]
            for yy in range(sc):
                for xx in range(2 * sc):
                    img.putpixel((ox + x * 2 * sc + xx, oy + y * sc + yy), col)


def main():
    os.makedirs(os.path.join(ROOT, "out", "work", "villages"), exist_ok=True)
    for c in [int(a) for a in sys.argv[1:]] or sorted(V.VILLAGES):
        v = V.VILLAGES[c]; pal = v["pal"]; t = tiles(c)
        sc = 4
        img = Image.new("RGB", (15 * (16 * sc + 6) + 6, 3 * (16 * sc + 6) + 6), (40, 40, 40))
        for i, g in enumerate(t):
            draw(img, g, pal, 6 + (i % 15) * (16 * sc + 6), 6 + (i // 15) * (16 * sc + 6), sc)
        img.save(os.path.join(ROOT, "out", "work", "villages", "twn%d_tiles.png" % c))
        if os.path.exists(os.path.join(ROOT, v["map"])):
            m = M.read_txt(os.path.join(ROOT, v["map"]))
            sc = 1
            img = Image.new("RGB", (48 * 16, 48 * 16))
            for y in range(48):
                for x in range(48):
                    draw(img, t[m[y * 48 + x]], pal, x * 16, y * 16, sc)
            img.save(os.path.join(ROOT, "out", "work", "villages", "twn%d_map.png" % c))


if __name__ == "__main__":
    main()
