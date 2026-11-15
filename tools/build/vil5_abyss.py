#!/usr/bin/env python3
"""Villaggio del capitolo 5 (prototipo): THE CITY OF THE ABYSS, isole di pietra sospese nel vuoto (15/11, TODO Z2).
Niente terreno continuo: otto isole unite da ponti di luce (est-ovest e nord-sud), ognuna con una cosa sola. Case a
cupola, guglie di cristallo, obelischi, statue senza volto. Cura: il cuore dell'Abisso, un cristallo che galleggia.
L'ingresso del sotterraneo e' la Bocca, sull'isola a nord.
Colori: 0 nero (il vuoto), 1 blu (pietra), 2 azzurro (pietra chiara, cristallo), 3 viola (bagliore, luce)."""
from tileart import A, grid, put, hline, vline, noise, over, canvas, cut, rnd

PAL = (0, 6, 14, 4)
NAME = "The City of the Abyss"
HEAL = "the heart of the abyss"

FLOOR = A("11111111", "11121111", "11111111", "11111101", "11111011", "11111111", "12111111", "11111111",
          "11111111", "11111211", "10111111", "11011111", "11111111", "11111112", "11211111", "11111111")


def dome():
    """casa a cupola 3x2 tile (24x32 pixel): cupola chiara con le nervature viola, la punta, il muro"""
    cv = [[9] * 24 for _ in range(32)]
    for y in range(4, 31):
        for x in range(24):
            if y <= 22:
                inside = ((x + 0.5 - 12) / 11.5) ** 2 + ((y - 22) / 18.0) ** 2 <= 1
            else:
                inside = 1 <= x <= 22
            if not inside:
                continue
            c = 2
            if x >= 16 and (x + y) % 2 == 0:
                c = 1                                   # ombra a destra
            if x in (6, 12, 17) and y % 4 != 1:
                c = 3                                   # nervature
            if y == 22:
                c = 3
            if y == 30:
                c = 0
            cv[y][x] = c
    for y in range(4, 31):                             # contorno
        xs = [x for x in range(24) if cv[y][x] != 9]
        if xs:
            cv[y][xs[0]] = 0 if y > 22 else 1; cv[y][xs[-1]] = 0
    for y in range(0, 5):
        cv[y][11] = 2; cv[y][12] = 2
    cv[0][11] = 3; cv[0][12] = 3; cv[1][10] = 3; cv[1][13] = 3
    return cv


DOME = dome()
DMID = cut(DOME, 1, 1, FLOOR)


def door(icon, sealed=False):
    g = [r[:] for r in DMID]
    for y in range(5, 15):
        for x in range(2, 6):
            if y > 6 or x in (3, 4):
                g[y][x] = 3 if sealed and (x + y) % 2 else 0
    for x, y in ((1, 7), (6, 7), (1, 10), (6, 10), (1, 13), (6, 13), (2, 5), (5, 5), (3, 4), (4, 4)):
        put(g, x, y, 3)
    for x, y in icon:
        put(g, x, y, 0)
    return g


HEART = canvas(                      # il cuore dell'Abisso 2x2: un cristallo sfaccettato che galleggia sopra un cerchio di rune
    "9999999229999999",
    "9999992222999999",
    "9999922322299999",
    "9999223332229999",
    "9992223333222999",
    "9922233333322299",
    "9222333003332229",
    "2222330000333222",
    "2223330000033322",
    "2223300330003322",
    "2223300330003322",
    "2223330000033322",
    "2222330000333221",
    "9222333003332219",
    "9922233333322199",
    "9992223333221999",
    "9999222332219999",
    "9999922322199999",
    "9999992221999999",
    "9999999219999999",
    "9999999999999999",
    "9999993993999999",
    "9999999999999999",
    "9993333333333999",
    "9933000000003399",
    "9330033333300339",
    "9300330000330039",
    "9330033333300339",
    "9933000000003399",
    "9993333333333999",
    "9999999999999999",
    "9999999999999999")

TILES = {
    # ---- il vuoto (solido)
    "WATER": ("Void", "the void", True,
              A("........", "........", "........", ".....1..", "........", "........", "........", "........",
                "........", ".1......", "........", "........", "........", "........", "......1.", "........")),
    "WATERL": ("Stars", "the void, a few stars", True,
               A("........", "..2.....", "........", "........", "......3.", "........", "........", ".1......",
                 "....2...", "...222..", "....2...", "........", ".......1", "..3.....", "........", "........")),
    "WATERR": ("Nebula", "a violet cloud in the void", True,
               A("........", "....33..", "..333333", ".3331333", "33313331", ".3333333", "..33133.", "...333..",
                 "......3.", "........", ".1......", "........", ".....33.", "....333.", "........", "........")),
    "CHIMNEY": ("Drifting rock", "a piece of the city drifting away", True,
                A("........", "........", "........", "...22...", "..22211.", ".2221111", "22211111", "12111111",
                  ".1111111", "..11111.", "...111..", "....1...", "........", "........", "..3.....", "........")),
    "FENCEV": ("Hanging chain", "a chain hanging into the void", True,
               A("...22...", "..2..2..", "..2..2..", "...22...", "...22...", "..2..2..", "..2..2..", "...22...",
                 "...22...", "..2..2..", "..2..2..", "...22...", "...33...", "..3333..", "...33...", "........")),
    # ---- le isole: pavimento e orli
    "GRASSA": ("Blue stone", "the stone of the islands", False, FLOOR),
    "GRASSB": ("Rune", "a rune carved in the stone", False,
               over(FLOOR, "        ", "        ", "  3333  ", " 3    3 ", " 3 33 3 ", " 3 3  3 ", " 3 33 3 ", " 3    3 ",
                    "  3333  ", "        ", "        ", "        ", "        ", "        ", "        ", "        ")),
    "GRASSC": ("Shards", "shards of crystal on the stone", False,
               over(FLOOR, "        ", "        ", "        ", "        ", "        ", "  2     ", "  22    ", " 2232   ",
                    " 2322   ", "  220   ", "        ", "      2 ", "     232", "      20", "        ", "        ")),
    "FLOWERS": ("Glow caps", "luminous mushrooms", False,
                over(FLOOR, "        ", "  33    ", " 3333   ", "  22    ", "  2   3 ", "     333", "      2 ", "      2 ",
                     " 33     ", "3333    ", " 22  3  ", " 2  333 ", "     2  ", "        ", "        ", "        ")),
    "COBBLE": ("Mosaic", "a mosaic floor", False,
               A("21112111", "12121212", "11211121", "12121212", "21112111", "12131212", "11211121", "12121212",
                 "21112111", "12121212", "11211121", "12121312", "21112111", "12121212", "11211121", "12121212")),
    "FENCE": ("Island rim", "the upper rim of an island", True,
              A("........", "........", "..1.....", "........", "........", ".....3..", "........", "........",
                "........", "2..22..2", "22222222", "21212121", "12121212", "11111111", "11211111", "11111111")),
    "GRAVE": ("Underside", "the rock under an island", True,
              A("11111111", "11121111", "11111111", "01111110", "01111210", "00111100", "00111100", "00011100",
                "00011000", "00011000", "00001000", "00001000", "........", "....3...", "........", "........")),
    "GRAVE2": ("Underside with roots", "the rock under an island, crystals growing down", True,
               A("11111111", "11111211", "11111111", "11011111", "11001110", "01002110", "01002100", "01003100",
                 "00002000", "00003000", "00002000", "00000000", "..3.....", "........", "........", "........")),
    "CRYPTL": ("Edge W", "the western edge of an island", True,
               A("....0111", "...01111", "...01111", "..011111", "...01211", "...01111", "....0111", "...01111",
                 "..011111", "..011111", "...01111", "....0111", "...01121", "...01111", "..011111", "...01111")),
    "CRYPTR": ("Edge E", "the eastern edge of an island", True,
               A("1110....", "11110...", "11110...", "111110..", "11210...", "11110...", "1110....", "11110...",
                 "111110..", "111110..", "11110...", "1110....", "12110...", "11110...", "111110..", "11110...")),
    # ---- ponti di luce (percorribili)
    "PATH": ("Light bridge", "a bridge of light, east-west", False,
             A("........", "........", "........", "22222222", "33333333", "32333233", "33333333", "33323333",
               "33333333", "32333323", "33333333", "22222222", "..3.....", "......3.", "........", "........")),
    "DIRT": ("Light bridge N-S", "a bridge of light, north-south", False,
             A(".233332.", ".233332.", ".232332.", ".233332.", ".233332.", ".233322.", ".233332.", ".233332.",
               ".233332.", ".223332.", ".233332.", ".233332.", ".233232.", ".233332.", ".233332.", ".233332.")),
    "BRIDGE": ("Stepping stone", "a disc of stone where two bridges meet", False,
               A("..2222..", ".211112.", "21111112", "21121112", "21111112", "21111112", "21111212", "21111112",
                 "21111112", "21211112", "21111112", "21111112", "21111112", "21111112", ".211112.", "..2222..")),
    # ---- case a cupola (3x2: / @ \ sopra, W porta R sotto)
    "CRYPTA": ("Dome NW", "a domed house", True, cut(DOME, 0, 0, FLOOR)),
    "CRYPTB": ("Dome top", "the spike on top of a dome", True, cut(DOME, 1, 0, FLOOR)),
    "CRYPTC": ("Dome NE", "a domed house", True, cut(DOME, 2, 0, FLOOR)),
    "BWALL": ("Dome SW", "the wall of a domed house", True, cut(DOME, 0, 1, FLOOR)),
    "BROOF": ("Dome SE", "the wall of a domed house", True, cut(DOME, 2, 1, FLOOR)),
    "HDOOR": ("Sealed door", "a door sealed with violet light", True, door([], sealed=True)),
    "DSMITH": ("Smith's door", "the door of the smith: an anvil", False,
               door([(2, 1), (3, 1), (4, 1), (5, 1), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3), (5, 3)])),
    "DALCH": ("Alchemist's door", "the door of the alchemist: a flask", False,
              door([(3, 0), (4, 0), (3, 1), (4, 1), (2, 2), (3, 2), (4, 2), (5, 2), (2, 3), (3, 3), (4, 3), (5, 3)])),
    "DHOME": ("Inn door", "the door of the inn: a mug", False,
              door([(2, 1), (3, 1), (4, 1), (2, 2), (3, 2), (4, 2), (5, 2), (2, 3), (3, 3), (4, 3)])),
    "SIGNS": ("Smith's stone", "a floating stone with the sign of the anvil", True,
              over(FLOOR, "        ", " 222222 ", " 2....2 ", " 2.33.2 ", " 233332 ", " 2.33.2 ", " 2.33.2 ", " 233332 ",
                   " 2....2 ", " 222222 ", "        ", "   33   ", "        ", "  0000  ", "        ", "        ")),
    "SIGNL": ("Alchemist's stone", "a floating stone with the sign of the flask", True,
              over(FLOOR, "        ", " 222222 ", " 2....2 ", " 2.33.2 ", " 2.33.2 ", " 233332 ", " 23..32 ", " 233332 ",
                   " 2....2 ", " 222222 ", "        ", "   33   ", "        ", "  0000  ", "        ", "        ")),
    # ---- arredi
    "TREE": ("Crystal spire", "a tall crystal", True,
             over(FLOOR, "   2    ", "   22   ", "  232   ", "  2320  ", "  2320  ", " 223220 ", " 2232202", " 2332202",
                  "22332202", "22332200", "2233220 ", "2233220 ", "22332200", "02222000", " 000000 ", "        ")),
    "BUSH": ("Crystals", "a cluster of crystals", True,
             over(FLOOR, "        ", "        ", "        ", "    2   ", " 2  22  ", " 22 23  ", " 23 230 ", " 23 2302",
                  "223022 2", "22302232", "22302230", "02200220", " 000000 ", "        ", "        ", "        ")),
    "LAMP": ("Flame orb", "a violet flame floating over a pedestal", True,
             over(FLOOR, "   33   ", "  3333  ", " 332233 ", " 332233 ", "  3333  ", "   33   ", "        ", "   22   ",
                  "  2222  ", "  2002  ", "  2222  ", "  2002  ", " 222222 ", " 000000 ", "        ", "        ")),
    "WELL": ("Faceless statue", "a statue without a face", True,
             over(FLOOR, "        ", "   22   ", "  2002  ", "  2002  ", "   22   ", "  2222  ", " 222222 ", " 2 22 2 ",
                  " 2 22 2 ", "   22   ", "   22   ", "  2222  ", " 222222 ", " 000000 ", "        ", "        ")),
    "STALL": ("Altar", "an altar with a violet flame", True,
              over(FLOOR, "        ", "   3    ", "  333   ", "   3    ", "22222222", "20000002", " 222222 ", "  2002  ",
                   "  2332  ", "  2002  ", "  2002  ", " 222222 ", "22222222", "00000000", "        ", "        ")),
    "SPIRE": ("Obelisk (top)", "the top of an obelisk", True,
              over(FLOOR, "        ", "        ", "   2    ", "   22   ", "   22   ", "  232   ", "  2320  ", "  2320  ",
                   "  2320  ", "  2320  ", "  2320  ", "  2320  ", "  2320  ", "  2320  ", "  2320  ", "  2320  ")),
    "WINDOW": ("Obelisk (base)", "the base of an obelisk", True,
               over(FLOOR, "  2320  ", "  2320  ", "  2320  ", "  2320  ", "  2320  ", "  2320  ", "  2320  ", "  2220  ",
                    "  2220  ", " 222200 ", " 222200 ", "22222200", "00000000", "        ", "        ", "        ")),
    # ---- cura e sotterraneo
    "FOUNTAIN": ("Rune ring", "the runes around the heart: standing here heals", False,
                 over(FLOOR, "        ", "  3  3  ", " 3    3 ", "   33   ", "  3  3  ", "3 3  3 3", "  3  3  ", "   33   ",
                      " 3    3 ", "  3  3  ", "        ", "   33   ", "  3  3  ", "   33   ", "        ", "        ")),
    "FOUNT0": ("Heart NW", "the heart of the Abyss, a floating crystal", True, cut(HEART, 0, 0, FLOOR)),
    "FOUNT1": ("Heart NE", "the heart of the Abyss", True, cut(HEART, 1, 0, FLOOR)),
    "FOUNT2": ("Heart SW", "the point of the crystal and the ring of runes under it", True, cut(HEART, 0, 1, FLOOR)),
    "FOUNT3": ("Heart SE", "the point of the crystal and the ring of runes under it", True, cut(HEART, 1, 1, FLOOR)),
    "TSTAIRS": ("The Maw", "the throat of the Abyss: the way down", False,
                A("22022022", "20002000", "00000000", "00033000", "00300300", "03003030", "03030030", "03030030",
                  "03003030", "00300300", "00033000", "00000000", "00000000", "00020002", "20222022", "22222222")),
    "BROOFA": ("Jaw W", "the western jaw of the Maw", True,
               over(FLOOR, "    2222", "   22222", "  222220", "  22220.", " 22220..", " 2220.2.", " 2220.22", " 2220..2",
                    " 2220...", " 2220.2.", " 2220.22", " 22220.2", "  22220.", "  222220", "   22222", "    2222")),
    "BROOFL": ("Jaw E", "the eastern jaw of the Maw", True,
               over(FLOOR, "2222    ", "22222   ", "022222  ", ".02222  ", "..02222 ", ".2.0222 ", "22.0222 ", "2..0222 ",
                    "...0222 ", ".2.0222 ", "22.0222 ", "2.02222 ", ".02222  ", "022222  ", "22222   ", "2222    ")),
}
