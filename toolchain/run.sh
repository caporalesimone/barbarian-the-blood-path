#!/bin/sh
# Runs a command in a toolchain container, with the project mounted at /work (13/11). Copyright (c) 2026 - Simone Caporale
#   toolchain/run.sh builder tools/build/asm.sh                 toolchain/run.sh emu-vice python3 tests/run.py -k SAVE
#   toolchain/run.sh builder                                    (interactive shell)
#   toolchain/run.sh barbarian-manual python3 tools/manual/gen_manual.py      (project image: full name)
# Name: builder, emu-vice, ... = image c64-<name>; the full name of an existing image is used as is.
# Runs as the host user (the files in out/ stay theirs); HOME in out/tmp/home.
# Variables passed: EMU_URL, C64_VIEW, DISPLAY, PULSE_SERVER, C64_MEMPROBE and those of C64_PASS_ENV (project toolchain.env).
# Extra docker options: C64_DOCKER_ARGS="--network c64 ...". Project: the folder above toolchain/ (or C64_PROJECT).
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
for v in EMU_URL C64_VIEW DISPLAY PULSE_SERVER C64_MEMPROBE ${C64_PASS_ENV:-}; do
    eval "[ -n \"\${$v+x}\" ]" && ENVS="$ENVS -e $v"
done
# shellcheck disable=SC2086
exec docker run --rm $TTY --init -u "$(id -u):$(id -g)" -e HOME=/work/out/tmp/home -e LANG=C.UTF-8 $ENVS \
    ${C64_DOCKER_ARGS:-} -v "$ROOT":/work -w /work "$IMG" "$@"
