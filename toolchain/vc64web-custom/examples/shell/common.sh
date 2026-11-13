# Variabili comuni degli esempi (si include con:  . "$(dirname "$0")/common.sh").
# Prima serve il demone acceso:   cd headless && node c64d.js &        (porta 7064)
# NODE_PATH: se playwright è installato globalmente:  export NODE_PATH=$(npm root -g)
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
C64="node $ROOT/headless/c64"
OUT=${OUT:-${TMPDIR:-/tmp}/c64-examples-output}   # fuori dal pacchetto
mkdir -p "$OUT"
# riparte da un C64 appena acceso, in pausa (stato noto)
fresh() { $C64 --quiet start; $C64 --quiet reset '{"hard":true}'; $C64 --quiet resume; $C64 --quiet ready >/dev/null; $C64 --quiet pause; }
