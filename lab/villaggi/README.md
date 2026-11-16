# lab/villaggi — concept dei villaggi dei capitoli (15/11, TODO Z2)

Copyright © 2026 - Simone Caporale

La build **non usa** questa cartella. I villaggi del gioco stanno in `tools/build/vilN_*.py` (tile, colori) e in
`data/town_mapN.txt` (mappe); come sono fatti: `docs/wiki/villaggio.md`.

| File | Contenuto |
|---|---|
| `concept_maps.py` | genera la **prima stesura** delle mappe dei villaggi 2–5 (`data/town_map2.txt` … `town_map5.txt`): una funzione per villaggio. Rilanciarlo **riscrive** i testi: dopo un ritocco a mano non va più usato per quel villaggio. `python3 lab/villaggi/concept_maps.py [capitolo ...]` (nel container: `lab64 run python3 ...`) |
| `mapkit.py` | attrezzi dello script: griglia 48 × 48, macchie, passaggi, arredi sparsi, controlli (tutto raggiungibile) e scrittura del testo con la legenda del villaggio |
| `proposta-a-temi/` | **proposta scartata, da valutare** (vedi sotto) |

## `proposta-a-temi/`: la prima proposta (scartata dal committente il 15/11)

Prima stesura dei villaggi 2–5: **la struttura del villaggio 1** (strade, piazza con la fontana, fiume con i ponti, case, cripta)
con **tile ridisegnati a tema** e altri colori: palude, neve, rovine, Abisso. Il committente: "I villaggi devono essere diversi,
non lo stesso villaggio con temi diversi […] non riusare la fontana o il fiume in tutti i casi"; "non mettere una cripta a
ogni villaggio". Il lavoro è conservato qui per poterlo valutare; non è collegato alla build e **non funziona più così com'è**
(usa il formato di prima: `theme_tile`, lettere e controlli del 15/11 mattina).

| File | Contenuto |
|---|---|
| `temi.py` | i tile a tema (palude, neve, rovine, Abisso) e le tavolozze |
| `concept_maps.py` | lo script che generava le quattro mappe |
| `town_map2.txt` … `town_map5.txt` | le mappe |
| `twn2_map.png` … `twn5_map.png` | anteprime delle mappe intere |
| `twn2_tiles.png` … `twn5_tiles.png` | i 45 tile di ogni tema |

Cosa se ne può riusare: i disegni di alcuni tile (abete, salice, masso, ghiaccio, lava, cristalli) e le tavolozze.
