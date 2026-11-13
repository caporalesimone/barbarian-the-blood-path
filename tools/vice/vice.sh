#!/bin/bash
# uso: vice.sh <immagine.d64|prg> <cicli> <screenshot.png> [opzioni extra VICE]
IMG=$1; CYC=$2; OUT=$3; shift 3
source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
${XRUN:+$XRUN -s "-screen 0 1024x768x24"} x64sc -silent -sounddev dummy $VROM -warp -limitcycles $CYC -exitscreenshot $OUT -autostart "$IMG" "$@" 2>&1 | tail -5
