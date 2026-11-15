#!/usr/bin/env python3
"""Villaggio del capitolo 3: THE LAST CAMP, un campo di guerra su tre terrazze di una montagna innevata (15/11, TODO Z2).
Niente acqua, niente case, niente piazza: tende di pelli, palizzata con le torri di guardia, pareti di roccia fra una
terrazza e l'altra con le scale di legno, il grande falo' (cura), i tumuli dei caduti. L'ingresso del sotterraneo e' la
bocca di una grotta nella parete nord.
Colori: 0 bianco (neve), 1 grigio scuro (ombre, ferro, buio), 2 marrone (roccia, pelli, legno), 3 rosso (fuoco, stendardi)."""
from tileart import A, grid, put, hline, vline, noise, over, canvas, cut, rnd, W, H

PAL = (1, 11, 9, 2)
NAME = "The Last Camp"
HEAL = "the great bonfire"


def snow(key, dens=0.02):
    g = grid(0); noise(g, 1, dens, rnd(key))
    return g


SLUSH = grid(2)
noise(SLUSH, 0, 0.06, rnd("slush0")); noise(SLUSH, 1, 0.07, rnd("slush1"))
SNOW = snow("snow")


def tent():
    """tenda 3x2 tile (24x32 pixel): cono di pelli cucite, palo con il pennone rosso, neve sulla falda sinistra"""
    cv = [[0] * 24 for _ in range(32)]
    for y in range(4, 29):
        half = 1 + (y - 4) * 11 // 24
        x0, x1 = 12 - half, 11 + half
        for x in range(x0, x1 + 1):
            cv[y][x] = 2
            if (x - 12) % 5 == 0 and y > 8:
                cv[y][x] = 1                              # cuciture verticali
            if y % 7 == 3 and x % 2 == 0:
                cv[y][x] = 1                              # punti
        cv[y][x0] = 1; cv[y][x1] = 1
        if y < 20 and x0 + 1 < 11:
            cv[y][x0 + 1] = 0                             # neve sulla falda
            if y % 3:
                cv[y][x0 + 2] = 0
    for x in range(1, 23):
        cv[29][x] = 1                                     # ombra a terra
    for y in range(0, 5):
        cv[y][11] = 1; cv[y][12] = 1                      # palo
    for (x, y) in ((13, 0), (14, 0), (15, 0), (13, 1), (14, 1), (15, 1), (16, 1), (13, 2), (14, 2)):
        cv[y][x] = 3                                      # pennone
    return cv


TENT = tent()
FLAP = cut(TENT, 1, 1)


def door(icon):
    """lembo aperto della tenda (buio dentro, un bagliore) con il simbolo rosso sopra"""
    g = [r[:] for r in FLAP]
    for y in range(5, 13):
        hw = 1 if y < 7 else 2
        for x in range(4 - hw, 4 + hw):
            g[y][x] = 1
    put(g, 3, 11, 3); put(g, 4, 11, 3); put(g, 3, 12, 3)
    for x, y in icon:
        put(g, x, y, 3)
    return g


FIRE = canvas(                       # il grande falo' 2x2: fiamme rosse, il cuore bianco, i tronchi, il cerchio di pietre
    "9999999939999999",
    "9999993999999999",
    "9999999339999999",
    "9993999339993999",
    "9999993333999999",
    "9999933333399999",
    "9939933333399399",
    "9999333333339999",
    "9999333033339999",
    "9993333003333999",
    "9993330003333999",
    "9933330000333399",
    "9933300000333399",
    "9933300000033399",
    "9333300000033339",
    "9333000000003339",
    "9333000000003339",
    "9333300000033339",
    "9933330000333399",
    "9923333003333299",
    "9122333333332219",
    "1212233333322121",
    "1221222332221221",
    "9122122222212219",
    "9912211221122199",
    "9111122112211119",
    "1001911111191001",
    "1011999999991101",
    "9119991001999119",
    "9999991011999999",
    "9999999119999999",
    "9999999999999999")


def fire(tx, ty):
    return cut(FIRE, tx, ty, SLUSH)


TILES = {
    # ---- terreno
    "GRASSA": ("Snow", "fresh snow", False, SNOW),
    "GRASSB": ("Footprints", "snow with footprints", False,
               over(SNOW, "        ", "  1     ", "  1     ", "        ", "     1  ", "     1  ", "        ", "        ",
                    " 1      ", " 1      ", "        ", "    1   ", "    1   ", "        ", "        ", "        ")),
    "GRASSC": ("Dry tufts", "dry grass poking out of the snow", False,
               over(snow("s3"), "        ", "        ", "  2     ", " 2 2    ", "  2     ", "  1     ", "        ", "      2 ",
                    "     2 2", "      2 ", "      1 ", "        ", "   2    ", "  2 2   ", "   1    ", "        ")),
    "FLOWERS": ("Snow drift", "a drift shaped by the wind", False,
                over(snow("s4", 0), "        ", "        ", "   1111 ", "  1     ", " 1      ", "        ", "        ", "      11",
                     "    11  ", "  11    ", " 1      ", "        ", "        ", "   111  ", "  1     ", "        ")),
    "PATH": ("Trodden snow", "the trodden paths of the camp: mud and snow", False, SLUSH),
    "COBBLE": ("Log floor", "a floor of split logs", False,
               A("22222212", "22222212", "21222222", "11111111", "22122222", "22122222", "22222221", "11111111",
                 "22222122", "22222122", "12222222", "11111111", "21222222", "21222222", "22221222", "11111111")),
    "DIRT": ("Wooden stairs", "log steps between two terraces", False,
             A("10000001", "12222221", "12222221", "11111111", "10000001", "12222221", "12222221", "11111111",
               "10000001", "12222221", "12222221", "11111111", "10000001", "12222221", "12222221", "11111111")),
    "BRIDGE": ("Planks", "planks laid on the snow", False,
               A("........", "11111111", "22222122", "22222122", "11111111", "21222222", "21222222", "11111111",
                 "22221222", "22221222", "11111111", "22122222", "22122222", "11111111", "........", "........")),
    # ---- roccia
    "BROOF": ("Cliff edge", "the snowy edge on top of a rock wall", True,
              A("........", "........", "........", "....1...", "........", "........", ".1......", "........",
                "0.0..0.0", "20002020", "22022222", "22222122", "21222122", "21222222", "22221222", "22221221")),
    "BWALL": ("Rock wall", "the rock face between two terraces", True,
              A("22122212", "22122212", "21122222", "21222221", "22222121", "22212122", "02212222", "00222212",
                "22222212", "22122122", "21122122", "21222222", "21222100", "22222220", "22122222", "22122212")),
    "BROOFA": ("Cliff foot", "rubble and snow at the foot of a rock wall", True,
               A("22122212", "21122122", "21222122", "22222222", "12221221", "22212222", "02222120", "00122200",
                 "0.022.00", "...00...", "..1.....", ".....21.", ".1...11.", "........", "...1....", "........")),
    "BROOFL": ("Mountain", "the rock of the mountain, with snow in the cracks", True,
               A("22222222", "22212222", "22122222", "22222220", "22222200", "22222222", "21222222", "22222122",
                 "22221222", "02222222", "00222222", "22222212", "22222122", "22222222", "22122222", "22222222")),
    "TREE": ("Fir", "a fir loaded with snow", True,
             A("...11...", "...01...", "..0011..", "..1111..", ".001111.", ".111111.", "..0011..", ".001111.",
               "00111111", "11111111", ".0001111", "00011111", "11111111", "...22...", "...22...", "..1221..")),
    "BUSH": ("Boulder", "a boulder with a cap of snow", True,
             A("........", "........", "........", "..0000..", ".000000.", "00222220", "02222212", "22212222",
               "22222222", "22122122", "22222221", ".222221.", "..1111..", "........", "........", "........")),
    # ---- tende (3x2: [ @ ] sopra, / porta \ sotto)
    "CRYPTL": ("Tent NW", "the left slope of a hide tent, with snow", True, cut(TENT, 0, 0)),
    "CRYPTB": ("Tent top", "the top of a tent: pole and red pennon", True, cut(TENT, 1, 0)),
    "CRYPTR": ("Tent NE", "the right slope of a hide tent", True, cut(TENT, 2, 0)),
    "CRYPTA": ("Tent SW", "the left side of a tent", True, cut(TENT, 0, 1)),
    "CRYPTC": ("Tent SE", "the right side of a tent", True, cut(TENT, 2, 1)),
    "HDOOR": ("Laced flap", "the flap of a tent, laced shut", True,
              over(FLAP, "        ", "        ", "        ", "        ", "   11   ", "  1  1  ", "   11   ", "  1  1  ",
                   "   11   ", "  1  1  ", "   11   ", "  1  1  ", "   11   ", "        ", "        ", "        ")),
    "DSMITH": ("Smith's tent", "the open flap of the smith's tent: an anvil", False,
               door([(2, 1), (3, 1), (4, 1), (5, 1), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3), (5, 3)])),
    "DALCH": ("Healer's tent", "the open flap of the alchemist's tent: a flask", False,
              door([(3, 0), (4, 0), (3, 1), (4, 1), (2, 2), (3, 2), (4, 2), (5, 2), (2, 3), (3, 3), (4, 3), (5, 3)])),
    "DHOME": ("Mess tent", "the open flap of the inn tent: a mug", False,
              door([(2, 1), (3, 1), (4, 1), (2, 2), (3, 2), (4, 2), (5, 2), (2, 3), (3, 3), (4, 3)])),
    "SIGNS": ("Smith's post", "a post with a hammer", True,
              over(SNOW, "        ", " 111111 ", " 1....1 ", " 1.33.1 ", " 133331 ", " 1.33.1 ", " 1.33.1 ", " 1....1 ",
                   " 111111 ", "   22   ", "   22   ", "   22   ", "   22   ", "   22   ", "  1111  ", "        ")),
    "SIGNL": ("Healer's post", "a post with a flask", True,
              over(SNOW, "        ", " 111111 ", " 1....1 ", " 1.33.1 ", " 1.33.1 ", " 133331 ", " 133331 ", " 1....1 ",
                   " 111111 ", "   22   ", "   22   ", "   22   ", "   22   ", "   22   ", "  1111  ", "        ")),
    # ---- palizzata, torri, cancello
    "FENCE": ("Palisade", "a palisade of pointed stakes", True,
              A("........", ".2...2..", ".2.2.2.2", "02020202", "22222222", "21212121", "21212121", "11111111",
                "21212121", "21212121", "21212121", "21212121", "21212121", "11111111", "........", "..1.....")),
    "FENCEV": ("Palisade (side)", "the palisade seen from the side", True,
               A("...2....", "..021...", "..221...", "..221...", "...2....", "..021...", "..221...", "..221...",
                 "...2....", "..021...", "..221...", "..221...", "...2....", "..021...", "..221...", "..221...")),
    "WATERL": ("Gate post", "a gate post with a torch", True,
               A("...33...", "..3303..", "..3333..", "...33...", "..1111..", "..0221..", "..2221..", "..2221..",
                 "..2121..", "..2221..", "..2221..", "..2121..", "..2221..", "..2221..", ".111111.", "........")),
    "WATERR": ("Skull post", "a post with the skull of a beast", True,
               A("........", ".1....1.", ".100001.", "..0000..", "..0101..", "..0000..", "...00...", "..1221..",
                 "..2221..", "..2121..", "..2221..", "..2221..", "..2121..", "..2221..", ".111111.", "........")),
    "GRAVE2": ("Watchtower top", "the roofed platform of a watchtower", True,
               A("........", "...00...", "..0000..", ".000000.", "00000000", "11111111", ".1....1.", ".1.33.1.",
                 ".1.33.1.", ".1....1.", "22222222", "21212121", "22222222", ".21..12.", ".2.11.2.", ".2.11.2.")),
    "GRAVE": ("Watchtower legs", "the crossed beams of a watchtower", True,
              A(".21..12.", ".2.11.2.", ".2.11.2.", ".21..12.", ".2....2.", ".21..12.", ".2.11.2.", ".2.11.2.",
                ".21..12.", ".2....2.", ".21..12.", ".2.11.2.", ".2.11.2.", ".21..12.", "11111111", "........")),
    # ---- arredi del campo
    "LAMP": ("Brazier", "an iron brazier", True,
             over(SNOW, "   3    ", "  3 3   ", "   33   ", "  3333  ", " 133331 ", " 111111 ", "  1111  ", "   11   ",
                  "   11   ", "  1  1  ", "  1  1  ", " 1    1 ", " 1    1 ", "        ", "        ", "        ")),
    "STALL": ("Weapon rack", "spears and a shield", True,
              over(SNOW, " 1  1  1", " 1  1  1", " 1  1  1", "22222222", " 1  1  1", " 1 331 1", " 13333 1", " 13333 1",
                   " 1 331 1", " 1  1  1", "22222222", " 1  1  1", " 1  1  1", "11 11 11", "        ", "        ")),
    "WELL": ("Supplies", "crates and a barrel under the snow", True,
             over(SNOW, "        ", " 0000   ", "111111  ", "122221  ", "121121  ", "122221  ", "1111110.", "    1001",
                  "   12221", "   11111", "   12221", "   12221", "   11111", "    111 ", "        ", "        ")),
    "CHIMNEY": ("Sled", "a sled loaded with furs", True,
                over(SNOW, "        ", "        ", "        ", "  0000  ", " 222220 ", "22122220", "22222122", "11111111",
                     "1      1", "11111111", " 1    1 ", "11111111", "        ", "        ", "        ", "        ")),
    "WINDOW": ("Cairn", "a cairn with the helmet of a fallen warrior", True,
               over(SNOW, "        ", "   11   ", "  1001  ", "  1111  ", "  1  1  ", "   00   ", "  0220  ", " 022220 ",
                    " 222122 ", "22122222", "22222212", "21222222", " 111111 ", "        ", "        ", "        ")),
    "SPIRE": ("War banner", "the red banner of the camp", True,
              over(SNOW, "  1     ", "  13333 ", "  133333", "  133033", "  133333", "  13333 ", "  1333  ", "  133   ",
                   "  1     ", "  1     ", "  1     ", "  1     ", "  1     ", "  1     ", " 111    ", "        ")),
    # ---- cura e sotterraneo
    "FOUNTAIN": ("By the fire", "a log to sit on by the bonfire: resting here heals", False,
                 over(SLUSH, "        ", "     3  ", "        ", "  3     ", "        ", " 111111 ", "12222221", "12122121",
                      "12222221", " 111111 ", "  1  1  ", "        ", "   3    ", "        ", "        ", "        ")),
    "FOUNT0": ("Bonfire NW", "the great bonfire", True, fire(0, 0)),
    "FOUNT1": ("Bonfire NE", "the great bonfire", True, fire(1, 0)),
    "FOUNT2": ("Bonfire SW", "the logs and the ring of stones", True, fire(0, 1)),
    "FOUNT3": ("Bonfire SE", "the logs and the ring of stones", True, fire(1, 1)),
    "TSTAIRS": ("Cave mouth", "the mouth of a cave in the rock wall: the way down", False,
                A("22122212", "21111122", "11111112", "10101011", "10111011", "11111111", "11111111", "11111111",
                  "11111111", "11131111", "11111111", "11111111", "11111111", "11111111", "21111112", "22111122")),
}
