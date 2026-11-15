#!/usr/bin/env python3
"""Concept delle mappe dei villaggi dei capitoli 2-5 (15/11, TODO Z2): scrive data/town_map2.txt ... town_map5.txt.
Come per il villaggio 1 (concept del 10/11), lo script serve a generare la prima stesura: poi la fonte e' il file di
testo in data/ (si ritocca a mano; rilanciare lo script lo riscrive). La build NON usa questo script.
Uso: python3 lab/villaggi/concept_maps.py [capitolo ...]
Lettere: LEGEND e ALIASES di tools/build/gen_maps.py (uguali per tutti i villaggi: cambia il disegno dei tile, tools/build/villages.py).
Controlli (gli stessi li rifa' tools/build/gen_maps.py a ogni build): porte, fontana, cripta, uscita, ingresso e portale
raggiungibili; nessun arredo entro 3 caselle dalle porte di negozi e locanda; mappa RLE entro il limite."""
import os, random, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
W = H = 48
GROUND = ".,`"
WALK = set(".,`:d+x=*~SLH>EP")
DECO = set("iB*swT")


class Map:
    def __init__(self, seed, border="T"):
        self.g = [["."] * W for _ in range(H)]
        self.r = random.Random(seed)
        for y in range(H):
            for x in range(W):
                if x < 2 or x >= W - 2 or y < 2 or y >= H - 2:
                    self.g[y][x] = border

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < W and 0 <= y < H else "T"

    def put(self, x, y, c, only=None):
        if 0 <= x < W and 0 <= y < H and (only is None or self.g[y][x] in only):
            self.g[y][x] = c

    def fill(self, x0, y0, x1, y1, c, only=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c, only)

    def rows(self, x, y, *rows):
        for j, r in enumerate(rows):
            for i, c in enumerate(r):
                if c != " ":
                    self.put(x + i, y + j, c)

    def house(self, x, y, w, roof="R", door="D", sign=None, chim=True):
        """casa larga w (dispari), alta 4: due file di tetto, muro (con l'insegna), muro con finestre e porta al centro.
        Ritorna la casella della porta."""
        m = x + w // 2
        self.fill(x, y, x + w - 1, y + 1, roof)
        if chim:
            self.put(x + 1 + (w > 5), y, "c")
        self.fill(x, y + 2, x + w - 1, y + 3, "W")
        if sign:
            self.put(m, y + 2, sign)
        else:
            self.put(m - 1 if w > 5 else m, y + 2, "o")
        for i in (1, w - 2):
            if abs(x + i - m) > 0:
                self.put(x + i, y + 3, "o")
        self.put(m, y + 3, door)
        return m, y + 3

    def crypt(self, x, y):
        self.rows(x, y, "/@\\", "[>]")
        return x + 1, y + 1

    def fountain(self, x, y, floor="+"):
        self.fill(x - 1, y - 1, x + 4, y + 4, floor, only=GROUND + ":d")
        self.rows(x, y, " ~~ ", "~12~", "~34~", " ~~ ")

    def channel(self, xs, y0, y1, w):
        """corso d'acqua da nord a sud: xs(y) = colonna della sponda sinistra, larghezza w (sponde comprese)"""
        for y in range(y0, y1 + 1):
            x = xs(y)
            self.put(x, y, "(")
            self.fill(x + 1, y, x + w - 2, y, "%")
            self.put(x + w - 1, y, ")")

    def pond(self, cx, cy, rx, ry):
        for y in range(cy - ry, cy + ry + 1):
            d = 1 - ((y - cy) / (ry + 0.3)) ** 2
            if d <= 0:
                continue
            hw = int(rx * d ** 0.5 + 0.5)
            if hw < 1:
                continue
            self.put(cx - hw, y, "(")
            self.fill(cx - hw + 1, y, cx + hw - 1, y, "%")
            self.put(cx + hw, y, ")")

    def bridge(self, x0, x1, y0, y1):
        self.fill(x0, y0, x1, y1, "x")

    def road(self, pts, c=":", w=1, over=GROUND + "*BTiws|vd"):
        """spezzata di tratti orizzontali e verticali; w = larghezza (verso destra / in basso)"""
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            assert xa == xb or ya == yb, (xa, ya, xb, yb)
            for y in range(min(ya, yb), max(ya, yb) + 1):
                for x in range(min(xa, xb), max(xa, xb) + 1):
                    for k in range(w):
                        self.put(x + (k if xa == xb else 0), y + (k if ya == yb else 0), c, over)

    def scatter(self, c, n, x0=2, y0=2, x1=W - 3, y1=H - 3, on=GROUND, keep=(), near=None):
        """n caselle di terreno diventano c; keep = [(x, y, raggio)] da lasciare libere"""
        tries = 0
        while n > 0 and tries < 20000:
            tries += 1
            x, y = self.r.randint(x0, x1), self.r.randint(y0, y1)
            if self.g[y][x] not in on:
                continue
            if any(max(abs(x - kx), abs(y - ky)) <= kr for kx, ky, kr in keep):
                continue
            if near and not any(self.get(x + dx, y + dy) in near for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                continue
            # non chiudere i passaggi: niente arredo accanto a un sentiero stretto
            if c in "TBiws" and any(self.get(x + dx, y + dy) in ":x=EP~" for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            self.g[y][x] = c
            n -= 1

    def find(self, c):
        return [(x, y) for y in range(H) for x in range(W) if self.g[y][x] == c]

    def keep(self):
        """zone senza arredi: 3 caselle dalle porte di negozi e locanda, 2 dai ponti e dalla cripta"""
        k = [(x, y, 3) for c in "SLH" for x, y in self.find(c)]
        k += [(x, y, 2) for c in "x>P" for x, y in self.find(c)]
        return k

    def reach(self):
        e = self.find("E")
        seen, todo = set(e), list(e)
        while todo:
            x, y = todo.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + dx, y + dy)
                if p not in seen and 0 <= p[0] < W and 0 <= p[1] < H and self.g[p[1]][p[0]] in WALK:
                    seen.add(p); todo.append(p)
        return seen

    def finish(self, vary, solid="T"):
        """caselle percorribili isolate -> solido; varianti del terreno con probabilita' vary"""
        seen = self.reach()
        for y in range(H):
            for x in range(W):
                if self.g[y][x] in WALK and (x, y) not in seen:
                    if self.g[y][x] not in GROUND + "*d":
                        for yy, r in enumerate(self.g):
                            print("%2d " % yy + "".join("?" if c in WALK and (xx, yy) not in seen else c for xx, c in enumerate(r)))
                        raise AssertionError("irraggiungibile: %s a (%d,%d)" % (self.g[y][x], x, y))
                    self.g[y][x] = solid
        for y in range(H):
            for x in range(W):
                if self.g[y][x] == "." and self.r.random() < vary:
                    self.g[y][x] = self.r.choice(",`,")
        for c in "SLH>E":
            assert len(self.find(c)) == 1, "serve una sola casella %s" % c
        assert len(self.find("=")) == 2 and len(self.find("P")) == 1
        px, py = self.find("P")[0]
        assert self.g[py + 1][px] in WALK, "la casella sotto il portale deve essere percorribile"
        for c in "SLH":                                  # arredi troppo vicini alle porte: diventano steccato
            for dx, dy in self.find(c):
                for y in range(dy - 3, dy + 4):
                    for x in range(dx - 3, dx + 4):
                        if self.get(x, y) in DECO:
                            self.g[y][x] = "|" if (x, y) not in seen else "."
        bad = [(x, y, c) for c in "SLH" for dx, dy in self.find(c) for y in range(dy - 3, dy + 4) for x in range(dx - 3, dx + 4)
               if self.get(x, y) in DECO]
        assert not bad, "arredi vicino alle porte: %s" % bad
        for c in "SLH":
            x, y = self.find(c)[0]
            assert self.g[y + 1][x] in WALK and (x, y + 1) in seen, "porta %s non raggiungibile" % c
        return ["".join(r) for r in self.g]


def rle_len(rows):
    import gen_maps as M
    return len(M.rle(bytes(ord(c) for r in rows for c in r)))


def write(n, title, notes, rows):
    p = os.path.join(ROOT, "data", "town_map%d.txt" % n)
    with open(p, "w") as f:
        f.write("; Mappa del villaggio del capitolo %d (48x48): %s. Una lettera per casella (tools/build/gen_maps.py, LEGEND e ALIASES).\n" % (n, title))
        f.write("; Le lettere sono quelle del villaggio 1; i disegni dei tile sono a tema (tools/build/villages.py).\n")
        f.write("; E=ingresso (arrivo dal capitolo prima)  P=posto del portale  ==uscita del capitolo (2 caselle)  >=porta della cripta\n")
        for l in notes:
            f.write("; " + l + "\n")
        f.write("; Prima stesura generata da lab/villaggi/concept_maps.py (15/11); da qui in poi la fonte e' questo file.\n")
        f.write("\n".join(rows) + "\n")
    print("town_map%d.txt: RLE ~%d B" % (n, rle_len(rows)))


# ------------------------------------------------------------------------------------------------ 2: Blackwater Mill
def blackwater():
    m = Map(2)
    # la palude: tre strisce di terra separate da due canali neri, con stagni e canneti
    c1 = lambda y: 10 + (1 if 8 <= y < 16 else 0) - (1 if 26 <= y < 33 else 0) + (1 if y >= 40 else 0)
    c2 = lambda y: 29 - (1 if 6 <= y < 12 else 0) + (1 if 24 <= y < 30 else 0) + (2 if y >= 41 else 0)
    m.channel(c1, 0, 47, 4)
    m.channel(c2, 0, 47, 5)
    m.pond(21, 8, 4, 3); m.pond(5, 22, 2, 3); m.pond(40, 33, 3, 2); m.pond(19, 40, 3, 2); m.pond(41, 9, 2, 2)
    # terra di mezzo: piazza con la fontana, locanda, case
    m.fill(17, 20, 26, 29, "+")
    m.fountain(20, 23)
    m.house(15, 13, 7, "l"); m.house(23, 14, 5, "R")
    hx, hy = m.house(15, 32, 7, "r", "H")
    m.house(24, 33, 5, "l")
    m.rows(18, 21, "s"); m.rows(25, 21, "s"); m.rows(17, 28, "i"); m.rows(26, 28, "i")
    # ovest: cappella sprofondata (cripta) con le lapidi, alchimista
    cx, cy = m.crypt(4, 5)
    for x, y, c in ((3, 9, "t"), (5, 9, "Y"), (7, 9, "t"), (3, 12, "Y"), (7, 12, "t")):
        m.put(x, y, c); m.put(x, y + 1, "d")
    m.fill(2, 4, 9, 4, "|"); m.fill(2, 15, 9, 15, "|", only=GROUND); m.put(6, 15, ".")
    ax, ay = m.house(3, 36, 5, "l", "L", "7")
    # est: il mulino a cavallo del canale (ruota nell'acqua), fabbro, portale
    m.fill(34, 13, 40, 14, "r"); m.fill(34, 15, 40, 17, "W"); m.put(35, 13, "c")
    m.rows(34, 16, "oWoDWoW")
    m.rows(32, 14, "AA", "AA", "AA")                    # ruota (tile SPIRE del tema) nell'acqua accanto al muro
    sx, sy = m.house(37, 24, 7, "R", "S", "5")
    m.fill(38, 39, 43, 43, "+"); m.put(42, 40, "P"); m.put(39, 42, "w")
    # pontili (larghi 2) e sentieri
    m.bridge(c1(11), c1(11) + 3, 11, 12); m.bridge(c1(30), c1(30) + 3, 30, 31)
    m.bridge(c2(21), c2(21) + 4, 21, 22); m.bridge(c2(38), c2(38) + 4, 38, 39)
    m.put(22, 46, "E"); m.put(22, 47, "T")
    m.road([(22, 46), (22, 37), (hx, 37), (hx, hy + 1)])
    m.road([(22, 37), (22, 30)]); m.road([(21, 19), (21, 18), (18, 18), (18, 17)])
    m.road([(21, 18), (25, 18)])
    m.road([(16, 21), (14, 21), (14, 11), (15, 11)]); m.road([(14, 11), (14, 12)])
    m.road([(9, 11), (6, 11), (6, 7), (cx, 7)]); m.road([(6, 11), (6, 16)]); m.road([(6, 16), (8, 16), (8, 30), (9, 30)])
    m.road([(14, 30), (14, 31)]); m.road([(14, 22), (14, 30)])
    m.road([(8, 30), (8, 34), (ax, 34)]); m.road([(ax, 34), (ax, ay + 1), (ax, 41)])
    m.road([(27, 21), (28, 21)]); m.road([(34, 21), (37, 21), (37, 19)]); m.road([(37, 21), (40, 21), (40, 23)])
    m.road([(40, 21), (45, 21)], w=2); m.put(46, 21, "="); m.put(46, 22, "="); m.put(47, 21, "T"); m.put(47, 22, "T")
    m.road([(sx, sy + 1), (sx, 30), (45, 30), (45, 37), (41, 37), (41, 38)])
    m.road([(27, 38), (30, 38)]); m.road([(22, 38), (26, 38)]); m.road([(36, 38), (38, 38), (38, 39)])
    k = m.keep()
    m.scatter("T", 70, keep=k); m.scatter("B", 12, keep=k); m.scatter("*", 40, keep=k, near="()")
    m.scatter("i", 6, keep=k, near=":+"); m.scatter("*", 14, keep=k)
    return m.finish(0.42)


# -------------------------------------------------------------------------------------------------- 3: The Last Camp
def lastcamp():
    m = Map(3)
    # bosco fitto di abeti e massi tutto intorno; al centro il campo dentro una palizzata ovale
    m.fill(2, 2, W - 3, H - 3, "T")
    m.scatter("B", 150, on="T")
    cx, cy, rx, ry = 21, 25, 16, 15
    inside = lambda x, y, k=0: ((x - cx) / (rx - k)) ** 2 + ((y - cy) / (ry - k)) ** 2 <= 1
    for y in range(H):
        for x in range(W):
            if inside(x, y):
                horiz = not inside(x, y - 1) or not inside(x, y + 1)
                m.g[y][x] = "." if inside(x, y, 1) else ("|" if horiz else "v")
    # torrente gelato a est, fuori dalla palizzata; oltre il ponte la miniera (cripta) nella roccia
    st = lambda y: 39 + (1 if 14 <= y < 22 else 0) - (1 if 30 <= y < 38 else 0)
    m.channel(st, 0, 47, 4)
    m.fill(43, 22, 45, 29, "."); m.fill(43, 20, 45, 21, "B")
    kx, ky = m.crypt(43, 22)
    m.bridge(st(25), st(25) + 3, 25, 26)
    # dentro il campo: sorgente calda al centro (fontana) sul tavolato, tende
    m.fill(17, 21, 26, 30, "+")
    m.fountain(20, 24)
    m.house(12, 14, 7, "r"); m.put(12, 13, "A"); m.put(18, 13, "A")          # tenda del comando con gli stendardi
    sx, sy = m.house(25, 14, 7, "R", "S", "5")
    ax, ay = m.house(9, 19, 5, "r", "L", "7")
    hx, hy = m.house(25, 32, 7, "l", "H")
    m.house(13, 32, 5, "R", chim=False)
    m.rows(13, 27, "ss"); m.rows(29, 23, "s"); m.rows(29, 28, "s")
    m.rows(16, 21, "i"); m.rows(27, 21, "i"); m.rows(16, 30, "i"); m.rows(27, 30, "i")
    m.fill(7, 27, 10, 30, "+"); m.put(8, 28, "P"); m.put(10, 27, "."); m.put(7, 30, ".")      # cerchio del portale
    for x in (16, 18, 20):                                                     # tumuli dei caduti, in fondo al campo
        m.put(x, 38, "t"); m.put(x, 39, "d")
    # cancelli e sentieri: ingresso a ovest, uscita a nord, miniera a est
    cut = GROUND + "TB|v"
    m.put(2, 25, "E")
    m.road([(3, 25), (16, 25)], over=cut)
    m.road([(21, 0), (21, 20)], w=2, over=cut); m.put(21, 0, "="); m.put(22, 0, "=")
    m.road([(27, 25), (38, 25)], w=2, over=cut)
    m.road([(43, 25), (44, 25), (44, 24)]); m.fill(43, 26, 44, 26, ":")
    m.road([(15, 18), (15, 19), (21, 19)]); m.road([(sx, sy + 1), (sx, 19), (23, 19)])
    m.road([(ax, ay + 1), (ax, 25)]); m.road([(9, 26), (9, 26)])
    m.road([(hx, hy + 1), (hx, 36), (22, 36), (22, 31)]); m.road([(15, 36), (22, 36)]); m.road([(18, 36), (18, 37)])
    k = m.keep()
    m.scatter("B", 8, keep=k, x0=6, x1=36, y0=11, y1=39); m.scatter("*", 26, keep=k); m.scatter("T", 14, keep=k, x0=6, x1=36, y0=11, y1=39)
    return m.finish(0.30)


# ---------------------------------------------------------------------------------------------------- 4: Ruin's Gate
def ruinsgate():
    m = Map(4)
    # la strada maestra da sud alla Porta (nord), una crepa di lava da nord a sud a est della strada
    lv = lambda y: 31 + (1 if 8 <= y < 14 else 0) + (2 if 14 <= y < 22 else 0) + (1 if 22 <= y < 28 else 0) - (1 if y >= 38 else 0)
    m.channel(lv, 0, 47, 4)
    m.road([(23, 46), (23, 3)], w=2)
    m.put(23, 46, "E"); m.fill(23, 47, 24, 47, "T")
    # la Porta: due torri spezzate e il muro di cinta
    m.fill(2, 4, 21, 5, "W", only=GROUND); m.fill(26, 4, 30, 5, "W", only=GROUND)
    m.fill(19, 2, 21, 5, "W"); m.fill(26, 2, 28, 5, "W"); m.put(20, 1, "A"); m.put(27, 1, "A")
    m.rows(19, 3, "WoW"); m.rows(26, 3, "WoW")
    m.fill(6, 4, 8, 5, "."); m.fill(13, 4, 14, 4, ".")                         # brecce nel muro
    m.put(23, 0, "="); m.put(24, 0, "="); m.fill(23, 1, 24, 2, ":")
    # piazza con la fontana secca, case in rovina
    m.fill(11, 20, 21, 29, "+")
    m.fountain(14, 23)
    m.house(4, 9, 7, "R"); m.house(13, 10, 5, "r"); m.house(4, 17, 5, "l", chim=False)
    ax, ay = m.house(3, 26, 7, "l", "L", "7")
    hx, hy = m.house(12, 34, 7, "r", "H")
    m.house(3, 37, 5, "R", chim=False)
    m.rows(8, 14, "WW W", "W   ", "W  W")                                    # muri senza tetto
    m.rows(15, 16, "W WW", "   W")
    m.rows(12, 21, "s"); m.rows(20, 28, "s"); m.rows(11, 28, "i"); m.rows(21, 20, "i")
    # est della lava: fucina, cattedrale crollata con la cripta, portale
    sx, sy = m.house(37, 8, 7, "R", "S", "5")
    m.rows(37, 24, "W WWW W", "W     W", "       ", "W     W")
    kx, ky = m.crypt(39, 26)
    m.put(38, 23, "A"); m.put(42, 23, "A")
    for x, y, c in ((37, 31, "t"), (39, 31, "Y"), (41, 31, "t"), (43, 31, "Y")):
        m.put(x, y, c); m.put(x, y + 1, "d")
    m.fill(38, 38, 43, 42, "+"); m.put(40, 39, "P"); m.put(42, 41, "w")
    # ponti di lastre e sentieri
    m.bridge(lv(16), lv(16) + 3, 16, 17); m.bridge(lv(35), lv(35) + 3, 35, 36)
    m.road([(25, 16), (32, 16)]); m.road([(25, 17), (32, 17)]); m.road([(37, 16), (40, 16), (40, 12)]); m.road([(37, 17), (40, 17)])
    m.road([(40, 17), (40, 22)]); m.road([(40, 28), (40, 30)]); m.road([(40, 30), (45, 30), (45, 36), (40, 36), (40, 37)])
    m.road([(25, 35), (29, 35)]); m.road([(25, 36), (29, 36)]); m.road([(34, 35), (40, 35)]); m.road([(34, 36), (39, 36)])
    m.road([(22, 24), (22, 25)]); m.road([(10, 25), (ax + 4, 25)][:0] or [(10, 24), (8, 24), (8, 31), (ax, 31), (ax, ay + 1)])
    m.road([(8, 31), (10, 31), (10, 39), (hx, 39), (hx, hy + 1)]); m.road([(hx, 39), (22, 39)])
    m.road([(16, 19), (16, 15), (15, 15)]); m.road([(16, 15), (22, 15)]); m.road([(7, 14), (7, 13)]); m.road([(7, 15), (15, 15)])
    m.road([(7, 15), (7, 14)]); m.road([(6, 22), (6, 21)]); m.road([(6, 22), (8, 22), (8, 24)]); m.road([(5, 42), (5, 41)]); m.road([(5, 42), (10, 42), (10, 39)])
    k = m.keep()
    m.scatter("T", 60, keep=k); m.scatter("B", 45, keep=k); m.scatter("*", 30, keep=k); m.scatter("d", 40, keep=k)
    m.scatter("i", 4, keep=k, near=":")
    return m.finish(0.45, solid="B")


# ------------------------------------------------------------------------------------------ 5: la citta' dell'Abisso
def abysscity():
    m = Map(5, border="%")
    # la citta' galleggia nel vuoto: tre isole di pietra separate da due crepe, ponti di luce
    for y in range(2, H - 2):
        m.put(2, y, ")"); m.put(W - 3, y, "(")
    r1 = lambda y: 14 + (1 if 16 <= y < 30 else 0)
    r2 = lambda y: 30 - (1 if 16 <= y < 30 else 0)
    m.channel(r1, 2, 45, 4); m.channel(r2, 2, 45, 4)
    m.fill(3, 2, 44, 2, "%"); m.fill(3, 45, 44, 45, "%")
    for y in (2, 45):
        for x in (2, 13, 14, 17, 18, 29, 30, 33, 34, 45):
            m.put(x, y, "%")
    # isola centrale: viale, piazza del mosaico con la fontana, la discesa nell'Abisso a nord, locanda a sud
    m.fill(19, 19, 28, 28, "+")
    m.fountain(22, 22)
    m.road([(23, 45), (23, 29)], w=2, over=GROUND + "%"); m.put(23, 45, "E"); m.put(24, 45, ":")
    m.road([(23, 18), (23, 9)], w=2)
    kx, ky = m.crypt(19, 9); m.put(19, 11, ":"); m.road([(20, 11), (22, 11)])
    m.fill(22, 3, 25, 8, "T"); m.road([(23, 8), (23, 3)], w=2, over="T"); m.put(23, 2, "="); m.put(24, 2, "=")
    for y in (11, 14, 32, 40):
        m.put(21, y, "t"); m.put(26, y, "t")
    hx, hy = m.house(19, 35, 5, "l", "H"); m.house(25, 35, 4 + 1, "R", chim=False)
    m.rows(20, 20, "i"); m.rows(27, 20, "i"); m.rows(20, 27, "i"); m.rows(27, 27, "i")
    # isola ovest: fabbro, case, altare; isola est: alchimista, portale
    sx, sy = m.house(5, 9, 7, "R", "S", "5")
    m.house(5, 20, 7, "r"); m.house(5, 33, 5, "l", chim=False)
    m.rows(8, 28, "s"); m.rows(11, 40, "Y"); m.rows(5, 40, "Y")
    ax, ay = m.house(37, 9, 7, "r", "L", "7")
    m.house(37, 21, 7, "R"); m.house(38, 34, 5, "l", chim=False)
    m.fill(36, 27, 42, 31, "+"); m.put(39, 28, "P"); m.put(37, 30, "Y"); m.put(41, 30, "Y")
    # ponti di luce (larghi 2) e strade
    for y in (15, 23, 39):
        m.bridge(r1(y), r1(y) + 3, y, y + 1); m.bridge(r2(y), r2(y) + 3, y, y + 1)
    for y in (15, 23, 39):
        m.road([(4, y), (13, y)]); m.road([(4, y + 1), (13, y + 1)]); m.road([(34, y), (43, y)]); m.road([(34, y + 1), (43, y + 1)])
        m.road([(18, y), (29, y)], over=GROUND); m.road([(18, y + 1), (29, y + 1)], over=GROUND)
    m.road([(4, 15), (4, 40)]); m.road([(43, 15), (43, 40)])
    m.road([(sx, sy + 1), (sx, 14)]); m.road([(ax, ay + 1), (ax, 14)]); m.road([(8, 24), (8, 25)][::-1]); m.road([(40, 25), (40, 26)])
    m.road([(7, 37), (7, 38)]); m.road([(40, 38), (40, 38)]); m.road([(hx, hy + 1), (22, 39)][:1] + [(hx, 39)])
    m.road([(27, 39), (27, 39)])
    k = m.keep()
    m.scatter("T", 40, keep=k); m.scatter("B", 30, keep=k); m.scatter("*", 30, keep=k)
    return m.finish(0.35, solid="B")


if __name__ == "__main__":
    todo = [int(a) for a in sys.argv[1:]] or [2, 3, 4, 5]
    if 2 in todo:
        write(2, "Blackwater Mill, il villaggio nella palude", [
            "Tre strisce di terra separate da due canali di acqua nera (pontili larghi 2), stagni e canneti. Ovest: cappella",
            "sprofondata con la cripta e le lapidi, alchimista. Centro: piazza con la fontana, locanda, ingresso a sud. Est: il",
            "mulino a cavallo del canale (ruota = tile A), fabbro, piazzetta del portale; uscita sul bordo est."], blackwater())
    if 3 in todo:
        write(3, "The Last Camp, il campo nella neve", [
            "Un campo dentro una palizzata ovale in un bosco di abeti e massi. Dentro: sorgente calda (fontana) sul tavolato,",
            "tenda del comando con gli stendardi (A), fabbro, alchimista, locanda, cerchio del portale. Fuori: torrente gelato a est",
            "con il ponte verso la miniera (cripta), tumuli a sud-est. Ingresso a ovest, uscita sul bordo nord."], lastcamp())
    if 4 in todo:
        write(4, "Ruin's Gate, il villaggio in rovina", [
            "Strada maestra da sud alla Porta (due torri spezzate e il muro di cinta con le brecce), crepa di lava da nord a sud",
            "con due ponti di lastre. Ovest: piazza con la fontana, case bruciate, alchimista, locanda (sud). Est: fucina,",
            "cattedrale crollata con la cripta e le tombe, piazzetta del portale. Ingresso a sud, uscita sul bordo nord (la Porta)."], ruinsgate())
    if 5 in todo:
        write(5, "la citta' dell'Abisso", [
            "Tre isole di pietra sospese nel vuoto (il bordo della mappa e' vuoto), separate da due crepe con ponti di luce.",
            "Centro: viale, piazza del mosaico con la fontana, discesa nell'Abisso a nord (cripta), locanda a sud. Ovest: fabbro.",
            "Est: alchimista e piazzetta del portale. Ingresso a sud; le caselle di uscita ci sono (formato) ma non si aprono."], abysscity())
