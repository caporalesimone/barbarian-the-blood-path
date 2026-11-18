#!/bin/bash
# Crea il d64 del gioco (11/11, regola del committente: una sola build, un solo disco).
# Uso: tools/build/mkdisk.sh [out.d64] [prg]   (default: out/work/disk.d64, out/work/game.zx0)
#   BARBARIAN = loader con il menu (storia / manuale / gioco); POKE 1020,1 prima del RUN = subito START (docs/wiki/cheats.md).
# File: BARBARIAN, START, GAME (ZX0), MENU, FMAP, TWN1..5 (villaggi dei capitoli, con il loro brano in coda),
# GFX1..8 (grafica dei capitoli: dungeon con il brano del capitolo in coda, boss con la mappa del piano del boss in coda;
# tools/build/bundle.py),
# SND0..n (brani, tools/build/gen_music.py), TITLE, LORE, LDAT, HELP, JUKEBOX, HL e SAVE-01..05 (salvataggi, Krill).
# TWN_LAYOUT (variabile d'ambiente, 15/11, TODO M1: posizione dei villaggi sul disco; vedi docs/wiki/FastLoader.md e PERF-DISK-21..25):
#   end     TWN1 fra i primi file; TWN2..TWN5 in fondo, con la grafica dei loro capitoli (come dal 15/11)
#   start   TWN1..TWN5 tutti insieme dove sta TWN1
#   chapter ogni TWNc subito prima di GFX(2c-1), GFX(2c) e BOSSCHc, cosi' quello che un capitolo carica sta vicino (capitolo 1 come
#           in "end"; BOSSCH2 e BOSSCH3 si spostano con il loro capitolo); TWN5 in fondo
#   hub     MENU, SND0 (il brano di ogni villaggio, snd_town_c), TWN1..TWN5 e FMAP uno dopo l'altro (stessi segmenti di directory
#           e stesse tracce di quello che un ingresso nel villaggio carica); il resto come in "end"
#   hubchap (PREDEFINITO dal 15/11 sera: decisione dopo le misure, docs/wiki/FastLoader.md) MENU, SND0, TWN1 e FMAP insieme (come "hub"); TWN2..TWN4 e BOSSCH2/3 con la grafica dei loro capitoli e TWN5 in fondo (come "chapter")
# Provare un layout senza lasciare la build normale: lab64 run env TWN_LAYOUT=start tools/build/mkdisk.sh
TWN_LAYOUT=${TWN_LAYOUT:-hubchap}
case $TWN_LAYOUT in end|start|chapter|hub|hubchap) ;; *) echo "mkdisk: TWN_LAYOUT=$TWN_LAYOUT sconosciuto (end|start|chapter|hub|hubchap)"; exit 1;; esac
# (11/11, ramo fast-loader) disco scritto con cc1541 (14/11: 4.2 di Lab64, compilato dai sorgenti): nomi con hash a 8 caratteri.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
OUT=${1:-out/work/disk.d64}; PRG=${2:-out/work/game.zx0}     # GAME compresso ZX0 (tools/build/pack.py)
rm -f "$OUT"
BRB=out/work/barbarian.prg
# (18/11, revisione dei file, docs/wiki/FastLoader.md 7.3) TWNc e GFXn con la coda (brano del luogo o mappa del boss): out/work/bundle/
python3 tools/build/bundle.py > out/work/bundle.log || { cat out/work/bundle.log; echo "mkdisk: errore delle code (bundle.py)"; exit 1; }
# (11/11, ramo fast-loader) salvataggi per Krill: file gia' presenti con la lunghezza giusta (il plugin di save
# riscrive solo file esistenti con lo stesso numero di blocchi): hl (elenco eroi) e save-01..05 (un file per eroe)
python3 - <<'PY' || { echo "mkdisk: errore file dei salvataggi"; exit 1; }
import re
lb = open("out/work/game.lbl").read()
g = lambda n: (lambda v: int(v[1:], 16) if v[0] == "$" else int(v))(re.search(r"^%s\s*=\s*(\$?[0-9a-f]+)" % n, lb, re.M).group(1))
sv, hl = g("SV_LEN"), g("HDR_LEN")
open("out/work/hl.prg", "wb").write(bytes([0, 0, g("SAVE_VER")]) + bytes(hl - 1))     # elenco vuoto della versione attuale
open("out/work/save.prg", "wb").write(bytes([0, 0xe0]) + bytes(sv))
PY
# cc1541 (nel PATH di lab64-tools: 4.2, compilato dai sorgenti nella build dell'immagine, build-scripts/sources.conf di Lab64): -M 8 = FILENAME_MAXLENGTH del loader (hash dei nomi); BARBARIAN primo (LOAD"*",8)
CC=cc1541
command -v $CC >/dev/null || { echo "mkdisk: manca cc1541: gira nel container lab64-tools (lab64 run ...)"; exit 1; }
# (14/11) -S 4 = interleave dei settori 4 (quello dei benchmark di Krill): con cc1541 4.2 l'interleave predefinito (10) dava il MENU
# in 3,23 s (limite 3,1 s, PERF-DISK-11); con 4 misurato: avvio 14,2 -> 11,4 s, MENU 3,23 -> 2,64 s, villaggio 5,0 -> 3,6 s.
# I file caricati dal KERNAL (BARBARIAN, START, LORE, HELP) misurati con LOAD: stessi tempi con 10 e con 4 (entro 0,1 s).
ARGS=(-S 4 -M 8 -n "blood path" -i "bp" -f barbarian -w $BRB -f start -w out/work/start.prg -f game -w "$PRG" -f lobby -w out/work/lobby.prg
      -f menu -w out/work/menu.prg)       # (18/11) modulo MENU: un file solo (prima menu1..menu5, tools/build/pack_menu.py)
HUB=0; case $TWN_LAYOUT in hub|hubchap) HUB=1;; esac     # HUB=1: il brano del villaggio (SND0) e i villaggi subito dopo MENU
[ $HUB = 1 ] && ARGS+=(-f snd0 -w out/work/snd/snd0.prg -f twn1 -w out/work/bundle/twn1.prg)
[ $TWN_LAYOUT = hub ] && ARGS+=(-f twn2 -w out/work/bundle/twn2.prg -f twn3 -w out/work/bundle/twn3.prg -f twn4 -w out/work/bundle/twn4.prg -f twn5 -w out/work/bundle/twn5.prg)
ARGS+=(-f fmap -w out/work/fmap.prg)
TW="1"; [ $TWN_LAYOUT = start ] && TW="1 2 3 4 5"; [ $HUB = 1 ] && TW=""
for c in $TW; do ARGS+=(-f twn$c -w out/work/bundle/twn$c.prg); done     # (15/11) villaggi dei capitoli, ognuno con tile, mappa e colori suoi (tools/build/villages.py): qui il capitolo 1, gli altri in fondo (5 = la citta' dell'Abisso, prototipo)
# (18/11) niente piu' BOSSCH1..3: la mappa del piano del boss sta nella coda di GFX(2c) (tools/build/bundle.py)
for f in out/work/bundle/gfx[12].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done     # capitolo 1: dungeon e boss (i file dei capitoli 2-4 in fondo al disco: lasciano ai file usati spesso le tracce di prima)
for f in out/work/snd/snd*.prg; do n=$(basename $f .prg); [ $HUB = 1 ] && [ $n = snd0 ] && continue; ARGS+=(-f $n -w $f); done     # brani (tools/build/gen_music.py)
ARGS+=(-f title -w out/work/title.prg -f lore -w out/work/lore.prg -f ldat -w out/work/ldat.prg -f help -w out/work/helpz.prg -f jukebox -w out/work/jukebox.prg)
ARGS+=(-f hl -w out/work/hl.prg -f ksave -w out/work/krill/save.prg)     # ksave: plugin di save di Krill, ricaricato a ogni save
for s in 1 2 3 4 5; do ARGS+=(-f save-0$s -w out/work/save.prg); done
# (18/11, PERF-12, docs/wiki/FastLoader.md 7.2) Krill cerca un file in una finestra di 11 voci della directory e, se non c'e',
# legge i settori della directory successivi in giro (solo in avanti). Dopo un salvataggio la finestra sta sui file di
# salvataggio: per la prima discesa nel piano 1 serve GFX1, che sta prima. Una voce in piu' (loop file di cc1541,
# stessi dati) subito dopo save-05 lo fa trovare senza fare il giro: villaggio -> piano 1 dopo un salvataggio 6,0 -> 3,8 s.
# Al suo posto prima c'erano QST0 e QST1, spostate in fondo. (18/11 pomeriggio) 50 voci: niente BOSSCHc (coda di GFX(2c)).
ARGS+=(-m -N -f gfx1 -l gfx1)      # (18/11 pomeriggio) senza la voce doppia di SND1: il brano del capitolo sta nella coda di GFX1
                                    # (tools/build/bundle.py); misurato: somma dei tempi 76,2 -> 73,6 s, nessun test fuori
# (17/11) menu dei trucchi: solo debug e test (asm.sh lo toglie in release). (18/11) in release al suo posto una voce in piu'
# di hl (loop file): la directory ha le stesse voci nelle stesse posizioni, quindi gli stessi tempi di debug.
if [ -f out/work/cheats.prg ]; then ARGS+=(-f cheats -w out/work/cheats.prg); else ARGS+=(-N -f hl -l hl); fi
case $TWN_LAYOUT in
  end)     for c in 2 3 4 5; do ARGS+=(-f twn$c -w out/work/bundle/twn$c.prg); done     # villaggi dei capitoli 2-5: in fondo, con la grafica dei loro capitoli (i file del capitolo 1 restano sulle prime tracce)
           for f in out/work/bundle/gfx[3-9].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done ;;     # capitoli 2-4 (segnaposto)
  hub)     for f in out/work/bundle/gfx[3-9].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done ;;
  start)   for f in out/work/bundle/gfx[3-9].prg; do n=$(basename $f .prg); ARGS+=(-f $n -w $f); done ;;
  chapter|hubchap) for c in 2 3; do ARGS+=(-f twn$c -w out/work/bundle/twn$c.prg
                                   -f gfx$((2*c-1)) -w out/work/bundle/gfx$((2*c-1)).prg -f gfx$((2*c)) -w out/work/bundle/gfx$((2*c)).prg); done
           ARGS+=(-f twn4 -w out/work/bundle/twn4.prg -f gfx7 -w out/work/bundle/gfx7.prg -f gfx8 -w out/work/bundle/gfx8.prg
                  -f twn5 -w out/work/bundle/twn5.prg) ;;
esac
# (18/11) le quest QST2..QST8 (piu' quest, tools/build/gen_quests.py) in fondo al disco: si leggono di rado (dettaglio di una
# quest) e cosi' non spostano i file dei capitoli 2-5 (PERF-DISK)
for f in out/work/qst[2-9].prg; do [ -f "$f" ] && ARGS+=(-f $(basename $f .prg) -w $f); done
for f in out/work/qst[01].prg; do [ -f "$f" ] && ARGS+=(-f $(basename $f .prg) -w $f); done     # (17/11) elenco delle quest; (18/11) in fondo (vedi le voci in piu' dopo save-05)
$CC "${ARGS[@]}" "$OUT" > out/work/mkdisk.log 2>&1 || { cat out/work/mkdisk.log; echo "mkdisk: errore cc1541"; exit 1; }
# (18/11) catena della directory con interleave 2 (cc1541 la scrive con 3): Krill legge i settori della directory uno dopo
# l'altro e con 2 ne trova uno ogni ~21 ms invece di ~32 ms; misurato: 0,1-0,6 s in meno su quasi tutti i caricamenti
# (PERF-DISK), nessuno piu' lento. Con 1 Krill non fa in tempo e perde un giro a settore (piu' lento di 3).
python3 tools/build/d64_dirilv.py "$OUT" ${DIR_ILV:-2} >> out/work/mkdisk.log || { echo "mkdisk: errore catena della directory"; exit 1; }
