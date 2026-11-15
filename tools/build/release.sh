#!/bin/bash
# Parte finale della release, DENTRO lab64-tools (13/11): la lancia ./build.sh --release dopo build, test e manuale.
# Con la versione di version.yaml; il disco e' out/work/disk.d64 (poi lo pubblica tools/build/publish.py in out/releases/v<V>/). Disco con GAME compresso in modo ottimo
# (./build.sh --release esporta ZX0_BEST=1), mappe della RAM e del disco in out/work/memory-map/ (14/11: niente zip dei sorgenti, regola del committente).
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
V=$(python3 tools/build/gen_version.py --print version)
tools/build/mkdisk.sh out/work/disk.d64 out/work/game.zx0
lab64 map --strict >/dev/null                # mappa automatica di Lab64 (out/work/memory-map/index.html); --strict: annotazioni giuste
echo "release v$V: out/work/disk.d64  out/work/memory-map/  out/work/manual/"
