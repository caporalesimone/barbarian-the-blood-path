#!/usr/bin/env python3
"""Taratura automatica dei mostri (data/rules.yaml) sul PG di riferimento per piano (tools/simulators/rules.py, sim_rules.py).

1. growth.ac_per_floor / att_per_floor: probabilita' di colpire il piu' stabili possibile dal piano 1 al 10
   (PG di riferimento contro il mostro base piu' forte del piano, e viceversa). Solo conti, niente simulazione.
2. growth.curve_hp / curve_dmg (indice = piano, MONOTONE): per ogni piano, griglia di moltiplicatori di vita e danno
   a partire dal valore del piano prima; obiettivi: boss con nome del piano ~70% di vittorie, gruppo di 3 base
   vinto >= 95% con vita finale ~60% e durata 4-8 s (4 pozioni: rossa, rossa, gialla, viola).
3. final_boss_hp_mult: boss finale al livello 20 (riferimento del piano 10, 4 pozioni) ~65% di vittorie.
Scrive i valori in data/rules.yaml (ricerca riproducibile: semi fissi).

Uso: python3 tools/simulators/fit_rules.py [--fights 60] [--check 400] [--dry]"""
import argparse, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules as RU
from rules import R, NF, VMAX, hit_chance, monster
import sim_rules as S

POTS = ["red", "red", "yellow", "violet"]      # cintura di riferimento nel dungeon (nell'Abisso: RU.abyss_belt, da potions.abyss_drop)


def hit_spread(acg, attg):
    R["growth"]["ac_per_floor"], R["growth"]["att_per_floor"] = acg, attg
    pg, mo = [], []
    for f in range(1, NF + 1):
        h = S.ref_hero(f)
        m = monster(RU.floor_types(f)[-1], f)
        pg.append(hit_chance(h.att, m["ac"] - h.pen))
        mo.append(hit_chance(m["att"], h.ac))
    return pg, mo


def fit_hit():
    best = None
    for acg in [0.6 + 0.1 * i for i in range(12)]:
        for attg in [0.6 + 0.1 * i for i in range(16)]:
            pg, mo = hit_spread(acg, attg)
            sc = (max(pg) - min(pg)) + (max(mo) - min(mo)) + abs(sum(pg) / NF - 0.70) + abs(sum(mo) / NF - 0.55)
            if best is None or sc < best[0]:
                best = (sc, acg, attg, pg, mo)
    _, acg, attg, pg, mo = best
    R["growth"]["ac_per_floor"], R["growth"]["att_per_floor"] = acg, attg
    return acg, attg, pg, mo


def ev(f, hp, dm, n):
    R["growth"]["curve_hp"], R["growth"]["curve_dmg"] = hp, dm
    G = S.groups(f)
    h = S.ref_hero(f, potions=POTS)
    b = S.series(h, G["boss del piano"], f, n=n, seed=11, boss_idx=0)
    g = S.series(h, G["3 base"], f, n=n, seed=12)
    return b, g


def score(b, g):
    return ((b["winp"] - 70) ** 2 / 25 + (g["hp_endp"] - 60) ** 2 / 50
            + (max(0, 4 - g["sec"]) + max(0, g["sec"] - 8)) ** 2 * 5 + (g["winp"] < 95) * 50)


HS = [0.5 + 0.25 * i for i in range(24)]       # moltiplicatori di vita provati (0.5 .. 6.25)
DS = [0.25 + 0.25 * i for i in range(16)]      # moltiplicatori di danno provati (0.25 .. 4)


def fit_curves(n):
    """programmazione dinamica: per ogni piano il costo di ogni coppia (vita, danno) e' indipendente dagli altri piani;
    la curva migliore e' quella di costo totale minimo tra quelle MONOTONE (mai in calo da un piano al successivo)."""
    cost = {}
    for f in range(1, NF + 1):
        for h in HS:
            for d in DS:
                b, g = ev(f, [1.0] * f + [h] + [1] * (NF - f), [1.0] * f + [d] + [1] * (NF - f), n)
                cost[f, h, d] = score(b, g)
        print("   piano %d valutato (%.0f s)" % (f, time.time() - T0), flush=True)
    best = {}                                   # (f, h, d) -> (costo totale fino a f, (h, d) del piano prima)
    for f in range(1, NF + 1):
        for h in HS:
            for d in DS:
                if f == 1:
                    best[f, h, d] = (cost[f, h, d], None)
                else:
                    prev = min(((best[f - 1, h2, d2][0], (h2, d2)) for h2 in HS for d2 in DS if h2 <= h and d2 <= d),
                               default=(float("inf"), None))
                    best[f, h, d] = (cost[f, h, d] + prev[0], prev[1])
    f = NF
    _, (h, d) = min((best[NF, h, d][0], (h, d)) for h in HS for d in DS)
    hp, dm = [h], [d]
    while f > 1:
        h, d = best[f, h, d][1]
        hp.insert(0, h)
        dm.insert(0, d)
        f -= 1
    return [1.0] + hp, [1.0] + dm


def fit_final(n):
    h = S.ref_hero(NF, NF, potions=POTS)
    best = None
    for mult in [0.25 + 0.25 * i for i in range(32)]:
        R["final_boss_hp_mult"] = mult
        st0 = monster("lord_of_ruin", NF)
        rng = S.random.Random(3)
        w = sum(1 for _ in range(n) if S.fight(h, [st0], rng, potions=POTS, final_boss=0)[0] == "win") * 100 / n
        if best is None or abs(w - 65) < abs(best[1] - 65):
            best = (mult, w)
    R["final_boss_hp_mult"] = best[0]
    return best


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


def write_yaml(acg, attg, hp, dm, fmult, note, table=None):
    p = os.path.join(RU.ROOT, "data", "rules.yaml")
    s = open(p).read()
    fl = lambda v: ("%g" % v)
    s = re.sub(r"ac_per_floor: [^,]*, att_per_floor: [^,]*,", "ac_per_floor: %s, att_per_floor: %s," % (fl(acg), fl(attg)), s)
    s = re.sub(r"curve_hp:  \[[^\]]*\]", "curve_hp:  [" + ", ".join(fl(x) for x in hp) + "]", s)
    s = re.sub(r"curve_dmg: \[[^\]]*\]", "curve_dmg: [" + ", ".join(fl(x) for x in dm) + "]", s)
    s = re.sub(r"final_boss_hp_mult: [^ ]*", "final_boss_hp_mult: %s" % fl(fmult), s)
    s = re.sub(r"# curve_hp / curve_dmg \(indice = piano\): .*\n", "# curve_hp / curve_dmg (indice = piano): %s\n" % note, s)
    if table is not None:
        rows = "\n".join("    - [%d, %d, %d, %g, %g]" % tuple(r) for r in table)
        s = re.sub(r"  table:[^\n]*\n(?:    - \[[^\]]*\]\n)+", "", s)
        s = s.replace("  limits: {byte: 255, word: 65535}", "  table:   # [V = piano - 10, CA +, ATT +, vita x, danno x] da tools/simulators/fit_rules.py; interpolata tra le righe\n" + rows + "\n  limits: {byte: 255, word: 65535}")
    open(p, "w").write(s)


T0 = time.time()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fights", type=int, default=40)
    ap.add_argument("--check", type=int, default=400)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--abyss-only", action="store_true")
    ap.add_argument("--final", action="store_true", help="ritara anche final_boss_hp_mult")
    a = ap.parse_args()
    if a.abyss_only:
        table = fit_abyss(max(20, a.fights // 2))
        if not a.dry:
            write_yaml(R["growth"]["ac_per_floor"], R["growth"]["att_per_floor"], R["growth"]["curve_hp"], R["growth"]["curve_dmg"], R["final_boss_hp_mult"], "", table)
            print("scritto data/rules.yaml")
        return
    acg, attg, pg, mo = fit_hit()
    print("1. ac_per_floor %.1f att_per_floor %.1f: PG colpisce %s; mostro colpisce %s" % (
        acg, attg, " ".join("%.0f" % (100 * x) for x in pg), " ".join("%.0f" % (100 * x) for x in mo)))
    hp, dm = fit_curves(a.fights)
    print("2. curve_hp", hp, "curve_dmg", dm, "(%.0f s)" % (time.time() - T0))
    R["growth"]["curve_hp"], R["growth"]["curve_dmg"] = hp, dm
    for f in range(1, NF + 1):
        b, g = ev(f, hp, dm, a.check)
        print("   piano %2d: boss %3.0f%%  3 base %3.0f%% vita %3.0f%% %.1f s" % (f, b["winp"], g["winp"], g["hp_endp"], g["sec"]))
    if a.final:
        mult, w = fit_final(a.check)
        print("3. boss finale: vita x%.2f -> %.0f%% di vittorie (%.0f s)" % (mult, w, time.time() - T0))
    else:
        mult = R["final_boss_hp_mult"]          # la scheda del boss finale e' tarata a mano (--final per rifarla)
    print("4. Abisso (indurimento %d)" % R["void"]["hardening"])
    table = fit_abyss(max(20, a.fights // 2))
    if not a.dry:
        note = "moltiplicatori cercati da tools/simulators/fit_rules.py (%s) sul PG di riferimento: boss ~70%%, 3 base vita ~60%%, 4-8 s." % time.strftime("%d/%m")
        write_yaml(acg, attg, hp, dm, mult, note, table)
        print("scritto data/rules.yaml")


if __name__ == "__main__":
    main()
