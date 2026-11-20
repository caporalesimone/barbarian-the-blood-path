#!/usr/bin/env python3
"""Floor run (20/11): the reference hero clears a whole floor, fight after fight, without going back to the village unless
he must. Needed to choose when the 8-slot belt becomes a reward (owner's decision P3, docs/wiki/quests.md sez. 7): a single
fight (sim_rules.series) never needs more than 4 potions, a floor does.

For each floor 1..20 and each belt size (4, 8): the monsters are those of the floor census (tools/simulators/data/
floor_census.json, the real game), split into encounters of 1..3 monsters (rooms), the floor boss alone at the end (the
chapter bosses of floors 5, 10, 15 alone; floor 20 is skipped: the final boss has its own fight in sim_rules.py).
The hero starts full, with a full belt in the potion mix of the floor (rules.yaml potions); between encounters there is no
healing (the game has none in the dungeon) [verify]; potions are drunk by sim_rules.fight (below potions.drink_below); after
each encounter he may find potions (each monster killed: drops.outcome.chest% x potion weight, each chest of the floor: its
items x potion weight; a found potion goes in a free belt slot). If after an encounter his life is under return_below and the
belt is empty, he goes back to the village (portal: full life, full belt) and the run goes on: one "return". A lost fight is
a death (village, full belt) and the run goes on.

Output: per floor and belt size, deaths and returns per floor (mean of N runs), the potions drunk and the potions left.
Usage: python3 tools/simulators/sim_floor.py [--runs N] [--floors a-b] [--sizes 4,8] [--return-below 0.5]
Report: out/work/simulators/sim_floor.txt"""
import argparse, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(ROOT, "tools", "build"))
import rules as RU  # noqa: E402
import sim_rules as S  # noqa: E402
import bestiary  # noqa: E402

B = bestiary.load_balance()
CENSUS = json.load(open(os.path.join(HERE, "data", "floor_census.json")))
TYPES = [None] + list(B["monsters"])           # census type 1..9 -> monster name (gen_db.py order)
RETURN_BELOW = 0.5                             # life fraction under which an empty belt sends him back
POT_W = B["loot"]["category_weights"]["potion"] / sum(B["loot"]["category_weights"].values())


def belt(floor, n):
    """n potions in the proportions of the potion weights of the floor (largest remainders), red first"""
    w = RU.potion_weights(floor)
    ks = sorted(w, key=lambda k: RU.R["potions"][k]["zone"])
    tot = sum(w.values())
    q = [n * w[k] / tot for k in ks]
    c = [int(x) for x in q]
    for i in sorted(range(len(ks)), key=lambda i: q[i] - c[i], reverse=True)[:n - sum(c)]:
        c[i] += 1
    return [k for k, m in zip(ks, c) for _ in range(m)]


def potion_found(floor, rng):
    """the colour of a found potion on the floor (weights of the floor)"""
    w = RU.potion_weights(floor)
    ks = list(w)
    return rng.choices(ks, weights=[w[k] for k in ks])[0]


def encounters(comp, rng):
    """monster names of the floor in encounters of 1..3; the boss last and alone"""
    boss = comp["boss"] - 1 if comp["boss"] else None
    rest = [TYPES[t] for i, t in enumerate(comp["m"]) if i != boss]
    rng.shuffle(rest)
    out = []
    while rest:
        k = min(len(rest), rng.choice((1, 2, 2, 3)))
        out.append((rest[:k], None))
        rest = rest[k:]
    if boss is not None:
        out.append(([TYPES[comp["m"][boss]]], 0))
    return out


def run(floor, size, rng, hero=None, mon=None, stats=None):
    """one floor run: (deaths, returns, potions drunk). hero: the hero (default: reference hero of the floor); mon(name, floor,
    boss) -> monster stats (default rules.monster); stats: dict filled by sim_rules.fight (20/11, sim_builds.py)"""
    lv = RU.R["reference"][floor].get("level", floor)
    hero = hero or S.ref_hero(floor, lv)
    mon = mon or (lambda n, f, boss: RU.monster(n, f, boss=boss))
    comp = CENSUS["seeds"][rng.choice(list(CENSUS["seeds"]))][str(floor)]
    full = belt(floor, size)
    pots = list(full)
    hp = hero.hpmax
    deaths = returns = drunk = 0
    chest_items = sum((2 if c & 3 == 1 else 3) for c in comp["ch"])
    found_per_kill = B["drops"]["outcome"]["chest"] / 100 * POT_W
    enc = encounters(comp, rng)
    for names, boss_idx in enc:
        mons = [mon(n, floor, i == boss_idx) for i, n in enumerate(names)]
        left = []
        before = len(pots)
        r, _, hp = S.fight(hero, mons, rng, potions=pots, hp0=hp, left=left, stats=stats)
        drunk += before - len(left)
        pots = left
        if r != "win":
            deaths += 1
            hp, pots = hero.hpmax, list(full)
            continue
        for _ in names:                                    # potions found on the bodies
            if rng.random() < found_per_kill and len(pots) < size:
                pots.append(potion_found(floor, rng))
        if hp < RETURN_BELOW * hero.hpmax and not pots:
            returns += 1
            hp, pots = hero.hpmax, list(full)
    for _ in range(chest_items):                           # chests of the floor (opened along the way: counted at the end)
        if rng.random() < POT_W and len(pots) < size:
            pots.append(potion_found(floor, rng))
    return deaths, returns, drunk


def main():
    global RETURN_BELOW
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=150)
    ap.add_argument("--floors", default="1-19")
    ap.add_argument("--sizes", default="4,8")
    ap.add_argument("--return-below", type=float, default=RETURN_BELOW, help="life fraction: empty belt and less life = back to the village")
    a = ap.parse_args()
    RETURN_BELOW = a.return_below
    lo, hi = (int(x) for x in a.floors.split("-"))
    sizes = [int(x) for x in a.sizes.split(",")]
    rng = random.Random(2011)
    lines = ["Floor run (sim_floor.py, 20/11): reference hero at his level, census of %d seeds (version %s), %d runs per point"
             % (len(CENSUS["seeds"]), CENSUS["version"], a.runs), "",
             "floor " + "".join("| belt %d: deaths returns drunk " % s for s in sizes)]
    for f in range(lo, hi + 1):
        row = "%5d " % f
        for s in sizes:
            d = r = k = 0
            for _ in range(a.runs):
                x, y, z = run(f, s, rng)
                d += x
                r += y
                k += z
            row += "|        %6.2f  %6.2f  %5.1f  " % (d / a.runs, r / a.runs, k / a.runs)
        lines.append(row)
        print(row, flush=True)
    od = os.path.join(ROOT, "out", "work", "simulators")
    os.makedirs(od, exist_ok=True)
    open(os.path.join(od, "sim_floor.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
