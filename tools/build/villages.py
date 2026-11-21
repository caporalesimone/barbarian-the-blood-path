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
import vil2_badwater, vil3_lastcamp, vil4_ruinsgate, vil5_abyss

TK_NAME = 25
MUST_SOLID = ("WATERL", "WATERR", "GRAVE", "GRAVE2", "CRYPTL", "CRYPTR", "CRYPTA", "CRYPTB", "CRYPTC")
MUST_WALK = ("DSMITH", "DALCH", "DHOME", "TSTAIRS", "FOUNTAIN", "PORTAL")


def _v(mod, n):
    return dict(name=mod.NAME, pal=mod.PAL, heal=mod.HEAL, map="data/town_map%d.txt" % n, tiles=mod.TILES)


VILLAGES = {
    1: dict(name="Aldric's Hollow", pal=(5, 9, 15, 3), heal="fountain of saint aldric", map="data/town_map.txt", tiles={}),
    2: _v(vil2_badwater, 2),
    3: _v(vil3_lastcamp, 3),
    4: _v(vil4_ruinsgate, 4),
    5: _v(vil5_abyss, 5),
}


# (17/11) Settori degli NPC vaganti, per villaggio: (x, y, larghezza, altezza) in caselle, al massimo NSEC (gen_maps.py).
# Ogni NPC vagante (il numero 1..NSEC) vive nel suo settore: nasce li' con probabilita' 7/8 e non ne esce mai. I settori seguono
# la forma del villaggio (almeno 20 caselle percorribili l'uno). Gli sprite liberi nel villaggio sono 5 (3..7): se in una
# finestra di gioco (21 x 13 caselle) i settori sono di piu', oltre il quinto NPC visibile non si disegna (gen_maps.py scrive
# il massimo di ogni villaggio).
def _grid(xs, ys, w, h):
    return [(x, y, w, h) for y in ys for x in xs]


SECTORS = {
    1: _grid((2, 13, 24, 35), (2, 13, 24, 35), 11, 11),           # griglia 4x4
    2: [(4, 9, 10, 14), (26, 10, 20, 6), (16, 16, 12, 7), (3, 26, 11, 12), (28, 28, 15, 8), (12, 36, 10, 5), (36, 36, 11, 5),
        (0, 41, 14, 5), (14, 41, 14, 5), (28, 41, 13, 5), (40, 17, 8, 23)],   # piattaforme
    3: [(8, 5, 13, 10), (21, 5, 12, 10), (33, 5, 12, 10), (2, 0, 8, 15), (3, 19, 11, 13), (14, 19, 10, 13), (24, 19, 10, 13),
        (34, 19, 11, 13), (4, 34, 11, 11), (15, 34, 10, 11), (25, 34, 10, 11), (35, 34, 11, 11)],   # tre terrazze
    4: _grid((2, 14, 26, 37), (2, 14, 26, 37), 11, 11),           # anello attorno al cratere (griglia 4x4)
    5: [(4, 5, 11, 8), (19, 4, 8, 9), (26, 4, 8, 9), (36, 5, 11, 8), (3, 21, 8, 8), (9, 21, 8, 8), (17, 20, 8, 10), (25, 20, 8, 10),
        (33, 20, 8, 10), (39, 20, 8, 10), (16, 38, 15, 6), (34, 36, 13, 7)],   # isole
}


def solid(c, town_tiles, base_solid):
    """lista dei tile solidi del villaggio c (indice = posto): bit 0 = solido, bit 1 (19/11) = barriera per gli NPC
    (calpestabile per l'eroe, mai per gli NPC che vagano: il traghetto; nel modulo TILES il campo "solido" vale "npc")"""
    t = VILLAGES[c]["tiles"]
    out = [(2 if t[n][2] == "npc" else int(t[n][2])) if n in t else int(n in base_solid) for n in town_tiles]
    for n in MUST_SOLID:
        assert out[town_tiles.index(n)], "villaggio %d: il posto %s deve essere solido" % (c, n)
    for n in MUST_WALK:
        assert not out[town_tiles.index(n)] & 1, "villaggio %d: il posto %s deve essere percorribile" % (c, n)
    return out


def tile_name(c, n):
    """(nome, descrizione) a tema del posto n nel villaggio c, o None (= quello del villaggio 1)"""
    t = VILLAGES[c]["tiles"]
    return t[n][:2] if n in t else None


# (21/11, committente) NPC fissi che danno le quest (docs/wiki/quests.md sez. 2: nomi T6): per villaggio, il primo sta nella
# piazza della fontana (casella scelta da gen_maps.giver, NPC 0: oggi ha la quest segnaposto 1 nel villaggio 1); gli altri (al
# massimo NFIX) vicino a un punto della mappa: ("tile", NOME) = baricentro dei tile di quel posto, ("door", DSMITH|DALCH|DHOME) =
# casella davanti alla porta, ("crypt",) = ingresso del sotterraneo, ("boat",) = primo approdo del traghetto. Un NPC fisso prende
# il posto del vagante del settore in cui sta (meno NPC nello stesso settore). Disegno: 0 villager, 1 woman, 2 elder, 3 guard
# (tools/build/npc_gfx.py). Nomi: al massimo FIX_NAME - 1 caratteri (etichetta della barra in alto).
FIXED = {
    1: [("hilde", None, 1), ("father osric", ("tile", "SPIRE"), 2), ("grom", ("door", "DSMITH"), 0), ("the gravedigger", ("crypt",), 2)],
    2: [("mama sabine", None, 1), ("corbeau", ("boat",), 0), ("little pip", ("door", "DALCH"), 0), ("the drummer", ("door", "DHOME"), 3)],
    3: [("sergeant brenna", None, 3), ("chaplain edric", ("crypt",), 2), ("quartermaster", ("door", "DSMITH"), 3)],
    4: [("the penitent", None, 2), ("the scavenger", ("door", "DALCH"), 0), ("the gatewarden", ("crypt",), 3)],
    5: [("the keeper", None, 2)],
}
