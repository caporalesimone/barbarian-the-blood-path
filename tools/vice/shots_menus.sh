#!/bin/bash
# Screenshot di tutte le schermate a menu (08/11, richiesta del committente: si conservano in docs/screens/ e si
# rifanno solo quelli cambiati). Uso: tools/vice/shots_menus.sh [nome ...]   (senza nomi: tutti)
# Poi tools/vice/menus_mosaic.py rifa' il mosaico docs/screens/tutti_i_menu.png con i PNG che ci sono.
cd "$(dirname "$0")/../.."
declare -A ENV=(
  [scheda]="TESTUI=2 TESTLVL=0"        [inventario]="TESTUI=4 TESTLVL=0"   [baule]="TESTUI=5 TESTLVL=6"
  [fabbro]="TESTUI=15"                 [alchimista]="TESTUI=17"
  [locanda]="TESTUI=21 TESTLVL=0"      [menu_gioco]="TESTUI=25 TESTLVL=2 CHEATS=0"
  [menu_iniziale]="TESTUI=30 TESTLVL=0" [nuovo_barbaro]="TESTUI=31 TESTLVL=0" [morte]="TESTUI=32 TESTLVL=2"
  [quit]="TESTUI=33 TESTLVL=2"         [badsave]="TESTUI=34 TESTLVL=0"     [io_screen]="TESTUI=35 TESTLVL=0"
  [leva]="TESTUI=36 TESTLVL=2"  [io_generico]="TESTUI=37 TESTLVL=0" [io_livello]="TESTUI=38 TESTLVL=0"        [mappa]="TESTUI=14 TESTLVL=6"
  [personaggio]="TESTUI=39 TESTLVL=2 TESTCL=9"  [personaggio_vuoto]="TESTUI=40 TESTLVL=2 TESTCL=7"
  [trucchi]="TESTUI=41 TESTLVL=2"
)
# (15/11) menu_gioco con CHEATS=0: il menu come lo vede il giocatore (release); "trucchi" = il menu dei trucchi, solo nelle build
# di debug e di test (CHEATS=1, src/game/cheats.asm)
declare -A WAIT=([locanda]=14 [baule]=3)
NAMES=("$@"); [ ${#NAMES[@]} -eq 0 ] && NAMES=(menu_iniziale nuovo_barbaro scheda inventario baule fabbro alchimista locanda menu_gioco quit morte mappa badsave io_screen io_generico io_livello leva personaggio personaggio_vuoto trucchi)
for n in "${NAMES[@]}"; do
  [ -z "${ENV[$n]}" ] && { echo "schermata sconosciuta: $n"; exit 1; }
  env NOKEYS=1 ${ENV[$n]} tools/build/asm.sh test >/dev/null 2>&1 || { echo "assemblaggio fallito: $n"; exit 1; }
  tools/vice/shot.sh "docs/screens/$n.png" "${WAIT[$n]:-6}" >/dev/null 2>&1 && echo "ok $n"
done
tools/build/asm.sh >/dev/null 2>&1          # di nuovo la build normale
tools/build/mkdisk.sh >/dev/null 2>&1   # e il disco (gli screenshot lo riscrivono)
python3 tools/vice/menus_mosaic.py
