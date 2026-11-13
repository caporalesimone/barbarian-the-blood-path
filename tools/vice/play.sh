#!/bin/bash
# VICE dal vivo CON IL SUONO sullo schermo del viewer (13/11): ultima build (o il disco indicato), velocita' reale, audio PulseAudio.
# Dall'host:  toolchain/viewer.sh exec tools/vice/play.sh [disco.d64]      poi http://localhost:6080 -> "Schermo dal vivo" -> Audio
# Tastiera dal browser (KasmVNC); il joystick e' quello di VICE sui tasti (Preferences di VICE). Si chiude con la finestra di VICE.
source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
cd "$ROOT"
D=${1:-$(ls out/blood_path_v*_1541.d64 2>/dev/null | sort -V | tail -1)}
[ -f "$D" ] || { echo "play.sh: nessun disco (./build.sh prima)"; exit 1; }
[ -n "${PULSE_SERVER:-}" ] || echo "play.sh: PULSE_SERVER non impostato: niente suono (usare toolchain/viewer.sh exec)"
exec x64sc $VROM -sounddev pulse -autostart "$D"
