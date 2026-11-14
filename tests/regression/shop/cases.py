import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Shops (besides the sanity/gold cases): potion belt slot choice at the alchemist."""
script("SHOP-SLOT-10", "potion: belt slot choice (W/S wrap, RUN/STOP cancels, fire pays)", [PY, os.path.join(H, "test_slot.py")])
