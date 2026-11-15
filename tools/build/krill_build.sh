#!/bin/bash
# Costruisce Krill's Loader r194 (src/third-party/krill/loader-v194.zip) con la nostra configurazione
# (src/common/krill/loaderconfig.inc). Tutto in out/work/krill/ (usa e getta, non si tocca src/third-party/). Serve solo cc65, make e
# perl: cc1541 (il programma C che scrive il disco) e' gia' compilato in lab64-tools (dai suoi sorgenti, stage cc1541-build di Lab64).
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
# (15/11, ex TODO A2, docs/FastLoader.md 4.1) correzione del codice del drive 1541 di r194: dopo un caricamento riuscito il drive tiene
# il primo blocco del file seguente nella directory ("prepare next file"); se quel file viene chiesto subito, il blocco si serve
# dalla cache, ma la lunghezza dell'ultimo blocco si calcola da LINKSECTOR41, che e' lo stesso byte ($7F) di TEMP, sporcato
# dall'hash del nome appena ricevuto (gethashval). Un file di un solo blocco caricato dopo il suo predecessore arrivava quindi
# accorciato o allungato (SND0 dopo MENU3: 118 B su 241; MENU3 dopo MENU2: 39 B oltre la fine) senza errore. L'hash usa ora
# PREVBLOCKINDEXPLUS1 ($29): non serve fra la fine di un caricamento e loadfile41, che lo azzera dopo l'hash, e il codice di
# salvataggio (save.s, che chiama findfile41) non lo usa. Stesso codice, due byte cambiati. (Non $74 NUMCONTIGUOUSBLOCKS: e'
# NUMBLOCKS del plugin di salvataggio, azzerato prima di findfile41: i salvataggi scrivevano un file vuoto.)
DC=$L/src/drives/drivecode1541.s
grep -q '^TEMP                   = LINKSECTOR41$' $DC && grep -q '^BLOCKSIZE              = TEMP$' $DC \
  || { echo "krill: drivecode1541.s diverso da r194, correzione TEMP non applicabile"; exit 1; }
sed -i -e 's/^TEMP                   = LINKSECTOR41$/TEMP                   = PREVBLOCKINDEXPLUS1; (barbarian, ex TODO A2) was LINKSECTOR41/' \
       -e 's/^BLOCKSIZE              = TEMP$/BLOCKSIZE              = LINKSECTOR41/' $DC
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
