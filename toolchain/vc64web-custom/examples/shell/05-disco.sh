#!/bin/sh
# Disco D64 di prova: lo crea, lo monta (core IN MARCIA), carica ed esegue il programma.
set -e; . "$(dirname "$0")/common.sh"
python3 "$ROOT/examples/tools/mk_d64.py" "$OUT/test.d64"
$C64 --quiet start; $C64 --quiet resume
$C64 --quiet attach 8 @"$OUT/test.d64" test.d64   # il drive vede il disco solo con il core in marcia
$C64 --quiet sleep 1500                            # tempo reale: il drive deve leggere il disco
$C64 --quiet pause
$C64 --compact driveState
$C64 sendText 'load"hello",8\n'; $C64 runFrames 300
$C64 sendText 'run\n';           $C64 runFrames 100
$C64 screenText | head -14
# oppure dalla cartella giochi:  cp "$OUT/test.d64" ../games/ ; C64_GAMES=../games c64 game test.d64
