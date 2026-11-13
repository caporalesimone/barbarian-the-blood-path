#!/bin/sh
# evento di prova: per N volte, a tempo T (scritto in ms), il fondo dello schermo diventa rosso e parte un tono da 1 kHz
N=${1:-10}; export DISPLAY=:99 PULSE_SERVER=unix:/run/pulse/native
xsetroot -solid black; sleep 2
for i in $(seq $N); do
  T=$(date +%s%3N); xsetroot -solid red & paplay /opt/proto/tone.wav & echo "EVENT $T"; wait
  sleep 0.6; xsetroot -solid black; sleep 1.5
done
