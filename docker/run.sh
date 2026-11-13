#!/bin/sh
# Esegue un comando in un container del progetto, con il progetto montato in /work (13/11). Copyright (c) 2026 - Simone Caporale
#   docker/run.sh builder tools/build/asm.sh            docker/run.sh emu-vice python3 tests/run.py -k SAVE
#   docker/run.sh builder                               (shell interattiva)
# Nome = barbarian-<nome>: builder, emu-vice, manual. Gira con l'utente dell'host (i file in out/ restano suoi); HOME in out/tmp/home.
# Variabili passate: RELEASE, ZX0_BEST, EMU_URL, BARBARIAN_VIEW, DISPLAY, C64_REALMENU e quelle delle varianti di build (TESTUI, ...).
# Opzioni docker in piu': BARBARIAN_DOCKER_ARGS="--network barbarian ...".
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
[ $# -ge 1 ] || { sed -n 2,6p "$0"; exit 1; }
IMG=barbarian-$1; shift
[ $# -ge 1 ] || set -- bash
TTY=""; if [ -t 0 ] && [ -t 1 ]; then TTY="-it"; fi
mkdir -p "$ROOT/out/tmp/home"
ENVS=""
for v in RELEASE ZX0_BEST EMU_URL BARBARIAN_VIEW DISPLAY C64_REALMENU NOKEYS AUTOY TSV NOMUSIC TESTSELL TMDBG TB TESTLVL TESTCL \
         TESTSP TESTX TESTY TESTUI TESTFIRE TESTSK TESTFZ TESTFZR TESTFZS TESTGOD LDCOL ERRLINES KRILL_ZP KRILL_INSTALL \
         KRILL_RESIDENT KRILL_TRANSIENT; do
    eval "[ -n \"\${$v+x}\" ]" && ENVS="$ENVS -e $v"
done
# shellcheck disable=SC2086
exec docker run --rm $TTY --init -u "$(id -u):$(id -g)" -e HOME=/work/out/tmp/home -e LANG=C.UTF-8 $ENVS \
    ${BARBARIAN_DOCKER_ARGS:-} -v "$ROOT":/work -w /work "$IMG" "$@"
