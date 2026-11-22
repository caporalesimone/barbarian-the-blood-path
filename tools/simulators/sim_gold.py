#!/usr/bin/env python3
"""Oro del gioco, piano per piano (rifatto il 20/11: Monte Carlo sul censimento dei piani veri).

Base: il censimento dei piani generati dal gioco vero (tools/vice/floor_census.py -> tools/simulators/data/floor_census.json:
per seme e piano 1..20 i tipi dei mostri, il boss del piano, i tipi dei bauli). Su quei piani si tirano le regole del codice
(src/game/game.asm, data/balance.yaml, data/items/items.tsv, data/rules.yaml):
  - mostro comune ucciso: chiave drops.key.chance %; un tiro drops.outcome: gold_only (min..max + per_dungeon_level x piano,
    al massimo 255) / chest (tesoro: oro + drops.chest.items oggetti) / nothing; chestLevel = per_floor x piano +
    llb_mult x llb(tipo) + strong_bonus se variante forte (la correzione della vita, +-hp_bonus, e' simmetrica: ignorata);
  - boss del piano (anche quello di un capitolo): chiave + tesoro con boss.loot_items oggetti, chestLevel + boss.loot_level_add;
  - bauli del piano: normale (livello piano + min(2 tiri) se bias_low), con chiave e d'oro (servono chiavi: massimo 10);
  - oro di un tesoro o baule: T x gold_amount (T = chestLevel / 8); piano 20: 4 bauli epici da final_gold e 3 oggetti
    (categorie 1..4, livello = T); nessun bottino dal boss finale;
  - oggetto: categoria da loot.category_weights, L = round(T x u^2) <= max_loot_level, il migliore della categoria con
    ilvl <= L (nessuno: altra categoria), pozione con le soglie per piano (rules.yaml potions, come gen_db.py);
    vendita = prezzo / shop_rules.sell_divisor (2 se manca: meta').
Ipotesi: livello del PG = piano (nessun bottino perso per livello alto), tutto ucciso e tutto aperto, nessuna spesa.
Abisso (piani > 20, non nel codice): composizione dei piani 16..19 al chestLevel del piano (ipotesi).

Uso:  python3 tools/simulators/sim_gold.py [--runs N] [--floors N] [--csv file]
Report: out/work/simulators/sim_gold.txt. Da Python: per_floor(lo, hi, abyss) (usata da chapters.py)."""
import argparse, json, math, os, random, statistics, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(ROOT, "tools", "build"))
import bestiary  # noqa: E402
import items_model as IM  # noqa: E402

B = bestiary.load_balance()
R = yaml.safe_load(open(os.path.join(ROOT, "data", "rules.yaml")))
CENSUS = json.load(open(os.path.join(HERE, "data", "floor_census.json")))
DR, CH, CL, LO = B["drops"], B["chests"], B["chest_level"], B["loot"]
SELL_DIV = B.get("shop_rules", {}).get("sell_divisor", 2)
MAXLL = LO["max_loot_level"]
NF = 20
KEYS_MAX = 10
FIN_GOLD = CH["final_gold"]
CATS = ["weapon", "armor", "shield", "ring", "potion", "scroll"]


def _llb():
    """loot_level_bonus dei tipi 0..9: tipo 0 = nessuno, poi i mostri di balance.yaml nell'ordine dei tipi del gioco
    (gen_db.py mon_llb: fallen .. lord_of_ruin)"""
    return [0] + [m.get("loot_level_bonus", 0) for m in B["monsters"].values()]


LLB = _llb()


def _items():
    """per categoria: lista (ilvl, prezzo) degli oggetti base di data/items/items.tsv, ordinata per ilvl"""
    rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(ROOT, "data", "items", "items.tsv"))]
    h = rows[0]
    cat = {c: [] for c in CATS}
    pots = {}
    for r in rows[1:]:
        d = dict(zip(h, r))
        if d.get("tier") != "base" or not d.get("price"):
            continue
        t = d["type"]
        if t in ("weapon", "armor", "shield", "ring"):
            cat[t].append((int(d["ilvl"] or 0), int(d["price"]), d["id"]))
        elif t == "potion":
            pots[d["id"]] = int(d["price"])
        elif t == "scroll":
            cat["scroll"].append((0, int(d["price"]), d["id"]))
    for c in cat:
        cat[c].sort()
    return cat, [pots.get(k, 0) for k in ("red", "yellow", "violet")]


ITEMS, POT_PRICE = _items()


def _pot_thresholds():
    """soglie pot_t1 / pot_t2 per piano 0..20, come gen_db.py"""
    pz = R["potions"]
    z = pz["zones"]
    zb = [1, round(z[0] * NF) + 1, round(z[1] * NF) + 1]
    t1, t2 = [], []
    for f in range(NF + 1):
        wt = []
        for kz in range(3):
            lo, hi = zb[kz], (zb[kz + 1] - 1 if kz < 2 else 10 ** 6)
            d = max(0, lo - f, f - hi)
            wt.append(1.0 if d == 0 else (pz["ramp"][d - 1] if d <= len(pz["ramp"]) else 0.0))
        tot = sum(wt) or 1
        t1.append(min(255, round(256 * wt[0] / tot)))
        t2.append(min(255, round(256 * (wt[0] + wt[1]) / tot)))
    return t1, t2


POT_T1, POT_T2 = _pot_thresholds()
_cw = LO["category_weights"]
CUM = list(__import__("itertools").accumulate(_cw.get(c, 0) for c in CATS))


def gen_item(rng, cl, floor, force=0):
    """valore di vendita di un oggetto nato con chestLevel cl"""
    t = min(cl, 255) // 8
    while True:
        if force:
            c = CATS[force - 1]
        else:
            r = rng.randrange(CUM[-1])
            c = CATS[next(i for i, v in enumerate(CUM) if r < v)]
        if c == "potion":
            if floor > NF:
                return POT_PRICE[2] // SELL_DIV
            r = rng.randrange(256)
            return POT_PRICE[0 if r < POT_T1[floor] else 1 if r < POT_T2[floor] else 2] // SELL_DIV
        if c == "scroll":
            return ITEMS["scroll"][0][1] // SELL_DIV
        u = rng.randrange(256) / 256
        lvl = min(MAXLL, t if force else round(t * u * u))
        best = [(p, k) for il, p, k in ITEMS[c] if il <= lvl]
        if best:                          # (21/11 evening) with the affixes of the game (af_gen / it_cost: items_model)
            p, k = best[-1]
            # (22/11, D9) no unique from the common treasures (only boss chests: IM.boss_unique_roll, not modelled here)
            return max(1, p + IM.affix_price(IM.affix_roll(rng, c, k, lvl, t))) // SELL_DIV


def chest_gold(rng, cl):
    t = min(cl, 255) // 8
    ga = CH["gold_amount"]
    return rng.randint(ga["min_per_loot_level"] * t, ga["max_per_loot_level"] * t)


def floor_run(rng, comp, floor, keys):
    """(oro trovato, valore di vendita del bottino, chiavi) di un piano"""
    gold = sell = 0
    if floor == NF:
        for k in range(4):
            gold += FIN_GOLD
            for _ in range(3):
                sell += gen_item(rng, 255, floor, k + 1)
        return gold, sell, keys
    out = DR["outcome"]
    g = DR["gold"]
    for i, ty in enumerate(comp["m"]):
        cl = CL["per_floor"] * floor + CL["llb_mult"] * LLB[ty] + (CL["strong_bonus"] if 5 <= ty <= 8 else 0)
        if i + 1 == comp["boss"]:
            keys = min(KEYS_MAX, keys + 1)
            cl += B["boss"]["loot_level_add"]
            gold += chest_gold(rng, cl)
            for _ in range(B["boss"]["loot_items"]):
                sell += gen_item(rng, cl, floor)
            continue
        if rng.randrange(100) < DR["key"]["chance"]:
            keys = min(KEYS_MAX, keys + 1)
        r = rng.randrange(100)
        if r < out["gold_only"]:
            gold += min(255, rng.randint(g["min"], g["max"]) + g["per_dungeon_level"] * floor)
        elif r < out["gold_only"] + out["chest"]:
            gold += chest_gold(rng, cl)
            for _ in range(rng.randint(DR["chest"]["items"]["min"], DR["chest"]["items"]["max"])):
                sell += gen_item(rng, cl, floor)
    for c in comp["ch"]:
        kind = {1: "normal", 2: "key", 3: "gold"}[c & 3]
        spec = CH[kind]
        if spec["key_required"]:
            if keys == 0:
                continue
            keys -= 1
        lo, hi = spec["loot_level"]["min"], spec["loot_level"]["max"]
        off = min(rng.randint(lo, hi), rng.randint(lo, hi)) if spec.get("bias_low") else rng.randint(lo, hi)
        cl = CL["per_floor"] * (floor + off)
        gold += chest_gold(rng, cl)
        for _ in range(rng.randint(spec["items"]["min"], spec["items"]["max"])):
            sell += gen_item(rng, cl, floor)
    return gold, sell, keys


def simulate(runs=400, floors=40, seed=20111):
    """per piano: (oro medio, deviazione, vendita media, mostri medi, bauli medi)"""
    seeds = list(CENSUS["seeds"])
    rng = random.Random(seed)
    g = {f: [] for f in range(1, floors + 1)}
    s = {f: [] for f in range(1, floors + 1)}
    for _ in range(runs):
        keys = 0
        for f in range(1, floors + 1):
            src = f if f <= NF else rng.choice([16, 17, 18, 19])
            comp = CENSUS["seeds"][rng.choice(seeds)][str(src)]
            gg, ss, keys = floor_run(rng, comp, f, keys)
            g[f].append(gg)
            s[f].append(ss)
    cen = {}
    for f in range(1, NF + 1):
        cen[f] = (statistics.mean(len(CENSUS["seeds"][k][str(f)]["m"]) for k in seeds),
                  statistics.mean(len(CENSUS["seeds"][k][str(f)]["ch"]) for k in seeds))
    return {f: (statistics.mean(g[f]), statistics.pstdev(g[f]), statistics.mean(s[f])) + cen.get(f, (None, None))
            for f in g}


_CACHE = {}


def per_floor(lo=1, hi=None, abyss=False):
    """oro trovato medio per piano fra lo e hi (compatibile con la versione del 10/11: [0] = oro)"""
    hi = hi or lo
    n = max(hi, NF) if not abyss else max(hi, NF + 1)
    if n not in _CACHE:
        _CACHE[n] = simulate(runs=300, floors=n)
    t = _CACHE[n]
    v = [t[f][0] for f in range(lo, hi + 1)]
    return (sum(v) / len(v),)


def purse_loss(t, caps, deposit_every):
    """oro perso per il tetto del borsello: caps(f) = tetto al piano f; deposito nella locanda ogni N piani (e a fine capitolo)"""
    out = {}
    for label, k in (("medio", 0), ("ricco (media + 2 dev.)", 2)):
        carried, lost = 100.0, 0.0
        for f in range(1, NF + 1):
            got = t[f][0] + k * t[f][1]
            room = max(0.0, caps(f) - carried)
            lost += max(0.0, got - room)
            carried += min(got, room)
            if f % deposit_every == 0 or f % 5 == 0:
                carried = 0.0
        out[label] = lost
    return out


def report(t, floors):
    gmax = B["player"]["gold_max"]
    lines = ["Oro del gioco (sim_gold.py, 20/11): censimento di %d semi (versione %s, GVER %s), vendita a 1/%d del prezzo"
             % (len(CENSUS["seeds"]), CENSUS["version"], CENSUS["gver"], SELL_DIV), "",
             "%5s %7s %6s %9s %9s %10s %12s %7s" % ("piano", "mostri", "bauli", "oro", "vendita", "oro cum", "oro+vend cum", "dev.oro")]
    cg = cs = 0.0
    for f in range(1, floors + 1):
        g, sd, s, m, c = t[f]
        cg += g
        cs += s
        lines.append("%5d %7s %6s %9.0f %9.0f %10.0f %12.0f %7.0f" % (
            f, "%.1f" % m if m is not None else "-", "%.1f" % c if c is not None else "-", g, s, cg, cg + cs, sd))
    lines.append("")
    for a, b in ((1, 5), (6, 10), (11, 15), (16, 20)):
        lines.append("capitolo %d (piani %d-%d): oro %6.0f, vendita %6.0f" % ((a + 4) // 5, a, b, sum(t[f][0] for f in range(a, b + 1)),
                                                                         sum(t[f][2] for f in range(a, b + 1))))
    tot = sum(t[f][0] for f in range(1, NF))
    lines.append("")
    lines.append("bauli epici: 10%% dell'oro dei piani 1-19 = %.0f (%.0f a baule; oggi final_gold = %d)" % (tot / 10, tot / 40, FIN_GOLD))
    lines.append("")
    lines.append("Borsello: oro perso per il tetto (oro trovato, partenza 100, niente spese)")
    steps = {"oggi: %d fisso" % gmax: lambda f: gmax,
             "500/1000/3000/5000 sui boss, 10000 col finale": lambda f: 500 if f <= 5 else 1000 if f <= 10 else 3000 if f <= 15 else 5000,
             "1000/3000/5000/10000 col primo passo della catena (quests.md, P2)": lambda f: 1000 if f <= 5 else 3000 if f <= 10 else 5000 if f <= 15 else 10000}
    for name, cap in steps.items():
        for every, lab in ((1, "deposito a ogni piano"), (5, "deposito a fine capitolo")):
            r = purse_loss(t, cap, every)
            lines.append("  %-66s %-26s %s" % (name, lab, ", ".join("%s %.0f" % kv for kv in r.items())))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=2000)
    ap.add_argument("--floors", type=int, default=40)
    ap.add_argument("--csv")
    a = ap.parse_args()
    a.floors = max(a.floors, NF)       # il report dei capitoli e del borsello usa i piani 1..20
    t = simulate(a.runs, a.floors)
    txt = report(t, a.floors)
    print(txt)
    od = os.path.join(ROOT, "out", "work", "simulators")
    os.makedirs(od, exist_ok=True)
    open(os.path.join(od, "sim_gold.txt"), "w").write(txt + "\n")
    if a.csv:
        with open(a.csv, "w") as fh:
            fh.write("floor,gold,gold_sd,sell\n")
            for f in range(1, a.floors + 1):
                fh.write("%d,%.1f,%.1f,%.1f\n" % (f, t[f][0], t[f][1], t[f][2]))


if __name__ == "__main__":
    main()
