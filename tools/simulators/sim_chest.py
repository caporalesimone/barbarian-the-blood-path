#!/usr/bin/env python3
"""chestLevel e contenuto dei tesori (data/balance.yaml: chest_level, loot) - stessa regola di mon_ll / gen_item /
lt_scan in src/game/game.asm.

  CL (1..255) = per_floor x piano + loot_level_bonus x llb_mult + strong_bonus + (+-hp_bonus) + boss
  T = CL / per_floor; per ogni oggetto L = round(T x u^2) (u = rand/256, u^2 troncato a 1/256 come nel codice);
  esce l'oggetto della categoria con il livello oggetto piu' alto <= L (nessuno: altra categoria); magia +N
  tirata fra 0 e bon_tab[L]. Bauli epici (sala del trono): L = T.

Stampa, per piano, la probabilita' di ogni oggetto in un tesoro di mostro comune, forte e boss, e il livello
medio. Uso: python3 tools/simulators/sim_chest.py [--n 20000]"""
import argparse, math, os, random, sys, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build"))   # (13/11) generatori in tools/build/
import rules as RU
import items_model as IM

import bestiary
B = bestiary.load_balance()       # balance.yaml + mostri (data/monsters/bestiary.tsv, 11/11)
CL = B["chest_level"]
LO = B["loot"]
CATS = ["weapon", "armor", "shield", "ring", "potion", "scroll"]
SEC = {"weapon": "weapons", "armor": "armors", "shield": "shields", "ring": "rings"}
ITEMS = {c: sorted(((it["ilvl"], k) for k, it in RU.R[SEC[c]].items() if it.get("loot") is not False))
         for c in SEC}
MAXLL = LO["max_loot_level"]
BON = LO["bonus"]


def bon_tab(l):
    return min(BON["max"], max(BON["min"], math.floor(l * BON["per_loot_level"])))


def chest_level(floor, mon=None, strong=False, boss=False, hp="avg"):
    cl = CL["per_floor"] * floor
    if mon:
        cl += B["monsters"][mon].get("loot_level_bonus", 0) * CL["llb_mult"]
    if strong:
        cl += CL["strong_bonus"]
    cl += {"hi": CL["hp_bonus"], "lo": -CL["hp_bonus"], "avg": 0}[hp]
    if boss:
        cl += B["boss"]["loot_level_add"]
    return max(1, min(255, cl))


def gen_item(cl, rng, force=None):
    """-> (categoria, nome, magia/caratteristica, L)"""
    t = cl // CL["per_floor"]
    w = LO["category_weights"]
    cum, s = [], 0
    for c in CATS:
        s += w[c]
        cum.append(s)
    while True:
        if force:
            cat = force
        else:
            r = rng.randrange(100)
            cat = next(c for c, cu in zip(CATS, cum) if r < cu)
        if cat == "potion":
            return cat, "potion", 0, 0
        if cat == "scroll":
            return cat, "portal_scroll", 0, 0
        if force:
            l = t
        else:
            u = rng.randrange(256)
            u2 = (u * u) >> 8
            l = (t * u2 + 128) >> 8   # arrotondato (gen_item)
        l = min(l, MAXLL)
        cands = [(il, k) for il, k in ITEMS[cat] if il <= l]
        if not cands:
            continue
        il, k = max(cands)
        # (21/11 evening) affixes as the game's af_gen (items_model.affix_roll): third value = number of affixes
        aff = IM.affix_roll(rng, cat, k, l, t)
        return cat, k, bool(aff["prefix"]) + bool(aff["suffix"]), l


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    a = ap.parse_args()
    rng = random.Random(7)
    names = [k for c in ("weapon", "armor", "shield", "ring") for _, k in ITEMS[c]]
    print("chestLevel: %d x piano + bonus; oggetti per piano (tesoro di un mostro comune medio / boss), %% per oggetto" % CL["per_floor"])
    print("%5s %4s %4s " % ("piano", "CL", "CLb") + " ".join("%7s" % n[:7] for n in names) + "  affissi")
    for floor in range(1, 21):
        mon = "zombie" if floor >= 4 else "skeleton"
        for boss in (False, True):
            cl = chest_level(floor, mon, strong=boss, boss=boss)
            cnt = {n: 0 for n in names}
            mag = tot = 0
            for _ in range(a.n):
                cat, k, b, l = gen_item(cl, rng)
                if k in cnt:
                    cnt[k] += 1
                    if cat != "ring":
                        mag += b
                        tot += 1
            row = "%5d %4d %4s " % (floor, chest_level(floor, mon), cl if boss else "")
            row += " ".join("%6.1f%%" % (100 * cnt[n] / a.n) for n in names)
            row += "  %.2f" % (mag / max(1, tot))
            print(row + ("  (boss)" if boss else ""))
    print("\nbauli epici (CL 255, L = T): " + ", ".join("%s" % gen_item(255, rng, force=c)[1] for c in ("weapon", "armor", "shield", "ring")))


if __name__ == "__main__":
    main()
