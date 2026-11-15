#!/usr/bin/env python3
"""Villaggi dei capitoli (15/11, TODO Z2, docs/villaggio.md): un file TWNc per capitolo con i SUOI tile, la SUA mappa, i
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
