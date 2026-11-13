import os, sys
from lib.runner import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Items (arena build): generation, breaking, repair, HUD warnings, clock; belt and scrolls."""
script("ITEM-10", "255 generated items, broken weapon, HUD warnings, TOD clock (repair: SHOP-FIX-10)", [PY, os.path.join(H, "test_items.py")])
script("BELT-10", "belt (4 potions, the fifth refused), scroll stack, portal", [PY, os.path.join(H, "test_belt.py")])
