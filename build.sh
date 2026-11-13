#!/bin/sh
# Build e test di "Barbarian: The Blood Path" (13/11: tutto nei container Docker; sull'host servono solo sh, Docker, git e curl).
#   ./build.sh               build (barbarian-builder) + smoke e sanity (barbarian-emu-vice)
#   ./build.sh --no-test     solo la build
#   ./build.sh --release     build + tutti i test (anche regression ed EMU-* su vc64web) + manuale PDF + tools/build/release.sh
#   ./build.sh --emu         come senza opzioni, con il demone vc64web acceso (test EMU-*: python3 tests/run.py regression -k EMU)
#   ./build.sh --view        i test aprono VICE sullo schermo del viewer: http://localhost:6080 (barbarian-emu-viewer)
#   ./build.sh --manual      solo il manuale PDF (barbarian-manual) in out/manual/
#   ./build.sh --images      rifa' tutte le immagini Docker (poi la build)
# Le immagini mancanti si costruiscono da sole (docker/images.sh); i programmi esterni (VICE, zx0, cc1541) se mancano si
# compilano una volta con third-party-tools/build.sh. Prima volta su un computer nuovo: ./validate_env.sh.
# Copyright (c) 2026 - Simone Caporale
set -eu
cd "$(dirname "$0")"
REL=0; NOTEST=0; EMU=0; VIEW=0; MANUAL=0; IMAGES=0
for a in "$@"; do
    case "$a" in --release) REL=1; EMU=1 ;; --no-test) NOTEST=1 ;; --emu) EMU=1 ;; --view) VIEW=1 ;; --manual) MANUAL=1 ;;
                 --images) IMAGES=1 ;; *) sed -n 2,13p "$0"; exit 1 ;; esac
done
command -v docker >/dev/null || { echo "Docker non trovato: ./validate_env.sh"; exit 1; }
docker info >/dev/null 2>&1 || { echo "il demone Docker non risponde: ./validate_env.sh"; exit 1; }
if [ $IMAGES = 1 ]; then docker/images.sh --force; fi
docker/images.sh builder emu-vice
MISS=""
[ -x third-party-tools/vice/bin/x64sc ] || MISS="$MISS vice"
[ -x third-party-tools/zx0/bin/zx0 ] || MISS="$MISS zx0"
[ -x third-party-tools/cc1541/bin/cc1541 ] || MISS="$MISS cc1541"
[ -z "$MISS" ] || third-party-tools/build.sh $MISS
export RELEASE=$REL
[ $REL = 1 ] && export ZX0_BEST=1          # release: GAME compresso in modo ottimo (tools/build/pack.py)

if [ $MANUAL = 1 ]; then
    docker/images.sh manual
    docker/run.sh manual python3 tools/manual/gen_manual.py; exit 0
fi

docker/run.sh builder tools/build/build_game.sh
[ $NOTEST = 1 ] && exit 0

# --- servizi per i test: rete comune, demone vc64web, viewer
NET=barbarian; docker network inspect $NET >/dev/null 2>&1 || docker network create $NET >/dev/null
DARGS="--network $NET"
cleanup() { [ $EMU = 1 ] && docker rm -f barbarian-emu-vc64web >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM
if [ $EMU = 1 ]; then
    docker/images.sh emu-vc64web
    docker rm -f barbarian-emu-vc64web >/dev/null 2>&1 || true
    docker run -d --rm --init --shm-size 1g --name barbarian-emu-vc64web --network $NET barbarian-emu-vc64web >/dev/null
    export EMU_URL=http://barbarian-emu-vc64web:7064
fi
if [ $VIEW = 1 ]; then
    docker/viewer.sh start
    DARGS="$DARGS -v barbarian-x11:/tmp/.X11-unix"; export BARBARIAN_VIEW=1 DISPLAY=:99
fi
BARBARIAN_DOCKER_ARGS="$DARGS" docker/run.sh emu-vice tests/run_tests.sh

if [ $REL = 1 ]; then
    docker/images.sh manual
    docker/run.sh manual python3 tools/manual/gen_manual.py
    docker/run.sh builder tools/build/release.sh
fi
V=$(sed -n 's/^version: "\(.*\)"/\1/p' version.yaml)
echo "== build OK v$V: out/blood_path_v${V}_1541.d64 =="
[ $REL = 1 ] || echo "   (test: smoke + sanity; tutti i test con ./build.sh --release)"
