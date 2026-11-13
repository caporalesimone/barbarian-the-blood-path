#!/bin/sh
# Video deterministico (muto, frame per frame, ffmpeg nel PATH). Va a tempo reale.
set -e; . "$(dirname "$0")/common.sh"
fresh
$C64 --out "$OUT/da-script.mp4" video "$ROOT/examples/scripts/01-ciao.txt" '{"every":2,"scale":2}'   # da file di script
$C64 --out "$OUT/da-loop.mp4"   video "$ROOT/examples/loops/bot-joy.js"   '{"every":2,"scale":1}'   # da ciclo JS
$C64 --out "$OUT/100-frame.mp4" video 100 '{"every":4,"scale":1}'                                  # N fotogrammi
