# tools/simulators/ — simulatori delle partite

Tutti gli script che simulano il gioco stanno qui e vanno tenuti allineati al codice a ogni cambio di regola
(`CLAUDE.md`). Leggono `data/rules.yaml`, `data/items/items.tsv` (oggetti, via `tools/build/items_db.py`), `data/balance.yaml`
e `data/chapters.yaml` (capitoli).

| Script | Cosa fa |
|---|---|
| `rules.py` | modello condiviso: PG, oggetti, mostri per piano, Abisso |
| `sim_rules.py` | combattimenti Monte Carlo e progressione; report `out/work/simulators/simulazione_regole.html` |
| `fit_rules.py` | taratura automatica di `growth`, `final_boss_hp_mult`, `void.table` (scrive `rules.yaml`) |
| `cmp_rules.py` | confronti fra configurazioni |
| `sim_durability.py` | durabilità generata e vita utile degli oggetti |
| `sim_chest.py` | chestLevel e probabilità di ogni oggetto per piano |
| `sim_gold.py` | oro trovato e valore di vendita per piano (Monte Carlo sul censimento `data/floor_census.json` dei piani veri, fatto da `tools/vice/floor_census.py`), bauli epici, borsello |
| `items_model.py` | (20/11, proposta) modello del database degli oggetti futuro (`data/items/next/`): generazione con qualità, affissi e unici, nome completo, prezzo, controlli dei dati |
| `sim_floor.py` | (20/11) piano intero: il PG di riferimento combatte tutti i mostri del piano (censimento) senza tornare in città, con la cintura a 4 o a 8: morti, ritorni, pozioni bevute (per scegliere la quest della cintura a 8) |
| `sim_purse.py` | (22/11) **borsello**: entrate (oro trovato, vendita) e spese (pozioni bevute, riparazioni) per piano; PG massimo, medio (1/2), prudente (1/3); per gruppi di tetti, ritorni in città per piano dovuti al tetto e passaggi dalla locanda per vendere; report `out/work/simulators/sim_purse.txt` |
| `sim_builds.py` | (20/11) **profili di PG**: gli stessi giri di piano di `sim_floor.py` per più PG (riferimento, forza, destrezza, costituzione, bilanciato) con le regole di oggi e con la **proposta** `data/rules_next.yaml` (4 punti a livello, FOR = danno, DES = colpire, COS = vita/pozioni/danno subito, mostri normalizzati sul bilanciato e spostati dagli obiettivi per piano); report `out/work/simulators/sim_builds.txt` e `.png`; piani senza i boss, metrica ogni 10 mostri, PG a livello piano +0/+1/+2 (`--offsets`), boss di capitolo e finale con e senza meccaniche, `--fit-bosses` (vita dei boss per il 60% del bilanciato); (22/11) `--fit-chapter abbot,...` (vita fissa dei boss dei capitoli di `rules.yaml chapter_bosses` per il 60% del PG di riferimento con le regole di oggi e le meccaniche del gioco); con `gear.mode: next` i profili scelgono fra le basi nuove (`data/items/next/bases.tsv`) coi requisiti in scala nuova (`next_req`) |
| `fit_stats.py` | (20/11) **costi delle caratteristiche** della proposta (`data/rules_next.yaml` `stats`): modello analitico veloce (vita + cintura / (tempo per uccidere × danno subito) contro i mostri del piano) e ricerca su griglia perché forza, destrezza e costituzione valgano quanto il bilanciato meno ~10%; `--show` per i costi attuali; poi verifica con `sim_builds.py` |
| `boss_scripts.py` | (20/11) meccaniche dei boss per `sim_rules.fight(script=...)`: quelle del codice (abate, Mother Stitch, Varok, evocazioni del boss finale) e le proposte del 20/11; numeri in `data/rules_next.yaml` `bosses` |
| `chapters.py` | (11/11) bilanciamento **per capitolo** (`data/chapters.yaml`): per ogni piano del capitolo, alla profondità globale, vittorie del PG di riferimento, chestLevel, oro; boss della mappa finale; Abisso a campione fino al piano 255 (`--chapter N --fights N --step N --csv f`) |

Il codice vero si misura con l'arena (`tools/vice/arena.py` + `src/test/arena.asm`, in VICE). `tests/test_balance.py`
gira sul simulatore a ogni build.
