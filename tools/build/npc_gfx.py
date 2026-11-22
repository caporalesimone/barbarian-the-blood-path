#!/usr/bin/env python3
"""Sprite degli NPC del villaggio (17/11, richiesta del committente: disegni diversi dall'eroe e colori che non si confondono
con il terreno). Quattro disegni visti di fronte, due fotogrammi l'uno (fermo / passo): 8 sprite multicolor 12x21 negli slot
12..19 ($A300-$A4FF), liberi nel villaggio (li' nel dungeon stanno i mostri del tema, ricopiati a ogni ingresso). Si caricano
con il modulo MENU (zona 4, src/menu.asm). Valori dei pixel come l'eroe: 1 = marrone (multicolor 0, colore 9), 2 = colore
dello sprite (vestito: quello dell'NPC, scelto diverso dai colori del villaggio), 3 = grigio chiaro (multicolor 1, colore 15).
Il vestito usa il 2, cosi' l'NPC resta visibile anche su un terreno marrone o grigio.
Puntatore = $8C + 2 x disegno + fotogramma (npc_draw, src/menu/npc.asm).
(18/11, committente) BANG: il "!" sopra la testa di chi ha una quest da dare, sprite in alta risoluzione (un colore) a $8C00
(puntatore $30, inizio della zona 5 del modulo MENU), disegnato a pixel doppi come gli NPC (12 colonne, X = acceso)."""

# righe 0..20; i fotogrammi del passo cambiano solo le righe da WALK_FROM in giu'
WALK_FROM = 15

# (22/11, committente: "semplici ma ben riconoscibili", colori che non si confondono con lo sfondo) i due multicolor degli
# sprite sono quelli dell'eroe e dei mostri (9 marrone, 15 grigio chiaro) e nei villaggi il terreno e' spesso marrone o
# grigio: la sagoma la fa quindi il colore del vestito (2), che incornicia anche la testa (cappello, fazzoletto, cappuccio,
# elmo); il viso e' grigio con gli occhi marroni. Prima capelli marroni ed elmo grigio sparivano sul terreno.
VILLAGER = [                   # contadino: cappello a tesa larga, tunica, cintura
    "............",
    "...222222...",
    ".2222222222.",
    "...333333...",
    "...313313...",
    "...333333...",
    "....3333....",
    "....2222....",
    "..22222222..",
    ".2222222222.",
    ".3222222223.",
    ".3222222223.",
    "..22222222..",
    "..11111111..",
    "..22222222..",
    "...22..22...",
    "...22..22...",
    "...22..22...",
    "...22..22...",
    "...11..11...",
    "..111..111..",
]
VILLAGER_W = [
    "....22.22...",
    "....22.22...",
    "....22..22..",
    "...22...22..",
    "...11...11..",
    "..111...111.",
]

WOMAN = [                      # donna: fazzoletto in testa, veste lunga con il grembiule grigio
    "....2222....",
    "...222222...",
    "..22333322..",
    "..23133132..",
    "..22333322..",
    "..22333322..",
    "...223322...",
    "....2222....",
    "...222222...",
    "..22222222..",
    ".3223333223.",
    ".3223333223.",
    "..22333322..",
    "..22333322..",
    ".2223333222.",
    ".2223333222.",
    ".2222332222.",
    ".2222222222.",
    ".2222222222.",
    "...11..11...",
    "............",
]
WOMAN_W = [
    "..222333322.",
    "..222233222.",
    "..222222222.",
    "..222222222.",
    "....11.11...",
    "............",
]

ELDER = [                      # anziano o religioso: cappuccio, barba grigia, veste fino ai piedi, bastone
    "....2222...3",
    "...222222..3",
    "..22333322.1",
    "..22313122.1",
    "..22333322.1",
    "..22333322.1",
    "...233332..1",
    "...233332..1",
    "..2223322231",
    ".222232222.1",
    ".222222222.1",
    ".322222222.1",
    "..22222222.1",
    "..22111122.1",
    "..22222222.1",
    "..22222222.1",
    "..22222222.1",
    "..22222222.1",
    "..22222222.1",
    "...11..11..1",
    "...........1",
]
ELDER_W = [
    "..22222222.1",
    "..22222222.1",
    "..22222222.1",
    "..22222222.1",
    "....11.11..1",
    "...........1",
]

GUARD = [                      # armato: elmo con i paraguance, scudo tondo grigio, lancia, schinieri
    "....2222...3",
    "...222222..3",
    "..22222222.1",
    "..23333332.1",
    "..23133132.1",
    "...333333..1",
    "....3333...1",
    "...222222..1",
    "..22222222.1",
    ".33222222231",
    "3333222222.1",
    "3333222222.1",
    ".33222222..1",
    "..11111111.1",
    "..22222222.1",
    "...33..33..1",
    "...33..33..1",
    "...33..33..1",
    "...33..33..1",
    "...11..11..1",
    "..111..111.1",
]
GUARD_W = [
    "....33.33..1",
    "....33.33..1",
    "....33..33.1",
    "...33...33.1",
    "...11...11.1",
    "..111...1111",
]

DESIGNS = [("villager", VILLAGER, VILLAGER_W), ("woman", WOMAN, WOMAN_W), ("elder", ELDER, ELDER_W), ("guard", GUARD, GUARD_W)]
HILDE = 1                      # disegno di chi da' la quest (npc_init)


def grid(rows):
    assert len(rows) == 21 and all(len(r) == 12 and set(r) <= set(".123") for r in rows), rows
    return [[0 if c == "." else int(c) for c in r] for r in rows]


def mc_bytes(g):
    out = []
    for y in range(21):
        for bx in range(3):
            v = 0
            for p in range(4):
                v = (v << 2) | g[y][bx * 4 + p]
            out.append(v)
    return out + [0]


def npc_sprites():
    """[(nome, fotogramma, 64 byte)] nell'ordine degli slot 12..19"""
    out = []
    for name, base, walk in DESIGNS:
        assert len(walk) == 21 - WALK_FROM, name
        out.append((name, 0, bytes(mc_bytes(grid(base)))))
        out.append((name, 1, bytes(mc_bytes(grid(base[:WALK_FROM] + walk)))))
    assert len(out) == 8
    return out


BANG = [
    "....XXXX....",
    "...XXXXXX...",
    "...XXXXXX...",
    "...XXXXXX...",
    "...XXXXXX...",
    "....XXXX....",
    "....XXXX....",
    "....XXXX....",
    ".....XX.....",
    ".....XX.....",
    "............",
    "....XXXX....",
    "....XXXX....",
    "....XXXX....",
] + ["............"] * 7
BANG_ROWS = 14                 # righe disegnate (npc_draw lo mette 18 righe sopra la testa dell'NPC)


def bang_sprite():
    """64 byte: sprite in alta risoluzione, ogni colonna di BANG = 2 pixel"""
    assert len(BANG) == 21 and all(len(r) == 12 and set(r) <= set(".X") for r in BANG)
    out = []
    for r in BANG:
        bits = "".join("11" if c == "X" else "00" for c in r)
        out += [int(bits[i:i + 8], 2) for i in (0, 8, 16)]
    return bytes(out + [0])
