# Bilanciamento

Numeri di gioco: `data/rules.yaml` (regole), `data/balance.yaml` (mondo, bottino, negozi), `data/items/items.tsv`
(database degli oggetti, 11/11: [items/README.md](items/README.md)), `data/chapters.yaml` (capitoli, per gli strumenti).

    python3 tools/build/gen_db.py     # balance.yaml -> src/db.asm (lo fa anche ./build.sh)
    ./build.sh                  # assembla out/work/game.prg

- `src/db.asm` e' GENERATO: non modificarlo a mano.
- Il generatore valida i valori (byte 0..255, min<=max, percentuali, ordine mostri,
  armi uniche sempre migliori delle normali, ogni loot_level ha candidati) e si ferma
  con un messaggio "ERRORE balance.yaml: ..." se qualcosa non torna.
- `dungeon_level` = piano corrente (1..max_dungeon_level). Ogni campo
  `per_dungeon_level: k` aggiunge k*(dungeon_level-1); k in passi da 0.125.
- Modificatori del boss in `boss:`; probabilita' in percento.
