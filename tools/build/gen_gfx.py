#!/usr/bin/env python3
"""Genera charset (tile 16x16 multicolor), sprite e costanti per il gioco C64.

Uscite:
  out/work/gfx/charset.bin   2048 byte  (256 caratteri)
  out/work/gfx/sprites.bin   2048 byte  (32 sprite da 64 byte)
  out/work/gfx_consts.inc  costanti per 64tass
  out/work/gfx/tiles.png, out/work/gfx/sprites.png  anteprime
"""
import random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rng = random.Random(1985)

# ----------------------------------------------------------------- tile ids
TILES = [
    "WALL", "WALLFACE", "FLOOR", "FLOORB", "FLOORC", "STAIRSD", "STAIRSU", "DHOME",
    "FREE8", "FREE9", "FREE10", "FREE11",  # liberi nei dungeon (06/11 sera: tolti gli oggetti a terra); villaggio: lapidi, cripta
    "GRASSA", "GRASSB", "PATH", "BWALL", "BROOF", "DSMITH", "DALCH",
    "SIGNL",                              # 09/11: nel posto lasciato dall'armaiolo (insegna dell'alchimista)
    "FOUNTAIN", "PORTAL", "TREE", "TSTAIRS",
    "CHEST", "FREE25", "FREE26",          # 10/11: un solo tile per i bauli (il tipo sta in ch_t); 25-26 liberi nei dungeon
    # arredi della citta'
    "COBBLE", "FOUNT0", "FOUNT1", "FOUNT2", "FOUNT3", "FLOWERS", "WINDOW", "WELL",   # 10/11: WINDOW al posto del barile
    "FENCE", "LAMP", "BUSH", "STALL",
    # facciate dei negozi: tetti diversi e insegne
    "BROOFA", "BROOFL", "SIGNS",
    "CHIMNEY",                            # 10/11: comignolo (al posto del fieno)
    "FENCEV", "SPIRE",                    # 10/11: steccato verticale a linea sola, guglia con la croce (chiesa)
]
SOLID = {"FREE9", "FREE10", "FREE11", "FREE25", "FREE26", "WALL", "WALLFACE", "BWALL", "BROOF", "TREE",
         "FOUNT0", "FOUNT1", "FOUNT2", "FOUNT3", "WINDOW", "WELL", "FENCE", "LAMP", "BUSH", "STALL", "BROOFA", "BROOFL", "SIGNS", "SIGNL",
         "CHIMNEY", "FENCEV", "SPIRE",
         "WATER", "WATERL", "WATERR", "GRAVE", "GRAVE2", "CRYPTL", "CRYPTR", "CRYPTA", "CRYPTB", "CRYPTC", "HDOOR"}
TID = {n: i for i, n in enumerate(TILES)}
NTILE_MAX = 48
# Villaggio (file GFX0): stessi 45 posti, ma quelli che in citta' non servono (muri, pavimenti, scale, posti liberi
# 8-11, bauli) ospitano tile solo del villaggio. I tile con un ruolo nel codice (porte, fontana, portale, cripta
# = TSTAIRS, erba, strade...) restano allo stesso posto (assert sotto). I nuovi tile nei posti 5, 6, 8-11, 24-26
# sono SOLIDI (ci si puo' stare sopra solo sui posti 0-4), cosi' il codice delle scale/raccolta non li vede mai.
TOWN_TILES = list(TILES)
TOWN_TILES[0:7] = ["GRASSC", "BRIDGE", "DIRT", "HDOOR", "WATER", "WATERL", "WATERR"]
TOWN_TILES[8:12] = ["GRAVE", "GRAVE2", "CRYPTL", "CRYPTR"]
TOWN_TILES[24:27] = ["CRYPTA", "CRYPTB", "CRYPTC"]
TTID = {n: i for i, n in enumerate(TOWN_TILES)}
# Legenda dei tile di dungeon (posti 0..DUN_NT-1 dei file GFX1/GFX2): un carattere per posto, usato dall'atlante grafico
# (tools/atlas/gen_atlas.py, data/atlas_dungeon.txt) e utile se un giorno si disegnano piani a mano. DUN_USED = posti che il
# codice dei dungeon mette davvero nella mappa; gli altri contengono la grafica del villaggio rimasta nel file.
DUN_LEGEND = {"WALL": "#", "WALLFACE": "=", "FLOOR": ".", "FLOORB": ",", "FLOORC": "`", "STAIRSD": ">", "STAIRSU": "<",
              "DHOME": "H", "FREE8": "1", "FREE9": "2", "FREE10": "3", "FREE11": "4", "GRASSA": "a", "GRASSB": "b",
              "PATH": ":", "BWALL": "W", "BROOF": "R", "DSMITH": "S", "DALCH": "L", "SIGNL": "7", "FOUNTAIN": "~",
              "PORTAL": "O", "TREE": "T", "TSTAIRS": "^", "CHEST": "c", "FREE25": "5", "FREE26": "6"}
DUN_USED = {"WALL", "WALLFACE", "FLOOR", "FLOORB", "FLOORC", "STAIRSD", "STAIRSU",
            "PORTAL", "CHEST"}
# sala del trono (file GFX8, tema 8; fino al 19/11 anche GFX2/4/6, i piani del boss dei capitoli): stessi posti, ma 7 = leva, 12 = linee della stella, 13 = cerchio del pentacolo
# (15/11, TODO C2) 8 = portale nero della leva (posto libero nei dungeon; l'unico dei posti liberi che si puo' calpestare)
TRONO_NAMES = {"DHOME": "LEVER", "GRASSA": "STAR", "GRASSB": "CIRCLE", "FREE8": "BLACKP"}
TRONO_USED = DUN_USED - {"STAIRSD"} | {"DHOME", "GRASSA", "GRASSB", "FREE8"}
for _n in ("DHOME", "GRASSA", "GRASSB", "PATH", "BWALL", "BROOF", "DSMITH", "DALCH", "SIGNL", "FOUNTAIN", "PORTAL",
           "TREE", "TSTAIRS", "COBBLE", "FLOWERS"):
    assert TTID[_n] == TID[_n], _n
assert all(n in SOLID for i, n in enumerate(TOWN_TILES) if i in (5, 6, 8, 9, 10, 11, 24, 25, 26)), "posti speciali: solo tile solidi"

W, H = 8, 16  # tile in pixel multicolor (8 larghi x 16 alti)


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


def rect(g, x0, y0, x1, y1, c, fill=None):
    if fill is not None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                put(g, x, y, fill)
    hline(g, y0, x0, x1, c); hline(g, y1, x0, x1, c)
    vline(g, x0, y0, y1, c); vline(g, x1, y0, y1, c)


def noise(g, c, dens, only=None, r=rng):
    for y in range(H):
        for x in range(W):
            if r.random() < dens and (only is None or g[y][x] in only):
                g[y][x] = c


def ellipse(g, cx, cy, rx, ry, c):
    for y in range(H):
        for x in range(W):
            # un pixel MC e' largo il doppio: compenso nell'asse x
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                g[y][x] = c


def floor_base(variant=0):
    g = grid(0)
    hline(g, 0, 0, 7, 1)
    hline(g, 8, 0, 7, 1)
    vline(g, 0, 0, 7, 1)
    vline(g, 4, 8, 15, 1)
    noise(g, 1, 0.04, only=[0])
    return g


def cobble_base():
    """selciato: ciottoli grigi (2) con fughe marroni (1)"""
    g = grid(2)
    for by in range(4):
        y = by * 4 + 3
        hline(g, y, 0, 7, 1)
        offs = (2, 6) if by % 2 == 0 else (0, 4)
        for x in offs:
            vline(g, x, by * 4, by * 4 + 2, 1)
    noise(g, 3, 0.03, only=[2])
    return g


_FC = None


def fountain_canvas():
    """fontana 2x2 tile = 16x32 pixel MC: vasca di pietra, acqua, piedistallo e getto"""
    global _FC
    if _FC is not None:
        return _FC
    cw, ch = 16, 32
    cv = [[2] * cw for _ in range(ch)]
    for y in range(ch):                                  # fondo selciato
        for x in range(cw):
            cv[y][x] = 2
    for by in range(8):
        y = by * 4 + 3
        for x in range(cw):
            cv[y][x] = 1
        offs = (2, 6, 10, 14) if by % 2 == 0 else (0, 4, 8, 12)
        for x in offs:
            for yy in range(by * 4, by * 4 + 3):
                cv[yy][x] = 1

    def ell(cx, cy, rx, ry, c):
        for y in range(ch):
            for x in range(cw):
                dx = (x + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    cv[y][x] = c
    ell(8, 19, 7.9, 12.4, 1)          # bordo scuro
    ell(8, 19, 7.1, 11.5, 2)          # orlo di pietra
    ell(8, 19, 5.9, 9.8, 1)           # ombra interna
    ell(8, 19, 5.2, 8.9, 3)           # acqua
    for (x, y) in ((4, 15), (5, 24), (11, 22), (10, 14), (6, 27), (12, 19), (3, 20), (9, 28)):
        cv[y][x] = 2                  # riflessi
    ell(8, 19, 2.6, 4.2, 1)           # piedistallo
    ell(8, 19, 1.9, 3.4, 2)
    for y in range(4, 17):            # colonna e getto
        cv[y][7] = 2
        cv[y][8] = 2
    for y in range(1, 6):
        cv[y][7] = 3
        cv[y][8] = 3
    for (x, y) in ((6, 1), (9, 1), (5, 2), (10, 2), (4, 4), (11, 4), (3, 7), (12, 7), (3, 10), (12, 10),
                   (4, 12), (11, 12), (5, 5), (10, 5), (4, 8), (11, 8)):
        cv[y][x] = 3                  # arco d'acqua
    _FC = cv
    return cv


def make_tile(name):
    g = grid(0)
    if name == "WALL":
        g = grid(1)
        noise(g, 0, 0.22)
        noise(g, 2, 0.04)
    elif name == "WALLFACE":
        g = grid(2)
        for by in range(4):
            y = by * 4 + 3
            hline(g, y, 0, 7, 0)
            offs = (3, 7) if by % 2 == 0 else (1, 5)
            for x in offs:
                vline(g, x, by * 4, by * 4 + 2, 0)
        hline(g, 0, 0, 7, 3)   # bordo illuminato in alto
        noise(g, 1, 0.12, only=[2])
    elif name == "FLOOR":
        g = floor_base()
    elif name == "FLOORB":
        g = floor_base()
        for i in range(5):
            put(g, 1 + i // 2, 2 + i * 2, 1)
        put(g, 5, 11, 2)
    elif name == "FLOORC":
        g = floor_base()
        for (x, y) in ((2, 3), (3, 3), (3, 4), (5, 12)):
            put(g, x, y, 2)
    elif name == "STAIRSD":
        g = grid(1)
        rect(g, 0, 0, 7, 15, 3)
        rect(g, 1, 1, 6, 14, 2)
        rect(g, 2, 2, 5, 13, 1)
        rect(g, 3, 3, 4, 12, 0, fill=0)
    elif name == "STAIRSU":
        g = grid(1)
        for y in range(H):
            m = y % 4
            for x in range(W):
                g[y][x] = (3, 2, 2, 1)[m]
        vline(g, 0, 0, 15, 0); vline(g, 7, 0, 15, 0)
    elif name in ("FREE8", "FREE9", "FREE10", "FREE11", "FREE25", "FREE26"):
        floor_base()                     # (stesso consumo del generatore casuale dei vecchi tile: gli altri tile
        g = grid(0)                      #  restano identici) posto libero, nessuna grafica
    elif name == "CHEST":                 # 10/11: unico tile dei bauli (normale, con la chiave, d'oro, epico)
        g = floor_base()
        art = {
            # 1 = contorno scuro, 2 = legno/corpo, 3 = metallo chiaro
            "CHEST": [
                "........",
                "..1111..",
                ".122221.",
                "12322321",
                "12322321",
                "11111111",
                "12333321",
                "12311321",
                "12333321",
                "12322321",
                "12322321",
                "11111111",
                ".1....1.",
            ],
        }[name]
        for y, row in enumerate(art):
            for x, ch in enumerate(row):
                if ch != ".":
                    put(g, x, y + 2, int(ch))
    elif name == "GRASSA":
        g = grid(0)
        noise(g, 1, 0.07)
    elif name == "GRASSB":
        g = grid(0)
        for _ in range(7):
            x, y = rng.randrange(1, 7), rng.randrange(2, 15)
            put(g, x, y, 1); put(g, x - 1, y - 1, 1); put(g, x + 1, y - 1, 1)
        if rng.random() < 0.9:
            put(g, rng.randrange(1, 7), rng.randrange(2, 14), 3)
    elif name == "PATH":
        g = grid(1)
        noise(g, 2, 0.12)
        noise(g, 0, 0.03)
    elif name == "BWALL":
        g = grid(2)
        for by in range(4):
            y = by * 4 + 3
            hline(g, y, 0, 7, 1)
            offs = (3, 7) if by % 2 == 0 else (1, 5)
            for x in offs:
                vline(g, x, by * 4, by * 4 + 2, 1)
    elif name == "BROOF":
        g = grid(1)
        for by in range(4):
            hline(g, by * 4 + 3, 0, 7, 2)
            hline(g, by * 4, 0, 7, 0 if by == 0 else 1)
        noise(g, 2, 0.06)
    elif name == "BROOFA":                # armeria: tegole a scaglie
        g = grid(1)
        for by in range(4):
            y0 = by * 4
            for x in range(W):
                if (x + by * 2) % 4 < 2:
                    put(g, x, y0 + 1, 2)
                else:
                    put(g, x, y0 + 2, 2)
            hline(g, y0 + 3, 0, 7, 0 if by == 3 else 1)
        noise(g, 2, 0.03)
    elif name == "BROOFL":                # alchimista: strisce oblique
        g = grid(1)
        for y in range(H):
            for x in range(W):
                if (x + y) % 4 < 2:
                    g[y][x] = 2
        for by in range(4):
            hline(g, by * 4 + 3, 0, 7, 1)
    elif name in ("SIGNS", "SIGNL"):   # insegna appesa al muro
        g = grid(2)
        for by in range(4):
            y = by * 4 + 3
            hline(g, y, 0, 7, 1)
            offs = (3, 7) if by % 2 == 0 else (1, 5)
            for x in offs:
                vline(g, x, by * 4, by * 4 + 2, 1)
        rect(g, 1, 3, 6, 12, 0, fill=1)
        vline(g, 3, 0, 2, 0); vline(g, 4, 0, 2, 0)     # catenella
        def pts(rows):
            return [(x, y) for y, xs in rows for x in xs]
        icon = {"SIGNS": pts([(5, (2, 3, 4, 5)), (6, (2, 3, 4)), (7, (3, 4)), (8, (3, 4)), (9, (2, 3, 4, 5)), (10, (2, 3, 4, 5))]),
                "SIGNL": pts([(5, (3, 4)), (6, (3, 4)), (7, (2, 3, 4, 5)), (8, (2, 5)), (9, (2, 3, 4, 5)), (10, (2, 3, 4, 5))])}[name]
        for (x, y) in icon:
            put(g, x, y, 3)
    elif name in ("DSMITH", "DALCH", "DHOME"):
        g = grid(2)
        for by in range(4):
            y = by * 4 + 3
            hline(g, y, 0, 7, 1)
        rect(g, 1, 1, 6, 15, 0, fill=1)     # porta
        hline(g, 1, 1, 6, 2)
        vline(g, 3, 2, 15, 0)
        put(g, 5, 9, 3)                      # maniglia
        icon = {"DSMITH": [(3, 4), (3, 5), (3, 6), (2, 7), (3, 7), (4, 7)],
                "DALCH": [(3, 4), (3, 5), (2, 6), (3, 6), (4, 6)],
                "DHOME": [(2, 4), (3, 4), (4, 4), (2, 5), (3, 5), (4, 5), (5, 5),       # boccale (09/11, locanda)
                          (2, 6), (3, 6), (4, 6), (5, 6), (2, 7), (3, 7), (4, 7)]}[name]
        for (x, y) in icon:
            put(g, x, y, 3)
    elif name == "FOUNTAIN":
        g = cobble_base()                 # vasca bassa davanti alla fontana: si cammina e cura
        ellipse(g, 4, 8, 4.0, 6.6, 1)
        ellipse(g, 4, 8, 3.5, 5.9, 3)
        for (x, y) in ((2, 5), (5, 7), (3, 10), (6, 12), (1, 9)):
            put(g, x, y, 2)
    elif name == "COBBLE":
        g = cobble_base()
    elif name in ("FOUNT0", "FOUNT1", "FOUNT2", "FOUNT3"):
        cv = fountain_canvas()
        i = int(name[-1])
        y0, x0 = (i // 2) * 16, (i % 2) * 8
        g = [row[x0:x0 + 8] for row in cv[y0:y0 + 16]]
    elif name == "FLOWERS":
        g = grid(0)
        noise(g, 1, 0.05)
        for (x, y, c) in ((1, 4, 3), (5, 3, 2), (3, 8, 2), (6, 10, 3), (1, 12, 3), (4, 13, 2)):
            put(g, x, y, c)
            put(g, x, y + 1, 1); put(g, x, y + 2, 1)
    elif name == "WINDOW":                # 10/11: finestra in un muro di mattoni (cornice, vetri, traversa, davanzale)
        g = make_tile("BWALL")
        rect(g, 1, 3, 6, 12, 1, fill=3)
        hline(g, 7, 2, 5, 1)                      # traversa
        put(g, 2, 4, 2); put(g, 5, 9, 2)          # riflessi
        hline(g, 13, 0, 7, 1)                     # davanzale
    elif name == "WELL":
        g = grid(0)
        noise(g, 1, 0.05)
        for r_, (a_, b_) in enumerate(((3, 4), (2, 5), (1, 6), (0, 7))):
            hline(g, 1 + r_, a_, b_, 1)               # tettino
        vline(g, 1, 5, 9, 1); vline(g, 6, 5, 9, 1)   # pali
        ellipse(g, 4, 12, 3.9, 3.6, 2)
        ellipse(g, 4, 12, 2.9, 2.5, 0)
        ellipse(g, 4, 12, 2.2, 1.7, 3)
        hline(g, 11, 3, 4, 2)
    elif name == "FENCE":
        g = grid(0)
        noise(g, 1, 0.05)
        hline(g, 6, 0, 7, 1); hline(g, 10, 0, 7, 1)
        for x in (0, 7):
            vline(g, x, 4, 13, 1)
            put(g, x, 3, 2)
    elif name == "LAMP":
        g = cobble_base()
        vline(g, 3, 5, 14, 2); vline(g, 4, 5, 14, 2)
        hline(g, 15, 2, 5, 1)
        ellipse(g, 4, 3, 2.2, 2.6, 3)
        hline(g, 5, 2, 5, 2)
        put(g, 3, 2, 2); put(g, 4, 2, 2)
    elif name == "BUSH":
        g = grid(0)
        noise(g, 1, 0.05)
        ellipse(g, 4, 10.5, 3.8, 5, 1)
        noise(g, 0, 0.3, only=[1])
        for (x, y) in ((2, 8), (5, 11), (3, 13)):
            put(g, x, y, 3)                           # bacche
    elif name == "STALL":
        g = cobble_base()
        for y in range(0, 7):
            for x in range(W):
                g[y][x] = 3 if (x // 2) % 2 == 0 else 2      # tendone a strisce
        hline(g, 6, 0, 7, 1)
        rect(g, 0, 7, 7, 15, 1, fill=1)
        hline(g, 8, 0, 7, 2)                           # bancone
        for (x, y) in ((1, 10), (3, 10), (5, 10), (2, 12), (4, 12), (6, 12)):
            put(g, x, y, 3 if (x + y) % 2 else 2)        # merce
    elif name == "PORTAL":               # 06/11: arco di pietra in piedi con un ovale luminoso nel vano (non tondo e
        g = grid(0)                      # basso come la fontana: si riconosce dalla forma anche con gli stessi colori)
        for y in range(16):
            for x in range(8):
                if y >= 3 or abs(x - 3.5) <= (1.5, 2.5, 3.5)[y]:
                    g[y][x] = 2          # pietra
        for y in range(3, 16):
            for x in range(2, 6):
                if y >= 4 or x in (3, 4):
                    g[y][x] = 1          # vano scuro
        for (x, y) in ((3, 5), (4, 5), (2, 6), (5, 6), (2, 7), (5, 7), (2, 8), (5, 8), (2, 9), (5, 9), (2, 10), (5, 10),
                       (2, 11), (5, 11), (3, 12), (4, 12), (3, 8), (4, 9)):
            put(g, x, y, 3)              # ovale luminoso con un lampo al centro
        for (x, y) in ((0, 7), (7, 7), (0, 12), (7, 12), (1, 15), (6, 15)):
            put(g, x, y, 1)              # giunti fra le pietre
    elif name == "TREE":
        g = grid(0)
        ellipse(g, 4, 8, 3.9, 7.8, 1)
        noise(g, 0, 0.35, only=[1])
        noise(g, 2, 0.05, only=[1])
        for y in range(H):
            for x in range(W):
                if g[y][x] == 0:
                    pass
    elif name == "TSTAIRS":               # porta della cripta (ingresso del dungeon): arco di pietra, buio dentro
        g = grid(2)
        noise(g, 1, 0.08)
        rect(g, 1, 2, 6, 15, 1, fill=0)
        hline(g, 1, 2, 5, 1)
        put(g, 2, 2, 1); put(g, 5, 2, 1)
        rect(g, 2, 3, 5, 15, 0, fill=0)
        vline(g, 3, 4, 6, 3); vline(g, 4, 4, 6, 3)   # scalini che scendono (riflesso)
        hline(g, 8, 3, 4, 2); hline(g, 11, 3, 4, 2)
    elif name == "CHIMNEY":               # 10/11: comignolo di mattoni su un tetto qualunque (fondo marrone come i tetti)
        g = grid(1)
        hline(g, 0, 0, 7, 0)
        rect(g, 2, 3, 5, 15, 2, fill=2)
        for y in (6, 9, 12):
            hline(g, y, 2, 5, 1)
        vline(g, 3, 7, 8, 1); vline(g, 4, 10, 11, 1); vline(g, 3, 13, 14, 1)
        hline(g, 2, 1, 6, 2); hline(g, 3, 1, 6, 1)   # cappello
        put(g, 3, 1, 3); put(g, 4, 0, 3)              # fumo
    elif name == "FENCEV":                # 10/11: steccato verticale a linea sola (lati del cimitero e dei giardini)
        g = grid(0)
        noise(g, 1, 0.05)
        vline(g, 3, 0, 15, 1); vline(g, 4, 0, 15, 1)
        for py in (3, 11):                        # paletti con la punta chiara
            hline(g, py, 2, 5, 1); hline(g, py + 1, 2, 5, 1)
            put(g, 3, py - 1, 2); put(g, 4, py - 1, 2)
    elif name == "SPIRE":                 # 10/11: guglia con la croce (sopra il campanile e la torretta della chiesa)
        g = grid(0)
        noise(g, 1, 0.04)
        vline(g, 3, 0, 5, 2); vline(g, 4, 0, 5, 2)
        hline(g, 1, 2, 5, 2)                      # croce
        for y in range(6, 16):
            hw = (y - 4) // 3
            hline(g, y, 3 - hw, 4 + hw, 1)
            if y % 3 == 0:
                hline(g, y, 3 - hw, 4 + hw, 2)    # tegole
    elif name == "GRASSC":                # erba con una pietra e un ciuffo
        g = grid(0)
        noise(g, 1, 0.05)
        put(g, 2, 6, 2); put(g, 3, 6, 2); put(g, 2, 7, 2)
        put(g, 6, 12, 1); put(g, 5, 11, 1); put(g, 7, 11, 1)
    elif name == "DIRT":                  # terra battuta (sentiero del cimitero)
        g = grid(1)
        noise(g, 0, 0.10)
        noise(g, 2, 0.04)
    elif name == "BRIDGE":                # ponte di legno sul ruscello (assi orizzontali, parapetti)
        g = grid(1)
        for y in range(2, 14, 3):
            hline(g, y, 0, 7, 0)
        hline(g, 0, 0, 7, 2); hline(g, 15, 0, 7, 2)
        hline(g, 1, 0, 7, 2); hline(g, 14, 0, 7, 2)
        for x in (0, 7):
            put(g, x, 2, 2); put(g, x, 13, 2)
    elif name == "WATER":                 # ruscello: acqua con riflessi
        g = grid(3)
        for y in range(H):
            x = (y * 3) % 8
            put(g, x, y, 2); put(g, (x + 4) % 8, y + 1 if y + 1 < H else y, 2)
        noise(g, 2, 0.06)
    elif name == "WATERL":                # sponda sinistra: erba, poi acqua
        g = grid(3)
        for y in range(H):
            w = 2 + ((y // 3) % 2)
            hline(g, y, 0, w, 0)
            put(g, w + 1, y, 1)
        noise(g, 2, 0.05, only=[3])
    elif name == "WATERR":                # sponda destra
        g = grid(3)
        for y in range(H):
            w = 5 - ((y // 3) % 2)
            hline(g, y, w, 7, 0)
            put(g, w - 1, y, 1)
        noise(g, 2, 0.05, only=[3])
    elif name == "GRAVE":                 # lapide arrotondata
        g = grid(0)
        noise(g, 1, 0.05)
        ellipse(g, 4, 5, 2.6, 3.0, 2)
        rect(g, 2, 5, 5, 12, 2, fill=2)
        hline(g, 7, 3, 4, 1); hline(g, 9, 3, 4, 1)
        hline(g, 13, 1, 6, 1)
    elif name == "GRAVE2":                # croce di pietra
        g = grid(0)
        noise(g, 1, 0.05)
        vline(g, 3, 2, 12, 2); vline(g, 4, 2, 12, 2)
        hline(g, 5, 1, 6, 2); hline(g, 6, 1, 6, 2)
        hline(g, 13, 2, 5, 1); hline(g, 14, 1, 6, 1)
    elif name in ("CRYPTL", "CRYPTR"):    # fianchi della cripta: blocchi di pietra, una fessura
        g = grid(2)
        for by in range(4):
            y = by * 4 + 3
            hline(g, y, 0, 7, 1)
            offs = (2, 6) if by % 2 == 0 else (0, 4)
            for x in offs:
                vline(g, x, by * 4, by * 4 + 2, 1)
        noise(g, 1, 0.06, only=[2])
        xx = 5 if name == "CRYPTL" else 2
        vline(g, xx, 5, 9, 0)
    elif name in ("CRYPTA", "CRYPTC"):    # tetto spiovente della cripta (pietra scura)
        g = grid(0)
        noise(g, 1, 0.05)
        for y in range(H):
            lim = int((15 - y) * 8 / 16)
            if name == "CRYPTA":
                hline(g, y, lim, 7, 2)
                if y >= 2:
                    put(g, lim, y, 1)
            else:
                hline(g, y, 0, 7 - lim, 2)
                if y >= 2:
                    put(g, 7 - lim, y, 1)
        for y in range(3, 16, 4):
            if name == "CRYPTA":
                hline(g, y, int((15 - y) * 8 / 16) + 1, 7, 1)
            else:
                hline(g, y, 0, 6 - int((15 - y) * 8 / 16), 1)
    elif name == "CRYPTB":                # fronte della cripta: teschio sull'arco
        g = grid(2)
        hline(g, 0, 0, 7, 1)
        for y in range(4, 16, 4):
            hline(g, y, 0, 7, 1)
        ellipse(g, 4, 7, 2.6, 3.4, 0)
        ellipse(g, 4, 7, 2.1, 2.9, 3)
        put(g, 3, 6, 0); put(g, 5, 6, 0)          # occhi
        put(g, 4, 8, 0)
        hline(g, 10, 3, 5, 0); put(g, 3, 11, 0); put(g, 5, 11, 0)
    elif name == "HDOOR":                 # porta di una casa qualunque (chiusa)
        g = grid(2)
        for by in range(4):
            y = by * 4 + 3
            hline(g, y, 0, 7, 1)
            offs = (3, 7) if by % 2 == 0 else (1, 5)
            for x in offs:
                vline(g, x, by * 4, by * 4 + 2, 1)
        rect(g, 2, 3, 5, 15, 1, fill=1)
        rect(g, 3, 4, 4, 14, 0, fill=0)
        put(g, 4, 10, 3)
    return g


def lever_tile():
    """Leva sospetta (sala del trono): piastra sul pavimento, asta inclinata, pomello."""
    g = floor_base()
    rect(g, 1, 11, 6, 14, 1, fill=1)                  # piastra
    hline(g, 11, 1, 6, 3)
    for i in range(8):                                # asta inclinata
        put(g, 2 + i // 2, 11 - i, 2)
    ellipse(g, 6, 3, 1.4, 1.6, 3)                     # pomello
    return g


def black_portal_tile():
    """Portale nero della leva (sala del trono, palette 4: 0 nero, 1 rosso, 2 rosa, 3 giallo; colori condivisi dallo schermo,
    quindi niente blu o grigio): stesso arco del portale normale, ma pietra rossa scura con il bordo rosa in alto e
    all'esterno, vano e ovale NERI (pixel 0) con un vortice rosso. Niente giallo: il portale normale e' giallo."""
    g = grid(0)
    for y in range(16):
        for x in range(8):
            if y >= 3 or abs(x - 3.5) <= (1.5, 2.5, 3.5)[y]:
                g[y][x] = 1                       # pietra rossa
    for y in range(16):
        for x in range(8):
            if g[y][x] == 1 and (y in (0, 1, 2) or x in (0, 7) or y == 15):
                g[y][x] = 2                       # bordo rosa, sul nero del pavimento
    for y in range(3, 15):
        for x in range(2, 6):
            if y >= 4 or x in (3, 4):
                g[y][x] = 0                       # vano nero
    for (x, y) in ((3, 6), (4, 7), (3, 8), (4, 9), (3, 10), (4, 11), (2, 12), (5, 5), (2, 7), (5, 10)):
        put(g, x, y, 1)                           # vortice rosso scuro nel nero
    return g


def tile_chars(g):
    """ritorna 4 caratteri (TL, TR, BL, BR) da 8 byte"""
    out = []
    for (y0, x0) in ((0, 0), (0, 4), (8, 0), (8, 4)):
        bs = []
        for y in range(y0, y0 + 8):
            v = 0
            for x in range(x0, x0 + 4):
                v = (v << 2) | g[y][x]
            bs.append(v)
        out.append(bs)
    return out


# ----------------------------------------------------------------- glifi HUD (hires 8x8, codici $18..$38)
HUDFONT = {
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["01110","10001","00001","00010","00100","01000","11111"],
    "3": ["11110","00001","00001","01110","00001","00001","11110"],
    "4": ["00010","00110","01010","10010","11111","00010","00010"],
    "5": ["11111","10000","11110","00001","00001","10001","01110"],
    "6": ["00110","01000","10000","11110","10001","10001","01110"],
    "7": ["11111","00001","00010","00100","01000","01000","01000"],
    "8": ["01110","10001","10001","01110","10001","10001","01110"],
    "9": ["01110","10001","10001","01111","00001","00010","01100"],
    "/": ["00001","00010","00010","00100","01000","01000","10000"],
    "H": ["10001","10001","10001","11111","10001","10001","10001"],
    "P": ["11110","10001","10001","11110","10000","10000","10000"],
    "X": ["10001","10001","01010","00100","01010","10001","10001"],
    "F": ["11111","10000","10000","11110","10000","10000","10000"],
    "L": ["10000","10000","10000","10000","10000","10000","11111"],
    "V": ["10001","10001","10001","10001","01010","01010","00100"],
    "M": ["10001","11011","10101","10101","10001","10001","10001"],
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "S": ["01111","10000","10000","01110","00001","00001","11110"],
    "W": ["10001","10001","10001","10101","10101","11011","10001"],
    "I": ["01110","00100","00100","00100","00100","00100","01110"],
    "R": ["11110","10001","10001","11110","10100","10010","10001"],
    "N": ["10001","11001","10101","10101","10011","10001","10001"],
    "D": ["11110","10001","10001","10001","10001","10001","11110"],
    "B": ["11110","10001","10001","11110","10001","10001","11110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "E": ["11111","10000","10000","11110","10000","10000","11111"],
    "C": ["01110","10001","10000","10000","10000","10001","01110"],
    "Y": ["10001","10001","01010","00100","00100","00100","00100"],
    "G": ["01110","10001","10000","10111","10001","10001","01111"],
    "J": ["00111","00010","00010","00010","00010","10010","01100"],
    "K": ["10001","10010","10100","11000","10100","10010","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "Q": ["01110","10001","10001","10001","10101","10010","01101"],
    "U": ["10001","10001","10001","10001","10001","10001","01110"],
    "Z": ["11111","00001","00010","00100","01000","10000","11111"],
}
# I codici carattere di un tile i sono i, 64+i, 128+i, 192+i. I glifi HUD stanno nei codici
# liberi: gruppo A subito dopo i tile (cifre contigue), gruppo B (barre contigue) a 104.. (dopo i
# TR dei tile). Il codice 63 resta vuoto (minimappa) e 176/177/240+ sono riservati.
HUD_A = ["0","1","2","3","4","5","6","7","8","9","SLASH","BLANK"]
HUD_B = ["BAR0","BAR1","BAR2","BAR3","BAR4","BAR5","BAR6","BAR7","BAR8",
         "POT","SCR","DOT","RULE","KEY"]
LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
HUD_BASE = len(TILES)
HUD_BASE_B = 64 + len(TILES) + 1
assert HUD_BASE + len(HUD_A) <= 63, "glifi HUD gruppo A oltre il codice 62"
assert HUD_BASE_B + len(HUD_B) <= 128, "glifi HUD gruppo B oltre 127"
# le 26 lettere (codice = ordine alfabetico nei posti liberi) riempiono gli spazi rimasti nei due gruppi
# e i codici liberi dei quarti 2 e 3 (176/177 sono le scale della minimappa, 240.. i quadranti): HUD_FREE = gli avanzi
LET_SLOTS = (list(range(HUD_BASE + len(HUD_A), 63)) + list(range(HUD_BASE_B + len(HUD_B), 128))
             + list(range(128 + HUD_BASE, 176)) + list(range(178, 192)) + list(range(192 + HUD_BASE, 240)))
assert len(LET_SLOTS) >= 26, "non bastano i codici liberi per l'alfabeto HUD"
HUD_WARN = ["WSWORD", "WARMOR", "WSHIELD", "LVUP"]   # icone degli avvisi nell'HUD (oggetto che si sta per rompere; LVUP 11/11: punti da spendere, tasto C)
assert len(LET_SLOTS) >= 26 + len(HUD_WARN), "non bastano i codici liberi per le icone degli avvisi HUD"
HUD_FREE = LET_SLOTS[26 + len(HUD_WARN):]     # codici ancora liberi (riserva)
HUD_NAMES = HUD_A + HUD_B + LETTERS + HUD_WARN
HUD_ID = {n: HUD_BASE + i for i, n in enumerate(HUD_A)}
HUD_ID.update({n: HUD_BASE_B + i for i, n in enumerate(HUD_B)})
HUD_ID.update({n: LET_SLOTS[i] for i, n in enumerate(LETTERS)})
HUD_ID.update({n: LET_SLOTS[26 + i] for i, n in enumerate(HUD_WARN)})


def hud_glyph(name):
    if name in HUDFONT or name == "SLASH":
        key = "/" if name == "SLASH" else name
        return [0] + [int(r, 2) << 2 for r in HUDFONT[key]]
    if name == "BLANK":
        return [0] * 8
    if name == "POT":
        return [0x18, 0x18, 0x3C, 0x7E, 0x7E, 0x7E, 0x3C, 0x00]
    if name == "SCR":
        return [0x7E, 0x42, 0x5A, 0x42, 0x5A, 0x42, 0x7E, 0x00]
    if name == "DOT":                    # trattino: posizione di un posto della cintura (HUD)
        return [0, 0x7E, 0, 0, 0, 0, 0, 0]
    if name == "RULE":
        return [0, 0, 0, 0, 0, 0, 0, 0xAA]   # multicolor %10: colore del regolo = BGCOL2 della palette
    if name == "WSWORD":                 # spada obliqua (avviso: arma che si sta per rompere)
        return [0x03, 0x07, 0x0E, 0x5C, 0x38, 0x30, 0x48, 0x80]
    if name == "WARMOR":                 # corpetto
        return [0x24, 0xE7, 0xFF, 0x7E, 0x7E, 0x7E, 0x3C, 0x00]
    if name == "WSHIELD":                # scudo
        return [0x7E, 0xFF, 0xDB, 0xFF, 0x7E, 0x7E, 0x3C, 0x18]
    if name == "LVUP":                   # (11/11) freccia in su: punti statistica da spendere (tasto C)
        return [0x18, 0x3C, 0x7E, 0xFF, 0x18, 0x18, 0x18, 0x00]
    if name == "KEY":
        return [0x38, 0x44, 0x44, 0x38, 0x10, 0x18, 0x10, 0x18]
    if name.startswith("BAR"):
        n = int(name[3:])
        if n == 0:                       # cella vuota: binario sottile (disegnato in colore scuro)
            return [0, 0, 0, 0x55, 0xAA, 0, 0, 0]
        fill = (0xFF << (8 - n)) & 0xFF  # piena/parziale: blocco a tutta altezza, senza contorno
        return [0, fill, fill, fill, fill, fill, fill, 0]
    raise KeyError(name)


def build_charset(names=TILES):
    cs = [[0] * 8 for _ in range(256)]
    tilegrids = {}
    for i, n in enumerate(names):
        g = make_tile(n)
        tilegrids[n] = g
        tl, tr, bl, br = tile_chars(g)
        cs[i] = tl; cs[64 + i] = tr; cs[128 + i] = bl; cs[192 + i] = br
    # glifi minimappa: 16 combinazioni di quadranti (colore %11), codice 240+idx
    for idx in range(16):
        rows = []
        for r in range(8):
            top = r < 4
            left = (idx & (1 if top else 4)) != 0
            right = (idx & (2 if top else 8)) != 0
            rows.append((0xF0 if left else 0) | (0x0F if right else 0))
        cs[240 + idx] = rows
    # scale giu' / su (pattern misto %11/%10), codici 176, 177
    cs[176] = [0xFF, 0xAA, 0xA5, 0xA5, 0xA5, 0xA5, 0xAA, 0xFF]
    cs[177] = [0xFF, 0xFF, 0xAA, 0xAA, 0xFF, 0xFF, 0xAA, 0xFF]
    for n, c in HUD_ID.items():
        assert not any(cs[c]), (n, c)
        cs[c] = hud_glyph(n)
    return cs, tilegrids


# ----------------------------------------------------------------- sprite
def sgrid(w=24, h=21):
    return [[0] * w for _ in range(h)]


def sput(g, x, y, c=1):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = c


def sellipse(g, cx, cy, rx, ry, c=1):
    for y in range(len(g)):
        for x in range(len(g[0])):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                g[y][x] = c


def srect(g, x0, y0, x1, y1, c=1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            sput(g, x, y, c)


def sline(g, x0, y0, x1, y1, c=1, thick=1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        for t in range(thick):
            sput(g, x + t, y, c)


def hires_bytes(g):
    out = []
    for y in range(21):
        for bx in range(3):
            v = 0
            for b in range(8):
                v = (v << 1) | (1 if g[y][bx * 8 + b] else 0)
            out.append(v)
    return out + [0]


def mc_bytes(g):
    """g: 12 x 21 con valori 0..3"""
    out = []
    for y in range(21):
        for bx in range(3):
            v = 0
            for p in range(4):
                v = (v << 2) | g[y][bx * 4 + p]
            out.append(v)
    return out + [0]


# ---- eroe (multicolor 12x21): 1 marrone, 2 pelle, 3 acciaio
HERO_DOWN = [
    "..3......3..",
    "..33....33..",
    "...333333...",
    "...333333...",
    "...222222...",
    "...212212...",
    "...222222...",
    "...211112...",
    ".3.111111.3.",
    ".3111111111.",
    ".2211331122.",
    ".2211111122.",
    ".2.111111.2.",
    ".2.133331.2.",
    "...111111...",
    "...11..11...",
    "...11..11...",
    "...11..11...",
    "...11..11...",
    "..111..111..",
    "..111..111..",
]
HERO_UP = [
    "..3......3..",
    "..33....33..",
    "...333333...",
    "...333333...",
    "...111111...",
    "...111111...",
    "...111111...",
    "...111111...",
    ".3.111111.3.",
    ".3111111111.",
    ".2211111122.",
    ".2211111122.",
    ".2.111111.2.",
    ".2.133331.2.",
    "...111111...",
    "...11..11...",
    "...11..11...",
    "...11..11...",
    "...11..11...",
    "..111..111..",
    "..111..111..",
]
HERO_LEFT = [
    "....3.......",
    "...33.......",
    "...3333.....",
    "...3333.....",
    "...2222.....",
    "..22122.....",
    "..22222.....",
    "...2111.....",
    "...11111....",
    "..3111111...",
    "..3112211...",
    "..3112211...",
    "..3.1111....",
    "..3.1331....",
    "....1111....",
    "....1111....",
    "....111.....",
    "....111.....",
    "....111.....",
    "...1111.....",
    "...1111.....",
]


def rows_to_grid(rows):
    return [[int(c) if c != "." else 0 for c in r] for r in rows]


def mirror_mc(g):
    return [list(reversed(r)) for r in g]


def hero_walk(g, f):
    """frame di camminata: sposto le gambe (righe 15..20)"""
    h = [list(r) for r in g]
    if f == 0:
        return h
    for y in range(15, 21):
        row = h[y]
        # alterno: gamba destra piu' in alto
        if y in (15, 16):
            h[y] = [0] * 12
            for x in range(12):
                if row[x] and x >= 6:
                    h[y][x] = row[x]
            for x in range(12):
                if row[x] and x < 6:
                    h[y - 0][x] = row[x]
            # gamba sinistra accorciata
        if y in (19, 20):
            h[y] = [0] * 12
            for x in range(12):
                if row[x]:
                    nx = x + (1 if x >= 6 else 0)
                    if 0 <= nx < 12:
                        h[y][nx] = row[x]
    # gamba sinistra piu' corta in frame 1
    for y in (19, 20):
        for x in range(0, 6):
            h[y][x] = 0
    h[19][3] = 1; h[19][4] = 1
    return h


def hero_sprites():
    import hero as H
    def walk(g, w):
        return g[:16] + w
    d, u, l = H.DOWN, H.UP, H.LEFT
    frames = [(d, walk(d, H.DOWN_W)), (u, walk(u, H.DOWN_W)), (l, walk(l, H.LEFT_W))]
    out = []
    for f0, f1 in frames:
        out.append(mc_bytes(rows_to_grid(f0)))
        out.append(mc_bytes(rows_to_grid(f1)))
    for f in (l, walk(l, H.LEFT_W)):             # destra = sinistra specchiata
        out.append(mc_bytes(mirror_mc(rows_to_grid(f))))
    return out


# ---- effetti
def slash_sprite(direction):
    g = sgrid()
    cx, cy = 12, 10
    import math
    # arco di taglio di fronte alla direzione
    ang0 = {0: 90, 1: 270, 2: 180, 3: 0}[direction]
    for a in range(-55, 56, 3):
        th = math.radians(ang0 + a)
        for rr in (8, 9, 10):
            x = round(cx + math.cos(th) * (rr + 1.5) * (1.0))
            y = round(cy + math.sin(th) * rr * 0.9)
            sput(g, x, y, 1)
    return hires_bytes(g)


def ring_sprite():
    g = sgrid()
    sellipse(g, 12, 10.5, 11.5, 10, 1)
    sellipse(g, 12, 10.5, 9.0, 7.6, 0)
    for k in range(0, 24, 4):
        sput(g, k, 10, 1)
    return hires_bytes(g)


# ---- mostri (hires 24x21)
def mon_fallen(f):
    g = sgrid()
    sellipse(g, 12, 6, 4.5, 4, 1)           # testa
    sput(g, 8, 1, 1); sput(g, 7, 0, 1); sput(g, 15, 1, 1); sput(g, 16, 0, 1)  # corna
    sput(g, 10, 5, 0); sput(g, 14, 5, 0); sput(g, 11, 8, 0); sput(g, 12, 8, 0); sput(g, 13, 8, 0)
    sellipse(g, 12, 13, 5.5, 4.5, 1)        # corpo
    off = 1 if f else 0
    sline(g, 7, 11, 3, 15 + off, 1, 2); sline(g, 17, 11, 21, 15 - off, 1, 2)
    srect(g, 8, 17, 10, 20 - off, 1); srect(g, 14, 17, 16, 20 - (1 - off), 1)
    return hires_bytes(g)


def mon_skeleton(f):
    g = sgrid()
    sellipse(g, 12, 4.5, 4.2, 4, 1)         # cranio
    for (x, y) in ((10, 4), (11, 4), (13, 4), (14, 4), (10, 5), (14, 5), (12, 7), (11, 7), (13, 7)):
        sput(g, x, y, 0)
    srect(g, 11, 8, 13, 9, 1)               # collo/colonna
    for y in (10, 12, 14):
        srect(g, 8, y, 16, y, 1)            # costole
    srect(g, 12, 9, 12, 16, 1)
    off = 1 if f else 0
    sline(g, 8, 10, 4, 14 + off, 1); sline(g, 16, 10, 20, 14 - off, 1)
    sline(g, 10, 16, 8, 20 - off, 1); sline(g, 14, 16, 16, 20 - (1 - off), 1)
    srect(g, 18, 8 - off, 19, 15, 1)        # arma
    return hires_bytes(g)


def mon_zombie(f):
    g = sgrid()
    sellipse(g, 12, 5.5, 4, 3.8, 1)
    sput(g, 10, 5, 0); sput(g, 14, 5, 0)
    sellipse(g, 12, 13, 7, 6, 1)            # corpo grosso
    off = 1 if f else 0
    srect(g, 2, 8 + off, 6, 10 + off, 1); srect(g, 18, 9 - off, 22, 11 - off, 1)
    srect(g, 7, 17, 10, 20 - off, 1); srect(g, 14, 17, 17, 20 - (1 - off), 1)
    for x in (9, 12, 15):
        sput(g, x, 12, 0)
    return hires_bytes(g)


def mon_imp(f):
    g = sgrid()
    sellipse(g, 12, 6, 4.2, 3.8, 1)
    for (x, y) in ((8, 3), (7, 2), (6, 1), (16, 3), (17, 2), (18, 1)):
        sput(g, x, y, 1)
    sput(g, 10, 6, 0); sput(g, 14, 6, 0); sput(g, 12, 8, 0)
    sellipse(g, 12, 13, 4.5, 4.5, 1)
    off = 1 if f else 0
    # ali
    sline(g, 7, 10, 1, 6 + off * 2, 1, 2); sline(g, 17, 10, 23, 6 + off * 2, 1, 1)
    srect(g, 0, 6 + off * 2, 2, 12, 1); srect(g, 21, 6 + off * 2, 23, 12, 1)
    srect(g, 9, 17, 10, 20 - off, 1); srect(g, 14, 17, 15, 20 - (1 - off), 1)
    return hires_bytes(g)


def mon_demon(f):
    g = sgrid()
    sellipse(g, 12, 5, 5, 4.2, 1)
    for (x, y) in ((7, 3), (6, 2), (5, 1), (4, 0), (17, 3), (18, 2), (19, 1), (20, 0)):
        sput(g, x, y, 1)
    for (x, y) in ((9, 5), (10, 5), (14, 5), (15, 5), (11, 8), (12, 8), (13, 8)):
        sput(g, x, y, 0)
    sellipse(g, 12, 13, 8, 6.5, 1)
    off = 1 if f else 0
    srect(g, 0, 7 + off * 2, 4, 14, 1); srect(g, 20, 7 + off * 2, 23, 14, 1)
    srect(g, 7, 17, 11, 20 - off, 1); srect(g, 13, 17, 17, 20 - (1 - off), 1)
    for x in (9, 12, 15):
        sput(g, x, 12, 0)
    return hires_bytes(g)


def hud_blank():
    return [0] * 64


def marker_sprite():
    g = sgrid()
    srect(g, 0, 0, 5, 5, 1)
    srect(g, 1, 1, 4, 4, 0)
    srect(g, 2, 2, 3, 3, 1)
    return hires_bytes(g)


def build_sprites():
    import monsters as M
    sp = [[0] * 64 for _ in range(32)]
    hero = hero_sprites()
    for i, d in enumerate(hero):
        sp[i] = d
    for d in range(4):
        sp[8 + d] = slash_sprite(d)
    for t, (_, fr, _) in enumerate(M.BASE):          # slot 12..19 (bank $A000): capitolo 1 (out/work/gfx/sprites.png, anteprima)
        sp[12 + t * 2] = mc_bytes(fr[0])
        sp[13 + t * 2] = mc_bytes(fr[1])
    sp[24] = hud_blank()
    sp[25] = marker_sprite()
    sp[26] = ring_sprite()
    return sp


def build_sprites2(mset=None):
    """16 slot a $8C00 (puntatori 48..63): varianti forti + posto del boss del set (tools/build/monsters.py chapter_set)"""
    import monsters as M
    base, strong, final = mset or M.chapter_set(1)
    sp = [[0] * 64 for _ in range(16)]
    for t, (_, fr, _) in enumerate(strong):
        sp[t * 2] = mc_bytes(fr[0])
        sp[t * 2 + 1] = mc_bytes(fr[1])
    sp[8] = mc_bytes(final[1][0])
    sp[9] = mc_bytes(final[1][1])
    return sp


def mon_bytes(mset):
    """sprite dei mostri base del set (slot 12..19 del banco $A000) e forti + boss ($8C00): vanno nel file del tema"""
    base = mset[0]
    mons = bytes(b for (_, fr, _) in base for f in range(2) for b in mc_bytes(fr[f]))
    strong = bytes(b for s in build_sprites2(mset)[0:10] for b in s)
    return mons, strong


# (15/11) blocco "info" in coda al file del tema: colori e nomi dei 9 tipi del set. gfx_install lo copia a NM_AT
# (fine degli slot sprite 58-63, $8Fxx: dopo il motivetto di combattimento SND_FBUF, persistente fino al tema dopo).
#   +0  9 byte  colore dello sprite dei tipi 1..9 (9 = posto del boss)           -> NM_AT-1+tipo (game.asm, build_sprites)
#   +9  9 byte  byte basso dell'indirizzo del nome del tipo 1..9 (tutto in una pagina: byte alto = >NM_AT)
#   +18 nomi    codici schermo, 0 finale (bar_name, bar.asm)
# Lunghezza fissa INFO_LEN (il blocco piu' lungo fra i file, gli altri riempiti con 0).
NM_TOP = 0x9000                      # NM_AT = NM_TOP - INFO_LEN


def scr_text(t):
    """testo -> codici schermo (ROM dei caratteri, maiuscole: la barra disegna i glifi della ROM)"""
    out = []
    for ch in t:
        if "a" <= ch <= "z":
            out.append(ord(ch) - 96)
        elif ch in " '-.":
            out.append(ord(ch))
        else:
            raise SystemExit("gen_gfx: carattere non ammesso nel nome di un mostro: %r (%s)" % (ch, t))
    return out


def info_raw(mset):
    """(colori, nomi in codici schermo) del set"""
    import monsters as M
    names = M.set_names(mset)
    cols = M.set_colors(mset)
    assert len(names) == 9 and all(0 < len(n) <= 24 for n in names), names   # 24 = larghezza della barra (nbuf)
    assert all(0 <= c <= 15 for c in cols)
    return cols, [scr_text(n) + [0] for n in names]


def info_len(raw):
    return 18 + sum(len(n) for n in raw[1])


def info_bytes(raw, n_len):
    cols, names = raw
    nm_at = NM_TOP - n_len
    lo, o = [], nm_at + 18
    for n in names:
        lo.append(o & 255)
        o += len(n)
    assert nm_at >> 8 == (o - 1) >> 8, "nomi dei mostri a cavallo di una pagina"
    d = bytes(cols) + bytes(lo) + bytes(b for n in names for b in n)
    return d + bytes(n_len - len(d))


# (12/11, committente) UN FILE DI GRAFICA PER CAPITOLO e tipo di piano: tile + mostri di quel capitolo.
# Per ogni capitolo c (1..CHAPTERS) due file: GFX(2c-1) = piani del dungeon, GFX(2c) = piano del boss (tile della sala
# del trono). Nessuna deduplica. (15/11) Ogni file porta il set di mostri del SUO capitolo (tools/build/monsters.py
# chapter_set: sprite, colori, nomi); il posto del boss: Lord of Ruin nei file del dungeon e nel piano del boss del
# capitolo 4, il boss del capitolo nei file del piano del boss dei capitoli 1-3.
CHAPTERS = 4


def M_names(m):
    import monsters as M
    return M.set_names(m)


def M_cols(m):
    import monsters as M
    return M.set_colors(m)


def chapter_sets():
    """[(numero del file, capitolo, boss?, set)] nell'ordine dei file GFX1..GFX(2*CHAPTERS)"""
    import monsters as M
    assert M.CHAPTERS == CHAPTERS
    out = []
    for c in range(1, CHAPTERS + 1):
        out.append((2 * c - 1, c, False, M.chapter_set(c, False)))
        out.append((2 * c, c, True, M.chapter_set(c, True)))
    return out


# ----------------------------------------------------------------- preview
C64 = [(0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189), (139, 63, 150), (85, 160, 73),
       (64, 49, 141), (191, 206, 114), (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80),
       (120, 120, 120), (148, 224, 137), (120, 105, 196), (159, 159, 159)]


def preview(cs, sp):
    pal_d = [C64[0], C64[11], C64[9], C64[7]]
    pal_t = [C64[5], C64[9], C64[15], C64[3]]
    sc = 4
    img = Image.new("RGB", (len(TILES) * 8 * 2 * sc + 8, 2 * 16 * sc + 24), (30, 30, 30))
    for row, pal in enumerate((pal_d, pal_t)):
        for i in range(len(TILES)):
            for part, (ox, oy) in enumerate(((0, 0), (4, 0), (0, 8), (4, 8))):
                code = (i, 64 + i, 128 + i, 192 + i)[part]
                for y in range(8):
                    b = cs[code][y]
                    for p in range(4):
                        c = (b >> (6 - 2 * p)) & 3
                        for yy in range(sc):
                            for xx in range(sc * 2):
                                X = i * 8 * 2 * sc + (ox + p) * 2 * sc + xx
                                Y = row * (16 * sc + 8) + (oy + y) * sc + yy
                                img.putpixel((X, Y), pal[c])
    img.save(os.path.join(ROOT, "out", "work", "gfx", "tiles.png"))
    # sprite
    sc = 3
    img = Image.new("RGB", (16 * 25 * sc + 8, 2 * 22 * sc + 8), (30, 30, 30))
    hero_pal = [(0, 0, 0), C64[9], C64[10], C64[15]]
    for i in range(27):
        mc = i < 8 or 12 <= i < 20
        d = sp[i]
        ox = (i % 16) * 25 * sc
        oy = (i // 16) * 22 * sc
        for y in range(21):
            for bx in range(3):
                b = d[y * 3 + bx]
                if mc:
                    for p in range(4):
                        c = (b >> (6 - 2 * p)) & 3
                        col = hero_pal[c]
                        for q in range(2):
                            for yy in range(sc):
                                for xx in range(sc):
                                    X = ox + (bx * 8 + p * 2 + q) * sc + xx
                                    Y = oy + y * sc + yy
                                    if c:
                                        img.putpixel((X, Y), col)
                else:
                    for p in range(8):
                        if (b >> (7 - p)) & 1:
                            for yy in range(sc):
                                for xx in range(sc):
                                    img.putpixel((ox + (bx * 8 + p) * sc + xx, oy + y * sc + yy), (230, 230, 230))
    img.save(os.path.join(ROOT, "out", "work", "gfx", "sprites.png"))


GFX_TOWN_AT = 0xEC00                 # file del villaggio (RAM sotto il KERNAL); (21/11) sopra il segmento CORE ($E000-)
assert GFX_TOWN_AT + 4 * 360 + 0x760 <= 0xFD00, "file del villaggio (tile + TOWN_MAX) oltre FMAP"
GFX_DUN_END = 0xF4E0                 # fine del buffer del tema (inizio della zona 2 del MENU, src/game/stash.asm MR2_AT)
# (15/11) il buffer del tema finisce sempre a GFX_DUN_END (lunghezza fissa); villaggio e tema non sono mai in RAM insieme
# (il villaggio si rilegge a ogni ingresso; 21/11: i due file cominciano quasi allo stesso indirizzo).
GFX_DUN_AT = None                    # calcolato in main(): GFX_DUN_END - lunghezza del file
DUN_NT = 27                          # tile dei dungeon: 0..26 (muri, pavimenti, scale, portale, bauli; 8-11 liberi)

def main():
    os.makedirs(os.path.join(ROOT, "out", "work", "gfx"), exist_ok=True)   # (11/11) file generati: out/work/gfx/, non piu' gfx/
    assert len(DUN_LEGEND) == DUN_NT and all(TID[n] < DUN_NT for n in DUN_LEGEND), "DUN_LEGEND: un carattere per posto 0..DUN_NT-1"
    assert len(set(DUN_LEGEND.values())) == DUN_NT, "DUN_LEGEND: caratteri ripetuti"
    assert max(TID[n] for n in ('WALL','FLOORC','STAIRSD','STAIRSU','PORTAL','CHEST')) < DUN_NT
    cs, _ = build_charset()
    for n in DUN_USED:                   # (06/11: i bauli erano spariti per un taglio sbagliato di questo file)
        assert any(any(cs[TID[n] + q * 64]) for q in range(4)), "tile %s del dungeon senza grafica" % n
    tcs, _ = build_charset(TOWN_TILES)
    sp = build_sprites()
    with open(os.path.join(ROOT, "out", "work", "gfx", "charset.bin"), "wb") as f:
        f.write(bytes(b for c in cs for b in c))
    with open(os.path.join(ROOT, "out", "work", "gfx", "sprites.bin"), "wb") as f:
        f.write(bytes(b for s in sp for b in s))
    with open(os.path.join(ROOT, "out", "work", "gfx", "sprites2.bin"), "wb") as f:
        f.write(bytes(b for s in build_sprites2() for b in s))
    # ---- grafica su file (caricata dal disco all'ingresso in un luogo, tenuta in cache nella RAM sotto il KERNAL)
    NT = len(TILES)
    tiles = bytes(b for q in range(4) for c in range(q * 64, q * 64 + NT) for b in cs[c])          # 4 strisce di NT caratteri
    fixed = bytes(b for q in range(4) for c in range(q * 64 + NT, q * 64 + 64) for b in cs[c])     # glifi HUD, minimappa...
    core = bytes(b for s in sp[0:12] for b in s)            # eroe + fendenti (slot 0..11)
    misc = bytes(b for s in sp[24:27] for b in s)           # slot 24..26
    mons, strong = mon_bytes(chapter_sets()[0][3])           # mostri base (slot 12..19), forti + boss ($8C00): misure
    open(os.path.join(ROOT, "out", "work", "gfx", "fixed_chr.bin"), "wb").write(fixed)
    open(os.path.join(ROOT, "out", "work", "gfx", "spr_core.bin"), "wb").write(core + misc)
    import npc_gfx                                          # (17/11) NPC del villaggio: slot 12..19, zona 4 del modulo MENU
    open(os.path.join(ROOT, "out", "work", "gfx", "npc_spr.bin"), "wb").write(b"".join(s for _, _, s in npc_gfx.npc_sprites()))
    open(os.path.join(ROOT, "out", "work", "gfx", "npc_bang.bin"), "wb").write(npc_gfx.bang_sprite())   # (18/11) "!", zona 5
    prg = lambda addr, data: bytes([addr & 255, addr >> 8]) + data
    ttiles = bytes(b for q in range(4) for c in range(q * 64, q * 64 + NT) for b in tcs[c])        # villaggio: TOWN_TILES
    open(os.path.join(ROOT, "out", "work", "gfx", "gfx0.prg"), "wb").write(prg(GFX_TOWN_AT, ttiles))
    # (15/11, TODO Z2) villaggi dei capitoli 2..: stessi posti, tile PROPRI (tools/build/villages.py, un modulo
    # vilN_*.py per villaggio); il villaggio 1 resta gfx0.prg. I loro disegni non usano il generatore casuale di questo
    # file: gli altri file non cambiano.
    import villages as V
    for c, v in V.VILLAGES.items():
        if not v["tiles"]:
            continue
        vcs = [list(ch) for ch in tcs]
        for i, n in enumerate(TOWN_TILES):
            if n in v["tiles"]:
                for q, ch in enumerate(tile_chars(v["tiles"][n][3])):
                    vcs[q * 64 + i] = ch
        vt = bytes(b for q in range(4) for ch in range(q * 64, q * 64 + NT) for b in vcs[ch])
        open(os.path.join(ROOT, "out", "work", "gfx", "twn%d.prg" % c), "wb").write(prg(GFX_TOWN_AT, vt))
    DN = DUN_NT                                             # dungeon: solo i tile 0..DN-1 (i tile del villaggio restano)
    def theme_tiles(boss):                                  # tile del dungeon (boss=True: sala del trono) senza mostri
        src = {i: i for i in range(DN)}
        if boss:                                            # sala del trono: pentacolo negli slot 12 (stella) e 13 (cerchio)
            src[TID["GRASSA"]] = TID["FLOWERS"]
            src[TID["GRASSB"]] = TID["GRASSB"]
        dt = bytes(b for q in range(4) for i in range(DN) for b in cs[q * 64 + src[i]])
        if boss:                                            # leva della sala del trono nello slot della porta di casa
            lv = tile_chars(lever_tile())
            dt = bytearray(dt)
            for q in range(4):
                o = (q * DN + TID["DHOME"]) * 8
                dt[o:o + 8] = bytes(lv[q])
            bp = tile_chars(black_portal_tile())          # portale nero nel posto libero 8 (T_BPORTAL)
            dt = bytearray(dt)
            for q in range(4):
                o = (q * DN + TID["FREE8"]) * 8
                dt[o:o + 8] = bytes(bp[q])
            dt = bytes(dt)
        return dt
    files = []
    dun_t, boss_t = theme_tiles(False), theme_tiles(True)   # una volta sola: lever_tile() usa il PRNG (byte diversi a ogni chiamata)
    # (18/11, TODO M11) capitoli a grotte (data/chapters.yaml map.style): nel file del tema dei piani muro, parete e
    # pavimenti di roccia (tools/build/cave_gfx.py) al posto dei mattoni; il file del boss resta com'e'
    import cave_gfx, chapters_db
    cave_t = bytearray(dun_t)
    for n_, gr in cave_gfx.tiles().items():
        for q, ch in enumerate(tile_chars(gr)):
            o = (q * DN + TID[n_]) * 8
            cave_t[o:o + 8] = bytes(ch)
    cave_t = bytes(cave_t)
    caves = {ch["id"] for ch in chapters_db.load()["chapters"] if (ch.get("map") or {}).get("style") == "caves"}
    # (18/11) palude (map.style swamp): acqua, riva, fango, passerelle e cancelli (tools/build/swamp_gfx.py)
    import swamp_gfx
    swamp_t = bytearray(dun_t)
    for n_, gr in swamp_gfx.tiles().items():
        for q, ch in enumerate(tile_chars(gr)):
            o = (q * DN + TID[n_]) * 8
            swamp_t[o:o + 8] = bytes(ch)
    swamp_t = bytes(swamp_t)
    swamps = {ch["id"] for ch in chapters_db.load()["chapters"] if (ch.get("map") or {}).get("style") == "swamp"}
    sets = chapter_sets()                                   # GFX(2c-1) dungeon, GFX(2c) boss del capitolo c
    raws = [info_raw(m) for _, _, _, m in sets]
    INFO = max(info_len(r) for r in raws)
    assert NM_TOP - INFO >= 0x8F00, "blocco info oltre la pagina $8F"
    import bestiary as BE                                   # (15/11) i nomi e i colori del gioco = quelli del bestiario
    best = BE.load()
    g = BE.game_rows(best)                                  # capitolo 1: le righe del gioco (il nome e' l'id con gli spazi)
    assert [r["id"].replace("_", " ") for r in g] == M_names(sets[0][3]), "capitolo 1: nomi diversi dal bestiario"
    for n, c, boss, m in sets:                              # ogni file: famiglie del capitolo (ordine del file) + posto del boss
        rs = [r for r in best if r["chapter"] == c]
        exp = [r for r in rs if r["tier"] == "base"] + [r for r in rs if r["tier"] == "strong"]
        exp.append(next(r for r in best if r["tier"] == ("boss" if boss and c < CHAPTERS else "final") and
                        (r["chapter"] == c or r["tier"] == "final")))
        nm_, cl_ = M_names(m), M_cols(m)
        import monsters as _M
        if boss and c in _M.SUMMONS:                        # (19/11) il mostro evocato dal boss (feticcio): non e' nel bestiario
            t_ = _M.SUMMONS[c][0] - 1
            exp = exp[:t_] + exp[t_ + 1:]; nm_ = nm_[:t_] + nm_[t_ + 1:]; cl_ = cl_[:t_] + cl_[t_ + 1:]
        assert [r["name"].lower() for r in exp] == nm_, "GFX%d: nomi %s, bestiario %s" % (n, nm_, [r["name"] for r in exp])
        assert [r["color"] for r in exp] == cl_, "GFX%d: colori %s, bestiario %s" % (n, cl_, [r["color"] for r in exp])
    # (19/11) piani del boss dei capitoli 1-3 (richiesta del committente: tema e forma propri): i tile del tema dei piani del
    # capitolo (mattoni, palude, grotte) piu' gli arredi del piano (tools/build/boss_gfx.py: sarcofagi, mulino, macerie...);
    # il boss finale (ultimo capitolo, GFX8) resta nella sala del trono
    import boss_gfx

    def cboss_tiles(c):
        bt = bytearray(cave_t if c in caves else swamp_t if c in swamps else dun_t)
        for n_, gr in boss_gfx.tiles(c).items():
            for q, ch in enumerate(tile_chars(gr)):
                o = (q * DN + TID[n_]) * 8
                bt[o:o + 8] = bytes(ch)
        return bytes(bt)
    # (19/11) arredi dei piani generati (tools/build/decor_gfx.py): nei file del tema dei piani GFX(2c-1), sul pavimento del tema
    import decor_gfx

    def theme_grid(tl, i):
        """griglia 8x16 del tile i di un tema (4 strisce di DN caratteri)"""
        g = [[0] * 8 for _ in range(16)]
        for q, (y0, x0) in enumerate(((0, 0), (0, 4), (8, 0), (8, 4))):
            for y in range(8):
                v = tl[(q * DN + i) * 8 + y]
                for x in range(4):
                    g[y0 + y][x0 + x] = (v >> (6 - 2 * x)) & 3
        return g

    def decor_tiles(c, tl):
        bt = bytearray(tl)
        for n_, gr in decor_gfx.tiles(c, theme_grid(tl, TID["FLOOR"])).items():
            for q, ch in enumerate(tile_chars(gr)):
                o = (q * DN + TID[n_]) * 8
                bt[o:o + 8] = bytes(ch)
        return bytes(bt)
    decor_gfx.write_inc(os.path.join(ROOT, "out", "work", "decor.inc"), TID)
    for (n, c, boss, m), r in zip(sets, raws):
        if boss and c < CHAPTERS:
            tl = cboss_tiles(c)
        else:
            tl = boss_t if boss else cave_t if c in caves else swamp_t if c in swamps else dun_t
        if not boss and c in decor_gfx.CHAPTERS:
            tl = decor_tiles(c, tl)
        files.append(tl + b"".join(mon_bytes(m)) + info_bytes(r, INFO))
    global GFX_DUN_AT
    GFX_DUN_AT = GFX_DUN_END - len(files[0])
    assert all(len(f) == len(files[0]) for f in files)
    assert len(files) <= 9                                  # nome "GFX" + una cifra
    for f, d in enumerate(files, 1):
        open(os.path.join(ROOT, "out", "work", "gfx", f"gfx{f}.prg"), "wb").write(prg(GFX_DUN_AT, d))
    for f in range(len(files) + 1, 10):                     # file di temi non piu' usati
        p = os.path.join(ROOT, "out", "work", "gfx", f"gfx{f}.prg")
        if os.path.exists(p):
            os.remove(p)
    with open(os.path.join(ROOT, "out", "work", "gfx_consts.inc"), "w") as f:
        f.write("; generato da tools/build/gen_gfx.py - non modificare\n")
        f.write("; T_* = numero del tile (slot 0..63 del charset: codici i, 64+i, 128+i, 192+i); nome e descrizione da\n")
        f.write("; tools/atlas/atlas_names.py (TILE), come nell'atlante grafico out/work/atlas/\n")
        try:
            sys.path.insert(0, os.path.join(ROOT, "tools", "atlas")); import atlas_names as _AN   # (13/11) in tools/atlas/
            _desc = {k: v[1] for k, v in _AN.TILE.items()}
        except Exception:
            _desc = {}
        for n, i in TID.items():
            f.write(f"T_{n:<12} = {i:<3}   ; {_desc.get(n, '')}\n".rstrip(" ;\n") + "\n")
        for n, i in TTID.items():
            if n not in TID:
                f.write(f"T_{n:<12} = {i:<3}   ; (solo villaggio) {_desc.get(n, '')}\n".rstrip(" \n") + "\n")
        f.write(f"GFX_NFILES = {len(files)}\n")
        f.write(f"CHAPTERS = {CHAPTERS}\n")
        for n, c in HUD_ID.items():
            f.write(f"G_{n} = {c}\n")
        # codifica "hud": un testo .text "slash" produce direttamente i glifi dell'HUD (maiuscole e minuscole)
        f.write('        .enc "hud"\n        .cdef " ", " ", G_BLANK\n        .cdef "0", "9", G_0\n        .cdef "/", "/", G_SLASH\n')
        for L in LETTERS:
            f.write(f'        .cdef "{L}", "{L}", G_{L}\n        .cdef "{L.lower()}", "{L.lower()}", G_{L}\n')
        f.write('        .enc "none"\n')
        f.write(f"GFX_NT = {NT}\nGFX_TSTRIP = {NT * 8}\nGFX_FSTRIP = {(64 - NT) * 8}\nGFX_DSTRIP = {DUN_NT * 8}\n")
        f.write(f"GFX_TOWN_AT = ${GFX_TOWN_AT:04x}\nGFX_DUN_AT = ${GFX_DUN_AT:04x}\n")
        f.write(f"GFX_MONS = {len(mons)}\nGFX_STRONG = {len(strong)}\nGFX_INFO = {INFO}\nGFX_DUN_END = ${GFX_DUN_END:04x}\n")
        f.write(f"NM_AT = ${NM_TOP - INFO:04x}            ; colori (9), indirizzi dei nomi (9), nomi dei mostri del set (blocco info)\n")
        f.write("solid_dun\n")
        row = [1 if n in SOLID else 0 for n in TILES] + [0] * (NTILE_MAX - len(TILES))
        f.write("    .byte " + ",".join(map(str, row)) + "\n")
    preview(cs, sp)
    print("ok: %d tile, %d byte charset, %d byte sprite" % (len(TILES), 2048, 2048))


if __name__ == "__main__":
    main()
