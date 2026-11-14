import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Level generator (reference maps with a fixed seed: a change must be intended, --update)."""
script("GEN-10", "reference maps, throne room from FMAP and from the cache", [PY, os.path.join(H, "test_gen.py")])
