#!/bin/sh
# Costruisce le immagini del progetto (13/11). Copyright (c) 2026 - Simone Caporale
#   docker/images.sh                       tutte quelle che mancano
#   docker/images.sh --force [nomi...]     le rifa' (nomi: builder emu-vice manual emu-viewer emu-vc64web)
# barbarian-tools-builder NON e' qui: e' usa e getta (third-party-tools/build.sh).
# BARBARIAN_CA_BUNDLE=FILE: CA di un proxy che intercetta TLS, passata come segreto alle build che scaricano con pip/npm.
set -eu
cd "$(dirname "$0")/.."
FORCE=0; [ "${1:-}" = "--force" ] && { FORCE=1; shift; }
NAMES="${*:-builder emu-vice manual emu-viewer emu-vc64web}"
SECRET=""; [ -n "${BARBARIAN_CA_BUNDLE:-}" ] && SECRET="--secret id=ca,src=$BARBARIAN_CA_BUNDLE"
have() { docker image inspect "barbarian-$1" >/dev/null 2>&1; }
for n in $NAMES; do
    if [ $FORCE = 0 ] && have $n; then continue; fi
    echo "== immagine barbarian-$n =="
    case $n in
    builder|emu-viewer) docker build -q -t barbarian-$n docker/$n >/dev/null ;;
    emu-vice)  have builder || "$0" builder; docker build -q -t barbarian-$n docker/$n >/dev/null ;;
    manual)    DOCKER_BUILDKIT=1 docker build -q $SECRET -t barbarian-$n docker/$n >/dev/null ;;
    emu-vc64web)                         # pagine dal builder (python), immagine dal Dockerfile del pacchetto (autonomo)
        have builder || "$0" builder
        docker/run.sh builder python3 third-party-tools/vc64web-custom/build.py --no-docker --no-ffmpeg-check --out out/vc64web
        DOCKER_BUILDKIT=1 docker build -q $SECRET -t barbarian-$n --build-context pages=out/vc64web third-party-tools/vc64web-custom >/dev/null ;;
    *) echo "immagine sconosciuta: $n"; exit 1 ;;
    esac
    echo "   $(docker image inspect -f '{{.Size}}' barbarian-$n | awk '{printf "%.0f MB", $1/1e6}')"
done
