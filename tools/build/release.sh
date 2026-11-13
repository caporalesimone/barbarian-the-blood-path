#!/bin/bash
# Parte finale della release, DENTRO barbarian-builder (13/11): la lancia ./build.sh --release dopo build, test e manuale.
# Con la versione di version.yaml; tutto in out/ (out/ ha solo l'ultima build). Disco con GAME compresso in modo ottimo
# (./build.sh --release esporta ZX0_BEST=1), mappe della RAM e del disco in out/memory-map/, zip dei sorgenti.
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
V=$(python3 tools/build/gen_version.py --print version)
rm -f out/blood_path*.d64 out/sources*.zip
tools/build/mkdisk.sh out/blood_path_v${V}_1541.d64 out/game.zx0
RELEASE=1 python3 tools/memory-map/gen_rammap.py out/memory-map/mappa_ram.html >/dev/null
python3 tools/memory-map/gen_diskmap.py out/blood_path_v${V}_1541.d64 out/memory-map/mappa_disco.html >/dev/null
zip -qr out/sources_v$V.zip src data tools tests docker roms third-party-tools lab/README.md build.sh validate_env.sh version.yaml \
    CLAUDE.md TODO.md README.md docs .gitignore .gitattributes \
    -x "*/__pycache__/*" "third-party-tools/*/bin/*" "third-party-tools/vice/src/*" "third-party-tools/cc1541/src/*" \
       "third-party-tools/vc64web-custom/out/*"
echo "release v$V: out/blood_path_v${V}_1541.d64  out/sources_v$V.zip  out/memory-map/  out/manual/"
