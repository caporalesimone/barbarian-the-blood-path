#!/bin/bash
# genera gli screenshot del manuale in manual/shots (build di test + VICE); poi tools/manual/gen_manual.py
# (menu, nuovo barbaro e morte dalle varianti TESTUI 30-32, come tools/vice/shots_menus.sh, 09/11)
source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
cd "$ROOT"; D=manual/shots; mkdir -p $D
one(){ # nome secondi[:live] VAR=..
  n=$1; sec=${2%%:*}; mode=; [[ $2 == *:live ]] && mode=live; shift 2
  # villaggio: il PG deve stare su una casella percorribile (regola del committente, 06/11)
  local tl= tx= ty=; for a in "$@"; do case $a in TESTLVL=*) tl=${a#*=};; TESTX=*) tx=${a#*=};; TESTY=*) ty=${a#*=};; esac; done
  if [ "$tl" = "0" ] && [ -n "$tx" ]; then python3 tools/vice/check_pos.py $tx $ty || { echo "KO $n"; return; }; fi
  # (15/11) CHEATS=0: il manuale e' per i giocatori, il menu di gioco senza la voce "cheats" delle build di test
  env NOKEYS=1 CHEATS=0 "$@" tools/build/asm.sh test >/dev/null 2>&1 || { echo "build KO $n"; return; }
  tools/vice/shot.sh $PWD/$D/$n.png $sec $mode; echo ok $n
}
one town 4 TESTLVL=0 TESTX=16 TESTY=31
one town2 4 TESTLVL=0 TESTX=30 TESTY=11
one townmap 4 TESTLVL=0 TESTUI=14
one dungeon 1.5:live TESTLVL=8 TESTCL=12 TESTSP=1     # copertina: SEMPRE tema rosso (palette 4: piano 8 con il seed di prova)
one dungeonmap 4 TESTLVL=4 TESTUI=22
one menu 3 TESTUI=30 TESTLVL=0
one newhero 3 TESTUI=31 TESTLVL=0
one death 3 TESTUI=32 TESTLVL=2
one hero 3 TESTUI=2
one inventory 3 TESTUI=4
one chest 2 TESTUI=5 TESTLVL=6
one shop_smith 3 TESTUI=15
one shop_alch 3 TESTUI=17
one stash 14 TESTUI=21 TESTLVL=0
one stairs 3 TESTUI=24 TESTLVL=2
one gamemenu 3 TESTUI=25 TESTLVL=2
one hudwarn 3 TESTUI=27 TESTLVL=0 TESTX=16 TESTY=31
tools/build/asm.sh >/dev/null 2>&1      # la build normale torna in out/
