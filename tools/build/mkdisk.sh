#!/bin/bash
# Crea il d64 del gioco (11/11, regola del committente: una sola build, un solo disco).
# Uso: tools/build/mkdisk.sh [out.d64] [prg]   (default: out/disk.d64, out/game.zx0)
#   BARBARIAN = loader con il menu (storia / manuale / gioco); POKE 1020,1 prima del RUN = subito START (docs/cheats.md).
# File: BARBARIAN, START, GAME (ZX0), MENU1..3, FMAP, TWN1..4 (villaggi dei capitoli), BOSSCH1..3 (piani dei boss),
# GFX1..8 (grafica dei capitoli: dungeon e boss),
# SND0..n (brani, tools/build/gen_music.py), TITLE, LORE, LDAT, HELP, JUKEBOX, HL e SAVE-01..05 (salvataggi, Krill).
# (11/11, ramo fast-loader) disco scritto con il cc1541 di Krill (sorgente nel pacchetto di Krill, src/third-party/krill): nomi con hash a 8 caratteri.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
OUT=${1:-out/disk.d64}; PRG=${2:-out/game.zx0}     # GAME compresso ZX0 (tools/build/pack.py)
rm -f "$OUT"
BRB=out/barbarian.prg
# (11/11, ramo fast-loader) salvataggi per Krill: file gia' presenti con la lunghezza giusta (il plugin di save
# riscrive solo file esistenti con lo stesso numero di blocchi): hl (elenco eroi) e save-01..05 (un file per eroe)
python3 - <<'PY' || { echo "mkdisk: errore file dei salvataggi"; exit 1; }
import re
lb = open("out/game.lbl").read()
g = lambda n: (lambda v: int(v[1:], 16) if v[0] == "$" else int(v))(re.search(r"^%s\s*=\s*(\$?[0-9a-f]+)" % n, lb, re.M).group(1))
sv, hl = g("SV_LEN"), g("HDR_LEN")
open("out/hl.prg", "wb").write(bytes([0, 0, g("SAVE_VER")]) + bytes(hl - 1))     # elenco vuoto della versione attuale
open("out/save.prg", "wb").write(bytes([0, 0xe0]) + bytes(sv))
PY
# cc1541 di Krill (nel PATH di c64-builder: compilato nella build dell'immagine dallo zip di Krill): -M 8 = FILENAME_MAXLENGTH del loader (hash dei nomi); BARBARIAN primo (LOAD"*",8)
CC=cc1541
command -v $CC >/dev/null || { echo "mkdisk: manca cc1541: gira nel container c64-builder (toolchain/run.sh builder ...)"; exit 1; }
ARGS=(-M 8 -n "blood path" -i "bp" -f barbarian -w $BRB -f start -w out/start.prg -f game -w "$PRG" -f lobby -w out/lobby.prg
      -f menu1 -w out/menu1.prg -f menu2 -w out/menu2.prg -f menu3 -w out/menu3.prg -f fmap -w out/fmap.prg)
for c in 1 2 3 4; do ARGS+=(-f twn$c -w out/gfx0.prg); done     # (12/11) villaggi dei capitoli: oggi copie del villaggio 1 (segnaposto)
for c in 1 2 3; do ARGS+=(-f bossch$c -w out/bossch$c.prg); done    # (12/11) piani del boss dei capitoli 1-3 (segnaposto, tools/build/gen_bossmap.py)
for f in out/gfx/gfx[12].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done     # capitolo 1: dungeon e boss (i file dei capitoli 2-4 in fondo al disco: lasciano ai file usati spesso le tracce di prima)
for f in out/snd/snd*.prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done     # brani (tools/build/gen_music.py)
ARGS+=(-f title -w out/title.prg -f lore -w out/lore.prg -f ldat -w out/ldat.prg -f help -w out/helpz.prg -f jukebox -w out/jukebox.prg)
ARGS+=(-f hl -w out/hl.prg -f ksave -w out/krill/save.prg)     # ksave: plugin di save di Krill, ricaricato a ogni save
for s in 1 2 3 4 5; do ARGS+=(-f save-0$s -w out/save.prg); done
for f in out/gfx/gfx[3-9].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done     # capitoli 2-4 (segnaposto)
$CC "${ARGS[@]}" "$OUT" > out/mkdisk.log 2>&1 || { cat out/mkdisk.log; echo "mkdisk: errore cc1541"; exit 1; }
