#!/bin/bash
# Parte finale della release, DENTRO c64-builder (13/11): la lancia ./build.sh --release dopo build, test e manuale.
# Con la versione di version.yaml; il disco e' out/work/disk.d64 (poi lo pubblica tools/build/publish.py in out/releases/v<V>/). Disco con GAME compresso in modo ottimo
# (./build.sh --release esporta ZX0_BEST=1), mappe della RAM e del disco in out/work/memory-map/ (14/11: niente zip dei sorgenti, regola del committente).
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
V=$(python3 tools/build/gen_version.py --print version)
tools/build/mkdisk.sh out/work/disk.d64 out/work/game.zx0
RELEASE=1 python3 tools/memory-map/gen_rammap.py out/work/memory-map/mappa_ram.html >/dev/null
python3 tools/memory-map/gen_diskmap.py out/work/disk.d64 out/work/memory-map/mappa_disco.html >/dev/null
python3 toolchain/memmap/c64map.py --work out/work --disk out/work/disk.d64 --out out/work/memory-map >/dev/null
echo "release v$V: out/work/disk.d64  out/work/memory-map/  out/work/manual/"
