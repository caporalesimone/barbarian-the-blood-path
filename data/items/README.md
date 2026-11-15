# Item database — `data/items/items.tsv`

Copyright © 2026 - Simone Caporale

The table of **every item** of the game (11/11), in the spirit of the item tables of Diablo
(DevilutionX `assets/txtdata/items/itemdat.tsv`): one row per item, **tab separated**, one column per property, an
**empty cell** = property not used by that type. It is the **starting point to create new items**: add a row, run the
build. Loader and checker: `tools/build/items_db.py` (`python3 tools/build/items_db.py` checks the table and prints it). The tools
read it through `items_db.load_rules()`, which merges the rows into the `data/rules.yaml` sections they always used
(`weapons`, `armors`, `shields`, `rings`, `potions`, `scrolls`, `void_weapons`): `tools/build/gen_db.py` (game data
`out/work/db.asm`), `tools/manual/gen_manual.py` (manual), `tools/simulators/` (balancing). The rules that are not items (durability, `dex_cap`,
`magic_max`, `start_weapon`, where potions drop) stay in `data/rules.yaml`; shops and loot weights in `data/balance.yaml`.

## Categories and types

| Category | Types | Notes |
|---|---|---|
| `consumable` | `potion`, `scroll` | used up: potions in the belt, scrolls in a pack stack (max 10) |
| `equipment` | `weapon`, `armor`, `shield`, `ring` | one slot each (weapon, armor, shield, ring); worn weapons, armors and shields wear out |

## Columns

| Column | Types | Meaning |
|---|---|---|
| `id` | all | identifier (lowercase, `_`): the game constant is `I_<ID>` (`out/work/db.asm`) |
| `category` | all | `consumable` or `equipment` (must match the type) |
| `type` | all | `weapon`, `armor`, `shield`, `ring`, `potion`, `scroll` |
| `name` | all (void: no) | name in the game, English, lowercase; at most 16 characters shown with the prefix/suffix (`gen_db.py` checks) |
| `hands` | weapon | `1` one-handed, `2` **two-handed**: no shield with it (game flag `itfl` bit 0) |
| `dice` | weapon | damage dice `NdS` |
| `rate` | weapon | frames between two basic attacks (Slash cooldown) |
| `pen` | weapon | penetration (−AC of the target) |
| `ac` | armor, shield | armor class bonus |
| `armor_type` | armor | `light`, `medium`, `heavy` (DEX modifier cap: `dex_cap` in `rules.yaml`) |
| `bonus` | ring | +N to the modifier of STR, DEX or CON (chosen when the ring is created) |
| `heal` | potion | healed HP in the dungeon (hero level L <= 20): a number or a formula (`L` = hero level, e.g. `4*L+40`) |
| `heal_abyss` | potion | healed HP in the Abyss (hero level L > 20, floors 21..255, level = floor): same format as `heal` (15/11, TODO J4); `gen_db.py` emits it as `pab_dn` / `pab_val`, read by `pot_heal` when the hero level is above `MAXLEVEL` |
| `cooldown` | potion | frames without any potion after drinking (50 = 1 s) |
| `zone` | potion | drop zone (0, 1, 2: `potions.zones` / `ramp` in `rules.yaml`) |
| `rarity` | potion | `common` (others: future) |
| `color` | potion | C64 colour of the icon |
| `ilvl` | weapon, armor, shield, ring, scroll | item level: lowest loot level where it drops |
| `price` | all in the game | shop price in gold (sell: half) |
| `shop_level` | potion, scroll | lowest hero level to see it in the shop |
| `tier` | all | `base` = in the game; `void` = Abyss weapons (levels 21+), **simulator only** |
| `notes` | all | free text, ignored by the tools |

Row order = item id: the game numbers the items by type (weapons, armors, shields, rings, potions, scrolls) and, inside
a type, in the order of the table (`0` = empty slot; at most 63 items).

## Two-handed weapons

`hands` = 2 sets bit 0 of `itfl`. The game code (`docs/oggetti.md`): in the **inventory** (`src/game/ui.asm`) and in the
**inn** (`src/ovl2.asm`, `h_equip`) a shield cannot be equipped with a two-handed weapon ("two-handed weapon."), and
equipping a two-handed weapon sends the shield back to the pack (or, at the inn, to the chest; refused if there is no
room). In combat a shield does not count and does not wear with a two-handed weapon (`src/game/combat.asm`). Tests:
`INV-2H-10/11`, `INN-2H-10/11`, `ITEMDB-10..12`. Dual wielding (two weapons) is not in the game: TODO.

## Adding an item

1. Add a row (all the columns of its type filled, the others empty). 2. `python3 tools/build/items_db.py` (checker).
3. `./build.sh`: `gen_db.py` checks name lengths, byte ranges, max 63 items. 4. If it can be sold, add it to a shop pool
in `data/balance.yaml`; if it is loot, it drops by `ilvl` and the category weights. 5. Run the balancing simulators
(`docs/balancing-guide.md`) and update `docs/oggetti.md`.
