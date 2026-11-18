import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Level generator (reference maps with a fixed seed: a change must be intended, --update)."""
script("GEN-10", "reference maps, throne room from FMAP and from the cache", [PY, os.path.join(H, "test_gen.py")])
script("GEN-11", "caves of chapter 3 (levels 11-14, 6 seeds): connected, border of wall, enough floor, generation under 1.2 s, palettes 9/11/10",
       [PY, os.path.join(H, "test_caves.py")])
script("GEN-12", "swamp of chapter 2 (levels 6-9, 8 seeds + 2 anagram seeds with different gates): entry and exit gates on two sides of the border, the exit of a level facing the entry of the next one (random path, at least 3 sides used), gates of a level at least 34 tiles apart, all reachable, generation under 1.2 s, palette 12",
       [PY, os.path.join(H, "test_swamp.py")])
script("GEN-13", "citadel of chapter 4 (levels 16-19, 6 seeds): connected, symmetric left/right (but the stairs), columns, big halls, generation under 1.0 s; no monster born in a wall or in the water on levels 1-19",
       [PY, os.path.join(H, "test_citadel.py")])
