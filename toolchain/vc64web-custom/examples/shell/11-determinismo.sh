#!/bin/sh
# Prova di regressione del determinismo (API 24). Bersaglio che LEGGE gli input: programma a $C000 che campiona $DC00
# (joystick 2 + colonne tastiera) in un istogramma a $C100-$C2FF, con il KERNAL attivo (buffer di tastiera a $0277).
# Bot: examples/loops/bot-input.js (joystick tenuto e a durata, tasto tenuto e a durata, carico CPU variabile).
# Esegue N volte normalmente + 2 volte con ripetizioni forzate (_forceRetry, opzione interna di prova): tutti gli hash devono coincidere,
# e l'istogramma deve mostrare che gli input sono arrivati. Uso: 11-determinismo.sh [N=5] [PASSI=300]. Exit 1 se fallisce.
set -e; . "$(dirname "$0")/common.sh"
N=${1:-5}; STEPS=${2:-300}; FR=$((STEPS*2))
fresh
$C64 --quiet poke 0xC000 '[173,0,220,41,31,168,185,0,193,24,105,1,153,0,193,208,239,185,0,194,24,105,1,153,0,194,76,0,192]'
$C64 --quiet setRegs '{"pc":"0xC000"}'; $C64 --quiet runFrames 2; $C64 --quiet saveState det0
BOT=$(cat "$ROOT/examples/loops/bot-input.js")
first=""; fail=0
one() {   # $1 = etichetta, $2 = opzioni runLoop
  $C64 --quiet loadState det0
  r=$($C64 --compact runLoop "$BOT" "$2")
  ex=$(echo "$r" | sed -n 's/.*"exact":\([a-z]*\).*/\1/p'); nr=$(echo "$r" | sed -n 's/.*"retriesTotal":\([0-9]*\).*/\1/p')
  h=$($C64 --compact stateHash | sed -n 's/^{"hash":"\([0-9a-f]*\)".*/\1/p')
  echo "$1: hash=$h exact=$ex ripetizioni=$nr"
  [ -z "$first" ] && first=$h
  [ "$h" = "$first" ] && [ "$ex" = "true" ] || fail=1
}
i=1; while [ $i -le $N ]; do one "run $i" "{\"frames\":$FR,\"every\":2}"; i=$((i+1)); done
one "ripetizione forzata a ogni passo" "{\"frames\":$FR,\"every\":2,\"_forceRetry\":1}"
one "2 ripetizioni ogni 3 passi" "{\"frames\":$FR,\"every\":2,\"_forceRetry\":2,\"_forceEvery\":3}"
vals=$($C64 --compact peek 0xC100 32 | tr -d '[]' | tr ',' '\n' | grep -vc '^0$' || true)
echo "valori diversi di \$DC00 osservati: $vals (atteso > 2: gli input arrivano al bersaglio)"
[ "$vals" -gt 2 ] || fail=1
[ $fail -eq 0 ] && echo "OK: esecuzioni identiche" || { echo "ERRORE: esecuzioni diverse o input non arrivati"; exit 1; }
