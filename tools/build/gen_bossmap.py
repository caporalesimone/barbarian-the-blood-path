#!/usr/bin/env python3
"""Mappe dei piani del boss dei capitoli (12/11, TODO M1, docs/wiki/capitoli.md): data/maps/bosschapN.txt -> out/work/bosschN.prg
(file BOSSCHN sul disco, N = capitolo 1..CHAPTERS-1; il capitolo CHAPTERS ha la sala del trono, FMAP).
Testo 48x48, una lettera per casella: '#' muro, '.' pavimento, '<' scale di arrivo, 'B' posto del boss (pavimento).
File: indirizzo di caricamento FIN_AT (come FMAP: stesso buffer sotto il KERNAL), 4 byte di intestazione (scale x, y;
boss x, y) e la mappa in RLE come FMAP (tools/build/gen_final.py rle). Il gioco la scompatta in MAP (src/game/disk.asm,
bmap_load) e la completa come la sala del trono (gen_cboss in src/game/gen_io.asm: post_walls).
Oggi i file sono segnaposto quadrati (richiesta del committente: "un livello banale, solo place holder")."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_final as F
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
W = H = 48
LEG = {"#": "WALL", ".": "FLOOR", "<": "STAIRSU", "B": "FLOOR"}
import gen_gfx as G
CHAPTERS = G.CHAPTERS


def build(n):
    src = os.path.join(ROOT, "data", "maps", "bosschap%d.txt" % n)
    rows = [l.rstrip("\n") for l in open(src) if not l.startswith(";")]
    assert len(rows) == H and all(len(r) == W for r in rows), "%s: servono %d righe da %d caratteri" % (src, H, W)
    T = F.tile_ids()
    find = lambda c: [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == c]
    st, bo = find("<"), find("B")
    assert len(st) == 1 and len(bo) == 1, "%s: una casella '<' e una 'B'" % src
    for r in rows:
        assert set(r) <= set(LEG), "%s: lettere ammesse %s" % (src, "".join(LEG))
    for y in (0, H - 1):
        assert set(rows[y]) == {"#"}, "%s: il bordo deve essere muro" % src
    m = bytes(T[LEG[c]] for r in rows for c in r)
    rl = F.rle(m)
    data = bytes([st[0][0], st[0][1], bo[0][0], bo[0][1]]) + rl
    assert F.FIN_AT + len(data) <= F.FIN_END, "mappa del boss troppo grande per il buffer di FMAP"
    out = os.path.join(ROOT, "out", "work", "bossch%d.prg" % n)
    open(out, "wb").write(bytes([F.FIN_AT & 255, F.FIN_AT >> 8]) + data)
    return out, len(data)


def placeholder(n):
    """segnaposto quadrato: sala 16 x 16 al centro, corridoio da sud, scale in basso, boss al centro"""
    g = [["#"] * W for _ in range(H)]
    for y in range(14, 30):
        for x in range(16, 32):
            g[y][x] = "."
    for y in range(30, 41):
        for x in (23, 24, 25):
            g[y][x] = "."
    g[40][24] = "<"
    g[21][24] = "B"
    hdr = ("; Mappa del piano del boss del capitolo %d (tools/build/gen_bossmap.py): SEGNAPOSTO quadrato (12/11, TODO M1).\n"
           "; '#' muro, '.' pavimento, '<' scale di arrivo, 'B' boss. Da ridisegnare.\n") % n
    open(os.path.join(ROOT, "data", "maps", "bosschap%d.txt" % n), "w").write(hdr + "\n".join("".join(r) for r in g) + "\n")


if __name__ == "__main__":
    if "--placeholders" in sys.argv:
        for n in range(1, CHAPTERS):
            placeholder(n)
    for n in range(1, CHAPTERS):
        print("%s %d B" % build(n))
