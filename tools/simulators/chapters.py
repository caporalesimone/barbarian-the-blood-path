#!/usr/bin/env python3
"""Balancing by chapter (11/11, docs/wiki/capitoli.md, docs/wiki/quests.md 3.8): the chapters come from data/chapters.yaml
(tools/build/chapters_db.py: LOCAL level 1..n of each chapter, the last one is the final map; GLOBAL depth 1..255 = the
difficulty) and the monsters from the chapter's bestiary (data/monsters/bestiary.tsv, tools/build/bestiary.py): every chapter
fights its own monsters (concept rows included: their stats are put in the simulator's rules only while simulating).
The Abyss (last chapter) mixes all the bestiaries and uses the Abyss rules of tools/simulators/rules.py (void reference hero, void.table).

For every generated level: win % of the reference hero against the typical groups of the chapter's bestiary (1 base,
3 base, 1 strong, the named level boss = strongest strong x boss), chestLevel (sim_chest.chest_level) and gold
(sim_gold.per_floor) at the global depth. For the final map: the chapter boss (4 potions of the zone of the depth).
Long chapters (the Abyss) are sampled every --step levels plus the last one.

Today's game (one village, levels 1-20 = depth 1-20) is not split in chapters yet: these are design numbers (TODO B11, M9).
Usage: python3 tools/simulators/chapters.py [--chapter N] [--fights N] [--step N] [--csv file]"""
import argparse, csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules as RU            # noqa: E402
import sim_rules as S         # noqa: E402
import sim_chest as SC        # noqa: E402
import sim_gold as SG         # noqa: E402
sys.path[:0] = [os.path.join(RU.ROOT, "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import chapters_db as CD      # noqa: E402
import bestiary as BE         # noqa: E402

NF = RU.NF
DATA = CD.load()
CHAPTERS = DATA["chapters"]
BEST = BE.load()
for _r in BEST:                                   # concept monsters known to the simulator (not to the game)
    RU.R["monsters"].setdefault(_r["id"], BE.rules_entry(_r))


def chapter(cid):
    for c in CHAPTERS:
        if c["id"] == cid:
            return c
    raise KeyError("chapter %s not in data/chapters.yaml" % cid)


def depth(ch, local):
    return CD.depth(ch, local)


def bestiary(ch):
    """monsters of the chapter (the Abyss = the last chapter: all of them)"""
    last = ch is CHAPTERS[-1] and not ch.get("final")
    return [r for r in BEST if last or r["chapter"] == ch["id"]]


def levels(ch, step=16):
    """generated local levels to simulate (the final map, if any, apart): all, or a sample of a long chapter"""
    n = ch["n_levels"] - (1 if ch.get("final") else 0)
    if n <= 40:
        return list(range(1, n + 1))
    return sorted(set(list(range(1, n + 1, step)) + [n]))


def hero(d):
    return S.ref_hero(d) if d <= NF else RU.void_hero(d)


def pots(d):
    z = RU.potion_zone(min(d, NF)) if d <= NF else 2
    return [("red", "yellow", "violet")[z]] * 4


def groups(ch, d):
    """typical groups of the chapter at depth d (like sim_rules.groups, on the chapter's bestiary)"""
    bs = bestiary(ch)
    base = [r["id"] for r in bs if r["tier"] == "base" and r["floor"] <= d] or [min((r for r in bs if r["tier"] == "base"), key=lambda r: r["floor"])["id"]]
    strong = [r["id"] for r in bs if r["tier"] == "strong" and r["floor"] <= d] or [min((r for r in bs if r["tier"] == "strong"), key=lambda r: r["floor"])["id"]]
    hard = base[-1]
    return {"1 base": [hard], "3 base": [base[-1], base[0], base[min(1, len(base) - 1)]],
            "1 strong": [strong[-1]], "level boss": [strong[-1]]}


def level_row(ch, local, fights):
    d = depth(ch, local)
    h = hero(d)
    pt = RU.abyss_belt(d) if d > NF else None      # (15/11, J4) Abisso: cintura attesa da potions.abyss_drop (heal_abyss)
    row = {"chapter": ch["id"], "level": local, "depth": d}
    for name, grp in groups(ch, d).items():
        r = S.series(h, grp, d, n=fights, boss_idx=(0 if name == "level boss" else None), potions=pt)
        row["win_" + name.replace(" ", "_")] = round(r["winp"])
    row["chest_level"] = SC.chest_level(d)
    row["gold"] = round(SG.per_floor(d, d, abyss=d > NF)[0])
    return row


def final_row(ch, fights):
    f = ch["final"]
    local = ch["n_levels"]
    d = depth(ch, local)
    boss = f["boss"]
    final = "final" in RU.R["monsters"][boss] and RU.R["monsters"][boss].get("final")
    h = hero(min(d, NF)) if d <= NF else hero(d)
    r = S.series(h, [boss], d, n=fights, final=bool(final), potions=pots(d))
    return {"chapter": ch["id"], "level": local, "depth": d, "final": f["name"], "boss": boss,
            "win_chapter_boss": round(r["winp"])}


def report(ids=None, fights=100, step=16):
    rows = []
    for ch in CHAPTERS:
        if ids and ch["id"] not in ids:
            continue
        print("== chapter %d: %s, local levels 1-%d, global depth %d-%d (%s)" % (
            ch["id"], ch["name"], ch["n_levels"], ch["first_depth"], ch["last_depth"],
            "in the game" if ch["implemented"] else "design: not in the game code"))
        print("  lvl depth | win% 1 base 3 base 1 strong  boss | chestLvl  gold   (bestiary of the chapter; no potions in the dungeon, in the Abyss the belt of potions.abyss_drop)")
        for l in levels(ch, step):
            r = level_row(ch, l, fights)
            rows.append(r)
            print("  %3d %5d | %12d %6d %8d %4d | %8d %5d" % (l, r["depth"], r["win_1_base"], r["win_3_base"],
                  r["win_1_strong"], r["win_level_boss"], r["chest_level"], r["gold"]))
        if ch.get("final"):
            r = final_row(ch, fights)
            rows.append(r)
            print("  %3d %5d | final map %s: %s, win %d%% (4 potions of the zone)" % (r["level"], r["depth"], r["final"], r["boss"], r["win_chapter_boss"]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, action="append")
    ap.add_argument("--fights", type=int, default=100)
    ap.add_argument("--step", type=int, default=16)
    ap.add_argument("--csv")
    a = ap.parse_args()
    rows = report(a.chapter, a.fights, a.step)
    if a.csv:
        keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("chapter", "level", "depth"), k))
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, keys)
            w.writeheader()
            w.writerows(rows)
        print("written", a.csv)


if __name__ == "__main__":
    main()
