#!/usr/bin/env python3
"""Model of the next item database (20/11, PROPOSAL: the game does not use it yet): bases, prefixes, suffixes and uniques of
data/items/next/, rules of data/items/next/affix_rules.yaml (owner's decisions O1-O14, E3: docs/wiki/oggetti.md, "Progetto:
affissi, unici e memoria"). Used by the simulators to tune the numbers before the game code exists (fase 2 of the quest plan).

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


def _int(v, d=0):
    return int(v) if str(v).strip() not in ("", "None") else d


RULES = yaml.safe_load(open(os.path.join(NEXT, "affix_rules.yaml")))
BASES = _rows("bases.tsv")
PREFIXES = _rows("prefixes.tsv")
SUFFIXES = _rows("suffixes.tsv")
UNIQUES = _rows("uniques.tsv")
BY_ID = {b["id"]: b for b in BASES}
SELL_DIV = yaml.safe_load(open(os.path.join(ROOT, "data", "balance.yaml")))["shop_rules"].get("sell_divisor", 2)
CATS = ["weapon", "armor", "shield", "ring"]
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
    out = round(v * s) if v > 0 else v
    return max(-RULES["value"]["max"], min(RULES["value"]["max"], out))


def eligible(rows, cat, level):
    ok = [r for r in rows if cat in r["item_types"].split(",") and _int(r["min_level"]) <= level]
    lo = min(level, RULES["affix_choice"]["top_level"]) * RULES["affix_choice"]["low_fraction"]
    win = [r for r in ok if _int(r["min_level"]) >= lo]
    return win or ok


def pick(rng, rows):
    w = [_int(r["chance"], 1) for r in rows]
    return rng.choices(rows, weights=w)[0] if rows else None


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
            p += round(_int(row["price_add"]) * (abs(val) / abs(ref) if row["power"] != "INDESTRUCTIBLE" else 1)) * (1 if val >= 0 else -1)
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
    wins = [u for u in UNIQUES if BY_ID[u["base"]]["type"] == c and _int(u["min_level"]) <= level <= _int(u["max_level"])]
    if wins and rng.randrange(q["unique_one_in"]) == 0:
        u = rng.choice(wins)
        item.update(base=u["base"], quality="unique", unique=u)
        item["price"] = price(item)
        item["sell"] = item["price"] // SELL_DIV
        return item
    pm = min(q["magic"]["max"], q["magic"]["base"] + q["magic"]["per_t"] * t)
    if c == "ring":
        n = RULES["rings"][b["id"]] if b["id"] in RULES["rings"] else 1
        want = ["prefix", "suffix"] if n == 2 else [rng.choice(["prefix", "suffix"])]
    elif rng.randrange(100) < pm:
        r = rng.randrange(100)
        a = q["affixes"]
        want = ["prefix"] if r < a["prefix"] else ["suffix"] if r < a["prefix"] + a["suffix"] else ["prefix", "suffix"]
    else:
        want = []
    for k in want:
        rows = eligible(PREFIXES if k == "prefix" else SUFFIXES, c, level)
        if b["id"] == "gold" and rows:
            top = max(_int(r["min_level"]) for r in rows)
            if k == "prefix":
                rows = [r for r in rows if _int(r["min_level"]) == top] or rows
        row = pick(rng, rows)
        if row:
            item[k] = (row, roll_value(rng, row, level))
    if item["prefix"] or item["suffix"]:
        neg = any(v < 0 for _, v in filter(None, (item["prefix"], item["suffix"])))
        item["quality"] = "cursed" if neg else "magic"
    item["price"] = price(item)
    item["sell"] = item["price"] // SELL_DIV
    return item


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
