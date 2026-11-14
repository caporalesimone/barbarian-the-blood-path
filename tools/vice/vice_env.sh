# Ambiente comune degli script di tools/vice/ (13/11, richiesta del committente: niente percorsi assoluti, tutto relativo al progetto).
# Uso (all'inizio dello script):  source "$(dirname "${BASH_SOURCE[0]}")/vice_env.sh"
#   ROOT   radice del progetto, ricavata dalla posizione di questo file (nessun percorso scritto a mano)
#   LAB64  la toolchain (14/11): variabile LAB64 (nei container /lab64) o la cartella accanto al progetto
#   R, RD  cartelle delle ROM: $LAB64/roms/vice-roms/C64 e .../DRIVES
#   VROM   opzioni di x64sc: impostazioni di fabbrica (-default: non conta la configurazione dell'utente) e TUTTE le ROM da roms/ di Lab64
#          (Kernal, Basic, chargen e quelle dei drive): VICE non cerca nulla nella sua cartella dati ne' in /usr/share
# VICE: quello del container lab64-tools (/opt/vice/bin, nel PATH).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAB64="${LAB64:-$(cd "$ROOT/.." && pwd)/lab64}"
R="$LAB64/roms/vice-roms/C64"; RD="$LAB64/roms/vice-roms/DRIVES"
VROM="-default -kernal $R/kernal-901227-03.bin -basic $R/basic-901226-01.bin -chargen $R/chargen-901225-01.bin -dos1541 $RD/dos1541-325302-01+901229-05.bin -dos1541II $RD/dos1541ii-251968-03.bin -dos1570 $RD/dos1570-315090-01.bin -dos1571 $RD/dos1571-310654-05.bin"
# display: un display virtuale per ogni VICE (xvfb-run), oppure lo schermo condiviso del viewer con C64_VIEW=1 (./build.sh --view)
if [ "${C64_VIEW:-0}" = 1 ] && [ -n "${DISPLAY:-}" ]; then XRUN=""; else XRUN="xvfb-run -a"; fi
