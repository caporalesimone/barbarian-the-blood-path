"""Tile e legenda dei piani del boss dei capitoli 1-3 (19/11, richiesta del committente: ogni piano del boss ha tema e forma propri,
legati al capitolo; docs/wiki/dungeon.md "Piani del boss dei capitoli 1-3"). Li usano tools/build/gen_gfx.py (file del tema del
boss GFX(2c): tile del tema dei piani del capitolo + i tile di questo modulo) e tools/build/gen_bossmap.py (lettere delle mappe
data/maps/bosschapN.txt). Il boss finale (GFX8, sala del trono con la stella) resta com'e'.

Posti usati (tile 0..26 del file del tema, gli stessi in tutti i capitoli): solidi FREE9, FREE10, FREE11, FREE25, FREE26 (liberi
nei dungeon, solidi in solid_dun); calpestabili GRASSA, GRASSB, PATH (liberi nei dungeon, mai trattati dal codice fuori dalla sala
del trono e dalla palude). Mai FREE8 (portale nero: etichetta "the endless abyss"), DHOME (Fire = locanda), le porte dei negozi,
FOUNTAIN, PORTAL, TSTAIRS, CHEST: hanno un ruolo nel codice.

Base per capitolo (data/chapters.yaml): 1 = mattoni del dungeon (GFX1), 2 = palude (tools/build/swamp_gfx.py), 3 = grotte
(tools/build/cave_gfx.py). Palette del piano: chapters.yaml final.palette (8 grigia con le fiamme gialle, 12 palude, 10 roccia
grigia). Classi dei pixel multicolor: 0 sfondo (nero), 1 pal_c1, 2 pal_c2, 3 colore della RAM.
Generatore casuale proprio: gli altri file non cambiano."""
import random

W, H = 8, 16

# lettera della mappa -> nome del tile (oltre a '#' muro, '.' pavimento, '<' scale di arrivo, 'B' boss sul pavimento)
LEGEND = {
    1: {"S": "FREE9", "P": "FREE10", "C": "FREE11", "A": "FREE25", "N": "FREE26", "b": "GRASSA", "r": "GRASSB", "g": "PATH"},
    2: {"M": "FREE9", "O": "FREE10", "C": "FREE11", "R": "FREE25", "T": "FREE26", "h": "GRASSA", "k": "GRASSB", "=": "PATH"},
    3: {"R": "FREE9", "Q": "FREE10", "K": "FREE11", "X": "FREE25", "F": "FREE26", "g": "GRASSA", "c": "GRASSB"},
}
# nome per l'atlante (tools/atlas/atlas_names.py: chiave "<SET>:<tile>") e descrizione
NAMES = {
    1: {"FREE9": ("sarcophagus", "stone sarcophagus with a carved cross (solid)"),
        "FREE10": ("pillar", "round stone pillar seen from above (solid)"),
        "FREE11": ("candelabrum", "iron candelabrum with three flames (solid)"),
        "FREE25": ("altar", "stone altar with a cloth and a golden relic (solid; side by side the slabs join)"),
        "FREE26": ("bone pile", "heap of skulls and bones (solid)"),
        "GRASSA": ("scattered bones", "crypt floor with bones and a skull (walkable)"),
        "GRASSB": ("carpet", "processional carpet with a golden border, down the nave to the altar (walkable)"),
        "PATH": ("tomb slab", "engraved grave slab in the floor (walkable)")},
    2: {"FREE9": ("hut wall", "wattle wall of the dollmaker's hut (solid)"),
        "FREE10": ("totem", "carved totem with two faces (solid)"),
        "FREE11": ("cauldron", "black cauldron with a green brew (solid)"),
        "FREE25": ("reeds", "reeds and bulrushes in the water (solid)"),
        "FREE26": ("hanging tree", "dead tree hung with straw dolls (solid)"),
        "GRASSA": ("rotten boards", "rotten floorboards of the hut, with holes and moss (walkable)"),
        "GRASSB": ("stepping stone", "flat stone in the water: the ford (walkable)"),
        "PATH": ("boardwalk", "planks over the water (as in the swamp levels, walkable)")},
    3: {"FREE9": ("rubble", "pile of fallen rock (solid)"),
        "FREE10": ("boulder", "big fallen boulder (solid)"),
        "FREE11": ("stalagmite", "stalagmite seen from above (solid)"),
        "FREE25": ("timber prop", "wooden prop of the tunnel, some broken (solid)"),
        "FREE26": ("fallen masonry", "cut stones of the bastion fallen into the cave (solid)"),
        "GRASSA": ("scree", "loose gravel of the landslide (walkable)"),
        "GRASSB": ("cracked floor", "cave floor cracked by the collapse (walkable)")},
}
SET_CODE = {1: "BOSS1", 2: "BOSS2", 3: "BOSS3"}      # set dell'atlante (5 lettere)


def legend_text(c):
    """riga di legenda per l'intestazione della mappa"""
    base = "'#' %s, '.' pavimento, '<' scale di arrivo, 'B' boss (pavimento)" % {1: "muro", 2: "acqua (il muro della palude)", 3: "roccia"}[c]
    return base + ", " + ", ".join("'%s' %s" % (k, NAMES[c][v][0]) for k, v in LEGEND[c].items())


def _g(c=0):
    return [[c] * W for _ in range(H)]


def _put(g, pts, c):
    for x, y in pts:
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c


def _art(g, rows, y0=0, cmap=None):
    """disegna righe di testo: cifra = classe, '.' = lascia"""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                g[y0 + y][x] = int(ch) if cmap is None else cmap[ch]
    return g


def _noise(g, r, c, dens, only=None):
    for y in range(H):
        for x in range(W):
            if r.random() < dens and (only is None or g[y][x] in only):
                g[y][x] = c


# ---------------------------------------------------------------- capitolo 1: cripta (mattoni, palette 8)
def _crypt_floor(r):
    """come floor_base di gen_gfx (fughe della classe 1): i tile della cripta si posano sullo stesso pavimento"""
    g = _g(0)
    for x in range(W):
        g[0][x] = g[8][x] = 1
    for y in range(8):
        g[y][0] = 1
    for y in range(8, 16):
        g[y][4] = 1
    return g


def crypt(r):
    out = {}
    out["FREE9"] = _art(_crypt_floor(r), [            # sarcofago: coperchio di pietra con la croce incisa
        ".111111.",
        "12222221",
        "12222221",
        "12211221",
        "12211221",
        "12111121",
        "12111121",
        "12211221",
        "12211221",
        "12211221",
        "12222221",
        "12333321",
        "12222221",
        "11111111",
        ".0....0.",
    ], 1)
    out["FREE10"] = _art(_crypt_floor(r), [           # colonna in vista 3/4: capitello, fusto illuminato a sinistra, base
        "00000000",
        "02222220",
        "01111110",
        ".032210.",
        ".032210.",
        ".032210.",
        ".032210.",
        ".032210.",
        ".032210.",
        ".032210.",
        ".032210.",
        ".032210.",
        "00222200",
        "02222220",
        "01111110",
        "00000000",
    ])
    out["FREE11"] = _art(_crypt_floor(r), [           # candelabro a tre bracci, fiamme gialle grandi
        ".3..3..3",
        "333.3.33",
        "333333.3",
        ".3..3..3",
        ".2..2..2",
        ".2222222",
        "....2...",
        "....2...",
        "....2...",
        "....2...",
        "....2...",
        "...222..",
        "..22222.",
        "..00000.",
    ], 1)
    out["FREE25"] = _art(_g(0), [                      # altare: lastra continua, drappo, reliquia d'oro
        "22222222",
        "22222222",
        "11111111",
        "21111112",
        "21133112",
        "21333312",
        "21133112",
        "21111112",
        "21111112",
        "21111112",
        "22222222",
        "22222222",
        "11111111",
        "20202020",
        "02020202",
        "00000000",
    ])
    out["FREE26"] = _art(_crypt_floor(r), [           # mucchio di teschi e ossa
        "........",
        "...22...",
        "..2002..",
        "..2222..",
        ".222.22.",
        "2002.200",
        "22222222",
        "2.2222.2",
        "22002222",
        "22222002",
        "2.2.2222",
        "22222222",
        "12212221",
        ".111111.",
    ], 1)
    g = _crypt_floor(r)                               # ossa sparse e un teschio
    _art(g, [
        "........",
        ".22.....",
        "..22....",
        "...22...",
        "........",
        ".....22.",
        "....2002",
        "....2222",
        ".....22.",
        "........",
        ".2222...",
        "........",
    ], 2)
    out["GRASSA"] = g
    out["GRASSB"] = _art(_g(1), [                      # tappeto: bordo d'oro ai lati, trama scura (si unisce in verticale)
        "31111113",
        "31.11.13",
        "31111113",
        "311..113",
        "31111113",
        "31.11.13",
        "31111113",
        "311..113",
        "31111113",
        "31.11.13",
        "31111113",
        "311..113",
        "31111113",
        "31.11.13",
        "31111113",
        "311..113",
    ], cmap={"3": 3, "1": 1, ".": 0})
    out["PATH"] = _art(_g(0), [                        # lastra tombale incisa
        "11111111",
        "12222221",
        "12222221",
        "12211221",
        "12100121",
        "12211221",
        "12211221",
        "12222221",
        "12100121",
        "12222221",
        "12011021",
        "12222221",
        "12222221",
        "12222221",
        "12222221",
        "11111111",
    ])
    return out


# ---------------------------------------------------------------- capitolo 2: isola nella palude (palette 12)
def _water(r):
    """come l'acqua di swamp_gfx: nero e verde a scacchiera su righe alterne, qualche increspatura"""
    g = [[(2 if (y % 2 == 0 and (x + y // 2) % 2 == 0) else 0) for x in range(W)] for y in range(H)]
    for _ in range(2):
        x, y = r.randrange(0, W - 2), r.randrange(1, H - 1)
        g[y][x] = g[y][x + 1] = 2
    return g


def _mud(r):
    g = _g(1)
    for y in range(H):
        for x in range(W):
            v = r.random()
            if v < 0.18:
                g[y][x] = 2
            elif v < 0.28:
                g[y][x] = 0
    return g


def island(r):
    out = {}
    out["FREE9"] = _art(_g(1), [                       # (19/11) muro della capanna della bambolaia: graticcio di rami
        "00000000",
        "12121212",
        "21212121",
        "00000000",
        "12121212",
        "21212121",
        "00000000",
        "12121212",
        "21212121",
        "00000000",
        "12121212",
        "21212121",
        "00000000",
        "10100101",
        "00000000",
        "00000000",
    ])
    out["FREE10"] = _art(_mud(r), [                    # totem intagliato con due facce
        "00....00",
        "01000010",
        "01111110",
        "01211210",
        "01111110",
        "00100100",
        "01111110",
        ".011110.",
        "01111110",
        "01211210",
        "01111110",
        "00100100",
        "01111110",
        ".011110.",
        ".022220.",
        ".000000.",
    ])
    out["FREE11"] = _art(_mud(r), [                    # calderone nero con l'intruglio che bolle
        "..2.....",
        "...2.2..",
        "..2..2..",
        "...22...",
        ".222222.",
        "00000000",
        "02222220",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        ".000000.",
        "..0000..",
        ".0.22.0.",
        "0.2222.0",
    ])
    g = _water(r)                                      # canne e tife nell'acqua
    for x in (0, 2, 3, 5, 7):
        top = r.randrange(1, 6)
        for y in range(top, H - 1):
            g[y][x] = 2
        g[top][x] = g[top + 1][x] = 1 if x in (2, 5) else 2
    for x in range(W):
        g[H - 1][x] = 1 if r.random() < 0.6 else 0
    out["FREE25"] = g
    out["FREE26"] = _art(_mud(r), [                    # (19/11) albero degli impiccati: rami neri con le bambole appese
        "0..0..0.",
        "0..0.0..",
        ".0.0.0.0",
        ".0.000.0",
        "2.000.0.",
        "2..00.2.",
        "22.00.2.",
        "2..00222",
        "...00.2.",
        "...00...",
        "...00...",
        "...000..",
        "..0000..",
        ".000000.",
        "00.00.00",
    ])
    g = _g(1)                                          # assi marce della capanna: fughe, buchi, muschio
    for y in (3, 7, 11, 15):
        for x in range(W):
            g[y][x] = 0
    for (x, y) in ((2, 5), (3, 5), (2, 6), (5, 9), (6, 9), (5, 10)):
        g[y][x] = 0
    _noise(g, r, 2, 0.08, only=(1,))
    out["GRASSA"] = g
    out["GRASSB"] = _art(_water(r), [                  # pietra piatta nell'acqua (guado)
        "........",
        "........",
        "..1111..",
        ".111111.",
        "11122111",
        "11111111",
        "11111111",
        "11111211",
        "11111111",
        ".111111.",
        "..1111..",
        "..0000..",
    ], 2)
    return out


# ---------------------------------------------------------------- capitolo 3: grotta crollata (palette 10)
def _cave_floor(r):
    """come il pavimento di cave_gfx: terra scura con ghiaia"""
    g = _g(0)
    _noise(g, r, 1, 0.09)
    _noise(g, r, 2, 0.02, only=(0,))
    return g


def collapse(r):
    out = {}
    out["FREE9"] = _art(_cave_floor(r), [              # mucchio di macerie
        "........",
        "....22..",
        "...2112.",
        "..22110.",
        ".2112222",
        "21101121",
        "21122110",
        "11211122",
        "22110211",
        "21122211",
        "11210112",
        "12211221",
        "01111110",
    ], 2)
    out["FREE10"] = _art(_cave_floor(r), [             # masso: luce in alto a sinistra, ombra in basso
        "..2222..",
        ".222221.",
        "22222211",
        "22221111",
        "22211111",
        "22111111",
        "21111111",
        "21111110",
        "11111110",
        "11111100",
        ".111100.",
        "..1100..",
        "..0000..",
    ], 1)
    out["FREE11"] = _art(_cave_floor(r), [             # stalagmite vista dall'alto: anelli fino alla punta chiara
        "...11...",
        "..1111..",
        ".112211.",
        ".122221.",
        "11222211",
        "11222211",
        "11122111",
        "11111111",
        ".111111.",
        ".011110.",
        "..0000..",
    ], 3)
    out["FREE25"] = _art(_cave_floor(r), [             # puntello di legno spezzato: palo e trave caduta
        "11111111",
        "12222221",
        "11111111",
        "..1221..",
        "..1221..",
        "..1221..",
        "..1221..",
        "..1221..",
        "..1221..",
        "..1221..",
        "..1221..",
        ".11221..",
        "1112211.",
        "11111111",
    ], 1)
    out["FREE26"] = _art(_cave_floor(r), [             # conci del bastione caduti: blocchi squadrati, uno inclinato
        "........",
        "2222.222",
        "2221.212",
        "1111.111",
        "........",
        "22222222",
        "22222212",
        "21222212",
        "11111111",
        "........",
        ".2222.22",
        "22212.21",
        "11111.11",
    ], 1)
    g = _cave_floor(r)                                 # ghiaia della frana
    _noise(g, r, 2, 0.20, only=(0, 1))
    _noise(g, r, 1, 0.20, only=(0,))
    out["GRASSA"] = g
    g = _cave_floor(r)                                 # crepe nel pavimento
    for (x, y) in ((3, 0), (3, 1), (4, 2), (4, 3), (5, 3), (6, 4), (5, 5), (4, 6), (3, 7), (2, 8), (2, 9), (1, 10), (1, 11),
                   (0, 12), (6, 11), (5, 12), (4, 13), (3, 14), (4, 14), (3, 15)):
        g[y][x] = 3
    out["GRASSB"] = g
    return out


def tiles(c):
    """{nome del tile: griglia 8x16 di classi 0..3} dei tile propri del piano del boss del capitolo c (1..3)"""
    return {1: crypt, 2: island, 3: collapse}[c](random.Random(1911 + c))
