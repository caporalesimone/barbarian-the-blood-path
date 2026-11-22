#!/usr/bin/env python3
"""Model of the item database (20/11; the game uses it since 21/11, uniques since 22/11): bases, prefixes, suffixes and uniques of
data/items/next/, rules of data/items/next/affix_rules.yaml (owner's decisions O1-O14, E3: docs/wiki/oggetti.md, "Progetto:
affissi, unici e memoria"). Used by the simulators to tune the numbers before the game code exists (fase 2 of the quest plan).

  unique_roll(rng, cat, level) -> a row of uniques.tsv or None (the game's un_roll)
  gen_item(rng, cl, cat=None)  -> dict: base, quality (normal/magic/unique/cursed), prefix/suffix (row, value), price, sell
  full_name(item)              -> "warrior's morning star of the craft"
  check()                      -> list of problems (names too long, values over a byte, missing rows): used by ITEMDB-NEXT-10

Command line: python3 tools/simulators/items_model.py [--level L] [--n N]   (N items born at item level L: share of
qualities, mean price, examples)."""
import argparse, csv, os, random
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NEXT = os.path.join(ROOT, "data", "items", "next")


def _rows(name):
    return list(csv.DictReader(open(os.path.join(NEXT, name)), delimiter="\t"))


_INT = {}


def _int(v, d=0):
    # (22/11) cached: the simulators call it tens of millions of times on the same few strings of the .tsv files
    try:
        return _INT[(v, d)]
    except (KeyError, TypeError):
        r = int(v) if str(v).strip() not in ("", "None") else d
        try:
            _INT[(v, d)] = r
        except TypeError:
            pass
        return r


RULES = yaml.safe_load(open(os.path.join(NEXT, "affix_rules.yaml")))
BASES = _rows("bases.tsv")
PREFIXES = _rows("prefixes.tsv")
SUFFIXES = _rows("suffixes.tsv")
UNIQUES = _rows("uniques.tsv")
BY_ID = {b["id"]: b for b in BASES}
SELL_DIV = yaml.safe_load(open(os.path.join(ROOT, "data", "balance.yaml")))["shop_rules"].get("sell_divisor", 2)
CATS = ["weapon", "armor", "shield", "ring"]
# (22/11, phase 6) chance of a unique as the game's un_roll: UN_T / 256 (gen_db.py: pct256(100 / unique_one_in))
UN_T = min(255, round(100 / RULES["quality"]["unique_one_in"] * 256 / 100))
CURSED_POWERS = None        # a row with a negative value is cursed


def scale(level):
    v = RULES["value"]
    return 1.0 if level <= v["scale_from"] else 1.0 + v["per_level"] * (level - v["scale_from"])


def roll_value(rng, row, level):
    a, b = _int(row["value1"]), _int(row["value2"])
    if row["power"] == "INDESTRUCTIBLE":
        return 1
    v = rng.randint(min(a, b), max(a, b))
    s = 1.0 if row["power"] in RULES["value"]["no_scale"] else scale(level)
    out = round(v * s)
    return max(-RULES["value"]["max"], min(RULES["value"]["max"], out))


def eligible(rows, cat, level):
    ok = [r for r in rows if cat in r["item_types"].split(",") and _int(r["min_level"]) <= level]
    lo = min(level, RULES["affix_choice"]["top_level"]) * RULES["affix_choice"]["low_fraction"]
    cursed = lambda r: _int(r["value1"]) < 0
    win = [r for r in ok if _int(r["min_level"]) >= lo or (RULES["affix_choice"].get("cursed_any_level") and cursed(r))]
    return win or ok


_ELIG = {}


def eligible_all(rows, cat, level):
    # (22/11) cached by table, category and level: the tables never change (the result is a shared list: do not modify it)
    k = (id(rows), cat, level)
    if k not in _ELIG:
        _ELIG[k] = [r for r in rows if cat in r["item_types"].split(",") and _int(r["min_level"]) <= level]
    return _ELIG[k]


def pick(rng, rows):
    # (21/11 evening, phase 4) life leech and thorns come after 2.0 (O5): weight 0 in the game (gen_db.py), here too
    rows = [r for r in rows if r["power"] not in ("LEECH", "THORNS")]
    w = [_int(r["chance"], 1) for r in rows]
    return rng.choices(rows, weights=w)[0] if rows else None


_SETS = {}


def _sets(k, c, level, top):
    """(22/11, cached) the row lists of affix_roll for one affix kind, category, item level and 'gold ring prefix'"""
    key = (k, c, level, top)
    if key not in _SETS:
        allr = eligible_all(PREFIXES if k == "prefix" else SUFFIXES, c, level)
        lo = min(level, RULES["affix_choice"]["top_level"]) * RULES["affix_choice"]["low_fraction"]
        cur = [r for r in allr if _int(r["value1"]) < 0]
        pos = [r for r in allr if _int(r["value1"]) >= 0]
        win = [r for r in pos if _int(r["min_level"]) >= lo]
        if top and win:
            mx = max(_int(r["min_level"]) for r in win)
            win = [r for r in win if _int(r["min_level"]) == mx]
            pos = [r for r in pos if _int(r["min_level"]) == mx]
        _SETS[key] = (cur, win or pos)
    return _SETS[key]


def base_for(cat, level):
    """the best base of the category with ilvl <= level (like lt_scan); None if none"""
    c = [b for b in BASES if b["type"] == cat and _int(b["ilvl"]) <= level]
    return max(c, key=lambda b: _int(b["ilvl"])) if c else None


def price(item):
    p = _int(BY_ID[item["base"]]["price"]) if item["quality"] != "unique" else _int(item["unique"]["price"])
    for k in ("prefix", "suffix"):
        if item.get(k):
            row, val = item[k]
            ref = _int(row["value1"]) or 1
            # (21/11 evening, as the game's it_cost) price_add with its sign: a cursed row (negative price_add) costs less
            p += round(_int(row["price_add"]) * (abs(val) / abs(ref) if row["power"] != "INDESTRUCTIBLE" else 1))
    return max(1, p)


def gen_item(rng, cl, cat=None, level=None):
    """an item born from a chest of level cl (T = cl / 8, L = round(T u^2) as gen_item); cat forces the category"""
    t = cl // 8
    level = level if level is not None else min(20 if t <= 20 else t, round(t * (rng.random() ** 2)))
    q = RULES["quality"]
    while True:
        c = cat or rng.choices(CATS, weights=[34, 20, 16, 10])[0]
        b = base_for(c, level)
        if b:
            break
        if cat:
            return None
    item = {"base": b["id"], "cat": c, "level": level, "quality": "normal", "prefix": None, "suffix": None}
    # unique inside its window
    u = unique_roll(rng, c, level)
    if u:
        item.update(base=u["base"], quality="unique", unique=u)
        item["price"] = price(item)
        item["sell"] = item["price"] // SELL_DIV
        return item
    for k, v in affix_roll(rng, c, b["id"], level, t).items():
        item[k] = v
    if item["prefix"] or item["suffix"]:
        neg = any(v < 0 for _, v in filter(None, (item["prefix"], item["suffix"])))
        item["quality"] = "cursed" if neg else "magic"
    item["price"] = price(item)
    item["sell"] = item["price"] // SELL_DIV
    return item



def affix_roll(rng, cat, base_id, level, t, force_magic=False):
    """(21/11 evening) the affixes of a new item as the game's af_gen: {"prefix": (row, value) or None, "suffix": ...}.
    t = chestLevel / 8 (magic chance), force_magic = shop magic item. Used by gen_item and by sim_chest / sim_gold"""
    q = RULES["quality"]
    item = {"prefix": None, "suffix": None}
    c = cat
    b = {"id": base_id}
    pm = min(q["magic"]["max"], q["magic"]["base"] + q["magic"]["per_t"] * t)
    if c == "ring":
        n = RULES["rings"][b["id"]] if b["id"] in RULES["rings"] else 1
        want = ["prefix", "suffix"] if n == 2 else [rng.choice(["prefix", "suffix"])]
    elif force_magic or rng.randrange(100) < pm:
        r = rng.randrange(100)
        a = q["affixes"]
        want = ["prefix"] if r < a["prefix"] else ["suffix"] if r < a["prefix"] + a["suffix"] else ["prefix", "suffix"]
    else:
        want = []
    for k in want:
        # (21/11 evening) the same steps as the game (src/game/combat.asm af_pick): cursed first with cursed_share %, else the
        # normal rows inside the window (none: without the window); no cursed row fits: a normal one; gold ring prefix: only
        # the rows of the highest min_level inside the window
        top = b["id"] == "gold" and k == "prefix"
        cur, good = _sets(k, c, level, top)
        cursed = not top and rng.randrange(100) < RULES["affix_choice"]["cursed_share"]
        row = pick(rng, cur) if cursed and cur else pick(rng, good)
        if row:
            item[k] = (row, roll_value(rng, row, level))
    return item


_UWIN = {}


def unique_roll(rng, cat, level):
    """(22/11, phase 6) the game's un_roll (af_gen, not in the shops): if a unique of category cat has level in its window,
    with probability UN_T / 256 one of them at random (its row of uniques.tsv), else None"""
    k = (cat, level)
    if k not in _UWIN:
        _UWIN[k] = [u for u in UNIQUES if BY_ID[u["base"]]["type"] == cat and _int(u["min_level"]) <= level <= _int(u["max_level"])]
    wins = _UWIN[k]
    if wins and rng.randrange(256) < UN_T:
        return rng.choice(wins)
    return None


def affix_price(aff):
    """price added by the affixes {"prefix": (row, value), ...} (it_cost: price_add with its sign)"""
    p = 0
    for k in ("prefix", "suffix"):
        if aff.get(k):
            p += _int(aff[k][0]["price_add"])
    return p

def full_name(item):
    if item["quality"] == "unique":
        return item["unique"]["name"]
    n = BY_ID[item["base"]]["name"]
    if item.get("prefix"):
        n = item["prefix"][0]["name"] + " " + n
    if item.get("suffix"):
        n = n + " " + item["suffix"][0]["name"]
    return n


def check():
    """problems of the data: names (O8), values in a byte up to level 255 (O10), references"""
    bad = []
    mx = RULES["names"]["max_full"]
    for b in BASES:
        for p in [None] + [r for r in PREFIXES if b["type"] in r["item_types"].split(",")]:
            for s in [None] + [r for r in SUFFIXES if b["type"] in r["item_types"].split(",")]:
                n = " ".join(x for x in ((p or {}).get("name"), b["name"], (s or {}).get("name")) if x)
                if len(n) > mx:
                    bad.append("name over %d: %s (%d)" % (mx, n, len(n)))
    for u in UNIQUES:
        if len(u["name"]) > RULES["names"]["max_unique"]:
            bad.append("unique name over %d: %s" % (RULES["names"]["max_unique"], u["name"]))
        if u["base"] not in BY_ID:
            bad.append("unique %s: unknown base %s" % (u["name"], u["base"]))
        if not _int(u["min_level"]) <= _int(u["max_level"]):
            bad.append("unique %s: empty window" % u["name"])
    for r in PREFIXES + SUFFIXES:
        if r["power"] == "INDESTRUCTIBLE":
            continue
        top = max(abs(_int(r["value1"])), abs(_int(r["value2"])))
        s = 1.0 if r["power"] in RULES["value"]["no_scale"] else scale(RULES["value"]["check_level"])
        if top * s > RULES["value"]["max"]:
            bad.append("affix %s: value %d x %.1f over %d before level %d" % (r["name"], top, s, RULES["value"]["max"],
                                                                             RULES["value"]["check_level"]))
    if len(PREFIXES) > 31 or len(SUFFIXES) > 63:
        bad.append("too many affixes for the item record (prefix id 5 bits, suffix id 6 bits)")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, default=10)
    ap.add_argument("--n", type=int, default=5000)
    a = ap.parse_args()
    rng = random.Random(20)
    items = [gen_item(rng, a.level * 8, level=a.level) for _ in range(a.n)]
    items = [i for i in items if i]
    from collections import Counter
    c = Counter(i["quality"] for i in items)
    print("item level %d, %d items: %s" % (a.level, len(items), ", ".join("%s %.1f%%" % (k, 100 * v / len(items)) for k, v in c.items())))
    print("mean price %.0f, mean sale %.0f" % (sum(i["price"] for i in items) / len(items), sum(i["sell"] for i in items) / len(items)))
    for i in items[:12]:
        print("  %-40s %-7s %5d" % (full_name(i), i["quality"], i["price"]))
    p = check()
    print("check: %s" % ("ok" if not p else "; ".join(p[:5]) + (" (+%d)" % (len(p) - 5) if len(p) > 5 else "")))


if __name__ == "__main__":
    main()
