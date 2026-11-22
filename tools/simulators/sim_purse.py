#!/usr/bin/env python3
"""Borsello (22/11, richiesta del committente): quanto pesa il tetto dell'oro addosso, capitolo per capitolo.

Il committente vuole un borsello che "si senta": all'inizio si torna spesso in citta' e l'upgrade e' un premio ambito; se con i
gradini di oggi (500, poi 1000/3000/5000/10000 dalla catena) non e' cosi', vanno ridimensionati. Questo script mette insieme
i simulatori che ci sono e conta, per piano e per capitolo:
  - entrate: oro trovato (sim_gold.py, censimento dei piani veri) e valore di vendita del bottino (1/4 del prezzo);
  - spese: pozioni bevute (sim_floor.py, PG di riferimento al suo livello, cintura da 4) al prezzo del negozio e riparazioni
    (usura del PG di riferimento: una riparazione di arma, armatura e scudo ogni RIP_FLOORS piani, rules.yaml durability,
    al 25% del prezzo dell'equipaggiamento di riferimento del piano);
  - PG "massimo" (tutto ucciso, tutto aperto, tutto venduto), "medio" (meta' delle entrate, indicazione del committente) e
    "prudente" (un terzo);
  - con un tetto T: quante volte per piano si deve tornare in citta' solo per il tetto (oro trovato in un piano / T, oltre
    ai ritorni per la cintura vuota di sim_floor), e quanti passaggi dalla locanda servono per vendere il bottino di un
    viaggio (vendita / T: il negozio non compra oltre il tetto, la locanda deposita l'oro addosso).
Ipotesi (non verificate in gioco): oro trovato e bottino del piano sono quelli di un piano esplorato tutto; un viaggio = un
piano; nessun acquisto di equipaggiamento; le pozioni trovate non sono sottratte da quelle comprate (stima per eccesso delle
spese). Uso: python3 tools/simulators/sim_purse.py [--runs N]. Report: out/work/simulators/sim_purse.txt"""
import argparse, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools", "build"))
import sim_gold as SG  # noqa: E402
import sim_floor as SF  # noqa: E402
import sim_rules as S  # noqa: E402
import rules as RU  # noqa: E402

NF = 20
RIP_FLOORS = 3                  # rules.yaml durability: "usura 2/1/1 per una riparazione ogni ~3 piani"
REP_PCT = RU.R["durability"]["repair_cost_percent"]
PRICE = {}
for _c, _lst in SG.ITEMS.items():
    for _il, _p, _k in _lst:
        PRICE[_k] = _p
CHAPTERS = [(1, 4), (6, 9), (11, 14), (16, 19)]
SETS = {
    "oggi (catena: 500, 1000 p.3, 3000 p.4, 5000 p.7, 10000 p.12)": [500, 1000, 3000, 5000],
    "committente (indicativa): 600 / 800 / 1000 / 1500": [600, 800, 1000, 1500],
    "scelta del 22/11 (nel gioco: balance.yaml player.purse; +250 per boss di capitolo)": [300, 550, 800, 1050],
}


def expenses(floor, runs, rng):
    """(pozioni bevute, spesa in pozioni, spesa in riparazioni) per piano, PG di riferimento"""
    k = 0
    for _ in range(runs):
        _, _, z = SF.run(floor, 4, rng)
        k += z
    drunk = k / runs
    w = RU.potion_weights(floor)
    tot = sum(w.values()) or 1
    pot = sum(w[c] / tot * SG.POT_PRICE[i] for i, c in enumerate(("red", "yellow", "violet")) if c in w)
    h = S.ref_hero(floor, RU.R["reference"][floor].get("level", floor))
    eq = sum(PRICE.get(x, 0) for x in (h.weapon, h.armor, h.shield) if x)
    rep = eq * REP_PCT / 100 / RIP_FLOORS
    return drunk, drunk * pot, rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=150)
    a = ap.parse_args()
    rng = random.Random(2211)
    t = SG.simulate(runs=a.runs * 2, floors=NF)
    rows = {}
    L = ["Borsello (sim_purse.py, 22/11): entrate e spese per piano, PG di riferimento al suo livello, cintura da 4", "",
         "piano  oro trov.  (ricco)  vendita  pozioni  spesa poz.  ripar.  netto max  netto/2  netto/3"]
    for f in range(1, NF):
        g, sd, s = t[f][0], t[f][1], t[f][2]
        dk, ep, er = expenses(f, a.runs, rng)
        net = g + s - ep - er
        rows[f] = dict(g=g, rich=g + 2 * sd, s=s, ep=ep, er=er, net=net)
        L.append("%5d  %9.0f  %7.0f  %7.0f  %7.1f  %10.0f  %6.0f  %9.0f  %7.0f  %7.0f" % (
            f, g, g + 2 * sd, s, dk, ep, er, net, (g + s) / 2 - ep - er, (g + s) / 3 - ep - er))
        print(L[-1], flush=True)
    L.append("")
    L.append("per capitolo (piani normali; boss esclusi): media per piano")
    L.append("cap  oro trov.  (ricco)  vendita  spese  netto max  netto/2  netto/3")
    for c, (p, q) in enumerate(CHAPTERS, 1):
        fs = range(p, q + 1)
        m = lambda k: sum(rows[f][k] for f in fs) / len(fs)  # noqa: E731
        sp = m("ep") + m("er")
        L.append("%3d  %9.0f  %7.0f  %7.0f  %5.0f  %9.0f  %7.0f  %7.0f" % (
            c, m("g"), m("rich"), m("s"), sp, m("net"), (m("g") + m("s")) / 2 - sp, (m("g") + m("s")) / 3 - sp))
    L.append("")
    L.append("Tetti per capitolo (il tetto valido per tutto il capitolo; il primo resta fino al premio della catena):")
    L.append("ritorni in citta' per piano dovuti SOLO al tetto (oro trovato del piano / tetto; > 1 = piu' di un ritorno per piano)"
             " e passaggi dalla locanda per vendere il bottino di un piano (vendita / tetto)")
    best = []
    for c, (p, q) in enumerate(CHAPTERS, 1):
        fs = range(p, q + 1)
        best.append(sum(rows[f]["g"] for f in fs) / len(fs))
    SETS["proposta: un piano di oro trovato (medio) del capitolo, arrotondato"] = [int(round(b, -2)) or 100 for b in best]
    for name, caps in SETS.items():
        L.append("  " + name)
        for c, (p, q) in enumerate(CHAPTERS, 1):
            fs = range(p, q + 1)
            T = caps[c - 1]
            for who, k in (("massimo", 1), ("medio (1/2)", 0.5), ("prudente (1/3)", 1 / 3)):
                ret = sum(rows[f]["g"] * k / T for f in fs) / len(fs)
                rich = sum(rows[f]["rich"] * k / T for f in fs) / len(fs)
                sell = sum(rows[f]["s"] * k / T for f in fs) / len(fs)
                L.append("    cap %d tetto %5d  %-15s ritorni/piano %.2f (ricco %.2f)  passaggi in locanda per vendere %.2f"
                         % (c, T, who, ret, rich, sell))
    od = os.path.join(SG.ROOT, "out", "work", "simulators")
    os.makedirs(od, exist_ok=True)
    open(os.path.join(od, "sim_purse.txt"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[-40:]))


if __name__ == "__main__":
    main()
