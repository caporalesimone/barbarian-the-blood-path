#!/bin/bash
# Parte finale della release, DENTRO c64-builder (13/11): la lancia ./build.sh --release dopo build, test e manuale.
# Con la versione di version.yaml; il disco e' out/disk.d64 (poi lo pubblica tools/build/publish.py in out/releases/v<V>/). Disco con GAME compresso in modo ottimo
# (./build.sh --release esporta ZX0_BEST=1), mappe della RAM e del disco in out/memory-map/, zip dei sorgenti.
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
V=$(python3 tools/build/gen_version.py --print version)
rm -f out/sources*.zip
tools/build/mkdisk.sh out/disk.d64 out/game.zx0
RELEASE=1 python3 tools/memory-map/gen_rammap.py out/memory-map/mappa_ram.html >/dev/null
python3 tools/memory-map/gen_diskmap.py out/disk.d64 out/memory-map/mappa_disco.html >/dev/null
zip -qr out/sources_v$V.zip src data tools tests toolchain lab/README.md build.sh validate_env.sh toolchain.env version.yaml \
    CLAUDE.md TODO.md README.md docs .gitignore .gitattributes \
    -x "*/__pycache__/*" "toolchain/vice/download/*" "toolchain/kasmvnc/download/*" \
       "toolchain/vc64web-custom/out/*"
echo "release v$V: out/disk.d64  out/sources_v$V.zip  out/memory-map/  out/manual/"
