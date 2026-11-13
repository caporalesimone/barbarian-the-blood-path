#!/bin/sh
# Memoria: peek/poke/dump/find; schermo: findText, border, cursor, screenshot, screenDiff.
set -e; . "$(dirname "$0")/common.sh"
fresh
$C64 pokeRange 0xC000 '[1,2,3,4]'    # array di byte = JSON valido
$C64 peek 0xC000 4                   # -> [1,2,3,4]
$C64 peekWord 0xC000                 # -> 513 (little endian)
$C64 dump 0xC000 16
$C64 find '[3,4]'                    # indirizzi in cui compare la sequenza
$C64 findText 'READY.'               # screen code -> {row,col,addr}
$C64 --compact cursor
$C64 border
$C64 screenSave prima                # schermo di riferimento
$C64 sendText 'print 1\n'; $C64 runFrames 30
$C64 --compact screenDiff prima null '{"tolerance":0}'    # pixel diversi rispetto a prima
