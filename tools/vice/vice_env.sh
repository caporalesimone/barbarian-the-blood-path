# Ambiente comune degli script di tools/vice/ (13/11). Uso (all'inizio dello script):  source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
#   ROOT   radice del progetto, ricavata dalla posizione di questo file
#   R, RD, VROM, XRUN   da Lab64 (py/vice_env.sh: ROM, opzioni di x64sc, display); LAB64 e' impostata nei suoi container
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
[ -n "${LAB64:-}" ] || { echo "gira nei container di Lab64 (lab64 run ...)"; exit 1; }
. "$LAB64/py/vice_env.sh"
