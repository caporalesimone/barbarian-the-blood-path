# tools/simulators/ — simulatori delle partite

Tutti gli script che simulano il gioco stanno qui e vanno tenuti allineati al codice a ogni cambio di regola
(`CLAUDE.md`). Leggono `data/rules.yaml`, `data/items/items.tsv` (oggetti, via `tools/build/items_db.py`), `data/balance.yaml`
e `data/chapters.yaml` (capitoli).

| Script | Cosa fa |
|---|---|
| `rules.py` | modello condiviso: PG, oggetti, mostri per piano, Abisso |
| `sim_rules.py` | combattimenti Monte Carlo e progressione; report `out/simulators/simulazione_regole.html` |
| `fit_rules.py` | taratura automatica di `growth`, `final_boss_hp_mult`, `void.table` (scrive `rules.yaml`) |
| `cmp_rules.py` | confronti fra configurazioni |
| `sim_durability.py` | durabilità generata e vita utile degli oggetti |
| `sim_chest.py` | chestLevel e probabilità di ogni oggetto per piano |
| `sim_gold.py` | oro raccoglibile nel dungeon e oro dei bauli epici |
| `chapters.py` | (11/11) bilanciamento **per capitolo** (`data/chapters.yaml`): per ogni piano del capitolo, alla profondità globale, vittorie del PG di riferimento, chestLevel, oro; boss della mappa finale; Abisso a campione fino al piano 255 (`--chapter N --fights N --step N --csv f`) |

Il codice vero si misura con l'arena (`tools/vice/arena.py` + `src/test/arena.asm`, in VICE). `tests/test_balance.py`
gira sul simulatore a ogni build.
