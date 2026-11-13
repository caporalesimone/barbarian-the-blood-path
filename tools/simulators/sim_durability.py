#!/usr/bin/env python3
"""Durabilita' degli oggetti (data/rules.yaml: durability) - stessa regola di dur_roll in src/game/game.asm.

Generazione: con probabilita' ilvl_weight_percent il livello oggetto pesa (uniforme fra min + floor_per_ilvl x ilvl
e max), altrimenti uniforme fra min e max. Usura: 1 punto con probabilita' 1/N per evento (colpo a segno per
l'arma, colpo subito per armatura e scudo). Stima della vita utile in piani con i colpi medi per piano del
simulatore (sim_rules.py: colpi del PG e colpi subiti nei combattimenti di riferimento).

Uso: python3 tools/simulators/sim_durability.py [--n 100000]"""
import argparse, os, random, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build"))   # (13/11) generatori in tools/build/
import rules as RU

D = RU.R["durability"]


def dur_roll(ilvl, rng=random):
    """Replica di dur_roll (src/game/game.asm)."""
    lo = D["min"]
    if rng.randrange(100) < D["ilvl_weight_percent"]:
        lo = D["min"] + D["floor_per_ilvl"] * ilvl
    return lo + rng.randrange(D["max"] + 1 - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100000)
    a = ap.parse_args()
    rng = random.Random(1)
    items = []
    for sec in ("weapons", "armors", "shields"):
        for k, it in RU.R[sec].items():
            if it.get("loot") is False:
                continue
            items.append((k, it["ilvl"], sec))
    print("durabilita': min %d max %d, peso del livello oggetto %d%% (minimo +%d per ilvl)" %
          (D["min"], D["max"], D["ilvl_weight_percent"], D["floor_per_ilvl"]))
    print("%-14s %4s %6s %6s %6s %7s %7s" % ("oggetto", "ilvl", "media", "p10", "p90", "<50", "<100"))
    for k, ilvl, sec in items:
        v = sorted(dur_roll(ilvl, rng) for _ in range(a.n))
        print("%-14s %4d %6.0f %6d %6d %6.1f%% %6.1f%%" % (k, ilvl, statistics.mean(v), v[a.n // 10], v[a.n * 9 // 10],
              100 * sum(1 for x in v if x < 50) / a.n, 100 * sum(1 for x in v if x < 100) / a.n))
    # usura misurata con il simulatore dei combattimenti (sim_rules.py): colpi a segno del PG e colpi subiti per
    # piano (mostri medi del piano, 15% forti dal piano 3, + il boss) e nel solo combattimento col boss
    import math, yaml
    import sim_rules as S
    W = D["wear"]
    import bestiary
    B = bestiary.load_balance()       # balance.yaml + mostri (data/monsters/bestiary.tsv, 11/11)
    mx, mn = B["spawn"]["max_monsters_per_level"], B["spawn"]["min_monsters_per_level"]
    NF, nst = RU.NF, len(mx)
    step = lambda L: nst if L == NF else max(1, min(nst - 1, round(L * (nst - 1) / (NF - 1))))
    POT = ["red", "red", "yellow", "violet"]
    pb = lambda H, d, p: sum(math.comb(H, k) * p ** k * (1 - p) ** (H - k) for k in range(d, H + 1)) if H >= d else 0.0
    pw = 1 / W["weapon_per_hit"]
    print("\nusura (1 punto ogni %d colpi a segno dell'arma, %d colpi subiti per l'armatura, %d per lo scudo), PG di riferimento:" %
          (W["weapon_per_hit"], W["armor_per_hit"], W["shield_per_hit"]))
    edur = lambda il: statistics.mean(dur_roll(il, rng) for _ in range(4000))
    print("%5s %6s %7s %7s %7s %7s | %s" % ("piano", "mostri", "arma", "armat.", "scudo", "piani/rip.",
                                          "boss: colpi, usura arma, P(rottura) con durabilita' 15 / 20 / 25 | avviso (%d%%)" % D["warn_percent"]))
    per_rep = []
    tw = 0
    for fl in range(1, NF):
        h = S.ref_hero(fl, potions=POT)
        g = S.groups(fl)
        n = a.n // 1000 if a.n >= 20000 else 20
        r1 = S.series(h, g["1 base"], fl, n=n)
        rs = S.series(h, g["1 forte"], fl, n=n)
        rb = S.series(h, g["boss del piano"], fl, n=n, boss_idx=0)
        m = (mx[step(fl) - 1] + mn[step(fl) - 1]) / 2
        fs = 0.15 if fl >= 3 else 0
        hits = m * ((1 - fs) * r1["pg_hits"] + fs * rs["pg_hits"]) + rb["pg_hits"]
        taken = m * ((1 - fs) * r1["m_hits"] + fs * rs["m_hits"]) + rb["m_hits"]
        tw += hits * pw
        H = round(rb["pg_hits"])
        rw = RU.R["reference"][fl]["weapon"]
        fr = edur(RU.R["weapons"][rw]["ilvl"]) / max(0.1, hits * pw)
        per_rep.append((fl, fr))
        wd = edur(RU.R["weapons"][rw]["ilvl"]) * D["warn_percent"] / 100     # soglia dell'avviso nell'HUD
        print("%5d %6.1f %7.0f %7.0f %7.0f %7.1f | %3d colpi, %4.1f punti, %4.0f%% / %4.0f%% / %4.0f%% | <= %2.0f, P(rottura) %3.0f%%" %
              (fl, m, hits * pw, taken / W["armor_per_hit"], taken / W["shield_per_hit"], fr, H, H * pw,
               100 * pb(H, 15, pw), 100 * pb(H, 20, pw), 100 * pb(H, 25, pw), wd, 100 * pb(H, max(1, int(wd)), pw)))
    deep = [fr for fl, fr in per_rep if fl >= 10]
    print("usura totale dell'arma nei piani 1-%d: ~%.0f punti; piani per riparazione (arma del PG di riferimento, "
          "durabilita' media): %.1f ai piani 10-%d" % (NF - 1, tw, statistics.mean(deep), NF - 1))
    hf = S.ref_hero(NF, potions=POT)
    rf = S.series(hf, ["lord_of_ruin"], NF, n=max(20, a.n // 2000), final=True)
    H = round(rf["pg_hits"])
    print("boss finale: %d colpi a segno, usura dell'arma ~%.0f punti; rottura solo con durabilita' <= %d circa" %
          (H, H * pw, max(d for d in range(1, 60) if pb(H, d, pw) >= 0.01)))
    print("\nriparazione: %d%% del prezzo, il massimo cala di 1 (sim: %d riparazioni possibili per durata %d)" %
          (D["repair_cost_percent"], 100, 100))


if __name__ == "__main__":
    main()
