#!/usr/bin/env python3
"""Villaggi dei capitoli (15/11, TODO Z2, docs/wiki/villaggio.md): un file TWNc per capitolo con i SUOI tile, la SUA mappa, i
SUOI colori, i SUOI tile solidi, il nome del SUO luogo di cura e le SUE posizioni (portale, ingresso del sotterraneo,
ingresso e uscita del villaggio, porte).

Ogni villaggio ha 45 posti di tile (gli stessi numeri di TOWN_TILES in tools/build/gen_gfx.py: nelle mappe di testo le
lettere sono quelle di LEGEND in tools/build/gen_maps.py, una per posto). Il CODICE conosce solo questi ruoli:
  DSMITH, DALCH, DHOME   porte di fabbro, alchimista e locanda (percorribili; Fire da 1 o 2 caselle davanti)
  TSTAIRS                ingresso del sotterraneo del capitolo (percorribile)
  FOUNTAIN               luogo di cura: starci sopra riempie la vita (percorribile)
  PORTAL                 il portale, messo dal gioco sulla casella P quando e' aperto
  PATH, DIRT, BRIDGE, COBBLE   "strade" nella minimappa;  WATER, WATERL, WATERR  "acqua" nella minimappa
  posti 5, 6, 8-11, 24-26 (WATERL, WATERR, GRAVE, GRAVE2, CRYPTL, CRYPTR, CRYPTA, CRYPTB, CRYPTC): sempre SOLIDI
Tutto il resto e' libero: ogni villaggio ridisegna i posti come vuole e decide quali sono solidi (un modulo vilN_*.py
per villaggio: PAL, NAME, HEAL, TILES = {posto: (nome, descrizione, solido, griglia 8x16)}; i posti non elencati
restano quelli del villaggio 1).

  pal   (sfondo, multicolor 1, multicolor 2, accento 0..7) = valori 0, 1, 2, 3 dei pixel
  heal  nome del luogo di cura nella barra in alto (minuscolo, al massimo TK_NAME - 1 caratteri)
  map   testo 48x48 in data/"""
import vil2_blackwater, vil3_lastcamp, vil4_ruinsgate, vil5_abyss

TK_NAME = 25
MUST_SOLID = ("WATERL", "WATERR", "GRAVE", "GRAVE2", "CRYPTL", "CRYPTR", "CRYPTA", "CRYPTB", "CRYPTC")
MUST_WALK = ("DSMITH", "DALCH", "DHOME", "TSTAIRS", "FOUNTAIN", "PORTAL")


def _v(mod, n):
    return dict(name=mod.NAME, pal=mod.PAL, heal=mod.HEAL, map="data/town_map%d.txt" % n, tiles=mod.TILES)


VILLAGES = {
    1: dict(name="Aldric's Crossing", pal=(5, 9, 15, 3), heal="fountain of saint aldric", map="data/town_map.txt", tiles={}),
    2: _v(vil2_blackwater, 2),
    3: _v(vil3_lastcamp, 3),
    4: _v(vil4_ruinsgate, 4),
    5: _v(vil5_abyss, 5),
}


# (17/11) Settori degli NPC vaganti, per villaggio: (x, y, larghezza, altezza) in caselle, al massimo NSEC (gen_maps.py).
# Ogni NPC vagante (il numero 1..8) vive nel suo settore: nasce li' con probabilita' 3/4 e non ne esce mai. I settori seguono
# la forma del villaggio e sono abbastanza grandi; gen_maps.py controlla che in una finestra di gioco (21 x 13 caselle) ce ne
# siano al massimo 5: gli sprite liberi nel villaggio sono 5 (3..7), quindi gli NPC visibili insieme non superano mai i 5.
SECTORS = {
    1: [(x, y, 15 if x < 32 else 14, 15 if y < 32 else 14) for x in (2, 17, 32) for y in (2, 17, 32) if (x, y) != (17, 17)],  # griglia 3x3 senza il centro
    2: [(4, 9, 10, 14), (26, 10, 20, 6), (16, 16, 12, 7), (28, 28, 15, 8), (12, 36, 10, 5), (36, 36, 11, 5), (0, 41, 41, 5)],  # piattaforme
    3: [(8, 5, 16, 10), (24, 5, 21, 10), (3, 19, 17, 13), (20, 19, 14, 13), (34, 19, 11, 13), (4, 34, 20, 11), (24, 34, 22, 11)],  # tre terrazze
    4: [(2, 2, 16, 15), (30, 2, 17, 15), (14, 6, 22, 11), (2, 17, 16, 13), (31, 17, 16, 13), (2, 30, 22, 16), (24, 30, 23, 16)],  # anello attorno al cratere
    5: [(4, 5, 11, 8), (19, 4, 15, 9), (36, 5, 11, 8), (3, 21, 14, 8), (17, 20, 16, 10), (33, 20, 14, 10), (16, 38, 15, 6), (34, 36, 13, 7)],  # isole
}


def solid(c, town_tiles, base_solid):
    """lista 0/1 dei tile solidi del villaggio c (indice = posto)"""
    t = VILLAGES[c]["tiles"]
    out = [int(t[n][2] if n in t else n in base_solid) for n in town_tiles]
    for n in MUST_SOLID:
        assert out[town_tiles.index(n)], "villaggio %d: il posto %s deve essere solido" % (c, n)
    for n in MUST_WALK:
        assert not out[town_tiles.index(n)], "villaggio %d: il posto %s deve essere percorribile" % (c, n)
    return out


def tile_name(c, n):
    """(nome, descrizione) a tema del posto n nel villaggio c, o None (= quello del villaggio 1)"""
    t = VILLAGES[c]["tiles"]
    return t[n][:2] if n in t else None
