#!/usr/bin/env python3
"""Attrezzi per i concept delle mappe dei villaggi (15/11, TODO Z2): una griglia 48x48 di lettere (LEGEND e ALIASES di
tools/build/gen_maps.py), funzioni per riempire, tracciare passaggi, spargere arredi, e i controlli finali.
Usato da lab/villaggi/concept_maps.py. La build NON usa questa cartella: la fonte delle mappe sono i testi in data/."""
import os, random, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import gen_gfx as G, gen_maps as M, villages as V     # noqa: E402
W = H = 48


class Map:
    def __init__(self, chapter, fill):
        self.c = chapter
        self.g = [[fill] * W for _ in range(H)]
        self.r = random.Random(chapter * 7919)
        sol = V.solid(chapter, G.TOWN_TILES, G.SOLID)
        inv = M.inv_legend()
        self.walk = {ch for ch, n in inv.items() if not sol[G.TTID[n]]}

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < W and 0 <= y < H else None

    def put(self, x, y, c, only=None):
        if 0 <= x < W and 0 <= y < H and c != " " and (only is None or self.g[y][x] in only):
            self.g[y][x] = c

    def fill(self, x0, y0, x1, y1, c, only=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c, only)

    def rows(self, x, y, *rows):
        """righe di lettere dalla casella (x, y); lo spazio lascia cio' che c'e'"""
        for j, r in enumerate(rows):
            for i, c in enumerate(r):
                self.put(x + i, y + j, c)

    def blob(self, cx, cy, rx, ry, c, only=None, jag=0.0):
        """macchia ovale (bordo irregolare con jag > 0)"""
        for y in range(H):
            for x in range(W):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1 + (self.r.uniform(-jag, jag) if jag else 0):
                    self.put(x, y, c, only)

    def road(self, pts, c, w=1, only=None, cv=None):
        """spezzata di tratti orizzontali e verticali; c = lettera dei tratti orizzontali, cv = dei verticali (default c);
        w = larghezza (verso il basso / a destra)"""
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            assert xa == xb or ya == yb, (xa, ya, xb, yb)
            for y in range(min(ya, yb), max(ya, yb) + 1):
                for x in range(min(xa, xb), max(xa, xb) + 1):
                    for k in range(w):
                        if xa == xb and ya != yb:
                            self.put(x + k, y, cv or c, only)
                        else:
                            self.put(x, y + k, c, only)

    def scatter(self, c, n, on, x0=0, y0=0, x1=W - 1, y1=H - 1, near=None, far=None, dist=1):
        """n caselle con lettera in `on` diventano c; near = solo accanto (entro dist) a queste lettere, far = mai accanto"""
        tries = 0
        while n > 0 and tries < 40000:
            tries += 1
            x, y = self.r.randint(x0, x1), self.r.randint(y0, y1)
            if self.g[y][x] not in on:
                continue
            around = {self.get(x + dx, y + dy) for dx in range(-dist, dist + 1) for dy in range(-dist, dist + 1)}
            if near and not (around & set(near)):
                continue
            if far and (around & set(far)):
                continue
            self.g[y][x] = c
            n -= 1

    def find(self, c):
        return [(x, y) for y in range(H) for x in range(W) if self.g[y][x] == c]

    def reach(self):
        e = self.find("E")
        seen, todo = set(e), list(e)
        while todo:
            x, y = todo.pop()
            for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if p not in seen and self.get(*p) in self.walk:
                    seen.add(p); todo.append(p)
        return seen

    def dump(self, seen=None):
        for y, r in enumerate(self.g):
            print("%2d " % y + "".join("?" if seen is not None and c in self.walk and (x, y) not in seen else c for x, c in enumerate(r)))

    def finish(self, close, keep=""):
        """caselle percorribili isolate: lettera in `keep` = errore, le altre diventano close(lettera) (un solido)"""
        seen = self.reach()
        for y in range(H):
            for x in range(W):
                c = self.g[y][x]
                if c in self.walk and (x, y) not in seen:
                    if c in keep or c in "SLH>=EP~":
                        self.dump(seen)
                        raise AssertionError("irraggiungibile: %s a (%d,%d)" % (c, x, y))
                    self.g[y][x] = close(c)
        return ["".join(r) for r in self.g]


def write(n, title, notes, rows):
    """scrive data/town_mapN.txt con la legenda del villaggio"""
    inv = M.inv_legend()
    v = V.VILLAGES[n]
    used = sorted({c for r in rows for c in r}, key=lambda c: G.TTID[inv[c]])
    p = os.path.join(ROOT, "data", "town_map%d.txt" % n)
    with open(p, "w") as f:
        f.write("; Mappa del villaggio del capitolo %d (48x48): %s. Una lettera per casella (tools/build/gen_maps.py).\n" % (n, title))
        f.write("; Le lettere sono i POSTI dei tile (gli stessi del villaggio 1); qui disegnano i tile di questo villaggio\n")
        f.write("; (tools/build/vil%d_*.py). E=ingresso  P=posto del portale  ==uscita del capitolo (2 caselle). Legenda:\n" % n)
        line = ";"
        for c in used:
            nm = "ingresso/uscita/portale" if c in M.ALIASES else (V.tile_name(n, inv[c]) or (inv[c].lower(),))[0]
            if c in M.ALIASES:
                continue
            item = "  %s=%s" % (c, nm)
            if len(line) + len(item) > 118:
                f.write(line + "\n"); line = ";"
            line += item
        f.write(line + "\n")
        for l in notes:
            f.write("; " + l + "\n")
        f.write("; Prima stesura: lab/villaggi/concept_maps.py (15/11); da qui in poi la fonte e' questo file.\n")
        f.write("\n".join(rows) + "\n")
    print("town_map%d.txt: RLE %d B" % (n, len(M.rle(M.read_txt(p)))))
