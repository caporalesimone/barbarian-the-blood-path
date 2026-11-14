#!/usr/bin/env python3
"""Item database (11/11): data/items/items.tsv is the source of truth for every item of the game (like the item tables
of Diablo / DevilutionX, assets/txtdata/items/itemdat.tsv). One row per item, tab separated, one column per property;
an empty cell = property not used by that type. Columns and rules: data/items/README.md.

Categories: `consumable` (potion, scroll) and `equipment` (weapon, armor, shield, ring). The row order is the item id in
the game (out/work/db.asm I_*: weapons, armors, shields, rings, potions, scrolls; 0 = empty), rows with tier `void` are the
Abyss weapons (simulator only, not in the game).

load_rules() = data/rules.yaml + the items merged back into the sections the tools always read (weapons, armors,
shields, rings, potions, scrolls, void_weapons), so tools/build/gen_db.py, tools/manual/gen_manual.py and tools/simulators/ see the same dict
as before. Usage: python3 tools/build/items_db.py   (checks the table and prints it)"""
import csv, os, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TSV = os.path.join(ROOT, "data", "items", "items.tsv")

COLUMNS = ["id", "category", "type", "name", "hands", "dice", "rate", "pen", "ac", "armor_type", "bonus", "heal",
           "cooldown", "zone", "rarity", "color", "ilvl", "price", "shop_level", "tier", "notes"]
TYPES = {"weapon": "equipment", "armor": "equipment", "shield": "equipment", "ring": "equipment",
         "potion": "consumable", "scroll": "consumable"}
SECTION = {"weapon": "weapons", "armor": "armors", "shield": "shields", "ring": "rings", "potion": "potions",
           "scroll": "scrolls"}
# columns each type must / may fill (the others must stay empty)
REQUIRED = {"weapon": ["hands", "dice", "rate", "pen", "ilvl"], "armor": ["ac", "armor_type", "ilvl", "name", "price"],
            "shield": ["ac", "ilvl", "name", "price"], "ring": ["bonus", "ilvl", "name", "price"],
            "potion": ["heal", "cooldown", "zone", "rarity", "color", "name", "price", "shop_level"],
            "scroll": ["ilvl", "name", "price", "shop_level"]}
OPTIONAL = {"weapon": ["name", "price"]}
COMMON = ["id", "category", "type", "tier", "notes"]
STRINGS = {"dice", "heal", "rarity", "name", "armor_type"}
RENAME = {"armor_type": "type"}           # key used in rules.yaml (armors: type light/medium/heavy)


def load(path=TSV):
    """The rows of the table as dicts (only the filled cells, typed), in file order. Raises ValueError on a bad table."""
    rows, seen = [], set()
    with open(path, newline="") as f:
        rd = csv.reader(f, delimiter="\t")
        head = next(rd)
        if head != COLUMNS:
            raise ValueError("items.tsv: columns %s, expected %s" % (head, COLUMNS))
        for n, cells in enumerate(rd, 2):
            if not cells or not "".join(cells).strip():
                continue
            if len(cells) != len(COLUMNS):
                raise ValueError("items.tsv line %d: %d cells, expected %d" % (n, len(cells), len(COLUMNS)))
            r = dict(zip(COLUMNS, (c.strip() for c in cells)))
            t = r["type"]
            if t not in TYPES:
                raise ValueError("items.tsv line %d: type '%s'" % (n, t))
            if r["category"] != TYPES[t]:
                raise ValueError("items.tsv line %d: %s is a %s, not %s" % (n, t, TYPES[t], r["category"]))
            if r["id"] in seen:
                raise ValueError("items.tsv line %d: duplicate id %s" % (n, r["id"]))
            seen.add(r["id"])
            if r["tier"] not in ("base", "void"):
                raise ValueError("items.tsv line %d: tier '%s'" % (n, r["tier"]))
            need = REQUIRED[t] + (["name", "price"] if t == "weapon" and r["tier"] == "base" else [])
            for c in need:
                if r[c] == "":
                    raise ValueError("items.tsv line %d (%s): column %s is required for a %s" % (n, r["id"], c, t))
            allowed = set(COMMON + REQUIRED[t] + OPTIONAL.get(t, []))
            for c in COLUMNS:
                if r[c] != "" and c not in allowed:
                    raise ValueError("items.tsv line %d (%s): column %s is not used by a %s" % (n, r["id"], c, t))
            if t == "weapon" and r["hands"] not in ("1", "2"):
                raise ValueError("items.tsv line %d (%s): hands must be 1 or 2" % (n, r["id"]))
            if r["tier"] == "void" and t != "weapon":
                raise ValueError("items.tsv line %d (%s): only weapons in tier void" % (n, r["id"]))
            out = {}
            for c in COLUMNS:
                v = r[c]
                if v == "" or c in ("notes",):
                    continue
                out[c] = v if c in STRINGS or c in COMMON else int(v)
            rows.append(out)
    return rows


def as_rules_entry(r):
    """One row in the rules.yaml shape (what gen_db/sim read): hands 2 -> two_handed: true."""
    e = {}
    for k, v in r.items():
        if k in ("id", "category", "type", "tier", "hands"):
            continue
        e[RENAME.get(k, k)] = v
    if r.get("hands") == 2:
        e["two_handed"] = True
    return e


def merge(R, rows):
    """Put the items into R (rules.yaml dict): sections in the order of the table; the settings that are not items
    (potions: zones, ramp, drink_below) stay after the items, as in the old rules.yaml."""
    for sec in list(SECTION.values()) + ["void_weapons"]:
        extra = {k: v for k, v in (R.get(sec) or {}).items() if not isinstance(v, dict)}
        R[sec] = {}
        R[sec + "_extra"] = extra
    for r in rows:
        sec = "void_weapons" if r["tier"] == "void" else SECTION[r["type"]]
        R[sec][r["id"]] = as_rules_entry(r)
    for sec in list(SECTION.values()) + ["void_weapons"]:
        R[sec].update(R.pop(sec + "_extra"))
    return R


def load_rules(root=ROOT):
    """rules.yaml + oggetti (data/items/items.tsv) + mostri del gioco (data/monsters/bestiary.tsv, 11/11)"""
    R = yaml.safe_load(open(os.path.join(root, "data", "rules.yaml")))
    import bestiary
    bestiary.merge_rules(R, bestiary.load(os.path.join(root, "data", "monsters", "bestiary.tsv")))
    return merge(R, load(os.path.join(root, "data", "items", "items.tsv")))


def can_equip_with(weapon, other_type):
    """Rule of the two-handed weapons (game code: itfl bit 0, docs/oggetti.md): with a two-handed weapon no shield."""
    return not (weapon.get("hands") == 2 and other_type == "shield")


if __name__ == "__main__":
    try:
        rows = load()
    except ValueError as e:
        print("ERROR", e)
        sys.exit(1)
    for r in rows:
        print("%-15s %-10s %-6s %-16s %s" % (r["id"], r["category"], r["type"], r.get("name", "-"),
                                             " ".join("%s=%s" % (k, v) for k, v in r.items()
                                                      if k not in ("id", "category", "type", "name", "tier"))))
    print("%d items (%d in the game, %d void)" % (len(rows), sum(r["tier"] == "base" for r in rows),
                                                  sum(r["tier"] == "void" for r in rows)))
