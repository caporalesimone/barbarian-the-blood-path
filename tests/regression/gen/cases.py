import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Level generator (reference maps with a fixed seed: a change must be intended, --update)."""
script("GEN-10", "reference maps, throne room from FMAP and from the cache", [PY, os.path.join(H, "test_gen.py")])
script("GEN-11", "caves of chapter 3 (levels 11-14, 6 seeds): connected, border of wall, enough floor, generation under 1.2 s, palettes 9/11/10",
       [PY, os.path.join(H, "test_caves.py")])
script("GEN-12", "swamp of chapter 2 (levels 6-9, 5 seeds): gates on the west and east borders, the east gate of a level on the row of the west gate of the next one, all reachable, generation under 1.2 s, palette 12",
       [PY, os.path.join(H, "test_swamp.py")])
