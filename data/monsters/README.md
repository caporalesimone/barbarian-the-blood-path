# Bestiario — `data/monsters/bestiary.tsv`

Copyright © 2026 - Simone Caporale

Un mostro per riga, **tab** come separatore, come `monstdat.tsv` di Diablo/DevilutionX (11/11). Loader e controllo:
`tools/build/bestiary.py` (`python3 tools/build/bestiary.py` stampa i bestiari per capitolo). Nel gioco entrano le righe con
`implemented = yes`, **nell'ordine del file** (base, forti, finale: il tipo del mostro nel codice = posizione): i 9 tipi del
capitolo 1 e i tipi 1–8 dei capitoli con `own_stats` (oggi il 2); le altre sono concept. (24/11) Le statistiche sono
**formule** per piano: `python3 tools/build/mon_stats.py` le controlla e stampa i valori del C64 a ogni piano. Pagina della wiki: [docs/wiki/bestiario.md](../../docs/wiki/bestiario.md).

| Colonna | Significato |
|---|---|
| `id` | identificatore (minuscolo, `_`); per le righe del gioco (capitolo 1) il nome mostrato è l'id con gli spazi |
| `chapter` | capitolo del bestiario (1..; il boss finale sta nell'ultimo capitolo della storia) |
| `tier` | `base`, `strong` (variante potenziata: stesso sprite, altro colore), `boss` (boss di capitolo), `final` (boss finale) |
| `strong_of` | per `strong`: il mostro base dello stesso capitolo |
| `name` | nome per manuale e documenti (inglese). (15/11) In minuscolo è il nome che la barra mostra nel gioco per i mostri dei capitoli 2–4 e per i boss di capitolo: la build controlla che coincida con i disegni (`tools/build/gen_gfx.py`) |
| `floor` | **primo piano** (profondità globale 1..255) in cui compare (`mt_fmin`: spawn) e da cui cresce: `FIRST` nelle formule, P = piano − FIRST |
| `level` | livello del mostro (esperienza e bottino) |
| `hp` | (24/11) formula della vita **media** al piano (il gioco la tira ±25% alla nascita) |
| `dmg` | dadi del colpo + formula del bonus (`1d6 + 2 + P`); il tiro è × `curve_dmg` del piano (`rules.yaml`) |
| `ac`, `att`, `save` | formule di classe armatura, bonus d'attacco, salvezza |
| `xp` | formula dell'esperienza |

**Formule** (24/11, [bestiario](../../docs/wiki/bestiario.md#statistiche-formule-del-bestiario-2411-toolsbuildmon_statspy)):
variabili `L` (piano), `P` (= `L − FIRST`, mai sotto 0), `FIRST` (colonna `floor`), `C` (capitolo del piano), `F` (piano nel
capitolo); `+ − * /`, parentesi, `min`, `max`, `round`; costanti con nome in `constants.yaml`. Nei piani in cui la riga si usa
la formula deve essere lineare (la build lo controlla): il C64 calcola `A + ((B × P + 8) >> 4)` con `A` = valore al primo piano e
`B` = crescita per piano × 16 (precisione 1/16).
| `speed` | velocità (pixel/fotogramma × 4; 8 = normale) |
| `color` | colore C64 dello sprite (0..15); (15/11) per ogni riga con uno sprite nel gioco deve coincidere con il disegno (controllo della build) |
| `loot_level_bonus` | bonus al livello del bottino |
| `flags` | `strong`, `final`, `stun_immune` (immune al blocco da colpo), `chapter_boss` |
| `ai` | comportamento voluto (oggi nel codice: inseguimento e mischia, evocazioni solo per il boss finale) |
| `sprite` | sprite usato (la famiglia: la variante forte usa lo sprite della base con un'aggiunta; `concept` = da disegnare). Dal 15/11 tutti i mostri dei capitoli 1–4 hanno lo sprite nel gioco (`tools/build/monsters.py`, `tools/build/monsters_chap.py`) |
| `implemented` | `yes` = **statistiche** nel gioco (capitolo 1: i tipi 1..9 di `gen_db.py`; capitoli con `own_stats`: i loro tipi 1..8, `tools/build/mon_stats.py`), `no` = statistiche e IA concept. Le righe `no` dei capitoli 3–4 hanno nel gioco sprite, colore e nome, ma usano le statistiche del tipo nella stessa posizione del capitolo 1 |
| `notes` | testo libero |

Aggiungere un mostro al gioco: riga con `implemented = yes` nel posto giusto (base prima dei forti, il finale in fondo),
sprite, `./build.sh`, simulatori (`docs/wiki/balancing-guide.md`), `docs/wiki/mostri.md`.
