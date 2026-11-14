#!/bin/sh
# Build e test di "Barbarian: The Blood Path" (13/11: tutto nei container Docker; sull'host servono solo sh, Docker, git e curl).
#   ./build.sh               build (c64-builder) + smoke e sanity (c64-emu-vice)
#   ./build.sh --no-test     solo la build
#   ./build.sh --release     build + tutti i test (anche regression ed EMU-* su vc64web) + manuale PDF + tools/build/release.sh
#   ./build.sh --emu         come senza opzioni, con il demone vc64web acceso (test EMU-*: python3 tests/run.py regression -k EMU)
#   ./build.sh --view        i test aprono VICE sullo schermo del viewer: http://localhost:6080 (c64-emu-viewer)
#   ./build.sh --manual      solo il manuale PDF (barbarian-manual) in out/manual/
#   ./build.sh --images      rifa' tutte le immagini Docker (toolchain e manuale; poi la build)
#   ./build.sh --keep N      quante versioni tenere in out/releases/ (default 5, KEEP_VERSIONS nell'ambiente)
# Gli artefatti di ogni build (disco, atlante, mappe, report dei test, manuale, zip dei sorgenti) finiscono in
# out/releases/v<versione>/ con manifest.json (tools/build/publish.py); out/releases/latest punta all'ultima.
# Le immagini mancanti si costruiscono da sole (toolchain/images.sh; il manuale: tools/manual/Dockerfile); i programmi esterni
# (VICE, zx0, cc1541) si compilano dentro le immagini. Prima volta su un computer nuovo: ./validate_env.sh.
# Configurazione della toolchain per questo progetto: toolchain.env.
# Copyright (c) 2026 - Simone Caporale
set -eu
cd "$(dirname "$0")"
REL=0; NOTEST=0; EMU=0; VIEW=0; MANUAL=0; IMAGES=0; KEEP=${KEEP_VERSIONS:-5}
while [ $# -gt 0 ]; do
    case "$1" in --release) REL=1; EMU=1 ;; --no-test) NOTEST=1 ;; --emu) EMU=1 ;; --view) VIEW=1 ;; --manual) MANUAL=1 ;;
                 --images) IMAGES=1 ;; --keep) shift; KEEP=${1:-}; case "$KEEP" in ''|*[!0-9]*|0) echo "--keep N: intero >= 1"; exit 1 ;; esac ;;
                 *) sed -n 2,18p "$0"; exit 1 ;; esac
    shift
done
command -v docker >/dev/null || { echo "Docker non trovato: ./validate_env.sh"; exit 1; }
docker info >/dev/null 2>&1 || { echo "il demone Docker non risponde: ./validate_env.sh"; exit 1; }
manual_image() {                          # immagine del progetto per il manuale (parte da c64-builder)
    if [ "${1:-}" = force ] || ! docker image inspect barbarian-manual >/dev/null 2>&1; then
        echo "== immagine barbarian-manual =="
        SECRET=""; [ -n "${C64_CA_BUNDLE:-}" ] && SECRET="--secret id=ca,src=$C64_CA_BUNDLE"
        # shellcheck disable=SC2086
        DOCKER_BUILDKIT=1 docker build -q $SECRET -t barbarian-manual tools/manual >/dev/null
    fi
}
if [ $IMAGES = 1 ]; then toolchain/images.sh --force; manual_image force; fi
toolchain/images.sh builder emu-vice
export RELEASE=$REL
[ $REL = 1 ] && export ZX0_BEST=1          # release: GAME compresso in modo ottimo (tools/build/pack.py)

if [ $MANUAL = 1 ]; then
    manual_image
    toolchain/run.sh barbarian-manual python3 tools/manual/gen_manual.py
    toolchain/run.sh builder python3 tools/build/publish.py --keep "$KEEP" --only-manual; exit 0
fi

toolchain/run.sh builder tools/build/build_game.sh
if [ $NOTEST = 1 ]; then toolchain/run.sh builder python3 tools/build/publish.py --keep "$KEEP"; exit 0; fi

# --- servizi per i test: rete comune, demone vc64web, viewer
NET=c64; docker network inspect $NET >/dev/null 2>&1 || docker network create $NET >/dev/null
DARGS="--network $NET"
cleanup() { [ $EMU = 1 ] && docker rm -f c64-emu-vc64web >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM
if [ $EMU = 1 ]; then
    toolchain/images.sh emu-vc64web
    docker rm -f c64-emu-vc64web >/dev/null 2>&1 || true
    docker run -d --rm --init --shm-size 1g --name c64-emu-vc64web --network $NET c64-emu-vc64web >/dev/null
    export EMU_URL=http://c64-emu-vc64web:7064
fi
if [ $VIEW = 1 ]; then
    toolchain/viewer.sh start
    DARGS="$DARGS -v c64-x11:/tmp/.X11-unix"; export C64_VIEW=1 DISPLAY=:99 PULSE_SERVER=unix:/tmp/.X11-unix/pulse
fi
C64_DOCKER_ARGS="$DARGS" toolchain/run.sh emu-vice tests/run_tests.sh

PUB="--keep $KEEP --tests"
if [ $REL = 1 ]; then
    manual_image
    toolchain/run.sh barbarian-manual python3 tools/manual/gen_manual.py
    toolchain/run.sh builder tools/build/release.sh
    PUB="$PUB --manual --release"
fi
# shellcheck disable=SC2086
toolchain/run.sh builder python3 tools/build/publish.py $PUB
echo "== build OK =="
[ $REL = 1 ] || echo "   (test: smoke + sanity; tutti i test con ./build.sh --release)"
