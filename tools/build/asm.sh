#!/bin/bash
# Assembla: tools/build/asm.sh [test] -> out/game.prg, moduli e TUTTI i programmi del disco (11/11: un solo START e un solo
# BARBARIAN; un solo disco dall'11/11, tools/build/mkdisk.sh). I passi lenti e
# indipendenti dal gioco (storia, manuale) girano solo se i loro ingressi cambiano (tools/build/cache_run.py).
# Per build completa + test usa ./build.sh [--release]
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
mkdir -p out                    # (11/11) anche i sorgenti generati stanno in out/
INC="-I src -I src/common -I src/game -I out"          # src/: un sorgente per file del disco; sottocartelle: common, game, lore, test
python3 tools/build/gen_version.py || exit 1
tools/build/krill_build.sh > out/krill.log || { cat out/krill.log; exit 1; }   # (11/11) Krill's Loader: out/krill/*.prg + out/krill.inc
python3 tools/build/gen_gfx.py >/dev/null
python3 tools/build/gen_font.py >/dev/null || exit 1
python3 tools/build/gen_music.py >/dev/null || exit 1
python3 tools/build/gen_db.py >/dev/null || exit 1
python3 tools/build/gen_maps.py >/dev/null || exit 1   # prima dell'assemblaggio: scrive town_places.inc (porte per la minimappa)
EXTRA="-D NOKEYS=0 -D AUTOY=0 -D TSV=0 -D TESTSELL=0 -D NOMUSIC=0 -D TMDBG=0 -D TESTBUILD=0 -D TESTLVL=${TESTLVL:-1} -D TESTCL=${TESTCL:-1} -D TESTSP=${TESTSP:-1} -D TESTX=${TESTX:-0} -D TESTY=${TESTY:-0} -D TESTUI=${TESTUI:-0} -D TESTFIRE=0 -D TESTSK=0 -D TESTFZ=0 -D TESTFZR=100 -D TESTFZS=0 -D TESTGOD=0"
if [ "$1" = "test" ]; then EXTRA="-D NOKEYS=${NOKEYS:-0} -D AUTOY=${AUTOY:-0} -D TSV=${TSV:-0} -D NOMUSIC=${NOMUSIC:-0} -D TESTSELL=${TESTSELL:-0} -D TMDBG=${TMDBG:-0} -D TESTBUILD=${TB:-1} -D TESTLVL=${TESTLVL:-1} -D TESTCL=${TESTCL:-1} -D TESTSP=${TESTSP:-1} -D TESTX=${TESTX:-0} -D TESTY=${TESTY:-0} -D TESTUI=${TESTUI:-0} -D TESTFIRE=${TESTFIRE:-0} -D TESTSK=${TESTSK:-0} -D TESTFZ=${TESTFZ:-0} -D TESTFZR=${TESTFZR:-100} -D TESTFZS=${TESTFZS:-0} -D TESTGOD=${TESTGOD:-0}"; fi
rm -f out/game.prg
64tass -a $EXTRA -L out/game.lst -l out/game.lbl $INC src/game.asm -o out/game.prg > out/build.log 2>&1 || { grep -v '^$' out/build.log | head -${ERRLINES:-40}; exit 1; }
tail -3 out/build.log
# build arena (tools/vice/arena.py): gioco con ARENA=1 + modulo src/test/arena.asm a $C900
ARX=$(echo "$EXTRA" | sed 's/-D NOKEYS=[0-9]*/-D NOKEYS=1/')
64tass -a $ARX -D ARENA=1 -L out/arena_game.lst -l out/arena_game.lbl $INC src/game.asm -o out/arena_game.prg > out/arena.log 2>&1 || { grep -v '^$' out/arena.log | head -20; exit 1; }
64tass -a $INC src/test/arena.asm -o out/arena.prg -l out/arena.lbl -L out/arena.lst >> out/arena.log 2>&1 || { grep -v '^$' out/arena.log | head -20; exit 1; }
# moduli su file: assemblati con le etichette del gioco (out/game.lbl)
64tass -a $INC src/lobby.asm -o out/lobby.prg -l out/lobby.lbl -L out/lobby.lst > out/ovl.log 2>&1 || { grep -v '^$' out/ovl.log | head -20; exit 1; }
64tass -a -b $INC src/menu.asm -o out/menu.bin -l out/menu.lbl -L out/menu.lst > out/menu.log 2>&1 || { grep -v "^$" out/menu.log | head -20; exit 1; }
MENUMSG=$(python3 tools/build/pack_menu.py) || exit 1        # file MENU = locanda e negozi, due zone compresse ZX0
python3 tools/build/gen_title.py >/dev/null || exit 1  # (anche in debug: l'atlante grafico mostra il titolo)
python3 tools/build/gen_start.py || exit 1
cat out/gfx/gfx0.prg out/town.map > out/gfx0.prg
python3 tools/build/pack.py || exit 1                 # GAME compresso ZX0 -> out/game.zx0 + out/pack.inc
# START (avvio del gioco): deve conoscere i byte di GAME + MENU + GFX0 (per dosare il titolo)
GODM=$(grep -E '^godmode\s*=' out/game.lbl | awk '{print $3}')      # (11/11) byte del god mode in GAME: START ci scrive il POKE 1021
# START (avvio del gioco, 11/11: uno per i due dischi) con la schermata di attesa e la musica (TITLE=0: niente titolo)
python3 tools/build/cache_run.py gen_lore --in tools/build/gen_lore.py data src/game.asm out/gfx out/gfx_consts.inc \
    --out out/ldat.prg out/lore.inc out/logo.inc -- python3 tools/build/gen_lore.py >/dev/null || exit 1   # storia: LDAT, logo
64tass -a $INC -D GODMODE=$GODM -D LDCOL=${LDCOL:-0} -D TITLE=0 src/start.asm -o out/start.prg -L out/start.lst -l out/start.lbl > out/start.log 2>&1 || { grep -v '^$' out/start.log | head -20; exit 1; }
64tass -a $INC -D LDCOL=${LDCOL:-0} src/lore.asm -o out/lore.prg -L out/lore.lst -l out/lore.lbl > out/lore.log 2>&1 || { grep -v '^$' out/lore.log | head -20; exit 1; }
python3 tools/build/cache_run.py gen_help --in tools/build/gen_help.py data/help.txt data/help_hud.json out/gfx out/gfx_consts.inc \
    --out out/help.inc -- python3 tools/build/gen_help.py >/dev/null || exit 1     # il manuale (HELP)
64tass -a $INC src/help.asm -o out/help.prg -L out/help.lst -l out/help.lbl > out/help.log 2>&1 || { grep -v '^$' out/help.log | head -20; exit 1; }
# (12/11, TODO M5b) HELP sul disco compresso ZX0 con il decompressore in testa (src/help/zx0sfx.asm): out/helpz.prg
python3 -c "import sys; sys.path.insert(0,'tools/build'); import pack; z,_=pack.zx0(open('out/help.prg','rb').read()[2:],'help'); open('out/help.zx0','wb').write(z)" || exit 1
64tass -a $INC src/help/zx0sfx.asm -o out/helpz.prg -L out/helpz.lst > out/helpz.log 2>&1 || { grep -v '^$' out/helpz.log | head -20; exit 1; }
64tass -a $INC src/barbarian.asm -o out/barbarian.prg -L out/barbarian.lst -l out/barbarian.lbl > out/barbarian.log 2>&1 || { grep -v '^$' out/barbarian.log | head -20; exit 1; }
# jukebox (prova di brani ed effetti con il player del gioco): sui due dischi (11/11; da rifare piu' bello, TODO E8)
64tass -a -q $INC -D AUTOPLAY=-1 src/jukebox.asm -o out/jukebox.prg -l out/jukebox.lbl > out/jukebox.log 2>&1 || { grep -v '^$' out/jukebox.log | head -20; exit 1; }
echo "moduli: lobby $(( $(stat -c %s out/lobby.prg) - 2 )) B, mappa villaggio $(stat -c %s out/town.map) B (max 1792)"
echo "$MENUMSG"
ls -la out/game.prg
python3 - <<'PY'
import re
l = {m.group(1): int(m.group(2), 16) for m in (re.match(r'(\w+)\s*=\s*\$([0-9a-f]+)', x) for x in open('out/game.lbl')) if m}
m1 = l['SCR_H'] + 800 - l['gfx_data']; m2 = l['FREE_RAM_END'] + 1 - l['code2_end']; m = min(m1, m2)
print(f"margine codice: {m1} B fino a $8720 (fine ${l['gfx_data']:04x}), {m2} B nel blocco $9C00-$9FFF")
if m1 < 1024:                          # il blocco $9C00 e' piccolo per costruzione: conta il margine sotto $8720
    print("*** ATTENZIONE: margine sotto $8720 inferiore a 1 KB: e' ora di liberare memoria ***")
PY
