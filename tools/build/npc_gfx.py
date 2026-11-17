#!/usr/bin/env python3
"""Sprite degli NPC del villaggio (17/11, richiesta del committente: disegni diversi dall'eroe e colori che non si confondono
con il terreno). Quattro disegni visti di fronte, due fotogrammi l'uno (fermo / passo): 8 sprite multicolor 12x21 negli slot
12..19 ($A300-$A4FF), liberi nel villaggio (li' nel dungeon stanno i mostri del tema, ricopiati a ogni ingresso). Si caricano
con il modulo MENU (zona 4, src/menu.asm). Valori dei pixel come l'eroe: 1 = marrone (multicolor 0, colore 9), 2 = colore
dello sprite (vestito: quello dell'NPC, scelto diverso dai colori del villaggio), 3 = grigio chiaro (multicolor 1, colore 15).
Il vestito usa il 2, cosi' l'NPC resta visibile anche su un terreno marrone o grigio.
Puntatore = $8C + 2 x disegno + fotogramma (npc_draw, src/game/quest.asm)."""

# righe 0..20; i fotogrammi del passo cambiano solo le righe da WALK_FROM in giu'
WALK_FROM = 15

VILLAGER = [
    "............",
    "....1111....",
    "...111111...",
    "...133331...",
    "...133331...",
    "...133331...",
    "....3333....",
    ".....33.....",
    "...222222...",
    "..22222222..",
    "..32222223..",
    "..32222223..",
    "..32222223..",
    "...222222...",
    "...111111...",
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

WOMAN = [
    "....1111....",
    "...111111...",
    "..11333311..",
    "..11333311..",
    "..11333311..",
    "..11333311..",
    "..11.33.11..",
    "...1.33.1...",
    "...222222...",
    "..22222222..",
    "..32222223..",
    "..32222223..",
    "...222222...",
    "...222222...",
    "..22222222..",
    "..22222222..",
    ".2222222222.",
    ".2222222222.",
    ".2222222222.",
    "...11..11...",
    "............",
]
WOMAN_W = [
    "..22222222..",
    ".2222222222.",
    "..222222222.",
    "..222222222.",
    "....11.11...",
    "............",
]

ELDER = [
    "....2222....",
    "...222222...",
    "..22333322..",
    "..22313122.1",
    "..22333322.1",
    "..22333322.1",
    "...233332..1",
    "...233332..1",
    "..2223322231",
    ".222222222.1",
    ".222222222.1",
    ".322222222.1",
    "..22222222.1",
    "..22222222.1",
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

GUARD = [
    "....3333..3.",
    "...333333.3.",
    "...333333.1.",
    "...133331.1.",
    "...333333.1.",
    "...333333.1.",
    "....3333..1.",
    ".....33...1.",
    "..22222222.1",
    ".2222222222.",
    ".32223322231",
    ".3222222222.",
    ".3222222223.",
    "..22222222..",
    "..11111111..",
    "...22..22...",
    "...22..22...",
    "...33..33...",
    "...33..33...",
    "...11..11...",
    "..111..111..",
]
GUARD_W = [
    "....22.22...",
    "....22.22...",
    "....33..33..",
    "...33...33..",
    "...11...11..",
    "..111...111.",
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
