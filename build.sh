#!/bin/sh
# Build e test di "Barbarian: The Blood Path" (13/11: tutto nei container Docker; sull'host servono solo sh, Docker, git e curl).
#   ./build.sh               TUTTO: disco + mappe RAM/disco + atlante + smoke e sanity + manuale PDF (lab64-pdf-gen)
#   ./build.sh --fast        solo il disco (salta atlante, mappe e manuale); smoke e sanity restano
#   ./build.sh --no-atlas    salta l'atlante grafico         --no-maps    salta le mappe della RAM e del disco
#   ./build.sh --no-manual   salta il manuale PDF            --no-test    salta smoke e sanity
#   ./build.sh --release     build completa + tutti i test (anche regression ed EMU-*, con la sonda: --probe) + manuale + tools/build/release.sh
#   ./build.sh --emu         i test con il demone vc64web acceso (test EMU-*: lab64 test regression -k EMU)
#   ./build.sh --view        i test aprono VICE sullo schermo del viewer: http://localhost:6080 (lab64-viewer); se il viewer e'
#                            gia' acceso lo fanno da soli (14/11), salvo --no-view
#   ./build.sh --no-view     i test su display virtuali anche con il viewer acceso
#   ./build.sh --probe       (14/11) sonda della memoria in VICE: RAM riempita con uno schema dopo il boot, salvata alla fine di ogni
#                            sessione dei test; la mappa automatica (memmap di Lab64) aggiunge la memoria scritta davvero
#   ./build.sh --manual      SOLO il manuale PDF (lab64-pdf-gen), senza rifare il disco
#   ./build.sh --images      rifa' tutte le immagini Docker di Lab64 (poi la build)
#   ./build.sh --keep N      quante versioni tenere in out/releases/ (default 5, KEEP_VERSIONS nell'ambiente)
# I flag si combinano (es. --fast --no-test = solo il disco). Gli artefatti di ogni build (disco, atlante, mappe, report dei
# test, manuale) finiscono in out/releases/v<versione>/ con manifest.json (tools/build/publish.py); out/releases/latest e' l'ultima.
# Toolchain: Lab64 (repository a parte), usato SOLO con il suo comando "lab64" (nel PATH: lab64 install, docs/getting-started.md);
# il gioco non sa dove sta Lab64. Le immagini mancanti si costruiscono da sole; i programmi esterni (VICE, zx0, cc1541) si
# compilano dentro le immagini. Prima volta su un computer nuovo: lab64 check-env. Configurazione di Lab64 per il gioco: lab64.env.
# Si lancia anche come "lab64 build [flag]" (C64_BUILD in lab64.env).
# Stato dal vivo (14/11, per la pagina del viewer): out/tmp/build.json (fase, esito), out/tmp/tests.json (lab64 test).
# Copyright (c) 2026 - Simone Caporale
set -eu
cd "$(dirname "$0")"
FLAGS="$*"; PROBE=0; REL=0; NOTEST=0; EMU=0; VIEW=0; NOVIEW=0; MANUAL=0; IMAGES=0; KEEP=${KEEP_VERSIONS:-5}; ATLAS=1; MAPS=1; MANUALDEF=1
while [ $# -gt 0 ]; do
    case "$1" in --release) REL=1; EMU=1; PROBE=1 ;; --no-test) NOTEST=1 ;; --emu) EMU=1 ;; --view) VIEW=1 ;; --no-view) NOVIEW=1 ;; --manual) MANUAL=1 ;; --probe) PROBE=1 ;;
                 --images) IMAGES=1 ;; --fast) ATLAS=0; MAPS=0; MANUALDEF=0 ;; --no-atlas) ATLAS=0 ;; --no-maps) MAPS=0 ;;
                 --no-manual) MANUALDEF=0 ;; --keep) shift; KEEP=${1:-}; case "$KEEP" in ''|*[!0-9]*|0) echo "--keep N: intero >= 1"; exit 1 ;; esac ;;
                 *) sed -n 2,24p "$0"; exit 1 ;; esac
    shift
done
[ $PROBE = 1 ] && MAPS=1 && NOTEST=0                 # la sonda serve alla mappa e gira nei test
# stato dal vivo per la pagina del viewer: out/tmp/build.json (scrittura atomica: file temporaneo + mv)
T0=$(date +%s); PHASE=avvio
status() {
    mkdir -p out/tmp
    printf '{"state":"%s","phase":"%s","flags":"%s","started":%s,"updated":%s}\n' "$1" "$PHASE" "$FLAGS" "$T0" "$(date +%s)" \
        > out/tmp/build.json.tmp && mv out/tmp/build.json.tmp out/tmp/build.json
}
phase() { PHASE=$1; status running; }
cleanup() { [ $EMU = 1 ] && lab64 down vc64web >/dev/null 2>&1 || true; }
on_exit() { rc=$?; cleanup; if [ $rc = 0 ]; then PHASE=fine; status ok; else status fail; fi; }
trap on_exit EXIT
trap 'exit 130' INT TERM
phase avvio
command -v lab64 >/dev/null || { echo "comando lab64 non trovato: installare Lab64 (<cartella di lab64>/bin/lab64 install)"; exit 1; }
command -v docker >/dev/null || { echo "Docker non trovato: lab64 check-env"; exit 1; }
docker info >/dev/null 2>&1 || { echo "il demone Docker non risponde: lab64 check-env"; exit 1; }
phase immagini
if [ $IMAGES = 1 ]; then lab64 images --force; fi
lab64 images tools
export RELEASE=$REL BUILD_ATLAS=$ATLAS BUILD_MAPS=$MAPS
[ $REL = 1 ] && export ZX0_BEST=1          # release: GAME compresso in modo ottimo (tools/build/pack.py)

if [ $MANUAL = 1 ]; then
    phase manuale
    lab64 manual
    lab64 run python3 tools/build/publish.py --keep "$KEEP" --only-manual; exit 0
fi

phase build
TB=$(date +%s)
lab64 run tools/build/build_game.sh
PUB="--keep $KEEP --build-seconds $(( $(date +%s) - TB ))"
[ $ATLAS = 1 ] && PUB="$PUB --atlas"
[ $MAPS = 1 ] && PUB="$PUB --maps"
if [ $NOTEST = 1 ]; then
    phase pubblicazione
    # shellcheck disable=SC2086
    lab64 run python3 tools/build/publish.py $PUB; exit 0
fi

# --- servizi per i test: demone vc64web (lab64 up: "lab64 run" lo raggiunge da solo), schermo del viewer (C64_VIEW=1)
phase test
[ $EMU = 1 ] && lab64 up vc64web
# viewer gia' acceso: i test si vedono sullo schermo dal vivo senza chiederlo (salvo --no-view)
[ $NOVIEW = 0 ] && [ -n "$(docker ps -q -f name=^lab64-viewer$)" ] && VIEW=1
if [ $VIEW = 1 ] && [ $NOVIEW = 0 ]; then export C64_VIEW=1; else export C64_VIEW=0; fi
if [ $PROBE = 1 ]; then rm -rf out/work/memprobe; export C64_MEMPROBE=1; fi
lab64 run tests/run_tests.sh
if [ $PROBE = 1 ]; then                    # mappa automatica di nuovo, con i dump della sonda (out/work/memprobe/)
    phase mappa
    lab64 map
fi

PUB="$PUB --tests"
if [ $REL = 1 ] || [ $MANUALDEF = 1 ]; then
    phase manuale
    if [ $REL = 1 ]; then lab64 manual --strict; else lab64 manual; fi   # release: pagina che trabocca = errore
    PUB="$PUB --manual"
fi
if [ $REL = 1 ]; then
    phase release
    lab64 run tools/build/release.sh
    PUB="$PUB --release --maps"          # release.sh rifa' sempre le mappe (RELEASE=1)
fi
phase pubblicazione
# shellcheck disable=SC2086
lab64 run python3 tools/build/publish.py $PUB
echo "== build OK =="
[ $REL = 1 ] || echo "   (test: smoke + sanity; tutti i test con ./build.sh --release; build veloce: ./build.sh --fast)"
