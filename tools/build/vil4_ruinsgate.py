#!/usr/bin/env python3
"""Villaggio del capitolo 4: RUIN'S GATE, la citta' in rovina sotto la cittadella (15/11, TODO Z2).
Niente fiume, niente fontana: un cratere al centro (dentro, vene di brace), la strada ad anello attorno, quattro raggi,
mura spezzate, colonne in piedi e cadute, case sventrate. I sopravvissuti stanno fra le rovine: fucina, torre
dell'alchimista, cantina della taverna (locanda). Cura: l'angelo che piange. L'ingresso del sotterraneo e' la saracinesca
delle segrete, nel corpo di guardia a nord. L'uscita del capitolo scende nel cratere.
Colori: 0 grigio scuro (cenere), 1 nero (carbone, buio), 2 grigio chiaro (pietra, ossa), 3 rosso (braci, fuoco)."""
from tileart import A, grid, put, hline, vline, noise, over, canvas, cut, rnd, bricks

PAL = (11, 0, 15, 2)
NAME = "Ruin's Gate"
HEAL = "the weeping angel"


def ash(key, d1=0.05, d2=0.015):
    g = grid(0); r = rnd(key)
    noise(g, 1, d1, r); noise(g, 2, d2, r)
    return g


ASH = ash("ash")
WALL = bricks(2, 1)
for _x, _y in ((4, 0), (4, 1), (5, 2), (5, 4), (4, 5), (4, 6), (3, 8), (3, 9), (2, 10), (2, 12), (1, 13)):
    put(WALL, _x, _y, 1)                                  # la crepa
for _x, _y in ((6, 9), (6, 10), (0, 5), (7, 13)):
    put(WALL, _x, _y, 0)                                  # mattoni caduti
PAVE = bricks(2, 1, (2, 6), (0, 4))
for _x, _y in ((1, 0), (1, 1), (5, 9), (6, 9), (5, 10), (3, 13), (7, 5)):
    put(PAVE, _x, _y, 0)

ANGEL = canvas(                      # l'angelo che piange 2x2: ali aperte, il capo chino, il piedistallo; una lacrima rossa
    "9999999999999999",
    "9999999229999999",
    "9999992222999999",
    "9999992112999999",
    "9999992322999999",
    "9929999229999299",
    "9222992222992229",
    "2222222222222222",
    "2212222222222122",
    "2221222222221222",
    "9222122222212229",
    "9922212222122299",
    "9992221221222999",
    "9999222222229999",
    "9999922222299999",
    "9999922222299999",
    "9999922222299999",
    "9999921221299999",
    "9999922222299999",
    "9999922112299999",
    "9999222222229999",
    "9999222222229999",
    "9991111111111999",
    "9992222222222999",
    "9992122222212999",
    "9992222222222999",
    "9992222112222999",
    "9992222222222999",
    "9911111111111199",
    "9122222222222219",
    "1111111111111111",
    "9999999999999999")

PIT = A("11111111", "11113111", "11131111", "11311111", "11131111", "11113311", "11111131", "11111113",
        "11111131", "31111311", "13113111", "11331111", "11131111", "11113111", "11111311", "11111111")


def rim(side):
    """orlo del cratere: cenere, bordo spezzato chiaro, poi il buio"""
    g = [r[:] for r in PIT]
    prof = (3, 2, 2, 3, 4, 3, 2, 3, 3, 2, 3, 4, 3, 2, 2, 3)
    if side in "LR":
        for y in range(16):
            w = prof[y]
            for x in range(w):
                put(g, x if side == "L" else 7 - x, y, 0)
            put(g, w if side == "L" else 7 - w, y, 2)
            if y % 3 == 0:
                put(g, w - 1 if side == "L" else 8 - w, y, 1)
    else:
        prof = (6, 5, 5, 6, 7, 6, 5, 6)
        for x in range(8):
            h = prof[x]
            for y in range(h):
                put(g, x, y if side == "T" else 15 - y, 0)
            put(g, x, h if side == "T" else 15 - h, 2)
            if x % 3 == 0:
                put(g, x, h - 1 if side == "T" else 16 - h, 1)
    return g


TILES = {
    # ---- terreno
    "GRASSA": ("Ash", "ground covered with ash", False, ASH),
    "GRASSB": ("Embers", "ash with live embers", False,
               over(ash("a2"), "        ", "        ", "  31    ", "  1     ", "        ", "        ", "     3  ", "     11 ",
                    "        ", "        ", " 3      ", " 1      ", "        ", "    31  ", "        ", "        ")),
    "GRASSC": ("Rubble", "ash and broken stones", False,
               over(ash("a3"), "        ", "        ", "  22    ", " 2221   ", " 2211   ", "  11  2 ", "     221", "      11",
                    "        ", "        ", "   2    ", "  221   ", "  11    ", "        ", "        ", "        ")),
    "FLOWERS": ("Bones", "what is left of the people of the city", False,
                over(ash("a4", 0.03, 0), "        ", "  222   ", " 22222  ", " 21212  ", " 22222  ", "  212   ", "        ", "     2  ",
                     " 2  2   ", "  22    ", "  22    ", " 2  2   ", "      2 ", "    222 ", "   2    ", "        ")),
    "PATH": ("Broken road", "the old road: cracked slabs", False,
             A("22222122", "22222122", "22221022", "11112111", "22122220", "22122222", "20122222", "11111101",
               "22221222", "22221222", "02221222", "11111211", "21222222", "21222202", "21222222", "11011111")),
    "COBBLE": ("Broken paving", "paving with holes", False, PAVE),
    "DIRT": ("Scorched earth", "burnt black ground", False,
             over(grid(1), "  0     ", "     0  ", " 0      ", "    3   ", "       0", "  0     ", "      0 ", " 0  0   ",
                  "        ", "   0   0", " 3      ", "     0  ", "  0     ", "       0", "    0   ", " 0      ")),
    "BRIDGE": ("Plank stair", "planks going down into the crater", False,
               A("10000001", "12222221", "12122221", "11111111", "10000001", "12222221", "12221221", "11111111",
                 "10000001", "12222221", "12222121", "11111111", "10000001", "12222221", "12122221", "11111111")),
    # ---- il cratere
    "WATER": ("Crater", "the dark of the crater, veined with embers", True, PIT),
    "WATERL": ("Crater rim W", "the broken edge of the crater", True, rim("L")),
    "WATERR": ("Crater rim E", "the broken edge of the crater", True, rim("R")),
    "GRAVE": ("Crater rim N", "the broken edge of the crater", True, rim("T")),
    "GRAVE2": ("Crater rim S", "the broken edge of the crater", True, rim("B")),
    # ---- mura e case sventrate
    "BWALL": ("Cracked wall", "cracked masonry", True, WALL),
    "BROOF": ("Broken wall top", "the jagged top of a ruined wall", True,
              over(WALL, "........", "........", "..2.....", ".222..2.", ".2222.22", "22222222", "        ", "        ",
                   "        ", "        ", "        ", "        ", "        ", "        ", "        ", "        ")),
    "CRYPTL": ("Wall end W", "where a wall has fallen: its broken end", True,
               over(WALL, "........", "......2.", ".....22 ", "....2   ", "...22   ", "....2   ", "..22    ", "...2    ",
                    ".222    ", "..22    ", "...2    ", ".22     ", "..2     ", "122     ", "22      ", "        ")),
    "CRYPTR": ("Wall end E", "where a wall has fallen: its broken end", True,
               over(WALL, "........", ".2......", " 22.....", "   2....", "   22...", "   2....", "    22..", "    2...",
                    "    222.", "    22..", "    2...", "     22.", "     2..", "     221", "      22", "        ")),
    "WINDOW": ("Empty window", "an empty window, fire inside", True,
               over(WALL, "        ", "        ", "  1111  ", " 111111 ", " 111111 ", " 111111 ", " 111111 ", " 111311 ",
                    " 113311 ", " 133331 ", " 133331 ", " 111111 ", "22222222", "        ", "        ", "        ")),
    "HDOOR": ("Blocked door", "a doorway choked with rubble", True,
              over(WALL, "        ", "  1111  ", " 111111 ", " 111111 ", " 111111 ", " 111111 ", " 111111 ", " 111211 ",
                   " 112221 ", " 122121 ", " 221222 ", " 222212 ", "12122221", "22221222", "21222122", "        ")),
    "BROOFA": ("Burnt beams", "the roof is gone: only charred beams", True,
               over(ASH, " 1    1 ", " 1    1 ", "11111111", " 1    1 ", " 1 3  1 ", " 1    1 ", " 1    1 ", "11111111",
                    " 1    1 ", " 1    13", " 1    1 ", "11111111", " 1    1 ", " 13   1 ", " 1    1 ", " 1    1 ")),
    "BROOFL": ("Broken tiles", "patches of roof tiles", True,
               A("12121.12", "21212..1", "1212...2", "111....1", "121..212", "212.2121", "121.1212", "111.1111",
                 "...12121", "..121212", ".2121212", ".1111111", "1212..21", "2121...2", "1212..21", "11111111")),
    "SPIRE": ("Broken turret", "the top of a tower, half fallen", True,
              over(ASH, "        ", "        ", "     2  ", " 2   22 ", " 22  22 ", " 22 222 ", " 2222221", " 2212221",
                   "22222221", "22122211", "22222121", "21222221", "22221221", "22222221", "22122221", "11111111")),
    "SIGNS": ("Smith's sign", "an anvil, hung on the ruin", True,
              over(WALL, "   11   ", "   11   ", " 111111 ", " 1....1 ", " 1.33.1 ", " 133331 ", " 1.33.1 ", " 1.33.1 ",
                   " 133331 ", " 1....1 ", " 111111 ", "        ", "        ", "        ", "        ", "        ")),
    "SIGNL": ("Alchemist's sign", "a flask, hung on the ruin", True,
              over(WALL, "   11   ", "   11   ", " 111111 ", " 1....1 ", " 1.33.1 ", " 1.33.1 ", " 133331 ", " 13..31 ",
                   " 133331 ", " 1....1 ", " 111111 ", "        ", "        ", "        ", "        ", "        ")),
    # ---- colonne
    "CRYPTA": ("Column (top)", "a broken column, upper part", True,
               over(ASH, "        ", "        ", "        ", "    2   ", "  2 22  ", "  2222  ", " 222222 ", "  1111  ",
                    "  2122  ", "  2122  ", "  2122  ", "  2122  ", "  2122  ", "  2122  ", "  2122  ", "  2122  ")),
    "CRYPTC": ("Column (base)", "a column, shaft and base", True,
               over(ASH, "  2122  ", "  2122  ", "  2122  ", "  2122  ", "  2122  ", "  2122  ", "  2122  ", "  2122  ",
                    "  2122  ", "  2122  ", "  1111  ", " 222222 ", " 222222 ", "11111111", " 1    1 ", "        ")),
    "CRYPTB": ("Fallen column", "the drums of a fallen column", True,
               over(ASH, "        ", "        ", "        ", "        ", "        ", " 222 222", "22221222", "21121211",
                    "22221222", "22221222", "21121211", "22221222", " 111 111", "        ", "   1    ", "        ")),
    # ---- arredi
    "TREE": ("Burnt tree", "a dead black tree", True,
             over(ASH, "1     1 ", " 1   1  ", " 1  1  1", "  1 1 1 ", "3 11 1  ", " 1 111  ", "  1113 1", "   11 1 ",
                  "1  111  ", " 1 11   ", "  111   ", "   11   ", "   11   ", "  1111  ", " 11  11 ", "1      1")),
    "BUSH": ("Rubble heap", "a heap of stones and beams", True,
             over(ASH, "        ", "        ", "        ", "    2   ", "   221  ", "  22211 ", " 2212221", " 2122211",
                  "22221221", "22122211", "21222121", "12221211", " 1111111", "        ", "        ", "        ")),
    "LAMP": ("Fire basket", "an iron basket with a fire", True,
             over(ASH, "   3    ", "  3 3   ", "   33   ", "  3333  ", " 133331 ", " 121121 ", "  1111  ", "   11   ",
                  "   11   ", "   11   ", "  1  1  ", "  1  1  ", " 1    1 ", "        ", "        ", "        ")),
    "STALL": ("Burnt cart", "a cart, burnt", True,
              over(ASH, "        ", "        ", "  3     ", " 33  1  ", " 3   11 ", "11111111", "12121211", "11212121",
                   "11111111", " 1    1 ", "111  111", "1 1  1 1", "111  111", " 1    1 ", "        ", "        ")),
    "WELL": ("Gibbet", "an iron cage hanging from a post", True,
             over(ASH, " 111111 ", " 1    1 ", " 1    1 ", " 1   111", " 1   1 1", " 1   121", " 1   1 1", " 1   121",
                  " 1   111", " 1      ", " 1      ", " 1      ", " 1      ", " 1      ", "111     ", "        ")),
    "CHIMNEY": ("Torn banner", "a torn red banner", True,
                over(ASH, "  1     ", "  13333 ", "  133 33", "  1333  ", "  13 33 ", "  133   ", "  1 3   ", "  1     ",
                     "  1     ", "  1     ", "  1     ", "  1     ", "  1     ", "  1     ", " 111    ", "        ")),
    "FENCE": ("Iron railing", "a bent iron railing", True,
              over(ASH, "        ", "        ", "        ", " 1  1  1", " 1  1  1", "11111111", " 1  1  1", " 1  1  1",
                   " 1  1 1 ", " 1  1 1 ", "11111111", " 1  1  1", " 1  1  1", "        ", "        ", "        ")),
    "FENCEV": ("Iron railing (side)", "iron railing, north-south", True,
               over(ASH, "   1    ", "  111   ", "   1    ", "   1    ", "   1    ", "   1    ", "  111   ", "   1    ",
                    "   1    ", "   1    ", "   1    ", "  111   ", "   1    ", "   1    ", "   1    ", "   1    ")),
    # ---- cura e sotterraneo
    "FOUNTAIN": ("Candles", "candles at the feet of the angel: standing here heals", False,
                 over(PAVE, "        ", "  3     ", "  3     ", "  2     ", "  2   3 ", " 111  3 ", "      2 ", "      2 ",
                      "     111", "   3    ", "   3    ", "   2    ", "   2    ", "  111   ", "        ", "        ")),
    "FOUNT0": ("Weeping angel NW", "the weeping angel: a wing", True, cut(ANGEL, 0, 0, ASH)),
    "FOUNT1": ("Weeping angel NE", "the weeping angel: a wing", True, cut(ANGEL, 1, 0, ASH)),
    "FOUNT2": ("Weeping angel SW", "the pedestal of the angel", True, cut(ANGEL, 0, 1, ASH)),
    "FOUNT3": ("Weeping angel SE", "the pedestal of the angel", True, cut(ANGEL, 1, 1, ASH)),
    "TSTAIRS": ("Portcullis", "the half raised portcullis of the castle dungeons: the way down", False,
                over(WALL, " 111111 ", "11111111", "12121211", "12121211", "12121211", "12121211", "1 1 1 11", "11111111",
                     "11111111", "11122111", "11111111", "11222211", "11111111", "12222221", "11131111", "11111111")),
}
