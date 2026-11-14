"""Opzioni di x64sc comuni (13/11): dal 14/11 stanno nella libreria VICE di Lab64 (../lab64/py/vicemon.py, in inglese).
Questo file resta per gli strumenti del gioco che le importano (tools/build/gen_help.py, tools/build/gen_music.py):
ROM_ARGS (impostazioni di fabbrica e TUTTE le ROM di Lab64 roms/), XRUN (display), wait_boot (attesa del C64 pronto)."""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # ricavata dalla posizione del file
os.environ.setdefault("C64_ROOT", ROOT)
LAB64 = os.environ.get("LAB64") or os.path.normpath(os.path.join(ROOT, "..", "lab64"))   # nei container /lab64 (run.sh)
sys.path.insert(0, os.path.join(LAB64, "py"))
from vicemon import ROM_ARGS, ROMS_ALL as ROMS, ROMS_C64, ROMS_DRIVES, XRUN, wait_boot  # noqa: E402,F401
