#!/bin/bash
# Assembla: tools/build/asm.sh [test|release-game] -> out/work/game.prg, moduli e TUTTI i programmi del disco (11/11: un solo START e un solo
# BARBARIAN; un solo disco dall'11/11, tools/build/mkdisk.sh). I passi lenti e
# indipendenti dal gioco (storia, manuale) girano solo se i loro ingressi cambiano (tools/build/cache_run.py).
# Per build completa + test usa ./build.sh [--release]
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
mkdir -p out/work                    # (11/11) anche i sorgenti generati stanno in out/
INC="-I src -I src/common -I src/game -I out/work"          # src/: un sorgente per file del disco; sottocartelle: common, game, lore, test
# (15/11) trucchi per i test (menu "cheats" nel menu RUN/STOP, src/game/cheats.asm): CHEATS=1 nella build di debug e in quelle di
# test (anche durante la release), CHEATS=0 nella release (RELEASE=1: con 0 non si assembla un solo byte dei trucchi); CHEATS
# nell'ambiente vince (es. CHEATS=0 tools/build/asm.sh test per gli screenshot del manuale).
CH0=${CHEATS:-}
if [ "$1" = "test" ]; then CHEATS=${CH0:-1}; elif [ "${RELEASE:-0}" = 1 ]; then CHEATS=${CH0:-0}; else CHEATS=${CH0:-1}; fi
EXTRA="-D NOKEYS=0 -D AUTOY=0 -D TSV=0 -D TESTSELL=0 -D NOMUSIC=0 -D TMDBG=0 -D TESTBUILD=0 -D TESTLVL=${TESTLVL:-1} -D TESTCL=${TESTCL:-1} -D TESTSP=${TESTSP:-1} -D TESTX=${TESTX:-0} -D TESTY=${TESTY:-0} -D TESTUI=${TESTUI:-0} -D TESTFIRE=0 -D TESTSK=0 -D TESTFZ=0 -D TESTFZR=100 -D TESTFZS=0 -D TESTGOD=0 -D CHEATS=$CHEATS"
if [ "$1" = "test" ]; then EXTRA="-D NOKEYS=${NOKEYS:-0} -D AUTOY=${AUTOY:-0} -D TSV=${TSV:-0} -D NOMUSIC=${NOMUSIC:-0} -D TESTSELL=${TESTSELL:-0} -D TMDBG=${TMDBG:-0} -D TESTBUILD=${TB:-1} -D TESTLVL=${TESTLVL:-1} -D TESTCL=${TESTCL:-1} -D TESTSP=${TESTSP:-1} -D TESTX=${TESTX:-0} -D TESTY=${TESTY:-0} -D TESTUI=${TESTUI:-0} -D TESTFIRE=${TESTFIRE:-0} -D TESTSK=${TESTSK:-0} -D TESTFZ=${TESTFZ:-0} -D TESTFZR=${TESTFZR:-100} -D TESTFZS=${TESTFZS:-0} -D TESTGOD=${TESTGOD:-0} -D CHEATS=$CHEATS"; fi
# (21/11) GAME in due passate: la prima (GENPASS=1) per i byte del generatore, che gen_imgz.py comprime in out/work/gen_img.zx0;
# la seconda (GENPASS=2) li include compressi (src/game.asm, copy_gfx). asm_game LOG -o PRG -L LST -l LBL [flag...]
asm_game() {
    local log=$1; shift
    mkdir -p out/tmp
    64tass -a "$@" -D GENPASS=1 $INC src/game.asm -o out/tmp/genpass1.prg -l out/tmp/genpass1.lbl -L out/tmp/genpass1.lst > "$log" 2>&1 || return 1
    local o="" prev=""                       # (21/11, TODO D15) file del segmento CORE accanto al PRG: game.prg -> core.prg
    for a in "$@"; do [ "$prev" = "-o" ] && o=$a; prev=$a; done
    python3 tools/build/gen_imgz.py out/tmp/genpass1.prg out/tmp/genpass1.lbl out/work/gen_img.zx0 "$(dirname "$o")/$(basename "$o" .prg | sed 's/game/core/').prg" >> "$log" 2>&1 || return 1
    64tass -a "$@" -D GENPASS=2 $INC src/game.asm >> "$log" 2>&1
}
if [ "$1" = "release-game" ]; then
    # solo GAME con i flag della release (CHEATS=0) in out/tmp/release_game.*, senza generatori ne' disco (servono i sorgenti
    # generati di una build gia' fatta): il controllo che la release non abbia i trucchi (test CHEAT-22)
    mkdir -p out/tmp
    asm_game out/tmp/release_game.log ${EXTRA/-D CHEATS=$CHEATS/-D CHEATS=0} -L out/tmp/release_game.lst -l out/tmp/release_game.lbl -o out/tmp/release_game.prg || { cat out/tmp/release_game.log; exit 1; }
    exit 0
fi
python3 tools/build/gen_version.py || exit 1
tools/build/krill_build.sh > out/work/krill.log || { cat out/work/krill.log; exit 1; }   # (11/11) Krill's Loader: out/work/krill/*.prg + out/work/krill.inc
python3 tools/build/gen_gfx.py >/dev/null
python3 tools/build/gen_font.py >/dev/null || exit 1
python3 tools/build/gen_music.py >/dev/null || exit 1
python3 tools/build/gen_db.py >/dev/null || exit 1
python3 tools/build/gen_qdata.py >/dev/null || exit 1   # (22/11) tabelle del motore delle quest: qtab.inc
python3 tools/build/gen_maps.py >/dev/null || exit 1   # prima dell'assemblaggio: scrive town_places.inc (porte per la minimappa)
rm -f out/work/game.prg
asm_game out/work/build.log $EXTRA -L out/work/game.lst -l out/work/game.lbl -o out/work/game.prg || { grep -v '^$' out/work/build.log | head -${ERRLINES:-40}; exit 1; }
tail -3 out/work/build.log
# build arena (tools/vice/arena.py): gioco con ARENA=1 + modulo src/test/arena.asm a $C900
ARX=$(echo "$EXTRA" | sed 's/-D NOKEYS=[0-9]*/-D NOKEYS=1/')
asm_game out/work/arena.log $ARX -D ARENA=1 -L out/work/arena_game.lst -l out/work/arena_game.lbl -o out/work/arena_game.prg || { grep -v '^$' out/work/arena.log | head -20; exit 1; }
64tass -a $INC src/test/arena.asm -o out/work/arena.prg -l out/work/arena.lbl -L out/work/arena.lst >> out/work/arena.log 2>&1 || { grep -v '^$' out/work/arena.log | head -20; exit 1; }
# (23/11) codice dei piani dei boss per l'arena: le stesse sorgenti con le etichette di arena_game (OVP_AT = $F4E0, theme.asm);
# tools/vice/arena.py lo carica per i piani dei boss dei capitoli e per il piano 20
for o in ovl_boss1 ovl_boss2 ovl_boss3 ovl_final; do
    [ -f src/game/$o.asm ] || { rm -f out/work/arena_$o.prg; continue; }
    64tass -a $INC -D ARENA_OVL=1 src/game/$o.asm -o out/work/arena_$o.prg -l out/work/arena_$o.lbl -L out/work/arena_$o.lst > out/work/arena_$o.log 2>&1 || { grep -v '^$' out/work/arena_$o.log | head -20; exit 1; }
done
# moduli su file: assemblati con le etichette del gioco (out/work/game.lbl)
64tass -a $INC src/lobby.asm -o out/work/lobby.prg -l out/work/lobby.lbl -L out/work/lobby.lst > out/work/ovl.log 2>&1 || { grep -v '^$' out/work/ovl.log | head -20; exit 1; }
64tass -a $INC src/qgiv.asm -o out/work/qgiv.prg -l out/work/qgiv.lbl -L out/work/qgiv.lst > out/work/qgiv.log 2>&1 || { grep -v '^$' out/work/qgiv.log | head -20; exit 1; }   # (22/11) modulo del villaggio delle quest (file "qstg")
for c in 1 2 3; do                  # (19/11) meccaniche dei boss dei capitoli 1-3: code di GFX2, GFX4, GFX6 (bundle.py)
    [ -f src/game/ovl_boss$c.asm ] || { rm -f out/work/ovl_boss$c.bin; continue; }
    64tass -a -b $INC src/game/ovl_boss$c.asm -o out/work/ovl_boss$c.bin -l out/work/ovl_boss$c.lbl -L out/work/ovl_boss$c.lst > out/work/ovl_boss$c.log 2>&1 || { grep -v '^$' out/work/ovl_boss$c.log | head -20; exit 1; }
done
64tass -a -b $INC src/game/ovl_final.asm -o out/work/ovl_final.bin -l out/work/ovl_final.lbl -L out/work/ovl_final.lst > out/work/ovl_final.log 2>&1 || { grep -v '^$' out/work/ovl_final.log | head -20; exit 1; }   # (19/11) codice del piano 20: coda di GFX8 (bundle.py)
for c in 1 2 3 4; do                # (19/11) arredi dei piani generati (capitolo 4: anche la cittadella): code di GFX1, 3, 5, 7
    64tass -a -b $INC -D DK_CHAP=$c src/game/ovl_decor.asm -o out/work/ovl_decor$c.bin -l out/work/ovl_decor$c.lbl -L out/work/ovl_decor$c.lst > out/work/ovl_decor$c.log 2>&1 || { grep -v '^$' out/work/ovl_decor$c.log | head -20; exit 1; }
done
rm -f out/work/gen_cit.bin out/work/gen_cit.lbl out/work/gen_cit.lst out/work/gen_cit.log
# (21/11 sera, TODO A1) schermata del personaggio: modulo CSHEET sul disco, assemblato con le etichette di GAME
64tass -a $INC src/csheet.asm -o out/work/csheet.prg -l out/work/csheet.lbl -L out/work/csheet.lst > out/work/csheet.log 2>&1 || { grep -v '^$' out/work/csheet.log | head -20; exit 1; }
if [ "$CHEATS" = 1 ]; then          # (17/11) menu dei trucchi: modulo CHEATS sul disco (solo debug e test)
    64tass -a $INC src/cheats.asm -o out/work/cheats.prg -l out/work/cheats.lbl -L out/work/cheats.lst > out/work/cheats.log 2>&1 || { grep -v '^$' out/work/cheats.log | head -20; exit 1; }
else
    rm -f out/work/cheats.prg out/work/cheats.lbl out/work/cheats.lst     # la release non ha il file (test CHEAT-22)
fi
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
# jukebox (prova di brani ed effetti con il player del gioco): sui due dischi (11/11; da rifare piu' bello, TODO E8); il listato (-L,
# 15/11) serve alla mappa della memoria del programma JUKEBOX (lab64 map)
64tass -a -q $INC -D AUTOPLAY=-1 src/jukebox.asm -o out/work/jukebox.prg -l out/work/jukebox.lbl -L out/work/jukebox.lst > out/work/jukebox.log 2>&1 || { grep -v '^$' out/work/jukebox.log | head -20; exit 1; }
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
