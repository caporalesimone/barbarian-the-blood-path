#!/bin/bash
# Parte finale della release, DENTRO c64-builder (13/11): la lancia ./build.sh --release dopo build, test e manuale.
# Con la versione di version.yaml; il disco e' out/disk.d64 (poi lo pubblica tools/build/publish.py in out/releases/v<V>/). Disco con GAME compresso in modo ottimo
# (./build.sh --release esporta ZX0_BEST=1), mappe della RAM e del disco in out/memory-map/ (14/11: niente zip dei sorgenti, regola del committente).
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
V=$(python3 tools/build/gen_version.py --print version)
tools/build/mkdisk.sh out/disk.d64 out/game.zx0
RELEASE=1 python3 tools/memory-map/gen_rammap.py out/memory-map/mappa_ram.html >/dev/null
python3 tools/memory-map/gen_diskmap.py out/disk.d64 out/memory-map/mappa_disco.html >/dev/null
echo "release v$V: out/disk.d64  out/memory-map/  out/manual/"
