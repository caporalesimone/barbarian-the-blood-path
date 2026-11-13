#!/bin/sh
# runLoop: logica dentro la pagina, nessuna chiamata HTTP per passo (≈ tempo reale).
set -e; . "$(dirname "$0")/common.sh"
fresh
$C64 --compact runLoop "$(cat "$ROOT/examples/loops/conta-memoria.js")" '{"frames":200}'
$C64 --compact runLoop "$(cat "$ROOT/examples/loops/bot-joy.js")" '{"frames":300,"every":2}'
