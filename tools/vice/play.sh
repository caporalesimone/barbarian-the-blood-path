#!/bin/bash
# VICE dal vivo CON IL SUONO sullo schermo del viewer (13/11): ultima build (o il disco indicato), velocita' reale, audio PulseAudio.
# Dall'host:  toolchain/viewer.sh exec tools/vice/play.sh [disco.d64]      poi http://localhost:6080 -> "Schermo dal vivo" -> Audio
# Tastiera del browser (KasmVNC) e overlay di /live.html (pulsanti Tastiera, Joy 1, Joy 2: arrivano a VICE come tasti, vedi docs/getting-started.md).
# Joystick 2 = porta 2 = quello del gioco: tastierino numerico di VICE (8 su, 2 giu', 4 sinistra, 6 destra, 7 9 1 3 diagonali, 0 fire).
# Joystick 1 = porta 1: keyset 1 di VICE su F13-F17 (tools/vice/play.vicerc, caricato con -addconfig; -config non lo legge).
# Chi usa la tastiera fisica senza tastierino gioca con W A S D e spazio/RETURN (il gioco li accetta). Si chiude con la finestra di VICE.
source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
cd "$ROOT"
D=${1:-$(ls out/blood_path_v*_1541.d64 2>/dev/null | sort -V | tail -1)}
[ -f "$D" ] || { echo "play.sh: nessun disco (./build.sh prima)"; exit 1; }
[ -n "${PULSE_SERVER:-}" ] || echo "play.sh: PULSE_SERVER non impostato: niente suono (usare toolchain/viewer.sh exec)"
exec x64sc $VROM -addconfig tools/vice/play.vicerc -sounddev pulse -controlport1device 1 -controlport2device 1 -keyset -joydev1 2 -joydev2 1 -autostart "$D"
