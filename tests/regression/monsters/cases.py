import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Monsters: chasing along walls, hero on corners."""
script("MON-AI-10", "awake monster reaches the hero along the wall (ANOANO level 2); hero on corners", [PY, os.path.join(H, "test_ai.py")])
