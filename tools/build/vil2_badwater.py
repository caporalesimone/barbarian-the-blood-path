#!/usr/bin/env python3
"""Villaggio del capitolo 2: BAD WATER, un villaggio di palafitte su un lago nero (15/11, TODO Z2; 19/11 tema voodoo).
Niente piazza, niente fiume, niente fontana: pontili e passerelle sull'acqua, capanne su pali, la casa degli spiriti con il
grande idolo (l'ingresso della palude e' il cancello d'ossa nel suo muro), l'albero delle bottiglie (cura), lanterne-teschio,
tamburi, rastrelliere di amuleti, i due traghetti sotto le piattaforme (caselle F di data/town_map2.txt).
Colori: 0 nero (l'acqua), 1 marrone (legno scuro, fango), 2 arancio (legno illuminato), 3 verde (alghe, canne, lumi)."""
from tileart import A, grid, put, hline, vline, noise, over, canvas, cut, rnd

PAL = (0, 9, 8, 5)
NAME = "Bad Water"
HEAL = "the bottle tree"

DECK = A("22212222", "22212222", "22212222", "11111111", "22222122", "22222122", "22222122", "11111111",
         "21222222", "21222222", "21222222", "11111111", "22221222", "22221222", "22221222", "11111111")
WALL = A("11111111", "22122212", "22122212", "22122212", "22122212", "21122212", "22122212", "22122112",
         "22122212", "22122212", "22122212", "22122212", "22112212", "22122212", "22122212", "11111111")
ROOF = A("11121112", "21112111", "11211121", "12111211", "11121112", "21112111", "11211121", "12111211",
         "11121112", "21112111", "11211121", "12111211", "11121112", "21112111", "11211121", "12111211")


def mud(key, tufts=()):
    g = grid(1); r = rnd(key)
    noise(g, 0, 0.07, r); noise(g, 2, 0.03, r)
    for x, y in tufts:
        put(g, x, y, 3); put(g, x - 1, y - 1, 3); put(g, x + 1, y - 1, 3); put(g, x, y - 2, 3)
    return g


def _sym(*left):
    """disegno largo 16 simmetrico dalle meta' sinistre (8 cifre)"""
    assert all(len(r) == 8 for r in left), [r for r in left if len(r) != 8]
    return [[0 if c == "." else int(c) for c in r + r[::-1]] for r in left]


# (19/11, tema voodoo) il grande idolo 2x2 nell'acqua accanto alla casa degli spiriti: maschera-teschio con le corna su un palo
IDOL = _sym("1.......", "11....11", ".11.1122", "..111222", "...12222", "..122222", "..123322", "..123322",
            "..122222", "..122221", "..122211", "...12222", "...12121", "...12121", "....1222", "....1111",
            ".....122", ".....122", "..2..122", "..2..122", ".222.122", "..2..122", ".....122", ".....122",
            ".....122", "...3.122", "..3.3122", ".3..3112", "3.3.3.11", "..3.....", ".11.....", "........")


def _bottle_tree():
    """l'albero delle bottiglie 2x2 (luogo di cura): albero morto nero con le bottiglie verdi appese; '9' = l'assito"""
    cv = [[9] * 16 for _ in range(32)]

    def P(x, y, c):
        if 0 <= x < 16 and 0 <= y < 32:
            cv[y][x] = c
    for y in range(7, 28):
        P(7, y, 0); P(8, y, 0)
        if y > 20:
            P(6, y, 0)
    for i in range(6):
        P(6 - i, 8 - i, 0); P(9 + i, 8 - i, 0); P(6 - i, 9 - i, 0); P(9 + i, 9 - i, 0)
    for i in range(5):
        P(7 - i // 2, 6 - i, 0); P(8 + i // 2, 6 - i, 0)
    for x, y in ((6, 14), (5, 13), (4, 13), (3, 12), (2, 12), (6, 20), (5, 19), (4, 19), (3, 18)):
        P(x, y, 0); P(15 - x, y, 0)
    for x in (5, 6, 9, 10):
        P(x, 27, 0)
    for x in (4, 6, 9, 11):
        P(x, 28, 0)
    for x, y in ((1, 4), (4, 6), (10, 6), (13, 4), (2, 13), (12, 13), (3, 19), (11, 19)):
        P(x, y, 0); P(x, y + 1, 0); P(x, y + 2, 3); P(x, y + 3, 3); P(x, y + 4, 3); P(x + 1, y + 3, 3); P(x + 1, y + 4, 3)
    for x in (2, 13):                                   # moccoli ai piedi
        P(x, 26, 3); P(x, 27, 2); P(x, 28, 2)
    return cv


BTREE = _bottle_tree()

# (19/11) il traghetto: una barca grande 3x1 ormeggiata sotto una piattaforma (prua, casella su cui si sale, poppa), con la
# tettoia e la lanterna verde in mezzo. Le altre barche del villaggio non ci sono piu': le uniche barche sono i due traghetti.
FERRY = canvas(
    "..........2..3333..2....",
    "..........2.322223.2....",
    "........2222333322222...",
    ".......222222222222222..",
    "......11111111111111111.",
    "..........1...33...1....",
    "1.........1..3223..1...1",
    "21........1...33...1..12",
    "221.......1........1.122",
    "2221111111111111111111122",
    ".22222222222222222222222.",
    ".2212222122221222212222..",
    "..222222222222222222222..",
    "...1111111111111111111...",
    "..3..33.......33....3...",
    "........................")
FERRY = [r[:24] for r in FERRY]


TILES = {
    # ---- acqua (solida): il lago
    "WATER": ("Black water", "the lake: black water, a ripple", True,
              A("........", "........", "..11....", "........", "........", "......11", "........", "........",
                "........", ".11.....", "........", "........", "....11..", "........", "........", "........")),
    "WATERL": ("Scum", "black water with green scum", True,
               A("........", "..33....", ".3333...", "..33..3.", ".....333", "......3.", "........", ".1......",
                 "...33...", "..3333..", "...333..", "........", "......33", ".....333", "..1...3.", "........")),
    "WATERR": ("Reeds", "reeds standing in the water", True,
               A("...2....", "...3..2.", ".2.3..3.", ".3.3..3.", ".3.3..3.", ".3.33.3.", ".3.3..3.", ".3.3..3.",
                 ".3.3.33.", ".33..3..", ".3...3..", ".3...3..", ".3..11..", "11......", "....11..", "........")),
    "FLOWERS": ("Water lilies", "lily pads on the black water", True,
                A("........", "..333...", ".33333..", ".333.3..", "..333...", "........", ".....33.", "....3333",
                  ".11.3323", "....3333", ".....33.", ".33.....", "3333....", "3323..11", ".33.....", "........")),
    "CRYPTB": ("Skull pole", "a post in the water with a skull on top", True,
               A("........", "..2222..", ".222222.", ".202202.", ".222222.", "..2020..", "...22...", "...21...",
                 "..2221..", "...21...", "...21...", ".332213.", "3..21..3", "..1111..", ".3....3.", "........")),
    "GRAVE": ("Ferry (bow)", "the bow of the ferry", True, cut(FERRY, 0, 0)),
    "GRAVE2": ("Ferry (stern)", "the stern of the ferry", True, cut(FERRY, 2, 0)),
    "TREE": ("Mangrove", "a mangrove with its roots in the water", True,
             A("..3333..", ".333333.", "33313333", "33333313", "31333333", "33331333", ".333333.", "3.3113.3",
               "3..11..3", "...11...", "...11..3", "3..11...", "..1111..", ".11..11.", "11....11", "1......1")),
    # ---- terra (la riva sud, gli isolotti)
    "GRASSA": ("Mud", "wet mud", False, mud("m1")),
    "GRASSB": ("Mud and grass", "mud with marsh grass", False, mud("m2", ((2, 5), (5, 11), (6, 4)))),
    "GRASSC": ("Puddle", "mud with a puddle", False,
               over(mud("m3"), "        ", "        ", "        ", "        ", "   ...  ", "  ..... ", " ...3...", " .......",
                    "  ..... ", "   ...  ", "        ", "        ", "        ", "     3  ", "        ", "        ")),
    "BUSH": ("Reed bed", "a thick clump of reeds on the mud", True,
             over(mud("m4"), "  2   2 ", "  3 2 3 ", " 23 3 3 ", " 33 3 32", " 33 3 33", " 33 3333", " 333 333", " 333 333",
                  " 3333333", "33333333", "33333333", "33333333", "13333331", " 133331 ", "        ", "        ")),
    # ---- pontili e passerelle (percorribili)
    "PATH": ("Walkway", "a plank walkway on posts, running east-west", False,
             A("11111111", "22122122", "22122122", "22122122", "22122122", "21122122", "22122122", "22122112",
               "22122122", "22122122", "22122122", "22122122", "22122122", "11111111", "1..1..1.", "1..1..1.")),
    "DIRT": ("Gangway", "a plank walkway running north-south", False,
             A("12222221", "11111111", "12222221", "12222221", "11111111", "12222221", "12221221", "11111111",
               "12222221", "12222221", "11111111", "12222221", "12122221", "11111111", "12222221", "12222221")),
    "COBBLE": ("Deck", "the deck of a platform", False, DECK),
    "BRIDGE": ("Ferry", "the ferry under the platform: stepping in takes you to the other landing", "npc", cut(FERRY, 1, 0)),
    "FOUNTAIN": ("Votive candles", "candles for the drowned: standing here heals", False,
                 over(DECK, "        ", "  3     ", "  3     ", " 121    ", " 121  3 ", " 111  3 ", "     121", "     121",
                      "     111", "   3    ", "   3    ", "  121   ", "  121   ", "  111   ", "        ", "        ")),
    "FOUNT0": ("Bottle tree NW", "the bottle tree: a dead tree hung with bottles that trap the spirits", True, cut(BTREE, 0, 0, DECK)),
    "FOUNT1": ("Bottle tree NE", "the bottle tree: a dead tree hung with bottles that trap the spirits", True, cut(BTREE, 1, 0, DECK)),
    "FOUNT2": ("Bottle tree SW", "the bottle tree: a dead tree hung with bottles that trap the spirits", True, cut(BTREE, 0, 1, DECK)),
    "FOUNT3": ("Bottle tree SE", "the bottle tree: a dead tree hung with bottles that trap the spirits", True, cut(BTREE, 1, 1, DECK)),
    # ---- arredi dei pontili
    "FENCE": ("Railing", "the railing of a platform, over the water", True,
              A("........", "........", "1..1..1.", "1..1..1.", "22222222", "1..1..1.", "1..1..1.", "22222222",
                "1..1..1.", "1..1..1.", "1..1..1.", "........", ".1......", "........", ".....1..", "........")),
    "FENCEV": ("Post line", "posts and a rope, north-south", True,
               A("...21...", "...21...", "..2221..", "...21...", "...21...", "...21...", "...21...", "..2221..",
                 "...21...", "...21...", "...21...", "...21...", "..2221..", "...21...", "...21...", "...21...")),
    "LAMP": ("Skull lantern", "a skull on a post, green light in its eyes", True,
             over(DECK, "  0000  ", " 033330 ", "03333330", "03033030", "03333330", " 030030 ", "  0000  ", "   00   ",
                  "   00   ", "   00   ", "   00   ", "   00   ", "   00   ", "  0000  ", " 000000 ", "        ")),
    "WELL": ("Drums", "two hide drums", True,
             over(DECK, "        ", "  0000  ", " 011110 ", "01111110", "01111110", "00111100", "02000020", "02022020",
                  "02200220", "02022020", "02200220", "02022020", "00222200", " 000000 ", "        ", "        ")),
    "STALL": ("Charm rack", "dolls and bottles hung on a frame", True,
              over(DECK, "0      0", "00000000", "0 0  0 0", "0 1  0 0", "0111 3 0", "0 1 3330", "0 1 3330", "01 1 3 0",
                   "0      0", "0  0   0", "0  1   0", "0 111  0", "0  1   0", "0 1 1  0", "00    00", "        ")),
    # ---- capanne su pali, mulino
    "BROOFA": ("Thatch ridge", "the ridge of a thatched roof", True,
               A("........", "........", "........", "22222222", "12121212", "21212121", "11211121", "12111211",
                 "11121112", "21112111", "11211121", "12111211", "11121112", "21112111", "11211121", "12111211")),
    "BROOF": ("Thatch eaves", "the lower edge of a thatched roof", True,
              over(ROOF, "        ", "        ", "        ", "        ", "        ", "        ", "        ", "        ",
                   "        ", "        ", "        ", "        ", "22222222", "11111111", "1.1.1.1.", "........")),
    "BROOFL": ("Spirit house roof", "the mossy roof of the spirit house", True,
               A("21112111", "21112111", "21312111", "11111111", "11211121", "11211121", "11211321", "11111111",
                 "21112111", "23112111", "21112111", "11111111", "11211121", "11211123", "11211121", "11111111")),
    "CHIMNEY": ("Smoke hole", "a clay chimney on the thatch", True,
                over(ROOF, "   3    ", "  3     ", "   3    ", "  2222  ", "  2112  ", "  2112  ", "  2222  ", "  1221  ",
                     "  1221  ", "  2222  ", " 222222 ", "        ", "        ", "        ", "        ", "        ")),
    "BWALL": ("Plank wall", "a wall of upright boards", True, WALL),
    "WINDOW": ("Lit window", "a small window, green light inside", True,
               over(WALL, "        ", "        ", "        ", " 111111 ", " 133131 ", " 133131 ", " 133131 ", " 111111 ",
                    " 133131 ", " 133131 ", " 111111 ", " 222222 ", "        ", "        ", "        ", "        ")),
    "HDOOR": ("Hut door", "the door of a hut, closed", True,
              over(WALL, "        ", "        ", "  1111  ", " 111111 ", " 112211 ", " 121121 ", " 121121 ", " 121121 ",
                   " 121121 ", " 121131 ", " 121121 ", " 121121 ", " 121121 ", " 121121 ", " 111111 ", "        ")),
    "SPIRE": ("Stilts", "the posts under a hut, in the water", True,
              A("11111111", "12211221", ".21..21.", ".21..21.", ".21..21.", ".21..21.", ".21..21.", ".21..21.",
                ".21..21.", ".21..21.", ".2133213", ".21..21.", "3213.21.", ".21..21.", ".1....1.", "........")),
    "SIGNS": ("Smith's sign", "an anvil on a board", True,
              over(WALL, "   11   ", "   11   ", " 111111 ", " 1....1 ", " 1.33.1 ", " 133331 ", " 1.33.1 ", " 1.33.1 ",
                   " 133331 ", " 1....1 ", " 111111 ", "        ", "        ", "        ", "        ", "        ")),
    "SIGNL": ("Alchemist's sign", "a flask on a board", True,
              over(WALL, "   11   ", "   11   ", " 111111 ", " 1....1 ", " 1.33.1 ", " 1.33.1 ", " 133331 ", " 13..31 ",
                   " 133331 ", " 1....1 ", " 111111 ", "        ", "        ", "        ", "        ", "        ")),
    "TSTAIRS": ("Bone gate", "an arch of bones in the wall of the spirit house: the way into the marsh", False,
                over(WALL, "        ", "  2222  ", " 232232 ", " 222222 ", "  2002  ", " 200002 ", "22000022", "20000002",
                     "20000002", "22000022", "20000002", "20000002", "22000022", "20000002", "20033002", "11111111")),
    "CRYPTL": ("Great idol NW", "the great idol of the spirit house: a horned skull mask on a post", True, cut(IDOL, 0, 0)),
    "CRYPTR": ("Great idol NE", "the great idol of the spirit house: a horned skull mask on a post", True, cut(IDOL, 1, 0)),
    "CRYPTA": ("Great idol SW", "the great idol of the spirit house: a horned skull mask on a post", True, cut(IDOL, 0, 1)),
    "CRYPTC": ("Great idol SE", "the great idol of the spirit house: a horned skull mask on a post", True, cut(IDOL, 1, 1)),
}
