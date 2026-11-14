#!/bin/bash
# Build del gioco DENTRO il container lab64-tools (13/11): niente test, niente VICE. Dall'host si usa ./build.sh, che
# lancia questo script nel container e poi i test in lab64-tools.   Uso (nel container): tools/build/build_game.sh
#  1. versioni: se i sorgenti sono cambiati dall'ultima build la versione cresce (tools/build/bump_version.py, impronta in
#     version.yaml), poi version.yaml -> out/work/version.inc
#  2. generatori dati: grafica, font, musica, tabelle di bilanciamento (balance.yaml)
#  3. assemblaggio (64tass) -> out/work/game.prg, controllo del margine di memoria, disco out/work/disk.d64
#  4. mappe della RAM e del disco (out/work/memory-map/), atlante grafico (out/work/atlas/): saltabili (BUILD_MAPS=0, BUILD_ATLAS=0)
#  (14/11) la pubblicazione degli artefatti in out/releases/v<versione>/ la fa ./build.sh con tools/build/publish.py
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
mkdir -p out/work                    # (11/11) anche i sorgenti generati stanno in out/
REL=${RELEASE:-0}
export RELEASE=$REL
echo "== versioni =="
python3 tools/build/bump_version.py               # build con cambiamenti: versione + 1 (version.yaml)
python3 tools/build/gen_version.py
echo "software $(python3 tools/build/gen_version.py --print version), salvataggi $(python3 tools/build/gen_version.py --print save_version), build $([ $REL = 1 ] && echo release + debug || echo debug)"
echo "== generatori =="
for g in gen_gfx gen_final gen_bossmap gen_font gen_music gen_db; do
    printf '%s ... ' $g; python3 tools/build/$g.py >/dev/null && echo ok || exit 1   # 10/11: un generatore che fallisce ferma la build
done
echo "== assemblaggio =="
tools/build/asm.sh && tools/build/mkdisk.sh || exit 1          # (11/11) un solo disco
DISK=out/work/disk.d64
# (14/11) BUILD_MAPS=0 / BUILD_ATLAS=0 (./build.sh --no-maps, --no-atlas, --fast) li saltano
if [ "${BUILD_MAPS:-1}" = 1 ]; then
    echo "== mappe RAM e disco ($DISK, out/work/memory-map/) =="
    python3 tools/memory-map/gen_rammap.py && python3 tools/memory-map/gen_diskmap.py $DISK || exit 1
    python3 "${LAB64:-../lab64}/memmap/c64map.py" --work out/work --disk $DISK --out out/work/memory-map || exit 1   # (14/11) mappa automatica di Lab64: index.html
fi
if [ "${BUILD_ATLAS:-1}" = 1 ]; then
    echo "== atlante grafico (out/work/atlas/) =="
    python3 tools/build/cache_run.py gen_atlas --in tools data out/work/gfx out/work/gfx_consts.inc out/work/gfx0.prg out/work/fmap.prg out/work/title.prg docs/screens \
        --out out/work/atlas/index.html -- python3 tools/atlas/gen_atlas.py || exit 1        # (11/11) solo se cambiano i suoi ingressi
fi
V=$(python3 tools/build/gen_version.py --print version)
echo "== disco v$V: $DISK (poi out/releases/v$V/blood_path_v${V}_1541.d64, tools/build/publish.py) =="
