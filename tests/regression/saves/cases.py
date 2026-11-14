import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Saves (Krill, 11/11): files hl and save-01..05 (cases 1-8 of test_saves.py, one VICE session per case) and the level states."""
for tid, n, d in [("SAVE-10", 1, "new disk: menu without error, no heroes"),
                  ("SAVE-11", 2, "hl (hero list) missing: menu without error, the game starts"),
                  ("SAVE-12", 3, "hero list zeroed / random / never written: no error, no heroes"),
                  ("SAVE-13", 4, "list from another version: offer to delete"),
                  ("SAVE-14", 5, "cycles new game -> level -> quit -> continue: the hero stays"),
                  ("SAVE-15", 6, "quit the game -> BASIC (READY.), no re-entry; Krill uninstalled: KERNAL LOAD from the disk works again"),
                  ("SAVE-16", 7, "details screen: delete the barbarian (cancel, confirm, new session)"),
                  ("PG-NEW-10", 8, "new barbarian through the UI: name, seed, joystick, F1, DEL")]:
    script(tid, d, [PY, os.path.join(H, "test_saves.py"), str(n)])
script("SAVE-REL-10", "saved level state (REL): monsters, chests, fog, return, repopulation", [PY, os.path.join(H, "test_rel.py")])
