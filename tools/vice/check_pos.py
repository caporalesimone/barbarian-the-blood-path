#!/usr/bin/env python3
"""Controlla che una posizione del PG nel villaggio sia valida (casella percorribile di data/town_map.txt):
lo usa tools/vice/shots_manual.sh prima di ogni screenshot del villaggio (regola: negli screenshot il PG sta solo in
posizioni valide; 06/11: il PG era finito in mezzo al torrente). Uso: check_pos.py X Y  (exit 1 se non valida)"""
import os, sys
HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build")   # tools/build/
sys.path.insert(0, HERE)
import gen_gfx as G          # noqa: E402
import gen_maps as M         # noqa: E402
x, y = int(sys.argv[1]), int(sys.argv[2])
rows = [l.rstrip("\n") for l in open(os.path.join(HERE, "..", "..", "data", "town_map.txt")) if not l.startswith(";")]
inv = M.inv_legend()
name = inv[rows[y][x]]
if name in G.SOLID:
    sys.exit("posizione del PG non valida nel villaggio: (%d,%d) = %s (solido)" % (x, y, name))
print("posizione (%d,%d) = %s: ok" % (x, y, name))
