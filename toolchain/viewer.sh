#!/bin/sh
# Viewer (13/11): shared screen WITH AUDIO to watch in the browser. Copyright (c) 2026 - Simone Caporale
#   toolchain/viewer.sh start | stop
#   toolchain/viewer.sh exec <command>     command in the c64-emu-vice container attached to the viewer screen and audio
#                                          (e.g. toolchain/viewer.sh exec tools/vice/play.sh: live VICE with sound)
# http://localhost:6080 (localhost only, one port): control center, live screen with audio (/live.html, KasmVNC), vc64web in the
# browser, the project out/ folder read-only. /live.html also has the overlay with C64 keyboard, Joy 1 and Joy 2 (the keys go
# through /input, see server.js).
# Variables: VIEW_PORT (6080), VIEW_PASSWORD (password of the WHOLE viewer, none by default), VIEW_SIZE (1280x1000),
#   VIEW_HOSTS (host names allowed besides localhost, 127.0.0.1, [::1], comma separated: e.g. behind a tunnel),
#   C64_VIEW_DISK (toolchain.env: disk proposed first in the index), C64_VIEW_TITLE (toolchain.env: project name in the page),
#   C64_VIEW_PLAYER (toolchain.env: command that starts VICE on a .d64; if set, start also runs the c64-emu-player container with
#   toolchain/viewer_player.py, and the "VICE" buttons of the index open that disk on the live screen).
# The viewer has no Docker socket (that would be root on the host): it talks to c64-emu-player through a Unix socket in the c64-x11 volume.
# The other containers use screen and audio by mounting the c64-x11 volume: DISPLAY=:99, PULSE_SERVER=unix:/tmp/.X11-unix/pulse
# (./build.sh --view does it by itself; the tests run with -sounddev dummy, so without sound).
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
stop) docker rm -f c64-emu-player c64-emu-viewer >/dev/null 2>&1 || true; echo "viewer stopped" ;;
exec)
    shift; [ $# -ge 1 ] || { sed -n 4,5p "$0"; exit 1; }
    start
    C64_VIEW=1 DISPLAY=:99 PULSE_SERVER=unix:/tmp/.X11-unix/pulse C64_DOCKER_ARGS="${C64_DOCKER_ARGS:-} -v c64-x11:/tmp/.X11-unix" \
        exec "$TC/run.sh" emu-vice "$@" ;;
*) sed -n 2,15p "$0"; exit 1 ;;
esac
