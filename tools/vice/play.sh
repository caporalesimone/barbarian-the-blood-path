#!/bin/bash
# VICE dal vivo CON IL SUONO sullo schermo del viewer (13/11): ultima build (o il disco indicato: file .d64 oppure versione, es. 1.238), velocita' reale, audio PulseAudio.
# Dall'host:  ../lab64/viewer.sh exec tools/vice/play.sh [disco.d64|versione]      poi http://localhost:6080 -> "Schermo dal vivo" -> Audio
# Tastiera del browser (KasmVNC) e overlay di /live.html (pulsanti Tastiera, Joy 1, Joy 2: arrivano a VICE come tasti, vedi docs/getting-started.md).
# Joystick 2 = porta 2 = quello del gioco: tastierino numerico di VICE (8 su, 2 giu', 4 sinistra, 6 destra, 7 9 1 3 diagonali, 0 fire).
# Joystick 1 = porta 1: keyset 1 di VICE su F13-F17 (tools/vice/play.vicerc, caricato con -addconfig; -config non lo legge).
# (14/11) --bare: VICE senza disco (READY. del BASIC), per le prove a mano; i dischi si montano dal menu di VICE (File).
# Accetta anche .prg, .t64, .crt, .g64 (autostart). Lo usa il lettore del viewer (../lab64/viewer_player.py, C64_VIEW_PLAYER).
# Chi usa la tastiera fisica senza tastierino gioca con W A S D e spazio/RETURN (il gioco li accetta). Si chiude con la finestra di VICE.
source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
cd "$ROOT"
# (14/11) i dischi stanno in out/releases/v<versione>/ (tools/build/publish.py); senza argomento: out/releases/latest
case "${1:-}" in
    --bare) D="" ;;
    "")   D=out/releases/latest/$(ls out/releases/latest 2>/dev/null | grep '_1541\.d64$' | head -1) ;;
    *.d64|*.g64|*.prg|*.t64|*.crt) D=$1 ;;
    *)    D=out/releases/v${1#v}/blood_path_v${1#v}_1541.d64 ;;
esac
[ "${1:-}" = --bare ] || [ -f "$D" ] || { echo "play.sh: nessun disco (./build.sh prima)"; exit 1; }
[ -n "${PULSE_SERVER:-}" ] || echo "play.sh: PULSE_SERVER non impostato: niente suono (usare ../lab64/viewer.sh exec)"
exec x64sc $VROM -addconfig tools/vice/play.vicerc -sounddev pulse -controlport1device 1 -controlport2device 1 -keyset -joydev1 2 -joydev2 1 ${D:+-autostart "$D"}
