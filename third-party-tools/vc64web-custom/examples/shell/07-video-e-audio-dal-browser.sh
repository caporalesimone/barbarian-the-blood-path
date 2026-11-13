#!/bin/sh
# Video + audio dal browser (tempo reale, non deterministico). Il core deve essere in marcia.
set -e; . "$(dirname "$0")/common.sh"
$C64 --quiet start; $C64 --quiet resume
# tono SID di prova: volume 15, voce 1 triangolo
$C64 --quiet poke 0xD418 15; $C64 --quiet poke 0xD405 0; $C64 --quiet poke 0xD406 0xF0; $C64 --quiet poke 0xD401 0x20; $C64 --quiet poke 0xD404 0x11
# a) 3 secondi con tastiera e joystick sotto il video, audio amplificato (l'audio del core è molto basso)
$C64 --out "$OUT/grab.webm" --compact grabBrowserVideoAndAudio '{"seconds":3,"keyboard":"below","joy2":"below","audioGain":8}'
# b) avvio e stop separati (nel mezzo puoi usare l'emulatore, anche con "c64 script")
$C64 grabBrowserVideoAndAudio '{"action":"start","joy2":"overlay"}'
$C64 sendText 'print "ciao"\n'; $C64 --quiet sleep 2000
$C64 --out "$OUT/grab2.webm" grabBrowserVideoAndAudio '{"action":"stop"}'
ffmpeg -y -loglevel error -i "$OUT/grab.webm" "$OUT/grab.mp4" && echo "convertito in $OUT/grab.mp4"
