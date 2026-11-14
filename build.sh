#!/bin/sh
# Build e test di "Barbarian: The Blood Path" (13/11: tutto nei container Docker; sull'host servono solo sh, Docker, git e curl).
#   ./build.sh               TUTTO: disco + mappe RAM/disco + atlante + smoke e sanity + manuale PDF (barbarian-manual)
#   ./build.sh --fast        solo il disco (salta atlante, mappe e manuale); smoke e sanity restano
#   ./build.sh --no-atlas    salta l'atlante grafico         --no-maps    salta le mappe della RAM e del disco
#   ./build.sh --no-manual   salta il manuale PDF            --no-test    salta smoke e sanity
#   ./build.sh --release     build completa + tutti i test (anche regression ed EMU-*) + manuale + tools/build/release.sh
#   ./build.sh --emu         i test con il demone vc64web acceso (test EMU-*: python3 tests/run.py regression -k EMU)
#   ./build.sh --view        i test aprono VICE sullo schermo del viewer: http://localhost:6080 (c64-emu-viewer); se il viewer e'
#                            gia' acceso lo fanno da soli (14/11), salvo --no-view
#   ./build.sh --no-view     i test su display virtuali anche con il viewer acceso
#   ./build.sh --manual      SOLO il manuale PDF (barbarian-manual), senza rifare il disco
#   ./build.sh --images      rifa' tutte le immagini Docker (toolchain e manuale; poi la build)
#   ./build.sh --keep N      quante versioni tenere in out/releases/ (default 5, KEEP_VERSIONS nell'ambiente)
# I flag si combinano (es. --fast --no-test = solo il disco). Gli artefatti di ogni build (disco, atlante, mappe, report dei
# test, manuale) finiscono in out/releases/v<versione>/ con manifest.json (tools/build/publish.py); out/releases/latest e' l'ultima.
# Le immagini mancanti si costruiscono da sole (toolchain/images.sh; il manuale: tools/manual/Dockerfile); i programmi esterni
# (VICE, zx0, cc1541) si compilano dentro le immagini. Prima volta su un computer nuovo: ./validate_env.sh.
# Configurazione della toolchain per questo progetto: toolchain.env.
# Stato dal vivo (14/11, per la pagina del viewer): out/tmp/build.json (fase, esito), out/tmp/tests.json (tests/run.py).
# Copyright (c) 2026 - Simone Caporale
set -eu
cd "$(dirname "$0")"
FLAGS="$*"; REL=0; NOTEST=0; EMU=0; VIEW=0; NOVIEW=0; MANUAL=0; IMAGES=0; KEEP=${KEEP_VERSIONS:-5}; ATLAS=1; MAPS=1; MANUALDEF=1
while [ $# -gt 0 ]; do
    case "$1" in --release) REL=1; EMU=1 ;; --no-test) NOTEST=1 ;; --emu) EMU=1 ;; --view) VIEW=1 ;; --no-view) NOVIEW=1 ;; --manual) MANUAL=1 ;;
                 --images) IMAGES=1 ;; --fast) ATLAS=0; MAPS=0; MANUALDEF=0 ;; --no-atlas) ATLAS=0 ;; --no-maps) MAPS=0 ;;
                 --no-manual) MANUALDEF=0 ;; --keep) shift; KEEP=${1:-}; case "$KEEP" in ''|*[!0-9]*|0) echo "--keep N: intero >= 1"; exit 1 ;; esac ;;
                 *) sed -n 2,22p "$0"; exit 1 ;; esac
    shift
done
# stato dal vivo per la pagina del viewer: out/tmp/build.json (scrittura atomica: file temporaneo + mv)
T0=$(date +%s); PHASE=avvio
status() {
    mkdir -p out/tmp
    printf '{"state":"%s","phase":"%s","flags":"%s","started":%s,"updated":%s}\n' "$1" "$PHASE" "$FLAGS" "$T0" "$(date +%s)" \
        > out/tmp/build.json.tmp && mv out/tmp/build.json.tmp out/tmp/build.json
}
phase() { PHASE=$1; status running; }
cleanup() { [ $EMU = 1 ] && docker rm -f c64-emu-vc64web >/dev/null 2>&1 || true; }
on_exit() { rc=$?; cleanup; if [ $rc = 0 ]; then PHASE=fine; status ok; else status fail; fi; }
trap on_exit EXIT
trap 'exit 130' INT TERM
phase avvio
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
phase immagini
if [ $IMAGES = 1 ]; then toolchain/images.sh --force; manual_image force; fi
toolchain/images.sh builder emu-vice
export RELEASE=$REL BUILD_ATLAS=$ATLAS BUILD_MAPS=$MAPS
[ $REL = 1 ] && export ZX0_BEST=1          # release: GAME compresso in modo ottimo (tools/build/pack.py)

if [ $MANUAL = 1 ]; then
    phase manuale
    manual_image
    toolchain/run.sh barbarian-manual python3 tools/manual/gen_manual.py
    toolchain/run.sh builder python3 tools/build/publish.py --keep "$KEEP" --only-manual; exit 0
fi

phase build
TB=$(date +%s)
toolchain/run.sh builder tools/build/build_game.sh
PUB="--keep $KEEP --build-seconds $(( $(date +%s) - TB ))"
[ $ATLAS = 1 ] && PUB="$PUB --atlas"
[ $MAPS = 1 ] && PUB="$PUB --maps"
if [ $NOTEST = 1 ]; then
    phase pubblicazione
    # shellcheck disable=SC2086
    toolchain/run.sh builder python3 tools/build/publish.py $PUB; exit 0
fi

# --- servizi per i test: rete comune, demone vc64web, viewer
NET=c64; docker network inspect $NET >/dev/null 2>&1 || docker network create $NET >/dev/null
DARGS="--network $NET"
phase test
if [ $EMU = 1 ]; then
    toolchain/images.sh emu-vc64web
    docker rm -f c64-emu-vc64web >/dev/null 2>&1 || true
    docker run -d --rm --init --shm-size 1g --name c64-emu-vc64web --network $NET c64-emu-vc64web >/dev/null
    export EMU_URL=http://c64-emu-vc64web:7064
fi
# viewer gia' acceso: i test si vedono sullo schermo dal vivo senza chiederlo (salvo --no-view)
[ $NOVIEW = 0 ] && [ -n "$(docker ps -q -f name=^c64-emu-viewer$)" ] && VIEW=1
if [ $VIEW = 1 ] && [ $NOVIEW = 0 ]; then
    toolchain/viewer.sh start
    DARGS="$DARGS -v c64-x11:/tmp/.X11-unix"; export C64_VIEW=1 DISPLAY=:99 PULSE_SERVER=unix:/tmp/.X11-unix/pulse
fi
C64_DOCKER_ARGS="$DARGS" toolchain/run.sh emu-vice tests/run_tests.sh

PUB="$PUB --tests"
if [ $REL = 1 ] || [ $MANUALDEF = 1 ]; then
    phase manuale
    manual_image
    toolchain/run.sh barbarian-manual python3 tools/manual/gen_manual.py
    PUB="$PUB --manual"
fi
if [ $REL = 1 ]; then
    phase release
    toolchain/run.sh builder tools/build/release.sh
    PUB="$PUB --release --maps"          # release.sh rifa' sempre le mappe (RELEASE=1)
fi
phase pubblicazione
# shellcheck disable=SC2086
toolchain/run.sh builder python3 tools/build/publish.py $PUB
echo "== build OK =="
[ $REL = 1 ] || echo "   (test: smoke + sanity; tutti i test con ./build.sh --release; build veloce: ./build.sh --fast)"
