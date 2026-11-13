#!/bin/sh
# status e abort: controllare e interrompere un job lungo senza pkill.
set -e; . "$(dirname "$0")/common.sh"
fresh
$C64 --compact runFrames 200000 &        # job lungo (≈ 66 minuti di tempo reale)
sleep 3
$C64 --compact status                    # busy, metodo, avanzamento
$C64 --compact abort                     # interrompe il job in corso
wait || true                             # il client del job ha ricevuto ERRORE ABORTED
$C64 --compact status                    # di nuovo libero
