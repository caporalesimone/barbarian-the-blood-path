import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Balance: rules simulator (fast) and arena on the real code."""
script("BAL-10", "d20 rules in the simulator: reference hero, weak hero, curves", [PY, os.path.join(H, "test_balance.py")])
script("ARENA-10", "arena: short repeatable series, sensible results", [PY, os.path.join(H, "test_arena.py")])
