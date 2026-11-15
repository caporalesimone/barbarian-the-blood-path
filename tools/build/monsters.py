"""Mostri multicolor 12x21 (ASCII): '.'=trasparente, 'b'=MC0 (marrone 9),
'c'=colore dello sprite (cambia per variante), 'g'=MC1 (grigio chiaro 15)."""

MAP = {".": 0, "b": 1, "c": 2, "g": 3}


def grid(rows):
    assert len(rows) == 21, len(rows)
    for r in rows:
        assert len(r) == 12, (r, len(r))
    return [[MAP[ch] for ch in r] for r in rows]


def overlay(base, extra):
    """extra: lista di 21 righe; i caratteri diversi da ' ' sostituiscono la base"""
    out = []
    for b, e in zip(base, extra):
        out.append("".join(eb if eb != " " else bb for bb, eb in zip(b, e.ljust(12))))
    return out


def legs(rows, a, b):
    """frame 1: sostituisce le righe dalla a alla fine con b"""
    return rows[:a] + b


# ------------------------------------------------------------------ FALLEN
FALLEN = [
    "............",
    "............",
    "..........g.",
    ".g....g..ggg",
    ".gc..cg...b.",
    "..cccc....b.",
    ".cgccgc...b.",
    ".cccccc...b.",
    ".cbbbbc...b.",
    "..cccc....b.",
    ".ccccccccbb.",
    "cccccccc.bc.",
    "c.cccccc..b.",
    "c.ccbbcc..b.",
    "c.cccccc..b.",
    "..bbbbbb..b.",
    "..cccccc....",
    "..cc..cc....",
    "..cc..cc....",
    "..cc..cc....",
    ".ccc..ccc...",
]
FALLEN_L1 = [
    "..cccccc....",
    "..cc...cc...",
    ".cc....cc...",
    ".cc.....cc..",
    "ccc.....ccc.",
]
# Capo dei Fallen ("Warchief"): copricapo di ossa, scudo, punta d'ascia
WARCHIEF_X = [
    " g g  g g   ",
    " bgbbbbgb   ",
    "  b    b  g ",
    "          gg",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    " g       g  ",
    "bgb         ",
    "bgb         ",
    "bbb         ",
    "            ",
    "            ",
    "  bggggb    ",
]

# ------------------------------------------------------------------ SKELETON
SKELETON = [
    "............",
    "............",
    "...cccccc...",
    "..cccccccc..",
    "..c..cc..c..",
    "..c..cc..c..",
    "..cccccccc..",
    "...c.cc.c...",
    "....cccc....",
    ".....cc....g",
    "..cccccccc.g",
    ".c..cccc..cg",
    ".c.cccccc.cg",
    ".c..cccc..cg",
    ".c.cccccc.bb",
    "....cccc...b",
    "...cc..cc...",
    "...c....c...",
    "...c....c...",
    "...c....c...",
    "..cc....cc..",
]
SKELETON_L1 = [
    "...cc..cc...",
    "...c.....c..",
    "..c......c..",
    "..c.......c.",
    ".cc.......cc",
]
# Skeleton King: corona, mantello, spada piu' lunga
KING_X = [
    "..g.gg.g....",
    "..bgbbgb...g",
    "..bbbbbb...g",
    "           g",
    "            ",
    "            ",
    "            ",
    "            ",
    "  g      g g",
    " bb      bbg",
    "bb        bg",
    "b           ",
    "b           ",
    "b           ",
    "b           ",
    "b           ",
]

# ------------------------------------------------------------------ ZOMBIE
ZOMBIE = [
    "............",
    "............",
    "...cccc.....",
    "..cccccc....",
    "..cgccgc....",
    "..cccccc....",
    "..cbbbc.....",
    "...cccc.....",
    "..bbbbbbb...",
    ".bbbbbbbbccc",
    ".bbcbbbbbccc",
    ".bbbbcbbb...",
    ".cbbbbbbb...",
    ".cbbbbbbbccc",
    "..bbbbbbbccc",
    "..gggggg....",
    "..gg..gg....",
    "..gg..gg....",
    "..cc..cc....",
    "..cc..cc....",
    ".ccc..ccc...",
]
ZOMBIE_L1 = [
    "..gg..gg....",
    "..gg...gg...",
    "..cc...cc...",
    ".cc.....cc..",
    "ccc.....ccc.",
]
# Lich: corona di spine, bastone con globo, cappuccio
LICH_X = [
    "..g.g.g...g.",
    "..gggggg.ggg",
    "..b    b..g.",
    ".b      b.b.",
    ".b      b.b.",
    "          b.",
    "          b.",
    "          b.",
    "          b.",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "  bbbbbb    ",
]

# ------------------------------------------------------------------ DEMON
DEMON = [
    "............",
    "............",
    ".g........g.",
    ".gg.cccc.gg.",
    "..gccccccg..",
    "...cgccgc...",
    "...cccccc...",
    "...cbbbbc...",
    "b...cccc...b",
    "bb.cccccc.bb",
    "bbcccccccccb",
    "bbcccbbcccbb",
    "bb.cccccc.bb",
    "b..cccccc..b",
    "...cccccc...",
    "...bbbbbb...",
    "...cc..cc...",
    "...cc..cc...",
    "...cc..cc...",
    "...cc..cc...",
    "..ggg..ggg..",
]
DEMON_L1 = [
    "...cc..cc...",
    "..cc....cc..",
    "..cc....cc..",
    ".cc......cc.",
    ".ggg....ggg.",
]
# Balrog: fiamme sulla testa, ali piu' grandi, frusta
BALROG_X = [
    "c..c.cc.c..c",
    ".cc.cccc.cc.",
    "g          g",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "   gbbbbg   ",
]

# ------------------------------------------------------------------ BOSS FINALE
# Lord of Ruin (07/11 sera): come il demone del logo della copertina (data/title_src.png): corna grosse che salgono
# verso l'esterno, ali spiegate dietro le spalle (membrana scura 'b', ossa 'c'), bocca spalancata con le zanne,
# artigli chiari, zoccoli. Colore 2 (rosso) come nel logo.
LORD = [
    "g..........g",
    "gg..cccc..gg",
    ".g.cccccc.g.",
    ".gccccccccg.",
    "..cgccccgc..",
    "..cccccccc..",
    "..cbbbbbbc..",
    "..cgbbbbgc..",
    "b..cccccc..b",
    "bb.cccccc.bb",
    "bbbccccccbbb",
    "gccccccccccg",
    "gbbccccccbbg",
    "bb.cbccbc.bb",
    "b..cccccc..b",
    "...bbbbbb...",
    "...cc..cc...",
    "...cc..cc...",
    "...cc..cc...",
    "...cc..cc...",
    "..ggg..ggg..",
]
LORD_L1 = [
    "...cc..cc...",
    "..cc....cc..",
    "..cc....cc..",
    ".cc......cc.",
    ".ggg....ggg.",
]


# ------------------------------------------------------------------ BOSS DEI CAPITOLI 1-3 (15/11, TODO Z2)
# Stanno al posto del boss finale nel file del piano del boss del loro capitolo (GFX2, GFX4, GFX6: SETS 2, 3, 4).
# The Hollow Abbot (capitolo 1): scheletro incappucciato in una tonaca marcia, il turibolo appeso alla catena.
ABBOT = [
    "....cccc....",
    "...cccccc...",
    "..ccggggcc..",
    "..cggggggc..",
    "..cgbggbgc..",
    "..cggggggc..",
    "..ccgbbgcc..",
    ".ccccggcccc.",
    "cccccccccccb",
    "ccbccccccbcb",
    "cc.cccccc.gb",
    "gg.cccccc.gb",
    "...cccccc..b",
    "..cccccccc.b",
    "..ccbccbcc.g",
    "..cccccccc.g",
    ".cccccccccgg",
    ".ccbccccbcgg",
    ".cccccccccc.",
    ".cccccccccc.",
    "cccc.cc.cccc",
]
ABBOT_L1 = [
    ".cccccccccgg",
    ".ccbccccbcgg",
    "cccccccccccc",
    ".cccccccccc.",
    ".ccc.cc.ccc.",
]
# The Miller of Blackwater (capitolo 2): un mugnaio enorme, cappello, grembiule, la mazza con la macina.
MILLER = [
    "...bbbbbb...",
    "..bbbbbbbb..",
    "...cccccc...",
    "..cgccccgc..",
    "..cccccccc..",
    "..ccbbbbcc..",
    "...cccccc..g",
    ".bbbggggbbbg",
    "bbbggggggbbb",
    "cbbggggggbbc",
    "cc.gggggg.cc",
    "cc.gggggg.cb",
    "gg.gggggg.bb",
    "...gggggg.bg",
    "..bbbbbbbbgg",
    "..bbb..bbbgg",
    "..bbb..bbb..",
    "..bbb..bbb..",
    "..bbb..bbb..",
    "..bbb..bbb..",
    ".gggg..gggg.",
]
MILLER_L1 = [
    "..bbb..bbb..",
    ".bbb....bbb.",
    ".bbb....bbb.",
    "bbb......bbb",
    "gggg....gggg",
]
# Varok the Oathbreaker (capitolo 3): il comandante caduto, elmo con le corna, spadone, lo scudo con la croce.
VAROK = [
    "..g......g..",
    "..gg.cc.gg..",
    "...gccccg...",
    "...cccccc...",
    "...cbccbc...",
    "...cccccc...",
    "g...cccc....",
    "g.cccccccc..",
    "gccccccccbbb",
    "g.ccbccbbggb",
    "g.ccccccbgbb",
    "b.ccccccbbgb",
    "bbccbbccbggb",
    "..ccccccbbbb",
    "..cccccc.bb.",
    "..bbbbbb....",
    "..cc..cc....",
    "..cc..cc....",
    "..cc..cc....",
    "..cc..cc....",
    ".ggg..ggg...",
]
VAROK_L1 = [
    "..cc..cc....",
    ".cc....cc...",
    ".cc....cc...",
    "cc......cc..",
    "ggg....ggg..",
]


def frames(base, l1, extra=None):
    f0 = base if extra is None else overlay(base, extra + [""] * (21 - len(extra)))
    f1 = legs(f0, 21 - len(l1), l1)
    return [grid(f0), grid(f1)]


# (nome, frame0, frame1, colore)
BASE = [
    ("fallen", frames(FALLEN, FALLEN_L1), 10),
    ("skeleton", frames(SKELETON, SKELETON_L1), 1),
    ("zombie", frames(ZOMBIE, ZOMBIE_L1), 13),
    ("demon", frames(DEMON, DEMON_L1), 4),
]
STRONG = [
    ("warchief", frames(FALLEN, FALLEN_L1, WARCHIEF_X), 3),
    ("skeleton king", frames(SKELETON, SKELETON_L1, KING_X), 7),
    ("lich", frames(ZOMBIE, ZOMBIE_L1, LICH_X), 14),
    ("balrog", frames(DEMON, DEMON_L1, BALROG_X), 8),
]
FINAL = ("lord of ruin", frames(LORD, LORD_L1), 2)

# ------------------------------------------------------------------ set di mostri (07/11 sera)
# Un set = 4 famiglie base + 4 varianti forti (stessi mtype 1..8: stesse statistiche di data/balance.yaml, altra
# grafica) + il boss finale. Gli sprite dei mostri viaggiano nel file GFXn del tema (tools/build/gen_gfx.py, THEME_SET),
# quindi un secondo set costa solo spazio su disco (1152 B per file), non RAM. Oggi un solo set; i nomi dei tipi
# (src/game/bar.asm) sono ancora unici: un set con nomi diversi li deve portare nel file del tema (TODO.md).
# (15/11) set 2-4: stessi mostri, ma nel posto del boss finale c'e' il boss del capitolo 1, 2, 3 (file del piano del boss).
# CBOSS_COL = colore dello sprite di ogni boss di capitolo (cb_col in src/game/game.asm, colonna color del bestiario).
SETS = {1: (BASE, STRONG, FINAL),
        2: (BASE, STRONG, ("the hollow abbot", frames(ABBOT, ABBOT_L1), 14)),
        3: (BASE, STRONG, ("the miller of blackwater", frames(MILLER, MILLER_L1), 8)),
        4: (BASE, STRONG, ("varok the oathbreaker", frames(VAROK, VAROK_L1), 7))}
CBOSS_COL = [SETS[s][2][2] for s in (2, 3, 4)]

