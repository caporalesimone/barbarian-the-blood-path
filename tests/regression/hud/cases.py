import os, sys
from lib.runner import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""HUD."""
script("HUD-XP-10", "XP line: thousands from 10000 (10K ... 65K)", [PY, os.path.join(H, "test_hudxp.py")])
