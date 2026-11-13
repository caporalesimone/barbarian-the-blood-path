#!/bin/sh
# Viewer (13/11): docker/viewer.sh start|stop. Schermo condiviso (volume barbarian-x11) mostrato nel browser: http://localhost:6080
# Con il viewer acceso: BARBARIAN_VIEW=1 DISPLAY=:99 BARBARIAN_DOCKER_ARGS="-v barbarian-x11:/tmp/.X11-unix" docker/run.sh emu-vice ...
# (./build.sh --view lo fa da solo). La porta e' aperta solo su localhost. Copyright (c) 2026 - Simone Caporale
set -eu
cd "$(dirname "$0")/.."
case "${1:-}" in
start)
    docker/images.sh emu-viewer
    if [ -z "$(docker ps -q -f name=^barbarian-emu-viewer$)" ]; then
        docker rm -f barbarian-emu-viewer >/dev/null 2>&1 || true
        docker run -d --rm --name barbarian-emu-viewer -p 127.0.0.1:${VIEW_PORT:-6080}:6080 -v barbarian-x11:/tmp/.X11-unix barbarian-emu-viewer >/dev/null
        for i in $(seq 50); do docker exec barbarian-emu-viewer test -S /tmp/.X11-unix/X99 2>/dev/null && break; sleep 0.2; done
    fi
    echo "viewer: http://localhost:${VIEW_PORT:-6080}";;
stop) docker rm -f barbarian-emu-viewer >/dev/null 2>&1 || true; echo "viewer fermato";;
*) sed -n 2,4p "$0"; exit 1;;
esac
