import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Monsters: chasing along walls, hero on corners."""
script("MON-AI-10", "awake monster reaches the hero along the wall (ANOANO level 2); hero on corners", [PY, os.path.join(H, "test_ai.py")])
script("MON-AI-11", "short path (mon_path): monsters that stayed in a corner or shook on a wall edge reach the hero (3 cases, ANOANO)", [PY, os.path.join(H, "test_path.py")])
