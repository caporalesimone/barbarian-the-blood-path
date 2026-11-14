#!/bin/sh
# Viewer (13/11): schermo condiviso CON AUDIO da guardare nel browser. Copyright (c) 2026 - Simone Caporale
#   toolchain/viewer.sh start | stop
#   toolchain/viewer.sh exec <comando>     comando nel container c64-emu-vice collegato allo schermo e all'audio del viewer
#                                          (es. toolchain/viewer.sh exec tools/vice/play.sh: VICE dal vivo con il suono)
# http://localhost:6080 (solo localhost, una sola porta): indice, schermo dal vivo con audio (/live.html, KasmVNC), ultima build in
# vc64web nel browser, cartella out/ del progetto in sola lettura. In /live.html anche l'overlay con tastiera C64, Joy 1 e Joy 2
# (i tasti passano da /input, vedi server.js).
# Variabili: VIEW_PORT (6080), VIEW_PASSWORD (password di TUTTO il viewer, di default nessuna), VIEW_SIZE (1280x1000),
#   VIEW_HOSTS (nomi di host ammessi oltre a localhost, 127.0.0.1, [::1], separati da virgole: es. dietro un tunnel),
#   C64_VIEW_DISK (toolchain.env: disco proposto per primo nell'indice), C64_VIEW_TITLE (toolchain.env: nome del progetto nella pagina),
#   C64_VIEW_PLAYER (toolchain.env: comando che avvia VICE su un .d64; se c'e', start avvia anche il container c64-emu-player con
#   toolchain/viewer_player.py, e i pulsanti "VICE" della pagina indice aprono quel disco sullo schermo dal vivo).
# Il viewer non ha il socket di Docker (sarebbe root sull'host): parla con c64-emu-player da un socket Unix nel volume c64-x11.
# Gli altri container usano schermo e audio montando il volume c64-x11: DISPLAY=:99, PULSE_SERVER=unix:/tmp/.X11-unix/pulse
# (./build.sh --view lo fa da solo; i test girano con -sounddev dummy, quindi senza suono).
set -eu
TC=$(cd "$(dirname "$0")" && pwd)
ROOT=${C64_PROJECT:-$(dirname "$TC")}
[ -f "$ROOT/toolchain.env" ] && . "$ROOT/toolchain.env"
start() {
    "$TC/images.sh" emu-viewer
    if [ -z "$(docker ps -q -f name=^c64-emu-viewer$)" ]; then
        docker rm -f c64-emu-viewer >/dev/null 2>&1 || true
        mkdir -p "$ROOT/out"
        docker run -d --rm --name c64-emu-viewer -p "127.0.0.1:${VIEW_PORT:-6080}:6080" -v c64-x11:/tmp/.X11-unix \
            -v "$ROOT/out":/srv/out:ro -e VIEW_PASSWORD="${VIEW_PASSWORD:-}" -e VIEW_HOSTS="${VIEW_HOSTS:-}" -e VIEW_SIZE="${VIEW_SIZE:-1280x1000}" \
            -e VIEW_DISK="${C64_VIEW_DISK:-}" -e VIEW_TITLE="${C64_VIEW_TITLE:-}" -e VIEW_PLAYER="${C64_VIEW_PLAYER:-}" c64-emu-viewer >/dev/null
        for i in $(seq 100); do docker exec c64-emu-viewer test -S /tmp/.X11-unix/pulse 2>/dev/null && break; sleep 0.2; done
    fi
    if [ -n "${C64_VIEW_PLAYER:-}" ] && [ -z "$(docker ps -q -f name=^c64-emu-player$)" ]; then
        docker rm -f c64-emu-player >/dev/null 2>&1 || true
        export C64_VIEW_PLAYER
        C64_VIEW=1 DISPLAY=:99 PULSE_SERVER=unix:/tmp/.X11-unix/pulse \
            C64_DOCKER_ARGS="-d --name c64-emu-player -e C64_VIEW_PLAYER -v c64-x11:/tmp/.X11-unix" \
            "$TC/run.sh" emu-vice python3 toolchain/viewer_player.py >/dev/null </dev/null
    fi
    echo "viewer: http://localhost:${VIEW_PORT:-6080}"
}
case "${1:-}" in
start) start ;;
stop) docker rm -f c64-emu-player c64-emu-viewer >/dev/null 2>&1 || true; echo "viewer fermato" ;;
exec)
    shift; [ $# -ge 1 ] || { sed -n 4,5p "$0"; exit 1; }
    start
    C64_VIEW=1 DISPLAY=:99 PULSE_SERVER=unix:/tmp/.X11-unix/pulse C64_DOCKER_ARGS="${C64_DOCKER_ARGS:-} -v c64-x11:/tmp/.X11-unix" \
        exec "$TC/run.sh" emu-vice "$@" ;;
*) sed -n 2,15p "$0"; exit 1 ;;
esac
