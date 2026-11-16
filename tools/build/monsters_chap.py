#!/usr/bin/env python3
"""Mostri dei capitoli 2-4 (15/11, richiesta del committente: "disegna i mostri per capitolo oltre che i boss").
Solo DISEGNI, nello stesso formato di tools/build/monsters.py: 12x21 multicolor, '.' trasparente, 'b' MC0 (marrone 9),
'c' colore dello sprite, 'g' MC1 (grigio chiaro 15). Per ogni mostro: figura, le ultime 5 righe del secondo fotogramma
(le gambe), la variante forte (righe sovrapposte dall'alto: ' ' = lascia la base), nome, colore.
Un capitolo = 4 famiglie base + 4 varianti forti, come il capitolo 1 (stessi mtype 1..8: la RAM non cresce).
Come entrano nel gioco (15/11): tools/build/monsters.py chapter_set -> tools/build/gen_gfx.py (file GFXn del capitolo:
sprite + blocco info con colori e nomi) e docs/wiki/bestiario.md. Statistiche e IA restano quelle del tipo 1..8."""

# ============================================================== CAPITOLO 2: la palude di Blackwater
# Drowned: un annegato gonfio, le alghe che pendono, le braccia in avanti
DROWNED = [
    "............",
    "....cccc....",
    "...cccccc...",
    "..bcgccgcb..",
    "..bccccccb..",
    "..bccbbcc.b.",
    "...cccccc.b.",
    "....cccc....",
    "..cccccccc..",
    ".cccccccccc.",
    "ccc.cccc.ccc",
    "cc.cccccc.cc",
    "gg.ccbbcc.gg",
    "g..cccccc..g",
    "...cccccc...",
    "...bccccb...",
    "...cc..cc...",
    "...cc..cc...",
    "..bcc..cc...",
    "...cc..ccb..",
    "..ggg..ggg..",
]
DROWNED_L1 = [
    "...cc..cc...",
    "..cc....cc..",
    "..cc....ccb.",
    ".bcc....cc..",
    ".ggg....ggg.",
]
# Drowned Hulk: spalle enormi, la catena dell'ancora in vita
HULK_X = [
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "gg        gg",
    "ggg      ggg",
    "            ",
    "            ",
    "            ",
    "            ",
    "   bggggb   ",
    "   bg  gb   ",
]
# Bog Crawler: un insetto basso e largo, sei zampe, antenne
CRAWLER = [
    "............",
    "............",
    "............",
    "............",
    "............",
    "............",
    "..g......g..",
    "...g....g...",
    "...cccccc...",
    "..cgccccgc..",
    "..cccccccc..",
    "b.ccbccbcc.b",
    ".bccccccccb.",
    "b.cccccccc.b",
    ".bccbccbccb.",
    "b.cccccccc.b",
    ".b.cccccc.b.",
    "b..gc..cg..b",
    "...g....g...",
    "............",
    "............",
]
CRAWLER_L1 = [
    ".b.cccccc.b.",
    ".b.gc..cg.b.",
    "b..g....g..b",
    "............",
    "............",
]
# Crawler Queen: la cresta di aculei, le sacche delle uova
QUEEN_X = [
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "  g g  g g  ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "   gg  gg   ",
    "            ",
    "   gg  gg   ",
]
# Mire Witchling: una piccola strega incappucciata, il bastone
WITCHLING = [
    "............",
    ".....cc.....",
    "....cccc....",
    "....cccc....",
    "...cccccc..g",
    ".cccccccccgb",
    "...cggggc..b",
    "...gbggbg..b",
    "...cggggc..b",
    "....cggc..gb",
    "...cccccccgb",
    "..ccccccc..b",
    "..ccbccbc..b",
    "..ccccccc..b",
    "..ccccccc..b",
    ".ccccccccc.b",
    ".ccbcccbcc.b",
    ".ccccccccc..",
    ".ccccccccc..",
    "..cc.cc.cc..",
    "............",
]
WITCHLING_L1 = [
    ".ccbcccbcc.b",
    ".ccccccccc..",
    "cccccccccc..",
    ".cc.ccc.cc..",
    "............",
]
# Hag of the Mere: cappello alto con la fascia, il globo sul bastone
HAG_X = [
    "    cc      ",
    "    cc    gg",
    "   bbbb   gg",
]
# Will-o'-Wisp: un fuoco fatuo, una fiamma con un volto dentro
WISP = [
    "............",
    ".....c......",
    "....cc......",
    "....ccc.....",
    "...cccc.....",
    "...ccccc....",
    "..cccgccc...",
    "..ccgggcc...",
    ".cccgggccc..",
    ".ccggbggcc..",
    ".ccgbgbgcc..",
    ".ccggggggc..",
    ".cccggggcc..",
    "..cccggccc..",
    "..cccccccc..",
    "...cccccc...",
    "...c.cc.c...",
    "..c..c...c..",
    ".....c......",
    "............",
    "............",
]
WISP_L1 = [
    "...c.cc.c...",
    "...c..c.c...",
    "..c...c..c..",
    "............",
    "............",
]
# Corpse Light: dentro la fiamma un teschio
CORPSE_X = [
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "    b b     ",
    "            ",
    "     b      ",
    "    b b     ",
]

# ============================================================== CAPITOLO 3: il bastione nella neve
# Ash Ghoul: ingobbito, artigli lunghi
GHOUL = [
    "............",
    "............",
    "...cccc.....",
    "..cccccc....",
    "..cbccbc....",
    "..cccccc....",
    "..cgbbgc....",
    "...cccc.....",
    ".cccccccc...",
    "ccccccccccc.",
    "cc.ccccc.ccc",
    "cc.cccccc.cc",
    "c..ccbccc..c",
    "g..cccccc..g",
    "gg.cccccc.gg",
    "g..bccccb..g",
    "...ccc.cc...",
    "...cc..cc...",
    "..ccc..cc...",
    "..cc...cc...",
    ".ggg...ggg..",
]
GHOUL_L1 = [
    "...cc..ccc..",
    "...cc...cc..",
    "...cc...ccc.",
    "..cc.....cc.",
    ".ggg.....ggg",
]
# Pyre Ghoul: le fiamme sulla testa
PYRE_X = [
    "  g  g      ",
    " g gg g     ",
    "  g  g      ",
]
# Bone Archer: uno scheletro con l'arco teso
ARCHER = [
    "............",
    "...cccc.....",
    "..cccccc..b.",
    "..cbccbc.b..",
    "..cccccc.b..",
    "...cbbc.b...",
    "...cccc.b...",
    "....cc..b...",
    ".ccccccccg..",
    "c..cccc.b.g.",
    "c.c.cc.cb..g",
    "c..cccc.b.g.",
    "c.c.cc.cbg..",
    "...cccc.b...",
    "....cc..b...",
    "...cccc..b..",
    "...c..c..b..",
    "...c..c...b.",
    "...c..c.....",
    "...c..c.....",
    "..gg..gg....",
]
ARCHER_L1 = [
    "...c..c..b..",
    "..c....c..b.",
    "..c....c....",
    ".c......c...",
    ".gg.....gg..",
]
# Bone Marksman: il cappuccio, la faretra
MARKSMAN_X = [
    " bbbbbb     ",
    "b      b    ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "g           ",
    "g           ",
]
# Hellhound: un mastino infernale, di profilo
HOUND = [
    "............",
    "............",
    "............",
    "............",
    "............",
    ".g..g.......",
    ".cc.cc......",
    "ccccccc.....",
    "cgcccccc....",
    "ccccccccc...",
    "bbcccccccccc",
    "gcgccccccccc",
    "..cccccccccc",
    "...ccccccccc",
    "...cccbccccb",
    "...ccccccccc",
    "...cc.cc.ccc",
    "...cc.c..cc.",
    "...c..c..c..",
    "...c..c..c..",
    "..gg.gg.gg..",
]
HOUND_L1 = [
    "...cc.cc.ccc",
    "..cc..cc..cc",
    "..c....c...c",
    ".c.....c...c",
    ".gg...gg..gg",
]
# Hellhound Alpha: corna piu' grandi, gli aculei sulla schiena
ALPHA_X = [
    "            ",
    "            ",
    "            ",
    "            ",
    "  g  g      ",
    "g g  g g    ",
    "            ",
    "            ",
    "       g g g",
    "      g g g ",
]
# Frost Wight: un re morto di ghiaccio, la corona, la spada
WIGHT = [
    "............",
    "..g.g.g.....",
    "..ggggg.....",
    "..ccccc.....",
    ".ccbcbcc....",
    ".ccccccc..g.",
    "..cbbbc...g.",
    "..ccccc...g.",
    ".ccccccc..g.",
    "ccccccccc.g.",
    "cc.ccc.ccbbb",
    "cc.cbc.cc.b.",
    "gg.ccc.gg...",
    "...ccc......",
    "..ccccc.....",
    "..ccccc.....",
    ".ccccccc....",
    ".ccccccc....",
    ".cc.c.cc....",
    ".c..c..c....",
    "............",
]
WIGHT_L1 = [
    ".ccccccc....",
    "cccccccc....",
    ".cc.cc.cc...",
    "..c.c...c...",
    "............",
]
# Wight Lord: la corona grande, lo scudo
WLORD_X = [
    " gg g gg    ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "bbb         ",
    "bgb         ",
    "bbb         ",
]

# ============================================================== CAPITOLO 4: la cittadella
# Imp: piccolo, le ali, la coda, il forcone
IMP = [
    "............",
    "............",
    "............",
    "..g....g....",
    "..cc..cc....",
    "..cccccc...g",
    "..cgccgc.g.g",
    "..cccccc..g.",
    "b..cbbc...g.",
    "bb.cccc.bbg.",
    "bbbccccbbbg.",
    ".bbccccbb.g.",
    "..cccccc..g.",
    "...cccc...g.",
    "...cccc.....",
    "..cccccc...c",
    "..cc..cc..c.",
    "..cc..cc.c..",
    "..cc..ccc...",
    "..cc..cc....",
    ".ggg..ggg...",
]
IMP_L1 = [
    "..cc..cc.c..",
    ".cc....ccc..",
    ".cc....cc...",
    "cc......cc..",
    "ggg.....ggg.",
]
# Imp Overseer: le corna grandi
OVERSEER_X = [
    "            ",
    "            ",
    " ggg  ggg   ",
]
# Blood Knight: armatura, elmo con il pennacchio, lo spadone
KNIGHT = [
    "....b.......",
    "...bb.......",
    "..cccc....g.",
    ".cccccc...g.",
    ".cgggggc..g.",
    ".cgbggbc..g.",
    ".cccccc...g.",
    "..cccc....g.",
    "cccccccc..g.",
    "ccgccgccc.g.",
    "cc.cccc.ccg.",
    "cc.cggc.cbbb",
    "gg.cccc.g.b.",
    "...cbbc...b.",
    "..cccccc....",
    "..cccccc....",
    "..ccc.ccc...",
    "..cc...cc...",
    "..cc...cc...",
    "..cc...cc...",
    ".ggg...ggg..",
]
KNIGHT_L1 = [
    "..ccc.ccc...",
    ".ccc...cc...",
    ".cc....ccc..",
    "cc......cc..",
    "ggg.....ggg.",
]
# Blood Champion: le corna sull'elmo, lo scudo
CHAMPION_X = [
    "g      g    ",
    "gg    gg    ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "bbb         ",
    "bgb         ",
    "bgb         ",
    "bbb         ",
]
# Gargoyle: una bestia di pietra, le ali aperte
GARGOYLE = [
    "............",
    "..g......g..",
    "..cc....cc..",
    "c..cccccc..c",
    "cc.cgccgc.cc",
    "cccccccccccc",
    "cccccbbccccc",
    "cc.cccccc.cc",
    "cc.cccccc.cc",
    "c.cccccccc.c",
    "c.ccbccbcc.c",
    "..cccccccc..",
    "..cccccccc..",
    "...cccccc...",
    "...ccbbcc...",
    "..cccccccc..",
    "..ccc..ccc..",
    "..cc....cc..",
    "..cc....cc..",
    ".gcc....ccg.",
    ".ggg....ggg.",
]
GARGOYLE_L1 = [
    "..ccc..ccc..",
    "..cc....cc..",
    ".ccc....ccc.",
    ".gc......cg.",
    "ggg......ggg",
]
# Stone Gargoyle: corna grandi, le crepe nella pietra (15/11, ritocco: le crepe erano 'g' = grigio chiaro 15, lo stesso
# colore del corpo (15): nel gioco sparivano; ora 'b', scure)
STONE_X = [
    " gg      gg ",
    "  g      g  ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "   b    b   ",
    "            ",
    "    b  b    ",
]
# Cultist: un uomo incappucciato, il pugnale
CULTIST = [
    "............",
    "....cccc....",
    "...cccccc...",
    "..ccbbbbcc..",
    "..cbggggbc..",
    "..cbgbbgbc..",
    "..ccbggbcc..",
    "...cccccc...",
    "..cccccccc..",
    ".cccccccccc.",
    "ccc.cccc.ccc",
    "cc.cccccc.cc",
    "gg.ccggcc.gg",
    "g..ccggcc..b",
    "...cccccc..b",
    "..cccccccc..",
    "..cccccccc..",
    ".cccccccccc.",
    ".cccccccccc.",
    ".cc.cccc.cc.",
    "............",
]
CULTIST_L1 = [
    "..cccccccc..",
    ".cccccccccc.",
    "cccccccccccc",
    ".ccc.cc.ccc.",
    "............",
]
# High Cultist: la mitra
HIGH_X = [
    "    gg      ",
    "   gbbg     ",
]

# capitolo -> 4 famiglie: (nome base, figura, gambe, colore, nome forte, sovrapposizione, colore forte)
CHAPTER_MONSTERS = {
    2: [("drowned", DROWNED, DROWNED_L1, 3, "drowned hulk", HULK_X, 14),
        ("bog crawler", CRAWLER, CRAWLER_L1, 5, "crawler queen", QUEEN_X, 13),
        ("mire witchling", WITCHLING, WITCHLING_L1, 4, "hag of the mere", HAG_X, 10),
        ("will-o'-wisp", WISP, WISP_L1, 13, "corpse light", CORPSE_X, 7)],
    3: [("ash ghoul", GHOUL, GHOUL_L1, 12, "pyre ghoul", PYRE_X, 8),
        ("bone archer", ARCHER, ARCHER_L1, 1, "bone marksman", MARKSMAN_X, 7),
        ("hellhound", HOUND, HOUND_L1, 2, "hellhound alpha", ALPHA_X, 10),
        ("frost wight", WIGHT, WIGHT_L1, 14, "wight lord", WLORD_X, 3)],
    4: [("imp", IMP, IMP_L1, 10, "imp overseer", OVERSEER_X, 8),
        ("blood knight", KNIGHT, KNIGHT_L1, 2, "blood champion", CHAMPION_X, 4),
        ("gargoyle", GARGOYLE, GARGOYLE_L1, 12, "stone gargoyle", STONE_X, 15),
        ("cultist", CULTIST, CULTIST_L1, 4, "high cultist", HIGH_X, 7)],
}

if __name__ == "__main__":       # anteprima: out/work/villages/monsters_chap.png (serve Pillow)
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import monsters as MO, gen_gfx as G
    from PIL import Image
    S = 4
    img = Image.new("RGB", (8 * (24 * S + 12) + 12, 3 * (21 * S + 12) + 12), (20, 20, 24))
    for r, c in enumerate(sorted(CHAPTER_MONSTERS)):
        for k, (n, fig, l1, col, sn, x, scol) in enumerate(CHAPTER_MONSTERS[c]):
            for v, (f, cc) in enumerate(((MO.frames(fig, l1), col), (MO.frames(fig, l1, x), scol))):
                g = f[0]
                ox, oy = 12 + (k * 2 + v) * (24 * S + 12), 12 + r * (21 * S + 12)
                for y in range(21):
                    for xx in range(12):
                        p = g[y][xx]
                        if p:
                            colr = G.C64[(None, 9, cc, 15)[p]]
                            for a in range(2 * S):
                                for b in range(S):
                                    img.putpixel((ox + xx * 2 * S + a, oy + y * S + b), colr)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "out", "work", "villages")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, "monsters_chap.png"))
    print("monsters_chap.png")
