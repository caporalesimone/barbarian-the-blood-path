# Ambiente comune degli script di tools/vice/ (13/11). Uso (all'inizio dello script):  source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
#   ROOT   radice del progetto, ricavata dalla posizione di questo file
#   R, RD, VROM, XRUN   dal comando lab64 (ROM, opzioni di x64sc, display): "lab64 vice-env" stampa la riga che li carica
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
command -v lab64 >/dev/null || { echo "gira nei container di Lab64 (lab64 run ...)"; exit 1; }
eval "$(lab64 vice-env)"
