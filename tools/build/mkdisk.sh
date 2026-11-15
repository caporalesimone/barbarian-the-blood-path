#!/bin/bash
# Crea il d64 del gioco (11/11, regola del committente: una sola build, un solo disco).
# Uso: tools/build/mkdisk.sh [out.d64] [prg]   (default: out/work/disk.d64, out/work/game.zx0)
#   BARBARIAN = loader con il menu (storia / manuale / gioco); POKE 1020,1 prima del RUN = subito START (docs/cheats.md).
# File: BARBARIAN, START, GAME (ZX0), MENU1..3, FMAP, TWN1..5 (villaggi dei capitoli), BOSSCH1..3 (piani dei boss),
# GFX1..8 (grafica dei capitoli: dungeon e boss),
# SND0..n (brani, tools/build/gen_music.py), TITLE, LORE, LDAT, HELP, JUKEBOX, HL e SAVE-01..05 (salvataggi, Krill).
# TWN_LAYOUT (variabile d'ambiente, 15/11, TODO M1: posizione dei villaggi sul disco; vedi docs/FastLoader.md e PERF-DISK-21..25):
#   end     (predefinito) TWN1 fra i primi file; TWN2..TWN5 in fondo, con la grafica dei loro capitoli (come dal 15/11)
#   start   TWN1..TWN5 tutti insieme dove sta TWN1
#   chapter ogni TWNc subito prima di GFX(2c-1), GFX(2c) e BOSSCHc, cosi' quello che un capitolo carica sta vicino (capitolo 1 come
#           in "end"; BOSSCH2 e BOSSCH3 si spostano con il loro capitolo); TWN5 in fondo
#   hub     MENU1..3, SND0 (il brano di ogni villaggio, snd_town_c), TWN1..TWN5 e FMAP uno dopo l'altro (stessi segmenti di directory
#           e stesse tracce di quello che un ingresso nel villaggio carica); il resto come in "end"
#   hubchap MENU1..3, SND0, TWN1 e FMAP insieme (come "hub"); TWN2..TWN4 e BOSSCH2/3 con la grafica dei loro capitoli e TWN5 in fondo (come "chapter")
# Provare un layout senza lasciare la build normale: lab64 run env TWN_LAYOUT=start tools/build/mkdisk.sh
TWN_LAYOUT=${TWN_LAYOUT:-end}
case $TWN_LAYOUT in end|start|chapter|hub|hubchap) ;; *) echo "mkdisk: TWN_LAYOUT=$TWN_LAYOUT sconosciuto (end|start|chapter|hub|hubchap)"; exit 1;; esac
# (11/11, ramo fast-loader) disco scritto con cc1541 (14/11: 4.2 di Lab64, compilato dai sorgenti): nomi con hash a 8 caratteri.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
OUT=${1:-out/work/disk.d64}; PRG=${2:-out/work/game.zx0}     # GAME compresso ZX0 (tools/build/pack.py)
rm -f "$OUT"
BRB=out/work/barbarian.prg
# (11/11, ramo fast-loader) salvataggi per Krill: file gia' presenti con la lunghezza giusta (il plugin di save
# riscrive solo file esistenti con lo stesso numero di blocchi): hl (elenco eroi) e save-01..05 (un file per eroe)
python3 - <<'PY' || { echo "mkdisk: errore file dei salvataggi"; exit 1; }
import re
lb = open("out/work/game.lbl").read()
g = lambda n: (lambda v: int(v[1:], 16) if v[0] == "$" else int(v))(re.search(r"^%s\s*=\s*(\$?[0-9a-f]+)" % n, lb, re.M).group(1))
sv, hl = g("SV_LEN"), g("HDR_LEN")
open("out/work/hl.prg", "wb").write(bytes([0, 0, g("SAVE_VER")]) + bytes(hl - 1))     # elenco vuoto della versione attuale
open("out/work/save.prg", "wb").write(bytes([0, 0xe0]) + bytes(sv))
PY
# cc1541 (nel PATH di lab64-tools: 4.2, compilato dai sorgenti nella build dell'immagine, sources.conf di Lab64): -M 8 = FILENAME_MAXLENGTH del loader (hash dei nomi); BARBARIAN primo (LOAD"*",8)
CC=cc1541
command -v $CC >/dev/null || { echo "mkdisk: manca cc1541: gira nel container lab64-tools (lab64 run ...)"; exit 1; }
# (14/11) -S 4 = interleave dei settori 4 (quello dei benchmark di Krill): con cc1541 4.2 l'interleave predefinito (10) dava il MENU
# in 3,23 s (limite 3,1 s, PERF-DISK-11); con 4 misurato: avvio 14,2 -> 11,4 s, MENU 3,23 -> 2,64 s, villaggio 5,0 -> 3,6 s.
# I file caricati dal KERNAL (BARBARIAN, START, LORE, HELP) misurati con LOAD: stessi tempi con 10 e con 4 (entro 0,1 s).
ARGS=(-S 4 -M 8 -n "blood path" -i "bp" -f barbarian -w $BRB -f start -w out/work/start.prg -f game -w "$PRG" -f lobby -w out/work/lobby.prg
      -f menu1 -w out/work/menu1.prg -f menu2 -w out/work/menu2.prg -f menu3 -w out/work/menu3.prg)
HUB=0; case $TWN_LAYOUT in hub|hubchap) HUB=1;; esac     # HUB=1: il brano del villaggio (SND0) e i villaggi subito dopo MENU1..3
[ $HUB = 1 ] && ARGS+=(-f snd0 -w out/work/snd/snd0.prg -f twn1 -w out/work/twn1.prg)
[ $TWN_LAYOUT = hub ] && ARGS+=(-f twn2 -w out/work/twn2.prg -f twn3 -w out/work/twn3.prg -f twn4 -w out/work/twn4.prg -f twn5 -w out/work/twn5.prg)
ARGS+=(-f fmap -w out/work/fmap.prg)
TW="1"; [ $TWN_LAYOUT = start ] && TW="1 2 3 4 5"; [ $HUB = 1 ] && TW=""
for c in $TW; do ARGS+=(-f twn$c -w out/work/twn$c.prg); done     # (15/11) villaggi dei capitoli, ognuno con tile, mappa e colori suoi (tools/build/villages.py): qui il capitolo 1, gli altri in fondo (5 = la citta' dell'Abisso, prototipo)
BC="1 2 3"; case $TWN_LAYOUT in chapter|hubchap) BC="1";; esac       # (chapter) BOSSCH2 e 3 vanno con il loro capitolo, in fondo
for c in $BC; do ARGS+=(-f bossch$c -w out/work/bossch$c.prg); done    # (12/11) piani del boss dei capitoli 1-3 (segnaposto, tools/build/gen_bossmap.py)
for f in out/work/gfx/gfx[12].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done     # capitolo 1: dungeon e boss (i file dei capitoli 2-4 in fondo al disco: lasciano ai file usati spesso le tracce di prima)
for f in out/work/snd/snd*.prg; do n=$(basename $f .prg); [ $HUB = 1 ] && [ $n = snd0 ] && continue; ARGS+=(-f $n -w $f); done     # brani (tools/build/gen_music.py)
ARGS+=(-f title -w out/work/title.prg -f lore -w out/work/lore.prg -f ldat -w out/work/ldat.prg -f help -w out/work/helpz.prg -f jukebox -w out/work/jukebox.prg)
ARGS+=(-f hl -w out/work/hl.prg -f ksave -w out/work/krill/save.prg)     # ksave: plugin di save di Krill, ricaricato a ogni save
for s in 1 2 3 4 5; do ARGS+=(-f save-0$s -w out/work/save.prg); done
case $TWN_LAYOUT in
  end)     for c in 2 3 4 5; do ARGS+=(-f twn$c -w out/work/twn$c.prg); done     # villaggi dei capitoli 2-5: in fondo, con la grafica dei loro capitoli (i file del capitolo 1 restano sulle prime tracce)
           for f in out/work/gfx/gfx[3-9].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done ;;     # capitoli 2-4 (segnaposto)
  hub)     for f in out/work/gfx/gfx[3-9].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done ;;
  start)   for f in out/work/gfx/gfx[3-9].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done ;;
  chapter|hubchap) for c in 2 3; do ARGS+=(-f twn$c -w out/work/twn$c.prg -f bossch$c -w out/work/bossch$c.prg
                                   -f gfx$((2*c-1)) -w out/work/gfx/gfx$((2*c-1)).prg -f gfx$((2*c)) -w out/work/gfx/gfx$((2*c)).prg); done
           ARGS+=(-f twn4 -w out/work/twn4.prg -f gfx7 -w out/work/gfx/gfx7.prg -f gfx8 -w out/work/gfx/gfx8.prg
                  -f twn5 -w out/work/twn5.prg) ;;
esac
$CC "${ARGS[@]}" "$OUT" > out/work/mkdisk.log 2>&1 || { cat out/work/mkdisk.log; echo "mkdisk: errore cc1541"; exit 1; }
