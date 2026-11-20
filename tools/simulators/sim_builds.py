#!/usr/bin/env python3
"""Hero profiles (20/11): the same floor runs of sim_floor.py for several heroes, to see whether every stat is worth points and
whether the second half of the game is too easy. Two rule sets:

  oggi  - the game today (data/rules.yaml): 1 point per level, STR = attack and damage, DEX = AC (armor cap) and attack speed,
          CON = life. Profiles: the reference hero (rules.yaml reference_alloc) and the profiles of data/rules_next.yaml with
          the same 19 points.
  next  - the PROPOSAL of data/rules_next.yaml (owner's decisions of 20/11): 4 points per level from level 1, STR = damage,
          DEX = attack + AC + speed, CON = life + potions + damage taken; potions heal a share of max life with a cap;
          monsters normalized on the "bilanciato" profile and moved by the per-floor targets (early floors easier, second
          half harder).

Gear: the reference gear of the floor (rules.yaml reference), adapted to the profile (heaviest armor type it wears, one-hand
sword and shield for "one", ring on its main stat). Each floor: the floor census (real game) as in sim_floor.py, belt of
--belt potions. Floor 20: the final boss fight (summons included) with the belt, --runs fights.

Output per rule set and profile: deaths, village returns and potions drunk per floor, hit chances, and the hero sheet.
Usage: python3 tools/simulators/sim_builds.py [--runs N] [--floors a-b] [--belt 4] [--rules oggi,next]
Report: out/work/simulators/sim_builds.txt (+ sim_builds.png if matplotlib is there)"""
import argparse, os, random, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules as RU  # noqa: E402
import sim_rules as S  # noqa: E402
import sim_floor as SF  # noqa: E402
from rules import R, NF, Dice, hit_chance  # noqa: E402

NX = yaml.safe_load(open(os.path.join(RU.ROOT, "data", "rules_next.yaml")))
PROFILES = NX["profiles"]
ARMOR_RANK = {"light": 0, "medium": 1, "heavy": 2}
_monster0 = RU.monster


def interp(tbl, f):
    """value of a {floor: value} table at floor f (linear between the given floors, flat outside)"""
    ks = sorted(tbl)
    if f <= ks[0]:
        return tbl[ks[0]]
    if f >= ks[-1]:
        return tbl[ks[-1]]
    lo = max(k for k in ks if k <= f)
    hi = min(k for k in ks if k >= f)
    return tbl[lo] if hi == lo else tbl[lo] + (tbl[hi] - tbl[lo]) * (f - lo) / (hi - lo)


def alloc(share, n):
    """n points one at a time, each to the stat furthest behind its share"""
    got = {k: 0 for k in share}
    out = []
    tot = sum(share.values())
    for i in range(n):
        k = max(share, key=lambda s: share[s] * (i + 1) / tot - got[s])
        got[k] += 1
        out.append(k)
    return out


def gear(prof, floor):
    """(weapon, armor, shield, magic, ring kind) of the profile on the floor, from the reference gear"""
    r = R["reference"][floor]
    weapon, shield = r["weapon"], r["shield"]
    if prof["weapon"] == "one" and R["weapons"][weapon].get("two_handed"):
        weapon = "sword"
        shield = shield or max((k for k, v in R["shields"].items() if v["ilvl"] <= floor), key=lambda k: R["shields"][k]["ilvl"])
    armor = r["armor"]
    ok = [k for k, v in R["armors"].items() if ARMOR_RANK[v["type"]] <= ARMOR_RANK[prof["armor"]] and v["ilvl"] <= floor]
    if armor and ARMOR_RANK[R["armors"][armor]["type"]] > ARMOR_RANK[prof["armor"]]:
        armor = max(ok, key=lambda k: R["armors"][k]["ac"])
    ring = r.get("ring", "")
    return weapon, armor, shield, r["magic"], (ring.split(":")[1] if ring else "")


# ------------------------------------------------------------------ rules of today
def hero_today(name, floor, level=None):
    """a hero with the rules of today; name 'riferimento' = the reference hero (reference_alloc and reference gear)"""
    level = level or floor
    if name == "riferimento":
        return S.ref_hero(floor, level)
    p = PROFILES[name]
    keep = R["player"]["reference_alloc"]
    R["player"]["reference_alloc"] = alloc(p["share"], len(keep))
    try:
        w, a, s, m, kind = gear(p, floor)
        rings = {p["ring"]: 2 * R["rings"][kind]["bonus"]} if kind else None
        h = RU.Hero(level, w, a, s, m, rings=rings)
    finally:
        R["player"]["reference_alloc"] = keep
    h.profile = name
    return h


# ------------------------------------------------------------------ proposal (rules_next.yaml)
def next_points(level):
    pt = NX["stats"]["points"]
    return pt["per_level"] * sum(1 for l in range(pt["first"], min(level, pt["last"]) + 1))


def soft(x):
    sf = NX["stats"]["soft_from"]
    return x if x <= sf else sf + (x - sf) // 2


class NextHero:
    """hero with the stats of data/rules_next.yaml; same attributes as rules.Hero for sim_rules.fight, plus dr10 (damage
    taken reduction in tenths of %) and heal(kind)"""
    def __init__(self, name, floor, level=None):
        st = NX["stats"]
        p = PROFILES[name]
        self.profile = name
        self.level = level = level or floor
        sc = dict(st["start"])
        for k in alloc(p["share"], next_points(level)):
            sc[k] += 1
        weapon, armor, shield, magic, kind = gear(p, floor)
        if kind:
            sc[p["ring"]] += R["rings"][kind]["bonus"] * st["ring_points"]
        self.sc = sc
        x = {k: soft(v - 10) for k, v in sc.items()}
        self.x = x
        self.prof = RU.prof(level)
        w = R["weapons"][weapon]
        self.weapon, self.two_handed = weapon, bool(w.get("two_handed"))
        self.dice, self.pen = Dice(w["dice"]), w["pen"]
        self.rate = w["rate"] + max(0, R["player"]["attack_speed"]["slow"] - x["dex"] // st["dex"]["speed_per"])
        self.speed = 1
        self.att = self.prof + x["dex"] // st["dex"]["att_per"] + magic
        self.dmg_k = x["str"] // st["str"]["dmg_per"] + magic
        ac, cap = 10, 99
        self.armor, self.shield = armor, "" if self.two_handed else shield
        if armor:
            ac += R["armors"][armor]["ac"] + magic
            cap = R["dex_cap"][R["armors"][armor]["type"]]
        if self.shield:
            ac += R["shields"][self.shield]["ac"] + magic
        self.ac = ac + min(x["dex"] // st["dex"]["ac_per"], cap)
        self.dc = 8 + self.prof + x["str"] // st["str"]["dc_per"]
        self.crit = 19 if level >= R["skills"]["brutal_critical_level"] else 20
        c = st["con"]
        self.hpmax = st["hp"]["base"] + (level - 1) * st["hp"]["per_level"] + c["hp_per_point"] * x["con"]
        self.dr10 = int(min(c["dr_max"], x["con"] * c["dr_pct"]) * 10)
        self.potb = min(c["potion_max"], x["con"] * c["potion_pct"])
        self.m = {k: v // 4 for k, v in x.items()}
        self.potions = []

    def skills(self):
        return [k for k, v in R["skills"].items() if isinstance(v, dict) and v["level"] <= self.level]

    def rage_bonus(self):
        d = R["skills"]["rage"]["damage"]
        return {"prof": self.prof, "strmod": self.m["str"]}.get(d) if isinstance(d, str) else int(d)

    def dmg_range(self):
        return self.dice.min + self.dmg_k, self.dice.max + self.dmg_k

    def heal(self, kind):
        p = NX["potions"][kind]
        return min(p["max"], self.hpmax * p["pct"] // 100) * (100 + self.potb) // 100


_NORM = {}


def floor_mix(f):
    """monster types of floor f in the census (all seeds), with their counts; the floor boss counted as a boss"""
    out = {}
    for seed in SF.CENSUS["seeds"].values():
        comp = seed[str(f)]
        b = comp["boss"] - 1 if comp["boss"] else None
        for i, t in enumerate(comp["m"]):
            k = (SF.TYPES[t], i == b)
            out[k] = out.get(k, 0) + 1
    return out


def norm(floor):
    """per-floor change of the monsters for the proposal. Today: the monsters of the floor census against the reference
    hero give the mean hit chances, time-to-kill and relative damage. Proposal: attack and AC moved by the same amount for
    every monster so that the MEAN hit chances against the 'bilanciato' profile are the targets m_hit / pg_hit; life and
    damage scaled to keep today's time-to-kill and relative damage, times the difficulty targets hp / dmg"""
    if floor in _NORM:
        return _NORM[floor]
    f = min(floor, NF)
    M = NX["monsters"]
    ref = S.ref_hero(f)
    bal = NextHero("bilanciato", f)
    mix = [(_monster0(n, f, boss=b), c) for (n, b), c in floor_mix(f).items()]
    tot = sum(c for _, c in mix)
    mean = lambda fn: sum(fn(m) * c for m, c in mix) / tot
    pm_cur = mean(lambda m: hit_chance(m["att"], ref.ac))
    pp_cur = mean(lambda m: hit_chance(ref.att, m["ac"] - ref.pen))
    tm, tp = interp(M["m_hit"], f), interp(M["pg_hit"], f)
    da = min(range(-60, 120), key=lambda d: abs(mean(lambda m: hit_chance(m["att"] + d, bal.ac)) - tm))
    dc = min(range(-60, 120), key=lambda d: abs(mean(lambda m: hit_chance(bal.att, m["ac"] + d - bal.pen)) - tp))
    pm = mean(lambda m: hit_chance(m["att"] + da, bal.ac))
    pp = mean(lambda m: hit_chance(bal.att, m["ac"] + dc - bal.pen))
    dpr_cur = pp_cur * (ref.dice.avg + ref.dmg_k) / ref.rate
    dpr_bal = pp * (bal.dice.avg + bal.dmg_k) / bal.rate
    hp_x = dpr_bal / dpr_cur * interp(M["hp"], f)
    dmg_x = bal.hpmax * pm_cur / (ref.hpmax * pm * (1 - bal.dr10 / 1000)) * interp(M["dmg"], f)
    _NORM[floor] = dict(att=da, ac=dc, hp=hp_x, dmg=dmg_x, pm_cur=pm_cur, pp_cur=pp_cur)
    return _NORM[floor]


def monster_next(name, floor, boss=False, scale=None):
    m = dict(_monster0(name, floor, boss=boss, scale=scale))
    n = norm(floor)
    m["att"] += n["att"]
    m["ac"] += n["ac"]
    m["save"] += n["att"] // 2
    m["hp_mult"] *= n["hp"]
    m["dmg_mult"] *= n["dmg"]
    return m


# ------------------------------------------------------------------ runs
def make(rules, name, floor):
    return hero_today(name, floor) if rules == "oggi" else NextHero(name, floor)


def run_floor(rules, name, floor, belt, runs, rng):
    S.monster = monster_next if rules == "next" else _monster0       # final boss summons too
    mon = (lambda n, f, b: monster_next(n, f, b)) if rules == "next" else None
    st = {}
    d = r = k = 0
    for _ in range(runs):
        h = make(rules, name, floor)
        x, y, z = SF.run(floor, belt, rng, hero=h, mon=mon, stats=st)
        d, r, k = d + x, r + y, k + z
    return dict(deaths=d / runs, returns=r / runs, drunk=k / runs,
                m_hit=100 * st["m_hits"] / max(1, st["m_swings"]), pg_hit=100 * st["pg_hits"] / max(1, st["pg_swings"]))


def run_final(rules, name, belt, runs, rng):
    S.monster = monster_next if rules == "next" else _monster0
    h = make(rules, name, NF)
    b = (monster_next if rules == "next" else _monster0)("lord_of_ruin", NF)
    pots = SF.belt(NF, belt)
    w = sum(S.fight(h, [b], rng, potions=list(pots), final_boss=0)[0] == "win" for _ in range(runs))
    return 100 * w / runs


def sheet(h):
    lo, hi = h.dmg_range()
    return "vita %4d  CA %2d  ATT %+3d  danno %2d-%-2d  cadenza %2d  rid.danno %4.1f%%  %s/%s/%s" % (
        h.hpmax, h.ac, h.att, lo, hi, h.rate, getattr(h, "dr10", 0) / 10, h.weapon, h.armor or "-", h.shield or "-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=60)
    ap.add_argument("--floors", default="1-19")
    ap.add_argument("--belt", type=int, default=4)
    ap.add_argument("--rules", default="oggi,next")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.floors.split("-"))
    sets = a.rules.split(",")
    names = {"oggi": ["riferimento"] + list(PROFILES), "next": list(PROFILES)}
    rng = random.Random(2011)
    L = ["Profili di PG (sim_builds.py, 20/11): %d giri per piano, cintura %d, censimento %s" % (a.runs, a.belt, SF.CENSUS["version"]),
         "Celle: morti / ritorni in citta' / pozioni bevute per piano. 'mostri' e 'PG' = % di colpi a segno.", ""]
    res = {}
    for rs in sets:
        L.append("=" * 20 + " regole: %s " % rs + "=" * 20)
        for n in names[rs]:
            L.append("%-13s" % n)
            for f in (1, 5, 10, 15, 20):
                L.append("   liv %2d  %s" % (f, sheet(make(rs, n, f))))
            if rs == "next":
                h = make(rs, n, 20)
                L.append("   caratteristiche al 20: FOR %d  DES %d  COS %d" % (h.sc["str"], h.sc["dex"], h.sc["con"]))
        L.append("")
        L.append("piano " + "".join("| %-23s" % n for n in names[rs]))
        for f in range(lo, hi + 1):
            row = "%5d " % f
            for n in names[rs]:
                x = run_floor(rs, n, f, a.belt, a.runs, rng)
                res[(rs, n, f)] = x
                row += "| %4.2f %4.2f %4.1f m%2.0f p%2.0f " % (x["deaths"], x["returns"], x["drunk"], x["m_hit"], x["pg_hit"])
            L.append(row)
            print(rs, row, flush=True)
        row = "boss  "
        for n in names[rs]:
            w = run_final(rs, n, a.belt, a.runs * 2, rng)
            res[(rs, n, "boss")] = w
            row += "| vinto %3.0f%%              " % w
        L.append(row)
        L.append("")
        L.append("per capitolo (morti+ritorni per piano, media):")
        for c, (p, q) in enumerate(((1, 5), (6, 10), (11, 15), (16, 19)), 1):
            fs = [f for f in range(max(p, lo), min(q, hi) + 1)]
            if fs:
                L.append("  cap %d  " % c + "  ".join("%s %.2f" % (n, sum(res[(rs, n, f)]["deaths"] + res[(rs, n, f)]["returns"] for f in fs) / len(fs))
                                                    for n in names[rs]))
        L.append("")
    od = os.path.join(RU.ROOT, "out", "work", "simulators")
    os.makedirs(od, exist_ok=True)
    open(os.path.join(od, "sim_builds.txt"), "w").write("\n".join(L) + "\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, len(sets), figsize=(7 * len(sets), 4), squeeze=False)
        for i, rs in enumerate(sets):
            ax = axs[0][i]
            for n in names[rs]:
                fs = list(range(lo, hi + 1))
                ax.plot(fs, [res[(rs, n, f)]["deaths"] + res[(rs, n, f)]["returns"] for f in fs], marker="o", ms=3, label=n,
                        color={"riferimento": "#888888", "forza": "#c0392b", "destrezza": "#27ae60", "costituzione": "#2471a3",
                               "bilanciato": "#8e44ad"}[n])
            ax.set_title("regole %s: morti + ritorni per piano (cintura %d)" % (rs, a.belt))
            ax.set_xlabel("piano")
            ax.set_xticks(range(lo, hi + 1))
            ax.grid(alpha=.3)
            ax.legend()
        fig.savefig(os.path.join(od, "sim_builds.png"), dpi=110, bbox_inches="tight")
    except ImportError:
        pass
    print("\n".join(L))


if __name__ == "__main__":
    main()
