#!/bin/sh
# Viewer (13/11): toolchain/viewer.sh start|stop. Copyright (c) 2026 - Simone Caporale
#   Pagina indice su http://localhost:6080 (solo localhost): schermo condiviso (volume c64-x11) in noVNC, ultima build da aprire
#   in vc64web nel browser (con audio), cartella out/ del progetto in sola lettura.
#   Variabili: VIEW_PORT (6080), VIEW_PASSWORD (password VNC, di default nessuna), VIEW_SIZE (1280x1000x24),
#   C64_VIEW_DISK (toolchain.env: disco proposto per primo nell'indice).
# Con il viewer acceso: C64_VIEW=1 DISPLAY=:99 C64_DOCKER_ARGS="-v c64-x11:/tmp/.X11-unix" toolchain/run.sh emu-vice ...
# (./build.sh --view lo fa da solo).
set -eu
TC=$(cd "$(dirname "$0")" && pwd)
ROOT=${C64_PROJECT:-$(dirname "$TC")}
[ -f "$ROOT/toolchain.env" ] && . "$ROOT/toolchain.env"
case "${1:-}" in
start)
    "$TC/images.sh" emu-viewer
    if [ -z "$(docker ps -q -f name=^c64-emu-viewer$)" ]; then
        docker rm -f c64-emu-viewer >/dev/null 2>&1 || true
        mkdir -p "$ROOT/out"
        docker run -d --rm --name c64-emu-viewer -p "127.0.0.1:${VIEW_PORT:-6080}:6080" -v c64-x11:/tmp/.X11-unix \
            -v "$ROOT/out":/srv/www/out:ro -e VIEW_PASSWORD="${VIEW_PASSWORD:-}" -e VIEW_SIZE="${VIEW_SIZE:-1280x1000x24}" \
            -e VIEW_DISK="${C64_VIEW_DISK:-}" c64-emu-viewer >/dev/null
        for i in $(seq 50); do docker exec c64-emu-viewer test -S /tmp/.X11-unix/X99 2>/dev/null && break; sleep 0.2; done
    fi
    echo "viewer: http://localhost:${VIEW_PORT:-6080}";;
stop) docker rm -f c64-emu-viewer >/dev/null 2>&1 || true; echo "viewer fermato";;
*) sed -n 2,8p "$0"; exit 1;;
esac
