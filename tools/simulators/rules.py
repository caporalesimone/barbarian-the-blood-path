#!/usr/bin/env python3
"""Motore delle regole NUOVE (docs/wiki/SISTEMA_COMBATTIMENTO.md), parametri in data/rules.yaml.
Solo calcoli, niente simulazione: usato da tools/simulators/sim_rules.py e, piu' avanti, dalla generazione del database
per l'assembly. Aritmetica come sul C64: interi, divisioni per difetto."""
import os, re, random, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import items_db  # noqa: E402
R = items_db.load_rules(ROOT)     # rules.yaml + data/items/items.tsv (11/11)
NF = R["dungeon"]["floors"]            # piani del dungeon (= livello massimo prima dell'Abisso)


# ------------------------------------------------------------------ dadi
class Dice:
    """'NdS+K' -> tiro; min/max/media"""
    def __init__(self, s):
        s = str(s).replace(" ", "")
        m = re.fullmatch(r"(?:(\d+)d(\d+))?([+-]\d+)?|(\d+)", s)
        if not m:
            raise ValueError("dadi: " + s)
        if m.group(4):
            self.n, self.s, self.k = 0, 0, int(m.group(4))
        else:
            self.n, self.s, self.k = int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0)
        self.text = s

    def roll(self, rng, times=1, extra=0):
        return sum(rng.randint(1, self.s) for _ in range(self.n * times)) + self.k + extra

    @property
    def min(self):
        return self.n + self.k

    @property
    def max(self):
        return self.n * self.s + self.k

    @property
    def avg(self):
        return self.n * (self.s + 1) / 2 + self.k

    def plus(self, n_dice=0, k=0):
        d = Dice("0")
        d.n, d.s, d.k = self.n + n_dice, self.s, self.k + k
        return d


def mod(score):
    # (22/11) never below 0, as the game's modv (cursed "of weakness" items can push STR under 10)
    return max(0, (score - 10) // 2)


# ------------------------------------------------------------------ PG
def pg_scores(level, rings=None):
    P = R["player"]
    sc = dict(P["scores"])
    for k in P["reference_alloc"][:pg_points(min(level, NF))]:     # (11/11) punti statistica spesi come il riferimento
        sc[k] += 1
    if level > NF:
        steps = (level - NF) // P["epic_every"]
        order = ["str", "con", "dex"]
        for i in range(steps):
            sc[order[i % 3]] += 1
    for k, v in (rings or {}).items():
        sc[k] += v
    return sc


def prof(level):
    e = R["player"].get("prof_every", 4)
    return 2 + (min(level, NF) - 1) // e + max(0, level - NF) // 4


def pg_points(level):
    """punti statistica guadagnati fino al livello (rules.yaml player.stat_points; = pl_pts di tools/build/gen_db.py)"""
    sp = R["player"]["stat_points"]
    return sum(sp["per_level"] for l in range(2, level + 1) if sp["first"] <= l <= sp["last"] and (l - sp["first"]) % sp["every"] == 0)


def pg_hpmax(level, rings=None, hp_level1=None):
    """vita massima (11/11, come recalc_stats): hp_level1 (CON/CONMOD) + (livello - 1) x (hp_per_level + mod COS), con la
    COS di adesso (retroattiva; anelli compresi: l'anello di COS da' N x (livello + 1) come nel gioco)"""
    sc = pg_scores(level, rings)
    expr = hp_level1 or R["player"]["hp_level1"]
    hp = eval(expr.replace("CONMOD", str(mod(sc["con"]))).replace("CON", str(sc["con"])))
    return hp + (level - 1) * (R["player"]["hp_per_level"] + mod(sc["con"]))


def ring_bonus(ring):
    """'str:copper' -> {'str': 1}; '' -> None"""
    if not ring:
        return None
    stat, kind = ring.split(":")
    return {stat: 2 * R["rings"][kind]["bonus"]}      # +N al modificatore = +2N al valore


class Hero:
    """PG con equipaggiamento: armi/armature/scudi per nome (data/rules.yaml), magia +N per pezzo, anello 'stat:tipo'.
    Un'arma c'e' sempre (non esiste il PG disarmato). Arma a due mani: lo scudo e' ignorato.
    Attacco e danno: sempre mod FOR (08/11: tolto il "finesse" del pugnale)."""
    def __init__(self, level, weapon="dagger", armor="", shield="", magic=0, wmagic=None, amagic=None, smagic=None,
                 rings=None, ring="", potions=(), hp_level1=None, affixes=None):
        self.level = level
        rings = rings or ring_bonus(ring)
        self.sc = pg_scores(level, rings)
        self.m = {k: mod(v) for k, v in self.sc.items()}
        self.prof = prof(level)
        self.hpmax = pg_hpmax(level, rings, hp_level1)
        w = R["weapons"].get(weapon) or R["void_weapons"][weapon]
        self.weapon = weapon
        self.two_handed = bool(w.get("two_handed"))
        self.wmagic = magic if wmagic is None else wmagic
        self.dice = Dice(w["dice"])
        self.rate, self.pen = w["rate"], w["pen"]
        AS = R["player"]["attack_speed"]          # (18/11) cadenza: arma + max(0, slow - per_dex x mod DES) (recalc_stats)
        self.rate += max(0, AS["slow"] - AS["per_dex"] * self.m["dex"])
        self.speed = 1
        amod = self.m["str"]
        self.att = self.prof + amod + self.wmagic
        dmod = amod
        self.dmg_k = dmod + self.wmagic
        ac = 10
        cap = 99
        self.armor, self.shield = armor, "" if self.two_handed else shield
        if armor:
            a = R["armors"][armor]
            ac += a["ac"] + (magic if amagic is None else amagic)
            cap = R["dex_cap"][a["type"]]
        if self.shield:
            ac += R["shields"][self.shield]["ac"] + (magic if smagic is None else smagic)
        self.ac = ac + min(self.m["dex"], cap)
        self.dc = 8 + self.prof + self.m["str"]
        self.crit = 19 if level >= R["skills"]["brutal_critical_level"] else 20
        self.potions = list(potions)
        # (21/11 evening, affixes phase 4, as recalc_stats / hurt_player) life, damage taken -N, penetration, speed (frames less, at least 6)
        af = affixes or {}
        self.hpmax += af.get("life", 0)
        self.gethit = af.get("gethit", 0)
        self.pen += af.get("pen", 0)
        self.rate = max(6, self.rate - af.get("speed", 0))

    def skills(self):
        return [k for k, v in R["skills"].items() if isinstance(v, dict) and v["level"] <= self.level]

    def dmg_range(self):
        return self.dice.min + self.dmg_k, self.dice.max + self.dmg_k

    def rage_bonus(self):
        d = R["skills"]["rage"]["damage"]
        return {"prof": self.prof, "strmod": self.m["str"]}.get(d) if isinstance(d, str) else int(d)


# ------------------------------------------------------------------ mostri
def monster(name, floor, boss=False, scale=None):
    """statistiche di un mostro del tipo `name` al piano `floor` (vita come dadi da tirare)"""
    t = chapter_entry(name, floor)
    g = R["growth"]
    sc = scale or R["monster_scale"]
    V = max(0, floor - NF) if not t.get("final") else 0     # piani dell'Abisso oltre il dungeon
    floor = min(floor, NF) if not t.get("final") else floor
    P = 0 if t.get("final") else max(0, floor - t["floor"])
    hp = Dice(t["hp"]).plus(n_dice=int(P * g["hp_dice_per_floor"]))
    m = dict(name=name, hp=hp, ac=t["ac"] + int(P * g["ac_per_floor"]), att=t["att"] + int(P * g["att_per_floor"]),
             dmg=Dice(t["dmg"]).plus(k=int(P * g["dmg_per_floor"])), save=t["save"] + int(P * g["att_per_floor"]) // 2,
             xp=t["xp"], level=floor + (2 if t.get("strong") else 0),      # come kill_monster: piano (+2 forte, +1 boss)
             hp_mult=sc["hp"] * curve(floor, "hp", t) * (R.get("final_boss_hp_mult", 1) if t.get("final") else 1),
             dmg_mult=sc["damage"] * curve(floor, "dmg", t),
             final=bool(t.get("final")), strong=bool(t.get("strong")), stun_immune=bool(t.get("stun_immune")))
    if V:                                                    # Abisso: segue il PG di riferimento (fit_void)
        vc = void_curve()
        v = min(V, len(vc["ac"]) - 1)
        m["ac"] += vc["ac"][v]
        m["att"] += vc["att"][v]
        m["save"] += vc["ac"][v] // 2
        m["hp_mult"] *= vc["hp"][v]
        m["dmg_mult"] *= vc["dmg"][v]
        m["level"] += V
    if boss and not m["final"]:
        b = R["boss"]
        m["hp_mult"] *= R["void"].get("boss_hp_mult", b["hp_mult"]) if V else b["hp_mult"]
        m["ac"] += b["ac_add"]
        m["att"] += b["att_add"]
        m["boss"] = True            # immune al blocco da colpo (decisione 4b, src/game/combat.asm hit_one)
        m["level"] += 1             # livello del mostro = piano (+2 forte) +1 boss (kill_monster)
    return m


_CH = {}


def chapter_entry(name, floor):
    """(24/11, M9) scheda del tipo `name` nei piani di un capitolo con own_stats (tools/build/mon_stats.py, come gfx_install):
    stessi dadi della vita e del danno del capitolo 1, bonus fissi, CA, ATT, salvezza ed esperienza del capitolo"""
    t = R["monsters"][name]
    c = (floor - 1) // 5 + 1 if 1 <= floor <= NF else 0
    if t.get("final") or not c:
        return t
    if c not in _CH:
        import mon_stats as MS, bestiary as BE
        own = MS.own_chapters()
        _CH[c] = None
        if c in own:
            B = BE.load_balance(ROOT)
            R1 = dict(R, monsters={r["id"]: BE.rules_entry(r) for r in BE.game_rows()})
            _CH[c] = ([r["id"] for r in BE.game_rows()], MS.chapter_tables(R1, B, c))
    if _CH[c] is None or name not in _CH[c][0]:
        return t
    ids, tb = _CH[c]
    x = ids.index(name) + 1
    hn, hs, hk = MS_dice(t["hp"])
    h = tb["hp_lo"][x] + 256 * tb["hp_hi"][x]
    dn, ds, _ = MS_dice(t["dmg"])
    e = dict(t, ac=tb["ac"][x], att=tb["att"][x], save=tb["sv"][x], xp=tb["xp_lo"][x] + 256 * tb["xp_hi"][x],
             hp="%dd%d%+d" % (hn, hs, round(h - hn * (hs + 1) / 2)) if hn else str(h),
             dmg="%dd%d%+d" % (dn, ds, tb["dk"][x]) if dn else str(tb["dk"][x]))
    return e


def MS_dice(s):
    import mon_stats as MS
    return MS.dice(s)


def curve(floor, what, t=None):
    """moltiplicatore per piano (growth.curve_hp / curve_dmg, indice = piano); il boss finale ne e' escluso"""
    if t is not None and t.get("final"):
        return 1.0
    c = R["growth"].get("curve_" + what)
    return c[min(floor, len(c) - 1)] if c else 1.0


# ------------------------------------------------------------------ Abisso
def void_hero(level, potions=()):
    """PG di riferimento nell'Abisso (livello = piano, NF+1..255): migliore spada vichinga con livello oggetto <= livello,
    armatura di piastre, magia +3 -> +8 (+1 ogni 40 piani), anello d'oro di forza"""
    v = R["void"]["reference"]
    mg = min(v["magic_max"], v["magic_base"] + (level - NF) // v["magic_every"])
    w = "viking_sword"
    for k, x in R["void_weapons"].items():
        if x["ilvl"] <= level:
            w = k
    return Hero(level, w, v["armor"], v["shield"], mg, ring="str:%s" % v["ring"], potions=potions)


VMAX = 255 - NF                         # ultimo V dell'Abisso (livello 255)
_VC = {}


def fit_void(hardening=None):
    """crescita dei mostri dell'Abisso per piano V (0..VMAX: livello NF..255) che segue il PG di riferimento:
    CA += crescita ATT del PG + indurimento, ATT += crescita CA del PG, danno x vita PG, vita x danno medio PG.
    Come sul C64: valori calcolati ogni 16 piani e interpolati in mezzo."""
    hard = R["void"]["hardening"] if hardening is None else hardening
    def pg(L):
        h = void_hero(L)
        return h.att, h.ac, h.hpmax, (h.dice.avg + h.dmg_k) * 50 / h.rate
    a0, c0, h0, d0 = pg(NF)
    pts = list(range(0, VMAX + 1, 16)) + [VMAX]
    samp = {}
    for V in pts:
        a, c, hp, d = pg(NF + V)
        samp[V] = (a - a0 + hard * V / VMAX, c - c0, hp / h0, d / d0)
    out = {"ac": [], "att": [], "hp": [], "dmg": []}
    for V in range(0, VMAX + 1):
        lo = max(p for p in pts if p <= V)
        hi = min(p for p in pts if p >= V)
        f = 0 if hi == lo else (V - lo) / (hi - lo)
        x = [samp[lo][i] + (samp[hi][i] - samp[lo][i]) * f for i in range(4)]
        out["ac"].append(int(round(x[0])))
        out["att"].append(int(round(x[1])))
        out["hp"].append(x[3])
        out["dmg"].append(x[2])
    _VC.clear()
    _VC.update(out)
    _VC["hardening"] = hard
    return out


def void_curve():
    """crescita per piano dell'Abisso: dalla tabella void.table di data/rules.yaml (righe [V, ca, att, vita, danno] a passi
    di 16 piani, interpolate) se c'e', altrimenti dal conto analitico (fit_void)"""
    if not _VC:
        tb = R["void"].get("table")
        if tb:
            out = {"ac": [], "att": [], "hp": [], "dmg": []}
            for V in range(0, VMAX + 1):
                lo = max(r for r in tb if r[0] <= V)
                hi = min(r for r in tb if r[0] >= V)
                f = 0 if hi[0] == lo[0] else (V - lo[0]) / (hi[0] - lo[0])
                x = [lo[i] + (hi[i] - lo[i]) * f for i in range(1, 5)]
                out["ac"].append(int(round(x[0])))
                out["att"].append(int(round(x[1])))
                out["hp"].append(x[2])
                out["dmg"].append(x[3])
            _VC.update(out)
        else:
            fit_void()
    return _VC


def floor_types(floor, strong=False):
    return [k for k, v in R["monsters"].items() if v["floor"] <= floor and bool(v.get("strong")) == strong and not v.get("final")]


def hit_chance(att, ac):
    return sum(1 for d in range(1, 21) if d == 20 or (d != 1 and d + att >= ac)) / 20


# ------------------------------------------------------------------ pozioni
def potion_zone(floor):
    """zona (0, 1, 2) del piano nel dungeon; oltre il dungeon: 2 (la viola; le altre pozioni escono ancora fino al piano
    dato da potions.abyss_drop: vedi abyss_weights / abyss_belt)"""
    z = R["potions"]["zones"]
    if floor > NF:
        return 2
    return 0 if floor <= round(z[0] * NF) else (1 if floor <= round(z[1] * NF) else 2)


def abyss_weights(floor):
    """(15/11, TODO J4) peso relativo di ogni pozione al piano dell'Abisso (floor > NF), da potions.abyss_drop:
    [a, b] = peso 1 fino al piano a, poi (b+1-piano)/(b+1-a) per a < piano <= b, 0 oltre b; la viola sempre 1"""
    ad = R["potions"]["abyss_drop"]
    out = {}
    for k, v in R["potions"].items():
        if not isinstance(v, dict) or "zone" not in v:
            continue
        if k in ad:
            a, b = ad[k]
            out[k] = 1.0 if floor <= a else ((b + 1 - floor) / (b + 1 - a) if floor <= b else 0.0)
        else:
            out[k] = 1.0
    return out


def abyss_belt(floor, slots=4):
    """cintura attesa all'Abisso: `slots` pozioni nelle proporzioni dei pesi di abyss_weights (resti piu' grandi), in ordine
    di zona (rossa, gialla, viola)"""
    w = abyss_weights(floor)
    ks = sorted(w, key=lambda k: R["potions"][k]["zone"])
    tot = sum(w.values())
    q = [slots * w[k] / tot for k in ks]
    n = [int(x) for x in q]
    for i in sorted(range(len(ks)), key=lambda i: q[i] - n[i], reverse=True)[:slots - sum(n)]:
        n[i] += 1
    return [k for k, c in zip(ks, n) for _ in range(c)]


def potion_weights(floor):
    """peso relativo di ogni pozione al piano: 1 nella propria zona, ramp[d-1] a d piani di distanza, 0 oltre
    (Abisso, piano > NF: abyss_weights)"""
    if floor > NF:
        return abyss_weights(floor)
    z = R["potions"]["zones"]
    b = [1, round(z[0] * NF) + 1, round(z[1] * NF) + 1, 10 ** 6]      # primo piano di ogni zona (+ fine)
    out = {}
    for k, v in R["potions"].items():
        if not isinstance(v, dict) or "zone" not in v:
            continue
        lo, hi = b[v["zone"]], b[v["zone"] + 1] - 1
        if v["zone"] == 2:
            hi = 10 ** 6
        d = max(0, lo - floor, floor - hi)
        ramp = R["potions"]["ramp"]
        out[k] = 1.0 if d == 0 else (ramp[d - 1] if d <= len(ramp) else 0.0)
    return out


# ------------------------------------------------------------------ bottino
def loot_items():
    """oggetti base con livello oggetto e rarita' (provvisorio: armi/armature/scudi comuni)"""
    out = {}
    for cat in ("weapons", "armors", "shields"):
        for k, v in R[cat].items():
            out[k] = dict(cat=cat, ilvl=v["ilvl"], rarity=R["loot"]["rarity"]["common"], chase=False)
    return out


def loot_g(d, chase=False):
    if d < 0:
        return 0
    t = R["loot"]["g_chase" if chase else "g_common"]
    return t[d] if d < len(t) else t[-1]


def loot_probs(area_level, items=None, cat=None):
    items = items or loot_items()
    w = {k: v["rarity"] * loot_g(area_level - v["ilvl"], v["chase"]) for k, v in items.items() if cat is None or v["cat"] == cat}
    s = sum(w.values())
    return {k: (x / s if s else 0) for k, x in w.items()}
