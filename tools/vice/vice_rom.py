"""Opzioni di x64sc comuni (13/11, regola del committente: niente percorsi del sistema, tutto relativo al progetto).
ROM_ARGS: impostazioni di fabbrica (-default: non conta la configurazione dell'utente) e TUTTE le ROM da <progetto>/toolchain/roms/vice-roms
(Kernal, Basic, chargen e quelle dei drive 1541, 1541-II, 1570, 1571): VICE non cerca nulla nella sua cartella dati ne' in
/usr/share/vice. VICE (x64sc) e' quello del container c64-emu-vice (/opt/vice/bin, nel PATH). Lo usano tests/lib/c64.py, tools/build/gen_help.py, tools/build/gen_music.py; la copia per gli script shell e'
tools/vice/vice_env.sh (tenerle uguali)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # ricavata dalla posizione del file
ROMS = os.path.join(ROOT, "toolchain", "roms", "vice-roms")          # (13/11) sottocartelle come VICE: C64/ e DRIVES/ (toolchain/roms/roms.md)
ROMS_C64 = os.path.join(ROMS, "C64")
ROMS_DRIVES = os.path.join(ROMS, "DRIVES")
ROM_ARGS = ["-default",
            "-kernal", ROMS_C64 + "/kernal-901227-03.bin", "-basic", ROMS_C64 + "/basic-901226-01.bin",
            "-chargen", ROMS_C64 + "/chargen-901225-01.bin",
            "-dos1541", ROMS_DRIVES + "/dos1541-325302-01+901229-05.bin", "-dos1541II", ROMS_DRIVES + "/dos1541ii-251968-03.bin",
            "-dos1570", ROMS_DRIVES + "/dos1570-315090-01.bin", "-dos1571", ROMS_DRIVES + "/dos1571-310654-05.bin"]

# Display (13/11): di norma ogni VICE ha il suo display virtuale (xvfb-run); con C64_VIEW=1 (./build.sh --view, container
# c64-emu-viewer) VICE si apre sullo schermo condiviso DISPLAY, che il viewer mostra nel browser (noVNC).
XRUN = [] if os.environ.get("C64_VIEW") == "1" and os.environ.get("DISPLAY") else ["xvfb-run", "-a"]
