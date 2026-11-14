#!/bin/bash
# Costruisce Krill's Loader r194 (src/third-party/krill/loader-v194.zip) con la nostra configurazione
# (src/common/krill/loaderconfig.inc). Tutto in out/work/krill/ (usa e getta, non si tocca src/third-party/). Serve solo cc65, make e
# perl: cc1541 (il programma C che scrive il disco) e' gia' compilato in lab64-tools (stage cc1541-build di Lab64).
# Uscite: out/work/krill/install.prg (INSTALL), loader.prg (resident, RESIDENT), save.prg (plugin, TRANSIENT),
#         out/work/krill.inc (simboli per 64tass, tools/build/krill_syms.py).
# Indirizzi (docs/FastLoader.md): ZP $41 (7 B; il plugin arriva a $57 mentre salva), INSTALL $0840 (dentro START, dopo lo stub BASIC),
# RESIDENT $0200, TRANSIENT $E820 (plugin di save: caricato dal file KSAVE a ogni save, sotto il KERNAL fra l'immagine
# del file dell'eroe e il buffer del plugin, src/game/rel.asm)
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ZP=${KRILL_ZP:-41}; INSTALL=${KRILL_INSTALL:-0840}; RESIDENT=${KRILL_RESIDENT:-0200}; TRANSIENT=${KRILL_TRANSIENT:-e820}
D=out/work/krill
rm -rf $D; mkdir -p $D
unzip -q src/third-party/krill/loader-v194.zip -d $D/pkg
L=$D/pkg/loader
mkdir -p $L/build/intermediate
CFG=$(cd src/common/krill && pwd)
( cd $L/src && make -s clean >/dev/null 2>&1; mkdir -p ../build/intermediate
  make -s save EXTCONFIGPATH=$CFG ZP=$ZP INSTALL=$INSTALL RESIDENT=$RESIDENT TRANSIENT=$TRANSIENT > ../../../krill.log 2>&1 ) || { tail -15 $D/krill.log; echo "krill: errore nel make"; exit 1; }
cp $L/build/install-c64.prg $D/install.prg
cp $L/build/loader-c64.prg $D/loader.prg
cp $L/build/save-c64.prg $D/save.prg
cp $L/build/loadersymbols-c64.inc $D/loadersymbols.inc
python3 tools/build/krill_syms.py || exit 1
echo "krill: install $(stat -c %s $D/install.prg) B, resident $(stat -c %s $D/loader.prg) B, save $(stat -c %s $D/save.prg) B"
