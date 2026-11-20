#!/usr/bin/env python3
"""Stat balance of the proposal (20/11, TODO B18): search the costs of data/rules_next.yaml "stats" so that the hero
profiles (forza, destrezza, costituzione, bilanciato) are about as strong, with the balanced one a little ahead (diminishing
returns: spreading points should pay).

Fast analytic model (no Monte Carlo), per floor and profile, against the monster mix of the floor (census, proposal monsters):
  power R = EHP / (TTK x DPS_in)
  EHP    = max life + the healing of a full belt (proposal potions, CON bonus)
  TTK    = mean time to kill a monster of the mix: life / (hit chance x mean damage incl. criticals / cadence)
  DPS_in = mean damage per frame of a monster of the mix: hit chance x mean damage x (1 - damage reduction) / 45
R is "how many monsters the hero beats with one belt" up to a constant. Score of a set of costs: sum over the floors of
(log R_profile - log R_bilanciato + margin)^2 for the three specialized profiles (margin = balanced ahead by ~10%).

Usage: python3 tools/simulators/fit_stats.py [--top 10] [--floors 4,8,12,16,19] [--margin 0.1]
       python3 tools/simulators/fit_stats.py --show       (power table of the costs in rules_next.yaml)
The chosen costs are copied by hand into data/rules_next.yaml and checked with sim_builds.py (Monte Carlo)."""
import argparse, itertools, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sim_builds as SB  # noqa: E402
import sim_floor as SF  # noqa: E402
from rules import hit_chance, R  # noqa: E402

SPEC = ["forza", "destrezza", "costituzione"]
GRID = {
    ("str", "dmg_per"): [2, 3, 4],
    ("dex", "att_per"): [4, 5, 6, 8],
    ("dex", "ac_per"): [6, 8, 10, 12],
    ("dex", "speed_per"): [2, 3, 4],
    ("con", "hp_per_point"): [3, 4, 5],
    ("con", "dr_pct"): [0.3, 0.4, 0.5],
    ("soft_from",): [24, 30, 40],
}


def power(name, floor):
    h = SB.NextHero(name, floor)
    mix = [(SB.monster_next(n, floor, b), c) for (n, b), c in SB.floor_mix(floor).items()]
    tot = sum(c for _, c in mix)
    crit = (21 - h.crit) / 20
    ttk = din = 0.0
    for m, c in mix:
        p = hit_chance(h.att, m["ac"] - h.pen)
        dmg = h.dice.avg * (1 + crit) + h.dmg_k
        dps = max(1e-6, p * dmg / h.rate)
        ttk += c * m["hp"].avg * m["hp_mult"] / dps
        din += c * hit_chance(m["att"], h.ac) * m["dmg"].avg * m["dmg_mult"] * (1 - h.dr10 / 1000) / R["timing"]["monster_attack"]
    ehp = h.hpmax + sum(h.heal(k) for k in SF.belt(floor, 4))
    return ehp / ((ttk / tot) * (din / tot))


def setp(key, v):
    d = SB.NX["stats"]
    for k in key[:-1]:
        d = d[k]
    d[key[-1]] = v


def score(floors, margin):
    SB._NORM.clear()
    s, rows = 0.0, {}
    for f in floors:
        lb = math.log(power("bilanciato", f))
        r = {n: math.log(power(n, f)) - lb for n in SPEC}
        rows[f] = r
        s += sum((v + margin) ** 2 for v in r.values())
    return s, rows


def show(floors, margin):
    s, rows = score(floors, margin)
    print("score %.3f  (potenza del profilo / bilanciato, livello = piano)" % s)
    print("piano " + "".join("%14s" % n for n in SPEC))
    for f, r in rows.items():
        print("%5d " % f + "".join("%13.0f%%" % (100 * math.exp(v)) for v in r.values()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--floors", default="4,8,12,16,19")
    ap.add_argument("--margin", type=float, default=0.1)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    floors = [int(x) for x in a.floors.split(",")]
    if a.show:
        show(floors, a.margin)
        return
    keys = list(GRID)
    out = []
    for vals in itertools.product(*(GRID[k] for k in keys)):
        for k, v in zip(keys, vals):
            setp(k, v)
        s, rows = score(floors, a.margin)
        out.append((s, vals, rows))
    out.sort(key=lambda x: x[0])
    print("chiavi: " + ", ".join(".".join(k) for k in keys))
    for s, vals, rows in out[:a.top]:
        worst = {n: min(r[n] for r in rows.values()) for n in SPEC}
        print("%.3f  %s  peggior piano: %s" % (s, vals, "  ".join("%s %.0f%%" % (n, 100 * math.exp(v)) for n, v in worst.items())))


if __name__ == "__main__":
    main()
