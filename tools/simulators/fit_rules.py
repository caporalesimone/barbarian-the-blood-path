#!/usr/bin/env python3
"""Taratura automatica della crescita dei mostri nell'Abisso (data/rules.yaml void.table) sul PG di riferimento.

(24/11) Le statistiche dei mostri nei piani 1-20 non si tarano piu' qui: sono le formule del bestiario
(data/monsters/bestiary.tsv, tools/build/mon_stats.py), scelte a mano con sim_rules.py, sim_builds.py e l'arena
(docs/wiki/balancing-guide.md). Prima del 24/11 questo script tarava la crescita comune (growth.ac_per_floor,
att_per_floor, curve_hp) e final_boss_hp_mult, che non esistono piu'.

Abisso: per ogni piano campione V, CA e ATT dal conto analitico e moltiplicatori di vita e danno su una griglia
(obiettivi in fit_abyss). Scrive void.table in data/rules.yaml (ricerca riproducibile: semi fissi).

Uso: python3 tools/simulators/fit_rules.py [--fights 40] [--dry]"""
import argparse, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules as RU
from rules import R, NF, VMAX
import sim_rules as S

VS = list(range(16, VMAX, 16)) + [VMAX]     # V = piano - NF; V = 0 e' il piano NF (riga fissa [0, 0, 0, 1, 1])


def fit_abyss(n):
    """tabella dell'Abisso (void.table): per ogni piano campione V, CA e ATT dal conto analitico (fit_void, con
    l'indurimento) e moltiplicatori di vita e danno (una riga per campione, indipendenti) cercati su una griglia grossa (n combattimenti) e poi
    raffinati attorno al migliore (5n); obiettivi: boss con nome con vittorie che calano dal 70% (livello 20) al 45% (255),
    gruppo di 3 base vinto >= 95% con vita finale ~60% e 4-8 s."""
    an = RU.fit_void()
    R["void"].pop("table", None)
    table = [[0, 0, 0, 1, 1]]
    ph, pd = 0.5, 0.5

    def trial(V, lv, fl, h, hm, dm, k, tgt):
        RU._VC.clear()
        RU._VC.update({"ac": an["ac"], "att": an["att"], "hp": [an["hp"][V] * hm] * 246, "dmg": [an["dmg"][V] * dm] * 246})
        b = S.series(h, ["balrog"], fl, n=k, seed=21, boss_idx=0)
        g = S.series(h, ["demon", "skeleton", "zombie"], fl, n=k, seed=22)
        sc = ((b["winp"] - tgt) ** 2 / 10 + (g["hp_endp"] - 60) ** 2 / 50
              + (max(0, 4 - g["sec"]) + max(0, g["sec"] - 8)) ** 2 * 10 + max(0, 95 - g["winp"]) ** 2 * 10)
        return sc, b["winp"], g["winp"], g["hp_endp"], g["sec"]

    for V in VS:
        lv = fl = NF + V
        h = RU.void_hero(lv, potions=RU.abyss_belt(fl))       # (15/11, J4) cintura attesa all'Abisso (potions.abyss_drop)
        tgt = 70 - 25 * V / VMAX
        best = None
        for hm in [0.5 + 0.25 * i for i in range(24)]:
            for dm in [0.5 + 0.25 * i for i in range(14)]:
                sc = trial(V, lv, fl, h, hm, dm, n, tgt)[0]
                if best is None or sc < best[0]:
                    best = (sc, hm, dm)
        _, hm0, dm0 = best
        best = None
        for hm in [max(0.5, hm0 + 0.125 * i) for i in range(-2, 3)]:
            for dm in [max(0.5, dm0 + 0.125 * i) for i in range(-2, 3)]:
                r = trial(V, lv, fl, h, hm, dm, 5 * n, tgt)
                if best is None or r[0] < best[0]:
                    best = (r[0], hm, dm) + r[1:]
        _, hm, dm, bw, gw, ghp, gs = best
        ph, pd = hm, dm
        table.append([V, an["ac"][V], an["att"][V], round(an["hp"][V] * hm, 2), round(an["dmg"][V] * dm, 2)])
        print("   V %3d (liv %3d): CA +%d ATT +%d vita x%.2f danno x%.2f -> boss %.0f%% (obiettivo %.0f) 3 base %.0f%% vita %.0f%% %.1f s (%.0f s)" % (
            V, lv, table[-1][1], table[-1][2], table[-1][3], table[-1][4], bw, tgt, gw, ghp, gs, time.time() - T0), flush=True)
    RU._VC.clear()
    R["void"]["table"] = table
    return table


def write_yaml(table):
    p = os.path.join(RU.ROOT, "data", "rules.yaml")
    s = open(p).read()
    rows = "\n".join("    - [%d, %d, %d, %g, %g]" % tuple(r) for r in table)
    s = re.sub(r"  table:[^\n]*\n(?:    - \[[^\]]*\]\n)+", "", s)
    s = s.replace("  limits: {byte: 255, word: 65535}", "  table:   # [V = piano - 10, CA +, ATT +, vita x, danno x] da tools/simulators/fit_rules.py; interpolata tra le righe\n" + rows + "\n  limits: {byte: 255, word: 65535}")
    open(p, "w").write(s)


T0 = time.time()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fights", type=int, default=40)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    print("Abisso (indurimento %d)" % R["void"]["hardening"])
    table = fit_abyss(max(20, a.fights // 2))
    if not a.dry:
        write_yaml(table)
        print("scritto data/rules.yaml")


if __name__ == "__main__":
    main()
