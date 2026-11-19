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
# Stanno al posto del boss finale nel file del piano del boss del loro capitolo (GFX2, GFX4, GFX6: CBOSS, chapter_set).
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
# Mother Stitch, the Dollmaker (capitolo 2, 19/11): la bambolaia della palude, cappello a tesa larga con le piume, viso
# pallido cucito, veste lunga con le toppe, l'ago enorme nella mano destra. Colore 4 (viola).
STITCH = [
    "...g.gg.g...",
    "..bbbbbbbb..",
    ".bbbbbbbbbb.",
    "...gggggg...",
    "..gbggggbg..",
    "...gggggg..g",
    "...gbgbgg..g",
    "..cccccccc.g",
    ".cccbccbccbg",
    "ccccccccccbg",
    "cc.cbccbc..g",
    "gc.cccccc..g",
    "b..ccbccc...",
    "bb.cccccc...",
    "b..cbccbc...",
    "..cccccccc..",
    "..ccbccccc..",
    ".cccccccbcc.",
    ".cccccccccc.",
    ".ccbccccccc.",
    "..bb....bb..",
]
STITCH_L1 = [                       # fotogramma 1: la gonna oscilla, un piede avanti
    "..cccbcccc..",
    ".ccbccccccc.",
    ".cccccccccc.",
    "..cccccbcc..",
    ".bb.....bb..",
]
# Il feticcio di Mother Stitch (19/11): bambola di paglia piantata su un palo, spilli in testa, il cuore cucito. Fermo, non
# attacca; nel file del piano del boss del capitolo 2 (GFX4) prende il posto del tipo 8 (FETISH_SLOT): li' i mostri normali
# non nascono mai (spawn_monsters esce subito nei piani del boss dei capitoli). Colore 8 (arancio, la paglia).
FETISH = [
    "............",
    "....g..g....",
    ".....gg.....",
    "...cccccc...",
    "..cccccccc..",
    "..cbbccbbc..",
    "..cccccccc..",
    "..cbcbcbcc..",
    "...cccccc...",
    "....bbbb....",
    "g..cccccc..g",
    ".gccccccccg.",
    "...cccccc...",
    "...ccggcc...",
    "...cccccc...",
    "...ccbbcc...",
    "....cccc....",
    ".....bb.....",
    ".....bb.....",
    "....bbbb....",
    "..bbbbbbbb..",
]
FETISH_X = [                        # fotogramma 1 (sovrapposto): gli spilli si muovono, il cuore pulsa
    "            ",
    "...g....g...",
    "....g..g....",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    ".g        g.",
    "..cccccccc..",
    "            ",
    "...cggggc...",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
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


# (nome nel gioco, [frame0, frame1], colore): il nome e' quello mostrato nella barra (id del bestiario con gli spazi)
BASE = [
    ("fallen", frames(FALLEN, FALLEN_L1), 10),
    ("skeleton", frames(SKELETON, SKELETON_L1), 1),
    ("zombie", frames(ZOMBIE, ZOMBIE_L1), 13),
    ("demon", frames(DEMON, DEMON_L1), 4),
]
STRONG = [
    ("fallen warchief", frames(FALLEN, FALLEN_L1, WARCHIEF_X), 3),
    ("skeleton king", frames(SKELETON, SKELETON_L1, KING_X), 7),
    ("lich", frames(ZOMBIE, ZOMBIE_L1, LICH_X), 14),
    ("balrog", frames(DEMON, DEMON_L1, BALROG_X), 8),
]
FINAL = ("lord of ruin", frames(LORD, LORD_L1), 2)
# boss dei capitoli 1-3 (15/11): nel posto del boss finale del file del piano del boss del loro capitolo
CBOSS = {1: ("the hollow abbot", frames(ABBOT, ABBOT_L1), 14),
         2: ("mother stitch", frames(STITCH, STITCH_L1), 4),
         3: ("varok the oathbreaker", frames(VAROK, VAROK_L1), 7)}

# ------------------------------------------------------------------ set di mostri per capitolo (07/11 sera, 15/11)
# Un set = 4 famiglie base + 4 varianti forti (stessi mtype 1..8: stesse statistiche di data/balance.yaml per profondita',
# altra grafica, altro nome, altro colore) + il posto del boss (tipo 9). Viaggia nel file GFXn del capitolo
# (tools/build/gen_gfx.py): sprite, colori e nomi (blocco "info" in coda al file, copiato da gfx_install a NM_AT).
# Capitolo 1: i mostri di sempre; capitoli 2-4: tools/build/monsters_chap.py (CHAPTER_MONSTERS, 15/11).
# Posto del boss: file del dungeon = Lord of Ruin (boss finale), file del piano del boss = boss del capitolo (1-3) o
# Lord of Ruin (capitolo 4, sala del trono).
CHAPTERS = 4


def chapter_monsters(c):
    """(base, strong) del capitolo c: 4 + 4 tuple (nome, [frame0, frame1], colore)"""
    if c == 1:
        return BASE, STRONG
    import monsters_chap as MC
    fam = MC.CHAPTER_MONSTERS[c]
    assert len(fam) == 4, "capitolo %d: servono 4 famiglie" % c
    base = [(n, frames(fig, l1), col) for (n, fig, l1, col, sn, x, scol) in fam]
    strong = [(sn, frames(fig, l1, x), scol) for (n, fig, l1, col, sn, x, scol) in fam]
    return base, strong


# (19/11) mostri evocati dal boss di un capitolo: nel file del piano del boss prendono il posto di un tipo forte (tipo 1..8),
# che li' non nasce mai. Capitolo -> (tipo, (nome, frame, colore)); tools/build/gen_gfx.py non li confronta con il bestiario.
SUMMONS = {2: (8, ("fetish", None, 8))}


def chapter_set(c, boss=False):
    """set del file del capitolo c: (base, strong, posto del boss); boss=True: file del piano del boss GFX(2c)"""
    base, strong = chapter_monsters(c)
    slot = CBOSS[c] if boss and c in CBOSS else FINAL
    if boss and c in SUMMONS:
        t, (n, _, col) = SUMMONS[c]
        assert 5 <= t <= 8, "il mostro evocato prende il posto di un tipo forte"
        strong = list(strong)
        strong[t - 5] = (n, [grid(FETISH), grid(overlay(FETISH, FETISH_X))], col)
    return base, strong, slot


def set_names(mset):
    """i 9 nomi del set (tipi 1..9) come li mostra la barra"""
    base, strong, slot = mset
    return [m[0] for m in base + strong + [slot]]


def set_colors(mset):
    base, strong, slot = mset
    return [m[2] for m in base + strong + [slot]]
