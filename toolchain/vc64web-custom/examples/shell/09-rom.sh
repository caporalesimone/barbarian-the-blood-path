#!/bin/sh
# ROM alternative: elenco, caricamento (valgono dal prossimo start), ritorno alle predefinite.
set -e; . "$(dirname "$0")/common.sh"
$C64 roms kernal                         # elenco dei file ROM trovati
$C64 --quiet stop
$C64 rom kernal 251104-04                # Kernal dell'SX-64
$C64 --compact rom                       # ROM utente attive
$C64 --quiet start; $C64 --quiet pause
$C64 --compact info
$C64 --quiet clearRoms; $C64 --quiet stop; $C64 --quiet start   # di nuovo le predefinite
