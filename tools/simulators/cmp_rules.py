#!/usr/bin/env python3
"""Confronti per il bilanciamento (docs/wiki/BILANCIAMENTO.md): valore di ogni oggetto, abilita' e pozione misurato con
il simulatore (tools/simulators/sim_rules.py). Stampa tabelle in Markdown.

Uso: python3 tools/simulators/cmp_rules.py [--fights 400]"""
import argparse, copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules as RU
from rules import R, NF, Hero, monster, hit_chance
import sim_rules as S

POTS = ["red", "red", "yellow", "violet"]


def md(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def run(h, floor, n, group=None, boss=False):
    G = S.groups(floor)
    g = group or G["boss del piano" if boss else "3 base"]
    return S.series(h, g, floor, n=n, seed=5, boss_idx=(0 if boss else None))


def cell(r):
    return "%.0f%% (%.0f%%, %.1f s)" % (r["winp"], r["hp_endp"], r["sec"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fights", type=int, default=400)
    a = ap.parse_args()
    N = a.fights
    out = []

    # 1. PG per livello: cosa da' il livello
    rows = []
    for lv in (1, 3, 5, 7, 9, 11, 13, 15, 17, NF):
        h = Hero(lv, "dagger", "", "")
        rows.append([lv, h.hpmax, "+%d" % h.prof, "%d/%d/%d" % (h.sc["str"], h.sc["dex"], h.sc["con"]), "+%d" % h.att, h.ac,
                     ", ".join(k for k in h.skills() if k != "slash") + (", critico 19-20" if h.crit == 19 else "")])
    out.append("## Crescita del PG per livello (pugnale, senza armatura)\n\n" + md(["livello", "vita", "comp.", "FOR/DES/COS", "ATT", "CA", "abilita'"], rows))

    # 2. armi a parita' di tutto il resto, piano 5 e piano 8 (riferimento del piano, arma variabile)
    for f in (4, 9, 15):
        r = R["reference"][f]
        rows = []
        for w in R["weapons"]:
            h = Hero(r.get("level", f), w, r["armor"], r["shield"], r["magic"], ring=r["ring"], potions=POTS)
            dps = (h.dice.avg + h.dmg_k) * 50 / h.rate
            rows.append([w, h.dice.text, "+%d" % h.dmg_k, "%d-%d" % h.dmg_range(), "%.0f ms" % (h.rate * 20), "%.1f" % dps, h.ac,
                         cell(run(h, f, N)), cell(run(h, f, N, boss=True))])
        out.append("## Armi al piano %d (livello %d, %s, %s, magia +%d)\n\n%s" % (
            f, r.get("level", f), r["armor"], r["shield"] or "niente scudo", r["magic"],
            md(["arma", "dadi", "fisso", "danno", "cadenza", "danno/s", "CA", "3 base", "boss"], rows)))

    # 3. armature e scudi (piano 5, spada)
    for f in (9, 17):
        r = R["reference"][f]
        rows = []
        for arm in [""] + list(R["armors"]):
            for sh in [""] + list(R["shields"]):
                h = Hero(r.get("level", f), "sword", arm, sh, r["magic"], ring=r["ring"], potions=POTS)
                m = monster(RU.floor_types(f)[-1], f)
                rows.append([arm or "-", sh or "-", h.ac, "%.0f%%" % (100 * hit_chance(m["att"], h.ac)), cell(run(h, f, N)), cell(run(h, f, N, boss=True))])
        out.append("## Armature e scudi al piano %d (livello %d, spada, magia +%d)\n\n%s" % (
            f, r.get("level", f), r["magic"], md(["armatura", "scudo", "CA", "mostro colpisce", "3 base", "boss"], rows)))

    # 4. anelli (piano 7)
    f = 13
    r = R["reference"][f]
    rows = []
    for ring in ["", "str:copper", "str:silver", "str:gold", "dex:gold", "con:gold"]:
        h = Hero(r.get("level", f), r["weapon"], r["armor"], r["shield"], r["magic"], ring=ring, potions=POTS)
        rows.append([ring or "-", h.hpmax, "+%d" % h.att, h.ac, "%d-%d" % h.dmg_range(), cell(run(h, f, N)), cell(run(h, f, N, boss=True))])
    out.append("## Anelli al piano %d (livello %d, riferimento)\n\n%s" % (f, r.get("level", f), md(["anello", "vita", "ATT", "CA", "danno", "3 base", "boss"], rows)))

    # 5. abilita': ogni abilita' tolta, al piano dove e' disponibile e al 10
    rows = []
    for f in (7, 13, NF):
        r = R["reference"][f]
        h = S.ref_hero(f, potions=POTS)
        base3, baseb = run(h, f, N), run(h, f, N, boss=True)
        rows.append([f, r.get("level", f), "tutte", cell(base3), cell(baseb)])
        for k in h.skills():
            if k == "slash":
                continue
            sk = copy.deepcopy(R["skills"])
            R["skills"][k]["level"] = 99
            h2 = S.ref_hero(f, potions=POTS)
            rows.append([f, r.get("level", f), "senza " + k, cell(run(h2, f, N)), cell(run(h2, f, N, boss=True))])
            R["skills"].clear()
            R["skills"].update(sk)
    out.append("## Abilita': quanto vale ognuna (tolta una alla volta)\n\n" + md(["piano", "livello", "abilita'", "3 base", "boss"], rows))

    # 6. pozioni
    rows = []
    for f in (4, 10, 16, NF):
        for pots, name in (([], "nessuna"), (["red"] * 4, "4 rosse"), (["yellow"] * 4, "4 gialle"), (["violet"] * 4, "4 viola"),
                           (POTS, "rossa, rossa, gialla, viola")):
            h = S.ref_hero(f, potions=pots)
            rb = run(h, f, N, boss=True)
            rows.append([f, name, cell(rb), "%.1f" % rb["pots"]])
    out.append("## Pozioni contro il boss del piano\n\n" + md(["piano", "cintura", "boss", "pozioni bevute"], rows))
    rows = []
    for f in list(range(1, NF + 1)) + [NF + 1, NF + 10, NF + 20, 45, 55, 70, 71, 100]:
        w = RU.potion_weights(f)
        tot = sum(w.values()) or 1
        rows.append([f] + ["%.0f%%" % (100 * w[k] / tot) for k in ("red", "yellow", "violet")])
    out.append("## Pozioni: quale esce per piano (peso relativo tra le tre)\n\n" + md(["piano", "rossa", "gialla", "viola"], rows))

    # 7. senza equipaggiamento (pugnale, niente armatura/scudo/magia/anello) al livello naturale
    rows = []
    for f in range(1, NF + 1):
        lv = R["reference"][f].get("level", f)
        h = Hero(lv, "dagger", "", "", 0, potions=POTS)
        rows.append([f, lv, cell(run(h, f, N, group=[RU.floor_types(f)[-1]])), cell(run(h, f, N)), cell(run(h, f, N, boss=True))])
    out.append("## Solo pugnale, niente armatura (livello naturale del piano)\n\n" + md(["piano", "livello", "1 base", "3 base", "boss"], rows))

    # 8. PG sopra o sotto il livello naturale, riferimento del piano
    rows = []
    for f in (2, 5, 8):
        for dl in (-4, -2, 0, 2, 4):
            lv = R["reference"][f].get("level", f) + dl
            if lv < 1 or lv > 20:
                continue
            h = S.ref_hero(f, lv, potions=POTS)
            rows.append([f, lv, "%+d" % dl, cell(run(h, f, N)), cell(run(h, f, N, boss=True))])
    out.append("## Livello diverso da quello naturale (equipaggiamento del piano)\n\n" + md(["piano", "livello", "differenza", "3 base", "boss"], rows))

    print("\n\n".join(out))


if __name__ == "__main__":
    main()
