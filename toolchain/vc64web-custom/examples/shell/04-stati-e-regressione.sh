#!/bin/sh
# Snapshot dello stato e regressione. regress check esce con 0 (PASS) o 1 (FAIL).
set -e; . "$(dirname "$0")/common.sh"
fresh
$C64 --compact saveState inizio
$C64 sendText 'print 1\n'; $C64 runFrames 60
$C64 --compact regress save dopo     # baseline: hash componenti + RAM + schermo + cicli
$C64 --compact loadState inizio      # torna esattamente allo stato salvato
$C64 sendText 'print 1\n'; $C64 runFrames 60
$C64 regress check dopo '{"ignore":["0x0400-0x07E7","0xD800-0xDBE7"]}' && echo "uguale" || echo "diverso"
$C64 --out "$OUT/stato.bin" saveState file '{"export":true}'   # stato su file
$C64 loadState @"$OUT/stato.bin"                               # ricaricato da file
