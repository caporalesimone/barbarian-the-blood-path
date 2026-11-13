#!/bin/sh
# Esegue un comando in un container della toolchain, con il progetto montato in /work (13/11). Copyright (c) 2026 - Simone Caporale
#   toolchain/run.sh builder tools/build/asm.sh                 toolchain/run.sh emu-vice python3 tests/run.py -k SAVE
#   toolchain/run.sh builder                                    (shell interattiva)
#   toolchain/run.sh barbarian-manual python3 tools/manual/gen_manual.py      (immagine del progetto: nome completo)
# Nome: builder, emu-vice, ... = immagine c64-<nome>; un nome completo di un'immagine esistente si usa cosi' com'e'.
# Gira con l'utente dell'host (i file in out/ restano suoi); HOME in out/tmp/home.
# Variabili passate: EMU_URL, C64_VIEW, DISPLAY e quelle di C64_PASS_ENV (toolchain.env del progetto).
# Opzioni docker in piu': C64_DOCKER_ARGS="--network c64 ...". Progetto: la cartella sopra toolchain/ (o C64_PROJECT).
set -eu
TC=$(cd "$(dirname "$0")" && pwd)
ROOT=${C64_PROJECT:-$(dirname "$TC")}
[ -f "$ROOT/toolchain.env" ] && . "$ROOT/toolchain.env"
[ $# -ge 1 ] || { sed -n 2,9p "$0"; exit 1; }
IMG=$1; shift
docker image inspect "$IMG" >/dev/null 2>&1 || IMG=c64-$IMG
[ $# -ge 1 ] || set -- bash
TTY=""; if [ -t 0 ] && [ -t 1 ]; then TTY="-it"; fi
mkdir -p "$ROOT/out/tmp/home"
ENVS=""
for v in EMU_URL C64_VIEW DISPLAY ${C64_PASS_ENV:-}; do
    eval "[ -n \"\${$v+x}\" ]" && ENVS="$ENVS -e $v"
done
# shellcheck disable=SC2086
exec docker run --rm $TTY --init -u "$(id -u):$(id -g)" -e HOME=/work/out/tmp/home -e LANG=C.UTF-8 $ENVS \
    ${C64_DOCKER_ARGS:-} -v "$ROOT":/work -w /work "$IMG" "$@"
