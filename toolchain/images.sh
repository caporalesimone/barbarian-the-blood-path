#!/bin/sh
# Costruisce le immagini della toolchain (13/11). Copyright (c) 2026 - Simone Caporale
#   toolchain/images.sh                       tutte quelle che mancano
#   toolchain/images.sh --force [nomi...]     le rifa' (nomi: builder emu-vice emu-viewer emu-vc64web)
# builder, emu-vice, emu-viewer: target del Dockerfile multi-stage toolchain/docker/Dockerfile (stage base comune, senza nome).
# emu-vc64web: pagine generate nel builder, immagine dal Dockerfile del pacchetto autonomo toolchain/vc64web-custom.
# c64-tools-builder NON e' qui: e' usa e getta (toolchain/build.sh). Immagini del progetto: le costruisce il progetto (./build.sh).
# C64_CA_BUNDLE=FILE: CA di un proxy che intercetta TLS, passata come segreto alle build che scaricano con npm.
set -eu
TC=$(cd "$(dirname "$0")" && pwd)
ROOT=${C64_PROJECT:-$(dirname "$TC")}
REL=${TC#"$ROOT"/}                     # toolchain/ vista dal container (progetto in /work)
FORCE=0; [ "${1:-}" = "--force" ] && { FORCE=1; shift; }
NAMES="${*:-builder emu-vice emu-viewer emu-vc64web}"
SECRET=""; [ -n "${C64_CA_BUNDLE:-}" ] && SECRET="--secret id=ca,src=$C64_CA_BUNDLE"
have() { docker image inspect "c64-$1" >/dev/null 2>&1; }
for n in $NAMES; do
    if [ $FORCE = 0 ] && have "$n"; then continue; fi
    echo "== immagine c64-$n =="
    case $n in
    builder|emu-vice) DOCKER_BUILDKIT=1 docker build -q --target "$n" -t "c64-$n" "$TC/docker" >/dev/null ;;
    emu-viewer)       DOCKER_BUILDKIT=1 docker build -q --target viewer -t c64-emu-viewer "$TC/docker" >/dev/null ;;
    emu-vc64web)
        have builder || "$0" builder
        (cd "$ROOT" && "$TC/run.sh" builder python3 "$REL/vc64web-custom/build.py" --no-docker --no-ffmpeg-check --out out/vc64web)
        # shellcheck disable=SC2086
        DOCKER_BUILDKIT=1 docker build -q $SECRET -t c64-emu-vc64web --build-context pages="$ROOT/out/vc64web" \
            "$TC/vc64web-custom" >/dev/null ;;
    *) echo "immagine sconosciuta: $n"; exit 1 ;;
    esac
    echo "   $(docker image inspect -f '{{.Size}}' "c64-$n" | awk '{printf "%.0f MB", $1/1e6}')"
done
