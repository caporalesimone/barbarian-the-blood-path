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
import boss_scripts as BS  # noqa: E402
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


def gear(prof, floor, sc=None):
    """(weapon, armor, shield, magic, ring kind) of the profile on the floor, from the reference gear. sc: scores of the hero
    (proposal): items whose requirements (rules_next.yaml requirements) are not met are replaced by the best one that is,
    among those the reference has by that floor (21/11)"""
    r = R["reference"][floor]
    req = NX.get("requirements", {}) if sc is not None else {}
    ok = lambda k: all(sc[st] >= v for st, v in req.get(k, {}).items())
    weapon, shield = r["weapon"], r["shield"]
    wl = R["weapons"][weapon]["ilvl"]
    if (prof["weapon"] == "one" and R["weapons"][weapon].get("two_handed")) or not ok(weapon):
        weapon = max((k for k, v in R["weapons"].items() if not v.get("two_handed") and v["ilvl"] <= wl and ok(k)),
                     key=lambda k: R["weapons"][k]["ilvl"])
    if not R["weapons"][weapon].get("two_handed"):
        sl = max([R["shields"][shield]["ilvl"]] if shield else [v["ilvl"] for v in R["shields"].values() if v["ilvl"] <= floor])
        cand = [k for k, v in R["shields"].items() if v["ilvl"] <= sl and ok(k)]
        shield = max(cand, key=lambda k: R["shields"][k]["ac"]) if cand else ""
    armor = r["armor"]
    if armor:
        al = R["armors"][armor]["ilvl"]
        cand = [k for k, v in R["armors"].items() if ARMOR_RANK[v["type"]] <= ARMOR_RANK[prof["armor"]] and v["ilvl"] <= al and ok(k)]
        armor = max(cand, key=lambda k: R["armors"][k]["ac"]) if cand else ""
    ring = r.get("ring", "")
    return weapon, armor, shield, r["magic"], (ring.split(":")[1] if ring else "")


# ------------------------------------------------------------------ next item bases (21/11)
def _next_bases():
    """weapons, armors and shields of data/items/next/bases.tsv (the future database: rate grows with the size of the weapon)"""
    import csv
    W, A, S_ = {}, {}, {}
    for r in csv.DictReader(open(os.path.join(RU.ROOT, "data", "items", "next", "bases.tsv")), delimiter="\t"):
        i = lambda k: int(r[k]) if r[k].strip() else 0
        if r["type"] == "weapon":
            W[r["id"]] = dict(dice=r["dice"], rate=i("rate"), pen=i("pen"), two_handed=r["hands"] == "2", ilvl=i("ilvl"), min_str=i("min_str"))
        elif r["type"] == "armor":
            A[r["id"]] = dict(ac=i("ac"), type=r["armor_type"], ilvl=i("ilvl"), min_str=i("min_str"))
        elif r["type"] == "shield":
            S_[r["id"]] = dict(ac=i("ac"), ilvl=i("ilvl"), min_str=i("min_str"))
    return W, A, S_


NW, NA, NS = _next_bases()


def next_req(item):
    """FOR required by a next base in the proposal's scale: the FOR of the 'bilanciato' profile (points and ring) req_lag levels
    before the item level, for the bases that have a requirement today (min_str); 0 = none"""
    b = NW.get(item) or NA.get(item) or NS.get(item)
    if not b or not b["min_str"]:
        return 0
    g = NX.get("gear", {})
    lv = max(1, b["ilvl"] - g.get("req_lag", 2))
    sc = dict(NX["stats"]["start"])
    for k in alloc(PROFILES["bilanciato"]["share"], next_points(lv)):
        sc[k] += 1
    ring = R["reference"][min(max(lv, 1), NF)].get("ring", "")
    if ring:
        sc[PROFILES["bilanciato"]["ring"]] += R["rings"][ring.split(":")[1]]["bonus"] * NX["stats"]["ring_points"]
    return sc["str"]


def gear_next(prof, floor, sc, x):
    """best next bases the profile can use on the floor (item level <= floor, FOR requirement met): weapon by damage per frame
    (two-handed only if 15% better than one-handed, the shield is lost), armor of its type by AC (DEX in the cap), shield by AC"""
    st = NX["stats"]
    ok = lambda k: sc["str"] >= next_req(k)
    # (21/11 proposta) armature e scudi: requisito sulla "robustezza" = media di FOR e COS (gear.armor_req: str_con)
    tough = (sc["str"] + sc["con"]) // 2 if NX.get("gear", {}).get("armor_req") == "str_con" else sc["str"]
    oka = lambda k: tough >= next_req(k)
    def wscore(k):
        w = NW[k]
        if st["str"].get("dmg_pct"):
            return Dice(w["dice"]).avg * (100 + x["str"] * st["str"]["dmg_pct"]) / 100 / rate_of(k, sc, x)
        return (Dice(w["dice"]).avg + x["str"] // st["str"]["dmg_per"]) / rate_of(k, sc, x)
    ws = [k for k, w in NW.items() if w["ilvl"] <= floor and ok(k)]
    one = max((k for k in ws if not NW[k]["two_handed"]), key=wscore)
    two = [k for k in ws if NW[k]["two_handed"]]
    weapon = one
    if prof["weapon"] != "one" and two:
        t = max(two, key=wscore)
        if wscore(t) > 1.15 * wscore(one):
            weapon = t
    ac_dex = x["dex"] // st["dex"]["ac_per"] if st["dex"].get("ac_per") else 0
    am = [k for k, a in NA.items() if a["ilvl"] <= floor and oka(k) and ARMOR_RANK[a["type"]] <= ARMOR_RANK[prof["armor"]]]
    armor = max(am, key=lambda k: NA[k]["ac"] + min(ac_dex, R["dex_cap"][NA[k]["type"]]) - armor_slow(k, sc) * 0.5) if am else ""
    sh = [k for k, s_ in NS.items() if s_["ilvl"] <= floor and oka(k)]
    shield = "" if NW[weapon]["two_handed"] or not sh else max(sh, key=lambda k: NS[k]["ac"])
    return weapon, armor, shield


def rate_of(weapon, sc, x):
    """cadence of a next weapon: its rate, then (21/11 proposal) FOR above the requirement makes big weapons handier:
    -1 frame every str.handling_per points above the requirement, never under str.handling_floor"""
    st = NX["stats"]["str"]
    r = NW[weapon]["rate"]
    if st.get("handling_per") and r > st.get("handling_floor", 14):
        r = max(st.get("handling_floor", 14), r - max(0, sc["str"] - next_req(weapon)) // st["handling_per"])
    return r


def armor_slow(armor, sc):
    """(21/11 proposal) frames added to the cadence by a medium/heavy armor, taken away by FOR above its requirement"""
    a = NX["stats"].get("armor_slow", {})
    if not armor or not a.get(NA[armor]["type"]):
        return 0
    return max(0, a[NA[armor]["type"]] - max(0, sc["str"] - next_req(armor)) // a.get("str_per", 6))


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
    """diminishing returns: past soft_from points each point is worth soft_rate (default 1/2; integer maths as on the C64)"""
    st = NX["stats"]
    sf = st["soft_from"]
    num, den = st.get("soft_rate", [1, 2])
    return x if x <= sf else sf + (x - sf) * num // den


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
        ring = R["reference"][floor].get("ring", "")              # l'anello conta anche per i requisiti degli oggetti
        if ring:
            sc[p["ring"]] += R["rings"][ring.split(":")[1]]["bonus"] * st["ring_points"]
        weapon, armor, shield, magic, kind = gear(p, floor, sc)
        self.sc = sc
        x = {k: soft(v - 10) for k, v in sc.items()}
        self.x = x
        nextgear = NX.get("gear", {}).get("mode") == "next"            # (21/11) basi nuove: data/items/next/bases.tsv
        if nextgear:
            weapon, armor, shield = gear_next(p, floor, sc, x)
        self.prof = RU.prof(level)
        w = NW[weapon] if nextgear else R["weapons"][weapon]
        self.weapon, self.two_handed = weapon, bool(w.get("two_handed"))
        self.dice, self.pen = Dice(w["dice"]), w["pen"]
        if st["str"].get("pen_per"):                                   # (21/11) FOR: sfondare la guardia
            self.pen += x["str"] // st["str"]["pen_per"]
        slow = st["dex"].get("slow", R["player"]["attack_speed"]["slow"])     # (21/11) la proposta puo' togliere il rallentamento
        wrate = rate_of(weapon, sc, x) if nextgear else w["rate"]
        self.rate = wrate + max(0, slow - (x["dex"] // st["dex"]["speed_per"] if st["dex"].get("speed_per") else 0))
        if nextgear:
            self.rate += armor_slow(armor, sc)
        # (21/11, committente) attacchi extra della DES: il k-esimo si sblocca a extra_first + (k-1) x extra_every punti e da li' sale di
        # extra_slopes[k-1] % a punto fino a extra_max % (probabilita' del secondo tiro, dopo il tiro normale andato a segno);
        # nell'Abisso (punti in piu') salgono tutti e se ne aggiungono altri con l'ultima pendenza
        d = st["dex"]
        self.extra, self.extra_chain = [], bool(d.get("extra_chain"))
        k = 1
        top = d.get("extra_count", 99) if level <= NF else 99      # nel dungeon al massimo extra_count; nell'Abisso di piu'
        at = lambda k: d.get("extra_first", d.get("extra_every", 0)) + (k - 1) * d.get("extra_every", 0)
        while d.get("extra_every") and x["dex"] >= at(k) and k <= top:
            sl = d["extra_slopes"][min(k, len(d["extra_slopes"])) - 1]
            self.extra.append(min(d["extra_max"], (x["dex"] - at(k)) * sl) / 100)
            k += 1
        self.speed = 1
        self.att = self.prof + (x["dex"] // st["dex"]["att_per"] if st["dex"].get("att_per") else 0) + magic
        if st["str"].get("dmg_pct"):                                  # (21/11) FOR in % del danno dell'arma (le armi grandi rendono)
            self.dmg_pct, self.dmg_k = x["str"] * st["str"]["dmg_pct"], magic
        else:
            self.dmg_pct, self.dmg_k = 0, x["str"] // st["str"]["dmg_per"] + magic
        ac, cap = 10, 99
        self.armor, self.shield = armor, "" if self.two_handed else shield
        AR = NA if nextgear else R["armors"]
        SH = NS if nextgear else R["shields"]
        if armor:
            ac += AR[armor]["ac"] + magic
            cap = R["dex_cap"][AR[armor]["type"]]
        if self.shield:
            ac += SH[self.shield]["ac"] + magic
        self.ac = ac + (min(x["dex"] // st["dex"]["ac_per"], cap) if st["dex"].get("ac_per") else 0)
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
        p = 100 + getattr(self, "dmg_pct", 0)
        return self.dice.min * p // 100 + self.dmg_k, self.dice.max * p // 100 + self.dmg_k

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
    # (21/11) attacchi extra della DES: contano solo sugli Slash (quota monsters.extra_weight del danno; le abilita' no)
    dpr_bal = pp * (bal.dice.avg * (100 + bal.dmg_pct) / 100 + bal.dmg_k) * (1 + M.get("extra_weight", 1) * sum(bal.extra)) / bal.rate
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
BOSS_FLOORS = {5: "abbot", 10: "stitch", 15: "varok", 20: "lord"}
MECH = ("base", "game", "new")          # no mechanics / as in the game today / game + proposals of 20/11


def make(rules, name, floor, off=0):
    lv = min(NF, floor + off)
    return hero_today(name, floor, lv) if rules == "oggi" else NextHero(name, floor, lv)


def mon_of(rules):
    return monster_next if rules == "next" else _monster0


def run_floor(rules, name, floor, belt, runs, rng, off=0):
    S.monster = mon_of(rules)                                       # final boss summons too
    mon = (lambda n, f, b: monster_next(n, f, b)) if rules == "next" else None
    st = {}
    d = r = k = 0
    for _ in range(runs):
        h = make(rules, name, floor, off)
        x, y, z = SF.run(floor, belt, rng, hero=h, mon=mon, stats=st)
        d, r, k = d + x, r + y, k + z
    nm = max(1, st.get("monsters", 0))
    return dict(deaths=d / runs, returns=r / runs, drunk=k / runs, per10=10 * (d + r) / nm, mons=nm / runs,
                m_hit=100 * st["m_hits"] / max(1, st["m_swings"]), pg_hit=100 * st["pg_hits"] / max(1, st["pg_swings"]))


def boss_fight(rules, name, floor, mech, belt, rng, off=0, hp_mult=None, hp_fixed=None):
    """one chapter boss (floors 5, 10, 15) or final boss (20) fight with a full belt: 'win' / 'lose' / 'time'.
    (22/11, D8/D16) rules 'oggi': a chapter boss in rules.yaml chapter_bosses has its fixed type and life (hp_fixed: a
    different life, for the fit)"""
    S.monster = mon_of(rules)
    key = BOSS_FLOORS[floor]
    cfg = NX["bosses"][key]
    hm = cfg["hp_mult"] if hp_mult is None else hp_mult
    mon = mon_of(rules)
    cb = (RU.R.get("chapter_bosses") or {}).get(key)
    if floor == NF:
        b = dict(mon("lord_of_ruin", NF))
    elif rules == "oggi" and cb:
        b = dict(mon(cb["type"], floor, True))
        b["hp_fixed"] = hp_fixed or cb["hp"]
    else:
        mix = [(n, c) for (n, isb), c in floor_mix(floor).items() if isb]
        n = rng.choices([x for x, _ in mix], weights=[c for _, c in mix])[0]
        b = dict(mon(n, floor, True))
    if rules == "next" and mech != "base":        # taratura della proposta: solo con le regole next e le meccaniche
        b["hp_mult"] *= hm
        b["dmg_mult"] *= cfg.get("dmg_mult", 1)
    script = None
    if mech != "base":
        script = BS.SCRIPTS[key](cfg, lambda n_, f_, bb: mon(n_, f_, boss=bb), floor, mech == "new", NX["bosses"]["skill"], rng)
    h = make(rules, name, floor, off)
    return S.fight(h, [b], rng, potions=list(SF.belt(floor, belt)), final_boss=(0 if floor == NF else None), script=script)[0]


def boss_win(rules, name, floor, mech, belt, n, rng, off=0, hp_mult=None, hp_fixed=None):
    return 100 * sum(boss_fight(rules, name, floor, mech, belt, rng, off, hp_mult, hp_fixed) == "win" for _ in range(n)) / n


def fit_chapter(floor, belt, n, rng, name="riferimento"):
    """(22/11, D16) fixed life of the chapter boss (rules today, mechanics of the game) for the hero `name` at the floor's
    level to win bosses.target.level0 of the fights (bisection); then the wins at +1, +2 levels"""
    goal = 100 * NX["bosses"]["target"]["level0"]
    lo, hi = 20, 3000
    for _ in range(11):
        mid = (lo + hi) // 2
        w = boss_win("oggi", name, floor, "game", belt, n, rng, 0, hp_fixed=mid)
        lo, hi = (mid, hi) if w > goal else (lo, mid)
    hp = (lo + hi) // 2
    return hp, [boss_win("oggi", name, floor, "game", belt, n, rng, o, hp_fixed=hp) for o in (0, 1, 2)]


def fit_boss(floor, belt, n, rng):
    """hp_mult of the boss (proposal rules, new mechanics) for the 'bilanciato' profile at the floor's level to win
    bosses.target.level0 of the fights (bisection)"""
    goal = 100 * NX["bosses"]["target"]["level0"]
    lo, hi = 0.2, 6.0
    for _ in range(9):
        mid = (lo + hi) / 2
        w = boss_win("next", "bilanciato", floor, "new", belt, n, rng, 0, mid)
        lo, hi = (mid, hi) if w > goal else (lo, mid)
    return round((lo + hi) / 2, 2)


def sheet(h):
    lo, hi = h.dmg_range()
    return "vita %4d  CA %2d  ATT %+3d  danno %2d-%-2d  cadenza %2d  rid.danno %4.1f%%  %s/%s/%s" % (
        h.hpmax, h.ac, h.att, lo, hi, h.rate, getattr(h, "dr10", 0) / 10, h.weapon, h.armor or "-", h.shield or "-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=100)
    ap.add_argument("--floors", default="1-19")
    ap.add_argument("--belt", type=int, default=4)
    ap.add_argument("--rules", default="oggi,next")
    ap.add_argument("--offsets", default="0,1,2", help="hero levels above the floor (farming)")
    ap.add_argument("--fit-bosses", action="store_true", help="only: hp_mult of each boss for the target (proposal rules)")
    ap.add_argument("--fit-chapter", help="(22/11) only: fixed life of these chapter bosses (e.g. abbot) for the target, rules today")
    a = ap.parse_args()
    rng = random.Random(2011)
    if a.fit_chapter:
        for k in a.fit_chapter.split(","):
            f = next(f for f, x in BOSS_FLOORS.items() if x == k)
            hp, ws = fit_chapter(f, a.belt, a.runs, rng)
            print("%-7s hp %d  vittorie liv +0/+1/+2: %s" % (k, hp, "/".join("%.0f" % w for w in ws)), flush=True)
        return
    if a.fit_bosses:
        for f, k in BOSS_FLOORS.items():
            print("%-7s hp_mult %.2f" % (k, fit_boss(f, a.belt, a.runs, rng)), flush=True)
        return
    lo, hi = (int(x) for x in a.floors.split("-"))
    sets = a.rules.split(",")
    offs = [int(x) for x in a.offsets.split(",")]
    names = {"oggi": ["riferimento"] + list(PROFILES), "next": list(PROFILES)}
    floors = [f for f in range(lo, hi + 1) if f not in BOSS_FLOORS]
    L = ["Profili di PG (sim_builds.py, 20/11): %d giri per piano, cintura %d, censimento %s, livelli del PG = piano %s"
         % (a.runs, a.belt, SF.CENSUS["version"], "/".join("%+d" % o for o in offs)),
         "Piani: (morti + ritorni in citta') ogni 10 mostri, per livello del PG piano%s. Boss: %% di vittorie con la cintura piena."
         % "/".join("%+d" % o for o in offs), ""]
    res, bres = {}, {}
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
        L.append("piano mostri " + "".join("| %-17s" % n for n in names[rs]))
        for f in floors:
            row, mons = "", 0
            for n in names[rs]:
                xs = [run_floor(rs, n, f, a.belt, a.runs, rng, o) for o in offs]
                for o, x in zip(offs, xs):
                    res[(rs, n, f, o)] = x
                mons = xs[0]["mons"]
                row += "| %-17s" % "/".join("%.2f" % x["per10"] for x in xs)
            L.append("%5d %6.1f " % (f, mons) + row)
            print(rs, L[-1], flush=True)
        L.append("")
        L.append("per capitolo, livello = piano (ogni 10 mostri; fra parentesi morti+ritorni per piano):")
        for c, (p, q) in enumerate(((1, 4), (6, 9), (11, 14), (16, 19)), 1):
            fs = [f for f in floors if p <= f <= q]
            if fs:
                L.append("  cap %d  " % c + "  ".join("%s %.2f (%.2f)" % (
                    n, sum(res[(rs, n, f, offs[0])]["per10"] for f in fs) / len(fs),
                    sum(res[(rs, n, f, offs[0])]["deaths"] + res[(rs, n, f, offs[0])]["returns"] for f in fs) / len(fs))
                    for n in names[rs]))
        L.append("")
        L.append("boss (%% vittorie, livello piano%s; meccaniche: base = nessuna, game = come nel gioco, new = gioco + proposte):"
                 % "/".join("%+d" % o for o in offs))
        L.append("(vita e danno dei boss x hp_mult / dmg_mult di rules_next.yaml solo con le regole next e le meccaniche; il boss"
                 " finale e' al piano 20 = livello massimo: +1/+2 non cambiano il PG)")
        L.append("boss            " + "".join("| %-17s" % n for n in names[rs]))
        for f, k in BOSS_FLOORS.items():
            for mech in MECH:
                row = "%-7s %-6s  " % (k, mech)
                for n in names[rs]:
                    ws = [boss_win(rs, n, f, mech, a.belt, a.runs, rng, o) for o in offs]
                    for o, w in zip(offs, ws):
                        bres[(rs, n, f, mech, o)] = w
                    row += "| %-17s" % "/".join("%.0f" % w for w in ws)
                L.append(row)
                print(rs, row, flush=True)
        L.append("")
    od = os.path.join(RU.ROOT, "out", "work", "simulators")
    os.makedirs(od, exist_ok=True)
    open(os.path.join(od, "sim_builds.txt"), "w").write("\n".join(L) + "\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        col = {"riferimento": "#888888", "forza": "#c0392b", "destrezza": "#27ae60", "costituzione": "#2471a3", "bilanciato": "#8e44ad"}
        fig, axs = plt.subplots(2, len(sets), figsize=(7 * len(sets), 8), squeeze=False)
        for i, rs in enumerate(sets):
            ax = axs[0][i]
            for n in names[rs]:
                ax.plot(floors, [res[(rs, n, f, offs[0])]["per10"] for f in floors], marker="o", ms=3, label=n, color=col[n])
            ax.set_title("regole %s: morti+ritorni ogni 10 mostri (liv = piano)" % rs)
            ax.set_xlabel("piano (senza i piani dei boss)")
            ax.set_xticks(floors)
            ax.grid(alpha=.3)
            ax.legend(fontsize=8)
            ax = axs[1][i]
            mech = "game" if rs == "oggi" else "new"
            xs = list(range(len(BOSS_FLOORS)))
            for n in names[rs]:
                for j, o in enumerate(offs):
                    ax.plot(xs, [bres[(rs, n, f, mech, o)] for f in BOSS_FLOORS], marker="o", ms=4, color=col[n],
                            ls=["-", "--", ":"][j % 3], label=n if j == 0 else None)
            ax.axhspan(55, 65, color="#f1c40f", alpha=.25)
            ax.set_xticks(xs)
            ax.set_xticklabels(["%s (p%d)" % (k, f) for f, k in BOSS_FLOORS.items()])
            ax.set_ylim(-3, 103)
            ax.set_title("regole %s, boss con meccaniche %s: %% vittorie (continua liv=piano, tratteggio +1, punti +2)" % (rs, mech), fontsize=9)
            ax.grid(alpha=.3)
            ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(od, "sim_builds.png"), dpi=110, bbox_inches="tight")
    except ImportError:
        pass
    print("\n".join(L))


if __name__ == "__main__":
    main()
