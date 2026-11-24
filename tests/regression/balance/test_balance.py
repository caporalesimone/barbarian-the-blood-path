#!/usr/bin/env python3
"""Balance checks with the d20 rules simulator (tools/simulators/sim_rules.py, fixed seed, ~2 s).

Wide thresholds: they catch gross regressions (broken data, inverted curves), not tuning.
The tuning is in docs/wiki/BILANCIAMENTO.md (tools/simulators/fit_rules.py)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools", "simulators"))
sys.argv = ["sim"]
import sim_rules as S
import rules as RU

bad = []
POT = ["red", "red", "yellow", "violet"]
# reference hero against the strongest base monster of the level: must win almost always
for fl in (1, 5, 10, 15, 19):
    m = RU.floor_types(fl)[-1]
    r = S.series(S.ref_hero(fl, potions=POT), [m], fl, n=150)
    print(f"level {fl:2}: reference hero against {m}: won {r['winp']:.0f}%")
    if r["winp"] < 85:
        bad.append(f"level {fl} against {m}: {r['winp']:.0f}% < 85%")
# a level-1 hero on level 10 must lose almost always (growth matters)
m = RU.floor_types(10)[-1]
h = S.ref_hero(1, potions=POT)
r = S.series(h, [m, m], 10, n=150)
print(f"level 10: level-1 hero against 2 x {m}: won {r['winp']:.0f}%")
if r["winp"] > 30:
    bad.append(f"level-1 hero on level 10 wins {r['winp']:.0f}% > 30%")
# the average hp of the monsters grows with the level: (24/11) every type inside a chapter (a chapter with own_stats,
# tools/build/mon_stats.py, gives its types other stats); the mean of the base types present over the whole dungeon (5%
# tolerance: a chapter changes the types, not the mean difficulty)
for name in ("skeleton", "demon"):
    def avg(fl):
        m = RU.monster(name, fl)
        return m["hp"].avg * m["hp_mult"]
    for c in range(4):
        hp = [avg(fl) for fl in range(5 * c + 1, min(5 * c + 6, RU.NF))]
        if any(b < a for a, b in zip(hp, hp[1:])):
            bad.append(f"average hp of {name} in chapter {c + 1} not growing: {[round(x) for x in hp]}")
# (24/11) mean of the base types PRESENT on the level (RU.floor_types: base_n of the game), what the player meets
mean = [sum(RU.monster(n, fl)["hp"].avg * RU.monster(n, fl)["hp_mult"] for n in RU.floor_types(fl)) / len(RU.floor_types(fl))
        for fl in range(1, RU.NF)]
print("mean hp of the base types present per level:", [round(x) for x in mean])
if any(b < a * 0.95 for a, b in zip(mean, mean[1:])):
    bad.append(f"mean hp of the base types per level not growing: {[round(x) for x in mean]}")
for b in bad:
    print("FAIL", b)
sys.exit(1 if bad else 0)
