#!/bin/bash
# Assembla: tools/build/asm.sh [test] -> out/work/game.prg, moduli e TUTTI i programmi del disco (11/11: un solo START e un solo
# BARBARIAN; un solo disco dall'11/11, tools/build/mkdisk.sh). I passi lenti e
# indipendenti dal gioco (storia, manuale) girano solo se i loro ingressi cambiano (tools/build/cache_run.py).
# Per build completa + test usa ./build.sh [--release]
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
mkdir -p out/work                    # (11/11) anche i sorgenti generati stanno in out/
INC="-I src -I src/common -I src/game -I out/work"          # src/: un sorgente per file del disco; sottocartelle: common, game, lore, test
python3 tools/build/gen_version.py || exit 1
tools/build/krill_build.sh > out/work/krill.log || { cat out/work/krill.log; exit 1; }   # (11/11) Krill's Loader: out/work/krill/*.prg + out/work/krill.inc
python3 tools/build/gen_gfx.py >/dev/null
python3 tools/build/gen_font.py >/dev/null || exit 1
python3 tools/build/gen_music.py >/dev/null || exit 1
python3 tools/build/gen_db.py >/dev/null || exit 1
python3 tools/build/gen_maps.py >/dev/null || exit 1   # prima dell'assemblaggio: scrive town_places.inc (porte per la minimappa)
EXTRA="-D NOKEYS=0 -D AUTOY=0 -D TSV=0 -D TESTSELL=0 -D NOMUSIC=0 -D TMDBG=0 -D TESTBUILD=0 -D TESTLVL=${TESTLVL:-1} -D TESTCL=${TESTCL:-1} -D TESTSP=${TESTSP:-1} -D TESTX=${TESTX:-0} -D TESTY=${TESTY:-0} -D TESTUI=${TESTUI:-0} -D TESTFIRE=0 -D TESTSK=0 -D TESTFZ=0 -D TESTFZR=100 -D TESTFZS=0 -D TESTGOD=0"
if [ "$1" = "test" ]; then EXTRA="-D NOKEYS=${NOKEYS:-0} -D AUTOY=${AUTOY:-0} -D TSV=${TSV:-0} -D NOMUSIC=${NOMUSIC:-0} -D TESTSELL=${TESTSELL:-0} -D TMDBG=${TMDBG:-0} -D TESTBUILD=${TB:-1} -D TESTLVL=${TESTLVL:-1} -D TESTCL=${TESTCL:-1} -D TESTSP=${TESTSP:-1} -D TESTX=${TESTX:-0} -D TESTY=${TESTY:-0} -D TESTUI=${TESTUI:-0} -D TESTFIRE=${TESTFIRE:-0} -D TESTSK=${TESTSK:-0} -D TESTFZ=${TESTFZ:-0} -D TESTFZR=${TESTFZR:-100} -D TESTFZS=${TESTFZS:-0} -D TESTGOD=${TESTGOD:-0}"; fi
rm -f out/work/game.prg
64tass -a $EXTRA -L out/work/game.lst -l out/work/game.lbl $INC src/game.asm -o out/work/game.prg > out/work/build.log 2>&1 || { grep -v '^$' out/work/build.log | head -${ERRLINES:-40}; exit 1; }
tail -3 out/work/build.log
# build arena (tools/vice/arena.py): gioco con ARENA=1 + modulo src/test/arena.asm a $C900
ARX=$(echo "$EXTRA" | sed 's/-D NOKEYS=[0-9]*/-D NOKEYS=1/')
64tass -a $ARX -D ARENA=1 -L out/work/arena_game.lst -l out/work/arena_game.lbl $INC src/game.asm -o out/work/arena_game.prg > out/work/arena.log 2>&1 || { grep -v '^$' out/work/arena.log | head -20; exit 1; }
64tass -a $INC src/test/arena.asm -o out/work/arena.prg -l out/work/arena.lbl -L out/work/arena.lst >> out/work/arena.log 2>&1 || { grep -v '^$' out/work/arena.log | head -20; exit 1; }
# moduli su file: assemblati con le etichette del gioco (out/work/game.lbl)
64tass -a $INC src/lobby.asm -o out/work/lobby.prg -l out/work/lobby.lbl -L out/work/lobby.lst > out/work/ovl.log 2>&1 || { grep -v '^$' out/work/ovl.log | head -20; exit 1; }
64tass -a -b $INC src/menu.asm -o out/work/menu.bin -l out/work/menu.lbl -L out/work/menu.lst > out/work/menu.log 2>&1 || { grep -v "^$" out/work/menu.log | head -20; exit 1; }
MENUMSG=$(python3 tools/build/pack_menu.py) || exit 1        # file MENU = locanda e negozi, due zone compresse ZX0
python3 tools/build/gen_title.py >/dev/null || exit 1  # (anche in debug: l'atlante grafico mostra il titolo)
python3 tools/build/gen_start.py || exit 1
# (15/11, TODO Z2) file dei villaggi TWNc = tile del villaggio + intestazione (posizioni, colori, nome della cura, tile solidi)
# + mappa RLE (tools/build/gen_maps.py, tools/build/villages.py). gfx0.prg = villaggio 1 (lo leggono START e gli strumenti).
cat out/work/gfx/gfx0.prg out/work/town1.map > out/work/gfx0.prg
cp out/work/gfx0.prg out/work/twn1.prg
for c in 2 3 4 5; do cat out/work/gfx/twn$c.prg out/work/town$c.map > out/work/twn$c.prg; done
python3 tools/build/pack.py || exit 1                 # GAME compresso ZX0 -> out/work/game.zx0 + out/work/pack.inc
# START (avvio del gioco): deve conoscere i byte di GAME + MENU + GFX0 (per dosare il titolo)
GODM=$(grep -E '^godmode\s*=' out/work/game.lbl | awk '{print $3}')      # (11/11) byte del god mode in GAME: START ci scrive il POKE 1021
# START (avvio del gioco, 11/11: uno per i due dischi) con la schermata di attesa e la musica (TITLE=0: niente titolo)
python3 tools/build/cache_run.py gen_lore --in tools/build/gen_lore.py data src/game.asm out/work/gfx out/work/gfx_consts.inc \
    --out out/work/ldat.prg out/work/lore.inc out/work/logo.inc -- python3 tools/build/gen_lore.py >/dev/null || exit 1   # storia: LDAT, logo
64tass -a $INC -D GODMODE=$GODM -D LDCOL=${LDCOL:-0} -D TITLE=0 src/start.asm -o out/work/start.prg -L out/work/start.lst -l out/work/start.lbl > out/work/start.log 2>&1 || { grep -v '^$' out/work/start.log | head -20; exit 1; }
64tass -a $INC -D LDCOL=${LDCOL:-0} src/lore.asm -o out/work/lore.prg -L out/work/lore.lst -l out/work/lore.lbl > out/work/lore.log 2>&1 || { grep -v '^$' out/work/lore.log | head -20; exit 1; }
python3 tools/build/cache_run.py gen_help --in tools/build/gen_help.py data/help.txt data/help_hud.json out/work/gfx out/work/gfx_consts.inc \
    --out out/work/help.inc -- python3 tools/build/gen_help.py >/dev/null || exit 1     # il manuale (HELP)
64tass -a $INC src/help.asm -o out/work/help.prg -L out/work/help.lst -l out/work/help.lbl > out/work/help.log 2>&1 || { grep -v '^$' out/work/help.log | head -20; exit 1; }
# (12/11, TODO M5b) HELP sul disco compresso ZX0 con il decompressore in testa (src/help/zx0sfx.asm): out/work/helpz.prg
python3 -c "import sys; sys.path.insert(0,'tools/build'); import pack; z,_=pack.zx0(open('out/work/help.prg','rb').read()[2:],'help'); open('out/work/help.zx0','wb').write(z)" || exit 1
64tass -a $INC src/help/zx0sfx.asm -o out/work/helpz.prg -L out/work/helpz.lst > out/work/helpz.log 2>&1 || { grep -v '^$' out/work/helpz.log | head -20; exit 1; }
64tass -a $INC src/barbarian.asm -o out/work/barbarian.prg -L out/work/barbarian.lst -l out/work/barbarian.lbl > out/work/barbarian.log 2>&1 || { grep -v '^$' out/work/barbarian.log | head -20; exit 1; }
# jukebox (prova di brani ed effetti con il player del gioco): sui due dischi (11/11; da rifare piu' bello, TODO E8)
64tass -a -q $INC -D AUTOPLAY=-1 src/jukebox.asm -o out/work/jukebox.prg -l out/work/jukebox.lbl > out/work/jukebox.log 2>&1 || { grep -v '^$' out/work/jukebox.log | head -20; exit 1; }
echo "moduli: lobby $(( $(stat -c %s out/work/lobby.prg) - 2 )) B, villaggi (intestazione + mappa, max 1888 B): $(for c in 1 2 3 4 5; do printf "%s " $(stat -c %s out/work/town$c.map); done)"
echo "$MENUMSG"
ls -la out/work/game.prg
python3 - <<'PY'
import re
l = {m.group(1): int(m.group(2), 16) for m in (re.match(r'(\w+)\s*=\s*\$([0-9a-f]+)', x) for x in open('out/work/game.lbl')) if m}
m1 = l['SCR_H'] + 800 - l['gfx_data']; m2 = l['FREE_RAM_END'] + 1 - l['code2_end']; m = min(m1, m2)
print(f"margine codice: {m1} B fino a $8720 (fine ${l['gfx_data']:04x}), {m2} B nel blocco $9C00-$9FFF")
if m1 < 1024:                          # il blocco $9C00 e' piccolo per costruzione: conta il margine sotto $8720
    print("*** ATTENZIONE: margine sotto $8720 inferiore a 1 KB: e' ora di liberare memoria ***")
PY
