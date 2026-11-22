#!/usr/bin/env python3
"""The bot on many seeds in a row, then one report of the loot of every level (22/11, TODO J15: is the loot of the levels
enough?). Each seed is a separate run of run.py (its own VICE); the reports are merged and compared with the simulator of
the chests (tools/simulators/sim_chest.py).
Usage (lab64-tools container):
    lab64 run python3 tests/bot/run_many.py [--seeds 10] [--max-level 5] [--minutes 6] [--cheat ...] [--name loot]
Output: out/work/bot/<name>_report.md and <name>_report.json (and one <name>_<seed>.json/.log per run)."""
import argparse, collections, json, os, random, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(ROOT, "out", "work", "bot")
sys.path.insert(0, os.path.join(ROOT, "tools", "simulators"))


def seeds(n):
    rng = random.Random(2211)
    a = "0123456789abcdefghijklmnopqrstuvwxyz"
    return ["".join(rng.choice(a) for _ in range(6)) for _ in range(n)]


def sim(levels, n=4000):
    """what the simulator says about a chest of a common monster and of the named boss on each level"""
    import sim_chest as SC
    out = {}
    rng = random.Random(7)
    for lv in levels:
        c = collections.Counter(); best = collections.Counter()
        for boss in (False, True):
            cl = SC.chest_level(lv, "skeleton", strong=boss, boss=boss)
            for _ in range(n):
                cat, k, b, l = SC.gen_item(cl, rng)
                c[cat] += 1
                if cat == "weapon" and k not in ("dagger",): best["weapon_better_than_dagger"] += 1
                if cat in ("weapon", "armor", "shield") and l >= 3: best["gear_ilvl3+"] += 1
        tot = sum(c.values())
        out[lv] = dict(categories={k: round(100 * v / tot, 1) for k, v in c.most_common()},
                       weapon_better_than_dagger=round(100 * best["weapon_better_than_dagger"] / tot, 1),
                       gear_ilvl3=round(100 * best["gear_ilvl3+"] / tot, 1))
    return out


def merge(name, runs):
    lv = collections.defaultdict(lambda: dict(runs=0, visits=0, seconds=0, deaths=0, potions=0, chests=0, kills=0, gold=0,
                                              items=collections.Counter(), quality=collections.Counter(), ilvl=[], names=collections.Counter(),
                                              weapon_better_than_dagger=0, gear_ilvl3=0, n_items=0, hero_in=[]))
    stops, heroes = [], []
    for r in runs:
        d = json.load(open(r))
        stops.append(d["summary"]["stop"]); heroes.append(d.get("hero", {}))
        seen = set()
        for row in d["summary"]["levels"]:
            x = lv[row["level"]]
            x["runs"] += 1; x["visits"] += row["visits"]; x["seconds"] += row["seconds"]; x["deaths"] += row["deaths"]
            x["potions"] += row["potions"]; x["chests"] += row["chests"]; x["kills"] += row["kills"]; x["gold"] += row["gold_found"]
            x["hero_in"].append(row["hero_level_in"])
        for e in d["events"]:
            if e["kind"] != "chest" or not e.get("items"):
                continue
            x = lv[e["level"]]
            for cat, il, q, nm in e["items"]:
                x["items"][cat] += 1; x["quality"][q] += 1; x["n_items"] += 1; x["names"][nm] += 1
                if cat in ("weapon", "armor", "shield"): x["ilvl"].append(il)
                if cat == "weapon" and nm.split()[-1] != "dagger": x["weapon_better_than_dagger"] += 1
                if cat in ("weapon", "armor", "shield") and il >= 3: x["gear_ilvl3"] += 1
    S = sim(sorted(lv))
    rep = dict(runs=len(runs), stops=collections.Counter(stops), levels={}, heroes=heroes, simulator=S)
    md = ["# Bottino misurato dal bot (%s, %d partite)" % (time.strftime("%d/%m %H:%M"), len(runs)), "",
          "Ogni partita: un seme diverso, nuovo eroe, il bot gioca fino al piano indicato o alla quarta morte. Bauli = bauli aperti dal bot (del piano e lasciati dai mostri). **Nota**: \"oggetti nei bauli\" conta il contenuto visto all'apertura; il simulatore (`sim_chest.py`) da' le percentuali per oggetto di un tesoro di un mostro comune (skeleton) e del boss con nome del piano.", "",
          "Come si sono fermate: " + ", ".join("%s x%d" % kv for kv in rep["stops"].items()), "",
          "| Piano | Visite | s per visita | Morti | Pozioni | Bauli | Uccisioni | Oro | Oggetti | per baule | armi/armat./scudi/anelli/pozioni/perg. | magici | ilvl medio equip | arma > pugnale | equip ilvl >= 3 | simulatore: arma > pugnale, equip ilvl >= 3 | livello eroe all'ingresso |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in sorted(lv):
        x = lv[k]; n = max(1, x["n_items"])
        it = x["items"]
        s = S.get(k, {})
        row = dict(visits=x["visits"], seconds=round(x["seconds"], 1), deaths=x["deaths"], potions=x["potions"], chests=x["chests"],
                   kills=x["kills"], gold=x["gold"], items=x["n_items"], by_category=dict(it), quality=dict(x["quality"]),
                   mean_gear_ilvl=round(sum(x["ilvl"]) / max(1, len(x["ilvl"])), 2), weapon_better_than_dagger=x["weapon_better_than_dagger"],
                   gear_ilvl3=x["gear_ilvl3"], names=dict(x["names"].most_common(12)), hero_level_in=x["hero_in"])
        rep["levels"][k] = row
        md.append("| %d | %d | %.0f | %d | %d | %d | %d | %d | %d | %.1f | %d/%d/%d/%d/%d/%d | %d | %.1f | %d (%.0f%%) | %d (%.0f%%) | %s%%, %s%% | %s |" % (
            k, x["visits"], x["seconds"] / max(1, x["visits"]), x["deaths"], x["potions"], x["chests"], x["kills"], x["gold"], x["n_items"],
            x["n_items"] / max(1, x["chests"]), it["weapon"], it["armor"], it["shield"], it["ring"], it["potion"], it["scroll"],
            x["quality"]["magic"] + x["quality"]["unique"], row["mean_gear_ilvl"], x["weapon_better_than_dagger"],
            100 * x["weapon_better_than_dagger"] / n, x["gear_ilvl3"], 100 * x["gear_ilvl3"] / n,
            s.get("weapon_better_than_dagger", "-"), s.get("gear_ilvl3", "-"), "-".join(str(h) for h in x["hero_in"][:12])))
    md += ["", "## Oggetti trovati più spesso, per piano", ""]
    for k in sorted(lv):
        md.append("- piano %d: %s" % (k, ", ".join("%s x%d" % kv for kv in lv[k]["names"].most_common(10)) or "-"))
    md += ["", "## Eroe a fine partita", ""]
    for h in heroes:
        if h: md.append("- livello %(level)d, str %(str)d dex %(dex)d con %(con)d, CA %(ac)d, oro %(gold)d, morti %(deaths)d: " % h + ", ".join(h["worn"]))
    json.dump(rep, open(os.path.join(OUT, name + "_report.json"), "w"), indent=1, default=dict)
    open(os.path.join(OUT, name + "_report.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--max-level", type=int, default=5)
    ap.add_argument("--minutes", type=float, default=6)
    ap.add_argument("--max-deaths", type=int, default=4)
    ap.add_argument("--cheat", nargs="*", default=[])
    ap.add_argument("--name", default="loot")
    ap.add_argument("--merge-only", action="store_true", help="only merge the reports already in out/work/bot")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    runs = []
    for s in seeds(a.seeds):
        f = os.path.join(OUT, "%s_%s.json" % (a.name, s))
        if not a.merge_only:
            cmd = [sys.executable, os.path.join(HERE, "run.py"), "--seed", s, "--name", "%s_%s" % (a.name, s), "--max-level",
                   str(a.max_level), "--minutes", str(a.minutes), "--max-deaths", str(a.max_deaths)]
            if a.cheat: cmd += ["--cheat"] + a.cheat
            t0 = time.time()
            r = subprocess.run(cmd, capture_output=True, text=True)
            last = [l for l in r.stdout.splitlines() if l.startswith("stop:")]
            print("seed %s: %.0f s, %s" % (s, time.time() - t0, last[0] if last else r.stdout[-200:] + r.stderr[-300:]), flush=True)
        if os.path.exists(f):
            runs.append(f)
    merge(a.name, runs)


if __name__ == "__main__":
    main()
