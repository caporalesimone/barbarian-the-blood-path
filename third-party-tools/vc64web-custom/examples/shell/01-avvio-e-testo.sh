#!/bin/sh
# Avvia l'emulatore, digita un comando BASIC e legge lo schermo.
set -e; . "$(dirname "$0")/common.sh"
fresh
$C64 sendText 'print 6*7\n'          # digita nella matrice tastiera ("\n" = RETURN)
$C64 runFrames 30                    # lascia eseguire 30 fotogrammi, poi il core si ferma
$C64 screenText                      # le 25 righe di testo
$C64 --compact state                 # stato: cicli, frozen, disco...
$C64 --out "$OUT/schermo.png" screenshot
