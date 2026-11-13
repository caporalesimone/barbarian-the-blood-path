#!/bin/bash
# Build del gioco DENTRO il container barbarian-builder (13/11): niente test, niente VICE. Dall'host si usa ./build.sh, che
# lancia questo script nel container e poi i test in barbarian-emu-vice.   Uso (nel container): tools/build/build_game.sh
#  1. versioni: se i sorgenti sono cambiati dall'ultima build la versione cresce (tools/build/bump_version.py, impronta in
#     version.yaml), poi version.yaml -> out/version.inc
#  2. generatori dati: grafica, font, musica, tabelle di bilanciamento (balance.yaml)
#  3. assemblaggio (64tass) -> out/game.prg, controllo del margine di memoria, disco out/disk.d64
#  4. mappe della RAM e del disco (out/memory-map/), atlante grafico (out/atlas/)
#  5. copia del disco con la versione nel nome: out/blood_path_vX.Y_1541.d64
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
mkdir -p out                    # (11/11) anche i sorgenti generati stanno in out/
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
DISK=out/disk.d64
echo "== mappe RAM e disco ($DISK, out/memory-map/), atlante grafico (out/atlas/) =="
python3 tools/memory-map/gen_rammap.py && python3 tools/memory-map/gen_diskmap.py $DISK || exit 1
python3 tools/build/cache_run.py gen_atlas --in tools data out/gfx out/gfx_consts.inc out/gfx0.prg out/fmap.prg out/title.prg docs/screens \
    --out out/atlas/index.html -- python3 tools/atlas/gen_atlas.py || exit 1        # (11/11) solo se cambiano i suoi ingressi
V=$(python3 tools/build/gen_version.py --print version)
rm -f out/blood_path_v*.d64
cp out/disk.d64 out/blood_path_v${V}_1541.d64      # (11/11) un solo disco
echo "== disco: out/blood_path_v${V}_1541.d64 =="
