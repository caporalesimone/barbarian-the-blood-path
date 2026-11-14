# Ambiente comune degli script di tools/vice/ (13/11). Uso (all'inizio dello script):  source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
#   ROOT   radice del progetto, ricavata dalla posizione di questo file
#   (14/11) R, RD, VROM, XRUN vengono da Lab64 (../lab64/py/vice_env.sh: ROM, opzioni di x64sc, display)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAB64="${LAB64:-$(cd "$ROOT/.." && pwd)/lab64}"
. "$LAB64/py/vice_env.sh"
