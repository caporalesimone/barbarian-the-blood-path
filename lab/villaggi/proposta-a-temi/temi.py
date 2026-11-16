#!/usr/bin/env python3
"""Villaggi dei capitoli (15/11, TODO Z2/M1, docs/wiki/villaggio.md): un file TWNc per capitolo con i SUOI tile, la SUA mappa, i
SUOI colori e le SUE posizioni (portale, cripta, ingresso, uscita, porte).

Ogni villaggio usa gli stessi 45 posti di tile del villaggio 1 (tools/build/gen_gfx.py TOWN_TILES: il codice del gioco
conosce i numeri, non i disegni), ma li ridisegna a tema: stesso ruolo (percorribile o solido, porta, fontana, acqua),
altro aspetto. Colori: 3 condivisi (sfondo = terreno, scuro, chiaro) + il colore dei caratteri (0..7, accento).

  theme   chiave in THEMES sotto (None = disegni del villaggio 1, make_tile di gen_gfx)
  pal     (sfondo, scuro, chiaro, accento 0..7): valori dei pixel 0, 1, 2, 3 dei tile
  map     testo 48x48 in data/ (lettere: LEGEND di tools/build/gen_maps.py, uguali per tutti i villaggi)
  names   nomi a tema dei tile per l'atlante (posto -> nome, descrizione); gli altri: quelli del villaggio 1

Disegni: una griglia 8x16 di valori 0..3 per tile (pixel multicolor larghi il doppio), come make_tile."""
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


# ------------------------------------------------------------------------------------------------------------ palude
def swamp(n, r, base):
    """Blackwater Mill: fango (0 marrone), nero (1: acqua, catrame), grigio (2: legno vecchio, pietra), verde (3: alghe, canne)"""
    if n == "GRASSA":
        g = grid(0); noise(g, 1, 0.05, r)
        for x, y in ((2, 4), (5, 11)):
            put(g, x, y, 3); put(g, x, y - 1, 3)
        return g
    if n == "GRASSB":                       # canne
        g = grid(0); noise(g, 1, 0.04, r)
        for x, y0, y1 in ((1, 3, 8), (3, 1, 7), (5, 8, 14), (6, 6, 13), (2, 10, 14)):
            vline(g, x, y0, y1, 3); put(g, x, y0 - 1, 2)
        return g
    if n == "GRASSC":                       # pozza
        return A("........", "....1...", "........", ".3......", ".3...3..", "..111...", ".111113.", "11311111",
                 "1111311.", ".11111..", "..111.2.", "......22", "........", "..1.....", "........", ".....3..")
    if n == "PATH":                         # passerella di assi
        g = grid(2)
        for y in (3, 7, 11, 15):
            hline(g, y, 0, 7, 1)
        for x, y in ((1, 1), (6, 1), (2, 5), (5, 5), (1, 9), (6, 9), (2, 13), (5, 13)):
            put(g, x, y, 1)
        noise(g, 0, 0.05, r, only=[2])
        return g
    if n == "DIRT":
        g = grid(0); noise(g, 1, 0.22, r); noise(g, 3, 0.03, r)
        return g
    if n == "COBBLE":
        g = bricks(2, 1, (2, 6), (0, 4)); noise(g, 3, 0.07, r, only=[2])
        return g
    if n == "BRIDGE":
        g = grid(2)
        for x in (1, 3, 5, 7):
            vline(g, x, 2, 13, 1)
        hline(g, 0, 0, 7, 1); hline(g, 1, 0, 7, 0); hline(g, 14, 0, 7, 0); hline(g, 15, 0, 7, 1)
        for x in (0, 4):
            put(g, x, 1, 2); put(g, x, 14, 2)
        return g
    if n == "WATER":
        g = grid(1)
        for y in range(H):
            x = (y * 5 + 2) % 8
            if y % 3 == 0:
                put(g, x, y, 3); put(g, (x + 1) % 8, y, 3)
        noise(g, 3, 0.04, r); noise(g, 2, 0.015, r)
        return g
    if n in ("WATERL", "WATERR"):
        g = grid(1)
        for y in range(H):
            w = 2 + ((y // 3) % 2)
            if n == "WATERL":
                hline(g, y, 0, w, 0); put(g, w + 1, y, 3)
                if y % 4 == 1: put(g, w, y, 3)
            else:
                hline(g, y, 7 - w, 7, 0); put(g, 6 - w, y, 3)
                if y % 4 == 2: put(g, 7 - w, y, 3)
        noise(g, 3, 0.04, r, only=[1])
        return g
    if n == "TREE":                         # salice: chioma verde scura con i rami che pendono
        return A("...33...", "..3313..", ".331333.", "33133133", "31331331", "33313313", "13133133", "31331313",
                 "31313131", "3.31313.", "3.3121.3", "..3121.3", "3..12..3", "...12...", "..2112..", ".21..12.")
    if n == "BUSH":                         # ceppo marcio con i funghi
        return A("........", "........", "..1..3..", "........", "...33...", "..3223..", "...22...", "..1111..",
                 ".122221.", ".121121.", ".122221.", ".121221.", "11222211", ".111111.", "..3..3..", "........")
    if n == "FLOWERS":                      # ninfee e giunchi
        return A("........", ".3...3..", ".3...3..", ".3..232.", "232..3..", ".3...3..", "........", "...3....",
                 "..232...", "...3..3.", "...3..3.", "......3.", ".3...232", ".3....3.", "232.....", ".3......")
    if n == "BROOF":                        # paglia nera di catrame
        g = grid(1)
        for by in range(4):
            hline(g, by * 4 + 3, 0, 7, 2)
            for x in range(by % 2, 8, 2):
                put(g, x, by * 4 + 2, 2)
        noise(g, 3, 0.07, r, only=[1])
        return g
    if n == "BROOFA":                       # assi con il muschio
        g = grid(1)
        for x in (2, 5):
            vline(g, x, 0, 15, 2)
        for y in (5, 11):
            hline(g, y, 0, 7, 2)
        noise(g, 3, 0.16, r, only=[1])
        return g
    if n == "BROOFL":                       # scandole
        g = grid(1)
        for by in range(4):
            for x in range(W):
                if (x + by * 2) % 4 == 0:
                    vline(g, x, by * 4, by * 4 + 2, 2)
            hline(g, by * 4 + 3, 0, 7, 2)
        noise(g, 3, 0.05, r, only=[1])
        return g
    if n == "BWALL":                        # tavole verticali
        g = grid(2)
        for x in (2, 5):
            vline(g, x, 0, 15, 1)
        hline(g, 15, 0, 7, 1)
        for x, y in ((0, 3), (3, 3), (6, 3), (0, 11), (3, 11), (6, 11)):
            put(g, x, y, 1)
        noise(g, 3, 0.04, r, only=[2])
        return g
    if n == "SPIRE":                        # ruota del mulino
        return A("..1111..", ".122221.", "12122121", "12211221", "12122121", "12211221", "12122121", "11111111",
                 "12122121", "12211221", "12122121", "12211221", "12122121", ".122221.", "..1111..", "3.3..3.3")
    if n == "FENCE":                        # pali legati
        g = grid(0); noise(g, 1, 0.04, r)
        for x in (1, 4, 7):
            vline(g, x, 3, 13, 2); put(g, x, 2, 1)
        hline(g, 7, 0, 7, 1)
        return g
    if n == "FENCEV":
        g = grid(0); noise(g, 1, 0.04, r)
        vline(g, 3, 0, 15, 2); vline(g, 4, 0, 15, 1)
        for y in (2, 9):
            hline(g, y, 2, 5, 2)
        return g
    if n == "GRAVE":                        # pietra sprofondata
        return A("........", "........", "...22...", "..2222..", "..2112..", "..2222..", "..2112..", "..2222..",
                 ".322223.", "33222233", "1.3113.1", "..1111..", "........", ".3......", "......1.", "........")
    return None


# ------------------------------------------------------------------------------------------------------------- neve
def snow(n, r, base):
    """The Last Camp: neve (0 bianco), grigio scuro (1: roccia, ombre), marrone (2: tronchi, pelli), ciano (3: ghiaccio)"""
    if n == "GRASSA":
        g = grid(0); noise(g, 3, 0.04, r)
        return g
    if n == "GRASSB":                       # ciuffi d'erba secca che spuntano
        g = grid(0); noise(g, 3, 0.03, r)
        for x, y in ((2, 5), (5, 11), (6, 3)):
            put(g, x, y, 1); put(g, x - 1, y - 1, 2); put(g, x + 1, y - 1, 2); put(g, x, y - 2, 2)
        return g
    if n == "GRASSC":                       # sasso con la neve sopra
        return A("........", "........", ".....3..", "........", "........", "...00...", "..1..1..", ".1....1.",
                 ".1.1..1.", ".111111.", "..3333..", "........", ".3......", "........", "......3.", "........")
    if n == "PATH":                         # neve calpestata, fango
        g = grid(2); noise(g, 0, 0.16, r); noise(g, 1, 0.08, r)
        return g
    if n == "DIRT":
        g = grid(2); noise(g, 1, 0.2, r)
        return g
    if n == "COBBLE":                       # tavolato di tronchi
        g = grid(2)
        for y in (3, 7, 11, 15):
            hline(g, y, 0, 7, 1)
        for x, y in ((0, 1), (4, 5), (2, 9), (6, 13)):
            put(g, x, y, 1); put(g, x + 1, y, 1)
        noise(g, 0, 0.04, r, only=[2])
        return g
    if n == "WATER":                        # ghiaccio con le crepe
        g = grid(3)
        for x, y in ((1, 1), (2, 2), (3, 2), (4, 3), (4, 4), (5, 5), (6, 5), (2, 9), (3, 10), (3, 11), (4, 12), (5, 12),
                     (6, 13), (0, 7), (1, 7), (7, 14)):
            put(g, x, y, 0)
        noise(g, 1, 0.025, r)
        return g
    if n in ("WATERL", "WATERR"):
        g = grid(3)
        for y in range(H):
            w = 2 + ((y // 4) % 2)
            if n == "WATERL":
                hline(g, y, 0, w, 0); put(g, w + 1, y, 1)
            else:
                hline(g, y, 7 - w, 7, 0); put(g, 6 - w, y, 1)
        noise(g, 0, 0.05, r, only=[3])
        return g
    if n == "TREE":                         # abete carico di neve
        return A("...11...", "...01...", "..0011..", "..1111..", ".001111.", ".111111.", "..0011..", ".001111.",
                 "00111111", "11111111", ".0001111", "00011111", "11111111", "...22...", "...22...", "..3223..")
    if n == "BUSH":                         # masso
        return A("........", "........", "........", "..0000..", ".001111.", "00111111", "01111211", "11121111",
                 "11111111", "11211121", "11111111", ".111111.", "..3333..", "........", "........", "........")
    if n == "FLOWERS":                      # cristalli di brina
        return A("........", "..3.....", ".333....", "..3...3.", ".....333", "......3.", "........", "...3....",
                 "..333...", "...3....", "........", ".3....3.", "333..333", ".3....3.", "........", "........")
    if n == "BROOF":                        # tenda di pelli cucite
        g = grid(2)
        for by in range(4):
            hline(g, by * 4 + 3, 0, 7, 1)
            for x in ((1, 5) if by % 2 else (3, 7)):
                put(g, x, by * 4 + 1, 1)
        hline(g, 0, 0, 7, 0)
        noise(g, 0, 0.06, r, only=[2])
        return g
    if n == "BROOFA":                       # tenda a strisce
        g = grid(2)
        for y in range(H):
            for x in range(W):
                if (x // 2) % 2 == 0:
                    g[y][x] = 3
        hline(g, 0, 0, 7, 0); hline(g, 15, 0, 7, 1); hline(g, 8, 0, 7, 1)
        return g
    if n == "BROOFL":                       # tetto di tronchi con la neve
        g = grid(2)
        for x in (1, 3, 5, 7):
            vline(g, x, 0, 15, 1)
        for x, y0, y1 in ((0, 0, 4), (2, 0, 2), (4, 0, 5), (6, 0, 3), (2, 9, 11), (6, 10, 12)):
            vline(g, x, y0, y1, 0)
        hline(g, 0, 0, 7, 0)
        return g
    if n == "BWALL":                        # tronchi orizzontali
        g = grid(2)
        for y in (3, 7, 11, 15):
            hline(g, y, 0, 7, 1)
        for x, y in ((2, 1), (6, 5), (1, 9), (5, 13)):
            put(g, x, y, 1); put(g, x + 1, y, 1)
        return g
    if n == "SPIRE":                        # stendardo
        return A("...1....", "...13333", "...13303", "...13333", "...1333.", "...133..", "...13...", "...1....",
                 "...1....", "...1....", "...1....", "...1....", "...1....", "..212...", ".00100..", "........")
    if n == "FENCE":                        # palizzata di pali appuntiti
        g = grid(0)
        for x in range(0, 8, 2):
            vline(g, x, 4, 14, 2); vline(g, x + 1, 5, 14, 1); put(g, x, 3, 2); put(g, x, 2, 0 if x % 4 else 2)
        hline(g, 9, 0, 7, 1); hline(g, 15, 0, 7, 3)
        return g
    if n == "FENCEV":
        g = grid(0)
        for y in range(0, 16, 4):
            hline(g, y + 1, 2, 5, 2); hline(g, y + 2, 2, 5, 2); hline(g, y + 3, 2, 5, 1); put(g, 3, y, 2)
        return g
    if n == "STALL":                        # casse e rastrelliera delle armi
        return A("1.1..1.1", "1.1..1.1", "1.1..1.1", "11111111", "1.1..1.1", "1.1..1.1", "22222222", "21222212",
                 "22122122", "22211222", "22122122", "21222212", "22222222", "11111111", ".3....3.", "........")
    if n == "LAMP":                         # braciere
        return A("...3....", "..3.3...", "...33...", "..3333..", ".133331.", ".111111.", "..1111..", "...11...",
                 "...11...", "..1..1..", "..1..1..", ".1....1.", ".1....1.", "........", "..3333..", "........")
    if n == "GRAVE":                        # tumulo di pietre
        return A("........", "........", "...1....", "...1....", ".11111..", "...1....", "...1....", "..000...",
                 ".01110..", "0111110.", "11211111", "11111211", ".111111.", "..3333..", "........", "........")
    return None


# ------------------------------------------------------------------------------------------------------------ rovine
def ruins(n, r, base):
    """Ruin's Gate: cenere (0 grigio), nero (1: carbone), grigio chiaro (2: macerie, ossa), rosso (3: braci, lava)"""
    if n == "GRASSA":
        g = grid(0); noise(g, 1, 0.06, r); noise(g, 2, 0.02, r)
        return g
    if n == "GRASSB":                       # braci
        g = grid(0); noise(g, 1, 0.08, r)
        for x, y in ((2, 4), (5, 9), (3, 13)):
            put(g, x, y, 3); put(g, x + 1, y, 1); put(g, x, y + 1, 1)
        return g
    if n == "GRASSC":                       # macerie
        return A("........", "....1...", "........", "..22....", ".2221...", ".2211...", "..11..2.", ".....221",
                 "......11", "........", ".1......", "...2....", "..221...", "..11....", "........", "......1.")
    if n == "PATH":                         # strada di lastre spaccate
        g = grid(2)
        for x, y in ((0, 3), (1, 3), (2, 4), (3, 4), (4, 4), (4, 5), (5, 6), (6, 6), (7, 6), (3, 5), (3, 6), (2, 7),
                     (2, 8), (2, 9), (1, 10), (0, 11), (5, 11), (5, 12), (6, 13), (7, 13), (5, 10), (4, 14), (4, 15)):
            put(g, x, y, 1)
        noise(g, 0, 0.1, r, only=[2])
        return g
    if n == "DIRT":
        g = grid(1); noise(g, 0, 0.3, r); noise(g, 3, 0.03, r)
        return g
    if n == "COBBLE":
        g = bricks(2, 1, (2, 6), (0, 4))
        for x, y in ((1, 0), (1, 1), (5, 9), (6, 9), (5, 10), (3, 13)):
            put(g, x, y, 0)
        noise(g, 3, 0.02, r, only=[2])
        return g
    if n == "BRIDGE":                       # lastroni di pietra
        g = grid(2)
        for y in (0, 15):
            hline(g, y, 0, 7, 1)
        for x in (3, 7):
            vline(g, x, 1, 7, 1)
        for x in (1, 5):
            vline(g, x, 8, 14, 1)
        hline(g, 7, 0, 7, 1)
        put(g, 2, 3, 0); put(g, 6, 11, 0); put(g, 6, 12, 0)
        return g
    if n == "WATER":                        # lava con la crosta
        g = grid(3)
        for x, y in ((1, 1), (2, 1), (2, 2), (5, 4), (6, 4), (6, 5), (5, 5), (1, 8), (2, 8), (1, 9), (4, 11), (5, 11),
                     (5, 12), (6, 12), (0, 14), (7, 14), (3, 6)):
            put(g, x, y, 1)
        for x, y in ((4, 2), (0, 5), (3, 9), (7, 9), (2, 13)):
            put(g, x, y, 2)
        return g
    if n in ("WATERL", "WATERR"):
        g = grid(3)
        for y in range(H):
            w = 2 + ((y // 3) % 2)
            if n == "WATERL":
                hline(g, y, 0, w, 0); put(g, w + 1, y, 1); put(g, w, y, 1 if y % 2 else 0)
            else:
                hline(g, y, 7 - w, 7, 0); put(g, 6 - w, y, 1); put(g, 7 - w, y, 1 if y % 2 else 0)
        noise(g, 1, 0.06, r, only=[3])
        return g
    if n == "TREE":                         # albero bruciato
        return A("1.....1.", ".1...1..", ".1..1..1", "..1.1.1.", "3.11.1..", ".1.111..", "..1113.1", "...11.1.",
                 "1..111..", ".1.11...", "..111...", "...11...", "...11...", "..1111..", ".11..11.", "1......1")
    if n == "BUSH":                         # mucchio di macerie
        return A("........", "........", "........", "....2...", "...221..", "..22211.", ".2212221", ".2122211",
                 "22221221", "22122211", "21222121", "12221211", ".1111111", "..3..1..", "........", "........")
    if n == "FLOWERS":                      # ossa e piccole fiamme
        return A("........", "..3.....", ".33.....", ".313....", "..1...2.", ".....22.", "..2.22..", "..222...",
                 ".22.2...", ".2......", ".....3..", "....33..", "....313.", ".....1..", "........", "..1.....")
    if n == "BROOF":                        # travi bruciate, il tetto non c'e' piu'
        g = grid(0)
        for x in (1, 5):
            vline(g, x, 0, 15, 1)
        for y in (2, 9, 13):
            hline(g, y, 0, 7, 1)
        for x, y in ((3, 5), (6, 6), (2, 11), (7, 14)):
            put(g, x, y, 3)
        noise(g, 1, 0.1, r, only=[0])
        return g
    if n == "BROOFA":                       # tegole rimaste a chiazze
        g = grid(1)
        for by in range(4):
            hline(g, by * 4 + 3, 0, 7, 2)
        for x, y, w in ((0, 0, 3), (5, 1, 2), (2, 5, 4), (0, 9, 2), (4, 10, 3), (1, 13, 5)):
            hline(g, y, x, x + w, 0); hline(g, y + 1, x, x + w - 1, 0)
        noise(g, 3, 0.04, r, only=[1])
        return g
    if n == "BROOFL":
        g = grid(1)
        for y in range(H):
            for x in range(W):
                if (x + y) % 4 == 0:
                    g[y][x] = 2
        for x, y in ((1, 2), (2, 2), (2, 3), (5, 8), (6, 8), (5, 9), (6, 9), (3, 13), (4, 13)):
            put(g, x, y, 0)
        noise(g, 3, 0.04, r, only=[1])
        return g
    if n == "BWALL":                        # muro crepato
        g = bricks(2, 1)
        for x, y in ((4, 0), (4, 1), (5, 2), (5, 4), (4, 5), (4, 6), (3, 8), (3, 9), (2, 10), (2, 12), (1, 13)):
            put(g, x, y, 1)
        put(g, 6, 9, 0); put(g, 6, 10, 0); put(g, 0, 5, 0)
        return g
    if n == "WINDOW":                       # finestra vuota, il fuoco dentro
        g = ruins("BWALL", r, base)
        for y in range(3, 13):
            hline(g, y, 1, 6, 1)
        for x, y in ((2, 11), (3, 10), (3, 11), (4, 11), (5, 12), (2, 12), (3, 12), (4, 12), (4, 9)):
            put(g, x, y, 3)
        hline(g, 13, 0, 7, 1)
        return g
    if n == "CHIMNEY":                      # comignolo spezzato
        return A("........", "..1.....", "........", "......1.", "........", "..2.....", "..22.2..", "..2222..",
                 "..2112..", "..2222..", "..1221..", "..2222..", "..2112..", "1.2222.1", "11222211", "11111111")
    if n == "SPIRE":                        # guglia spezzata
        return A("........", "........", "........", "....2...", "...22...", "...21...", "..122...", "..2221..",
                 "..2122..", ".122221.", ".221222.", ".222122.", "12222221", "22122212", "22221222", "11111111")
    if n == "FENCE":                        # steccato rotto
        return A("........", "........", "........", "2.......", "1......2", "1...2..1", "11111..1", "1...1...",
                 "1...1..1", "1.11111.", "1......1", "1......1", "1......1", "........", "..1.....", "........")
    if n == "FENCEV":
        return A("...11...", "...11...", "..2112..", "..1111..", "...11...", "...1....", "........", "....1...",
                 "...11...", "...11...", "..2112..", "..1111..", "...11...", "...11...", "...1....", "........")
    if n == "STALL":                        # carro bruciato
        return A("........", "........", "..3.....", ".33..1..", ".3...11.", "11111111", "12121211", "11212121",
                 "11111111", ".1....1.", "111..111", "1.1..1.1", "111..111", ".1....1.", "........", "..1..1..")
    if n == "LAMP":                         # lampione piegato, spento
        return A("........", "........", "..111...", ".1...1..", ".1....1.", ".3....1.", "......1.", ".....11.",
                 ".....1..", "....11..", "....1...", "....1...", "....1...", "....1...", "...111..", "..11111.")
    if n == "WELL":                         # pozzo crollato
        return A("........", "........", "........", "........", "......1.", "..1.....", "........", "..2222..",
                 ".221122.", "22111122", "21111112", "21131112", "22111122", ".222222.", "..1111..", "........")
    return None


# ------------------------------------------------------------------------------------------------------------ abisso
def abyss(n, r, base):
    """La citta' dell'Abisso: pietra blu (0), nero (1: il vuoto), azzurro (2: mura, cristallo), viola (3: bagliore)"""
    if n == "GRASSA":
        g = grid(0)
        for x, y in ((1, 3), (2, 3), (3, 4), (5, 10), (6, 10), (6, 11)):
            put(g, x, y, 1)
        return g
    if n == "GRASSB":                       # runa incisa
        return A("........", "........", "..3333..", ".3....3.", ".3.33.3.", ".3.3..3.", ".3.33.3.", ".3....3.",
                 "..3333..", "........", "........", "1.......", ".1......", "......1.", "........", "........")
    if n == "GRASSC":                       # scheggia di cristallo
        return A("........", "........", "......1.", ".....1..", "........", "..2.....", "..22....", ".2232...",
                 ".2322...", ".22321..", "..2211..", "...11...", "........", ".1......", "..1.....", "........")
    if n == "PATH":                         # lastre chiare
        g = grid(2)
        hline(g, 7, 0, 7, 1); hline(g, 15, 0, 7, 1)
        vline(g, 3, 0, 6, 1); vline(g, 7, 8, 14, 1)
        for x, y in ((1, 2), (5, 4), (2, 11), (5, 12)):
            put(g, x, y, 0)
        return g
    if n == "DIRT":
        g = grid(0); noise(g, 2, 0.1, r); noise(g, 1, 0.06, r)
        return g
    if n == "COBBLE":                       # mosaico
        g = grid(2)
        for y in range(H):
            for x in range(W):
                if (x + y // 2) % 4 == 0:
                    g[y][x] = 0
        for y in (7, 15):
            hline(g, y, 0, 7, 1)
        for x, y in ((2, 3), (6, 11)):
            put(g, x, y, 3)
        return g
    if n == "BRIDGE":                       # ponte di luce
        g = grid(3)
        hline(g, 0, 0, 7, 2); hline(g, 15, 0, 7, 2); hline(g, 1, 0, 7, 1); hline(g, 14, 0, 7, 1)
        for y in range(2, 14):
            for x in range(W):
                if (x + y) % 4 == 0:
                    g[y][x] = 2
        return g
    if n == "WATER":                        # il vuoto, qualche stella
        g = grid(1)
        for x, y, c in ((2, 2, 2), (6, 6, 3), (1, 10, 3), (5, 13, 2), (4, 4, 3)):
            put(g, x, y, c)
        return g
    if n in ("WATERL", "WATERR"):           # orlo spezzato della pietra
        g = grid(1)
        for y in range(H):
            w = (2, 3, 3, 2, 1, 2, 3, 2, 2, 1, 2, 3, 3, 2, 1, 2)[y]
            if n == "WATERL":
                hline(g, y, 0, w, 0); put(g, w + 1, y, 2)
            else:
                hline(g, y, 7 - w, 7, 0); put(g, 6 - w, y, 2)
        put(g, 5 if n == "WATERL" else 2, 9, 3)
        return g
    if n == "TREE":                         # guglia di cristallo
        return A("...2....", "...22...", "..232...", "..2321..", "..2321..", ".223221.", ".2232212", ".2332212",
                 "22332212", "22332211", "2233221.", "2233221.", "22332211", "12222111", ".111111.", "..1..1..")
    if n == "BUSH":                         # grappolo di cristalli
        return A("........", "........", "........", "....2...", ".2..22..", ".22.23..", ".23.231.", ".23.2312",
                 "223122.2", "22312232", "22312231", "12211221", ".111111.", "..1..1..", "........", "........")
    if n == "FLOWERS":                      # funghi luminosi
        return A("........", "..33....", ".3333...", "..22....", "..2...3.", ".....333", "......2.", "......2.",
                 ".33.....", "3333....", ".22..3..", ".2..333.", ".....2..", "........", "1.......", "........")
    if n == "BROOF":                        # ardesia nera con le vene viola
        g = grid(1)
        for by in range(4):
            hline(g, by * 4 + 3, 0, 7, 3)
            put(g, (by * 3 + 1) % 8, by * 4 + 1, 2)
        hline(g, 0, 0, 7, 2)
        return g
    if n == "BROOFA":                       # scaglie
        g = grid(1)
        for by in range(4):
            y0 = by * 4
            for x in range(W):
                put(g, x, y0 + (1 if (x + by * 2) % 4 < 2 else 2), 3)
            hline(g, y0 + 3, 0, 7, 2 if by == 3 else 1)
        return g
    if n == "BROOFL":
        g = grid(1)
        for y in range(H):
            for x in range(W):
                if (x + y) % 4 == 0:
                    g[y][x] = 2
                elif (x + y) % 4 == 2 and y % 2:
                    g[y][x] = 3
        return g
    if n == "BWALL":                        # blocchi lisci con una vena
        g = bricks(2, 1, (3,), (7,))
        for x, y in ((1, 1), (5, 5), (2, 9), (6, 13)):
            put(g, x, y, 3)
        return g
    if n == "SPIRE":                        # corno con il globo
        return A("...33...", "..3223..", "..3223..", "...33...", "...22...", "...22...", "..2112..", "..2112..",
                 "..2112..", ".221122.", ".221122.", ".221122.", "22211222", "22211222", "22211222", "11111111")
    if n == "FENCE":                        # catena fra due pilastrini
        return A("........", "........", "........", "22....22", "23....32", "22....22", "21.11.12", "211..112",
                 "21....12", "21....12", "21....12", "22....22", "11....11", "........", "..1.....", "........")
    if n == "FENCEV":
        return A("...1....", "...1....", "..222...", "..232...", "..222...", "...1....", "...1....", "...1....",
                 "...1....", "...1....", "..222...", "..232...", "..222...", "...1....", "...1....", "...1....")
    if n == "GRAVE":                        # statua senza volto
        return A("........", "...22...", "..2112..", "..2112..", "...22...", "..2222..", ".222222.", ".2.22.2.",
                 ".2.22.2.", "...22...", "...22...", "..2222..", ".222222.", ".111111.", "........", "........")
    if n == "GRAVE2":                       # obelisco
        return A("........", "...2....", "...22...", "...22...", "..232...", "..2321..", "..2321..", "..2321..",
                 "..2321..", "..2321..", "..2221..", "..2221..", ".222211.", ".222211.", ".111111.", "........")
    if n == "STALL":                        # altare
        return A("........", "...3....", "..333...", "...3....", "22222222", "21111112", ".222222.", "..2112..",
                 "..2112..", "..2332..", "..2112..", "..2112..", ".222222.", "22222222", "11111111", "........")
    if n == "WELL":                         # pozzo senza fondo
        return A("........", "........", "..2222..", ".221122.", "22111122", "21111112", "21131112", "21111112",
                 "21111112", "21113112", "22111122", ".221122.", "..2222..", "..1111..", "........", "........")
    return None


THEMES = {"swamp": swamp, "snow": snow, "ruins": ruins, "abyss": abyss}

VILLAGES = {
    1: dict(name="Aldric's Crossing", theme=None, pal=(5, 9, 15, 3), map="data/town_map.txt", names={}),
    2: dict(name="Blackwater Mill", theme="swamp", pal=(9, 0, 12, 5), map="data/town_map2.txt", names={
        "GRASSA": ("Mud", "wet ground"), "GRASSB": ("Reeds", "mud with reeds"), "GRASSC": ("Puddle", "mud with a black puddle"),
        "PATH": ("Boardwalk", "plank walkway"), "DIRT": ("Peat", "dark soft ground"), "BRIDGE": ("Pier", "planks over the black water"),
        "WATER": ("Black water", "the marsh: black water with green scum"), "WATERL": ("Marsh bank W", "mud, reeds, water"),
        "WATERR": ("Marsh bank E", "water, reeds, mud"), "TREE": ("Willow", "weeping willow"), "BUSH": ("Rotten stump", "stump with mushrooms"),
        "FLOWERS": ("Water lilies", "lilies and rushes"), "BROOF": ("Tar thatch", "black thatched roof"),
        "BROOFA": ("Mossy planks", "plank roof with moss"), "BROOFL": ("Shingles", "shingle roof"), "BWALL": ("Plank wall", "vertical boards"),
        "SPIRE": ("Mill wheel", "the water wheel of the mill"), "FENCE": ("Tied poles", "pole fence"), "FENCEV": ("Pole fence V", "vertical pole fence"),
        "GRAVE": ("Sunken stone", "a gravestone sinking into the mud")}),
    3: dict(name="The Last Camp", theme="snow", pal=(1, 11, 9, 3), map="data/town_map3.txt", names={
        "GRASSA": ("Snow", "fresh snow"), "GRASSB": ("Dry tufts", "snow with dry grass"), "GRASSC": ("Snowy stone", "a stone under the snow"),
        "PATH": ("Trodden snow", "mud and snow"), "DIRT": ("Frozen mud", "dark frozen ground"), "COBBLE": ("Log floor", "duckboards of the camp"),
        "WATER": ("Ice", "the frozen stream"), "WATERL": ("Ice bank W", "snow, then ice"), "WATERR": ("Ice bank E", "ice, then snow"),
        "TREE": ("Fir", "fir loaded with snow"), "BUSH": ("Boulder", "boulder with a snow cap"), "FLOWERS": ("Frost", "frost crystals"),
        "BROOF": ("Hide tent", "tent of sewn hides"), "BROOFA": ("Striped tent", "striped canvas"), "BROOFL": ("Log roof", "logs with snow"),
        "BWALL": ("Log wall", "horizontal logs"), "SPIRE": ("Banner", "the standard of the camp"), "FENCE": ("Palisade", "pointed stakes"),
        "FENCEV": ("Palisade V", "pointed stakes, vertical"), "STALL": ("Supplies", "weapon rack and crates"), "LAMP": ("Brazier", "iron brazier"),
        "GRAVE": ("Cairn", "pile of stones with a marker")}),
    4: dict(name="Ruin's Gate", theme="ruins", pal=(12, 0, 15, 2), map="data/town_map4.txt", names={
        "GRASSA": ("Ash", "ground covered with ash"), "GRASSB": ("Embers", "ash with live embers"), "GRASSC": ("Rubble", "ash with rubble"),
        "PATH": ("Broken road", "cracked slabs"), "DIRT": ("Scorched earth", "burnt ground"), "COBBLE": ("Broken paving", "paving with holes"),
        "BRIDGE": ("Stone slabs", "slabs over the lava"), "WATER": ("Lava", "lava with a black crust"), "WATERL": ("Lava bank W", "ash, crust, lava"),
        "WATERR": ("Lava bank E", "lava, crust, ash"), "TREE": ("Burnt tree", "a dead black tree"), "BUSH": ("Rubble heap", "pile of stones"),
        "FLOWERS": ("Bones", "bones and small flames"), "BROOF": ("Burnt beams", "the roof is gone"), "BROOFA": ("Broken tiles", "patches of tiles"),
        "BROOFL": ("Broken slates", "slates with holes"), "BWALL": ("Cracked wall", "cracked masonry"), "WINDOW": ("Empty window", "fire inside"),
        "CHIMNEY": ("Broken chimney", "what is left of a chimney"), "SPIRE": ("Broken spire", "the stump of a spire"),
        "FENCE": ("Broken fence", "a few boards"), "FENCEV": ("Broken fence V", "a few posts"), "STALL": ("Burnt cart", "a cart, burnt"),
        "LAMP": ("Bent lamp", "a street lamp, bent and dark"), "WELL": ("Fallen well", "a well full of embers")}),
    5: dict(name="The City of the Abyss", theme="abyss", pal=(6, 0, 14, 4), map="data/town_map5.txt", names={
        "GRASSA": ("Blue stone", "floor of the city"), "GRASSB": ("Rune", "a rune carved in the floor"), "GRASSC": ("Shard", "a crystal shard"),
        "PATH": ("Pale slabs", "the streets of the city"), "DIRT": ("Dust", "stone dust"), "COBBLE": ("Mosaic", "mosaic floor"),
        "BRIDGE": ("Light bridge", "a bridge of light over the void"), "WATER": ("Void", "the void, a few stars"), "WATERL": ("Edge W", "broken edge of the stone"),
        "WATERR": ("Edge E", "broken edge of the stone"), "TREE": ("Crystal spire", "a tall crystal"), "BUSH": ("Crystals", "cluster of crystals"),
        "FLOWERS": ("Glow caps", "luminous mushrooms"), "BROOF": ("Veined slate", "black slate with violet veins"), "BROOFA": ("Scales", "scale roof"),
        "BROOFL": ("Woven roof", "diagonal weave"), "BWALL": ("Smooth blocks", "blocks with a vein"), "SPIRE": ("Horn", "horn with an orb"),
        "FENCE": ("Chain", "chain between two posts"), "FENCEV": ("Chain V", "vertical chain"), "GRAVE": ("Faceless statue", "a statue without a face"),
        "GRAVE2": ("Obelisk", "a small obelisk"), "STALL": ("Altar", "an altar"), "WELL": ("Bottomless well", "a well with no bottom")}),
}
NVIL = len(VILLAGES)


def theme_tile(theme, name, base):
    """griglia del tile `name` nel tema (None = quella del villaggio 1). base(name) = make_tile di gen_gfx."""
    if theme is None:
        return None
    r = random.Random("%s/%s" % (theme, name))
    return THEMES[theme](name, r, base)
