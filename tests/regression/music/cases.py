import os, sys
from lib.runner import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""In-game music."""
script("MUSIC-10", "songs per level, buffer = SNDn files, combat and resume, copy under I/O", [PY, os.path.join(H, "test_music.py")])
