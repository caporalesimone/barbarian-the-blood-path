#!/usr/bin/env python3
"""(22/11, decisioni D1-D19 del committente, docs/wiki/quests.md) Tabelle delle quest per il motore residente di GAME
(src/game/qengine.asm), da data/quests/next/quests.yaml e data/monsters/bestiary.tsv -> out/work/qtab.inc.

Numero della quest (QID) nel gioco: 1..12 i passi della catena, 13..27 le accessorie nell'ordine del file (a1.1 = 13).
Le ripetibili non ci sono (D18: dopo). Tabelle da 0 (indice = QID - 1), una riga per quest:
  qt_ty  bit 0-3 tipo dell'obiettivo (QG_*), bit 4-6 capitolo
  qt_p1  K / IM: tipo di mostro (M_*: base del capitolo 1..N_BASE, forte N_BASE+1..); P / B / IC: primo piano; C: capitolo
  qt_p2  P / B / IC: ultimo piano; IM: soglia su 256 della caduta (256 / one_in)
  qt_n   quantita' da raggiungere (B, C, IC: di solito 1)
  qt_it  oggetto di quest (1..; 0 = nessuno): nome in qi_lo / qi_hi (codici schermo, "found: ...")
G (oro all'NPC) e V (offerta al falo') li gestisce il modulo del villaggio (QGIV): qui solo il tipo e l'oro in p1/p2.
Il tipo di mostro di un capitolo e' la sua posizione nel bestiario (base e forte del capitolo, nell'ordine del file): i capitoli
2-4 usano gli stessi tipi del capitolo 1 con altri nomi e grafica (da verificare quando si estende ai capitoli 2-4, D13)."""
import csv
import os
import sys
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "out", "work", "qtab.inc")
QG = {"K": 1, "B": 2, "P": 3, "IM": 4, "IC": 5, "C": 6, "G": 7, "V": 8}
CH_LV = 5


def die(m):
    sys.exit("gen_qdata: " + m)


def main():
    q = yaml.safe_load(open(os.path.join(ROOT, "data", "quests", "next", "quests.yaml")))
    best = list(csv.DictReader(open(os.path.join(ROOT, "data", "monsters", "bestiary.tsv")), delimiter="\t"))
    mt = {}
    for c in range(1, 5):
        base = [m for m in best if int(m["chapter"]) == c and m["tier"] == "base"]
        strong = [m for m in best if int(m["chapter"]) == c and m["tier"] == "strong"]
        for i, m in enumerate(base):
            mt[(c, m["name"].lower())] = mt[(c, m["id"])] = i + 1
        for i, m in enumerate(strong):
            mt[(c, m["name"].lower())] = mt[(c, m["id"])] = len(base) + i + 1
    items = list(q["quest_items"])
    qs = [x for x in q["quests"] if x["kind"] == "chain"] + [x for x in q["quests"] if x["kind"] == "side"]
    if [x["id"] for x in qs[:12]] != list(range(1, 13)) or len(qs) != 27:
        die("servono 12 passi della catena e 15 accessorie")
    ty, p1, p2, n, it = [], [], [], [], []
    for x in qs:
        c, g = int(x["chapter"]), x["goal"]
        t = g["type"]
        a = b = 0
        k = int(g.get("count", 1)) if not isinstance(g.get("count"), list) else 0
        lv = g.get("level")
        lo, hi = (lv[0], lv[-1]) if isinstance(lv, list) else (lv, lv)
        if t == "K":
            a = mt.get((c, g["monster"])) or die("%s: mostro %s non nel capitolo %d" % (x["id"], g["monster"], c))
        elif t == "I" and g["from"] == "monster":
            t = "IM"
            a = mt.get((c, g["monster"])) or die("%s: mostro %s non nel capitolo %d" % (x["id"], g["monster"], c))
            b = min(255, round(256 / int(g["one_in"])))
        elif t == "I":
            t = "IC"
            a, b = lo, hi
        elif t == "P":
            a, b = lo, hi
        elif t == "B":
            if "chapter" in g:                 # un boss con nome di un piano del capitolo (non il boss del capitolo)
                a, b = (c - 1) * CH_LV + 1, c * CH_LV - 1
            else:
                a, b = lo, hi
            k = 1
        elif t == "C":
            a, k = c, 1
        elif t in ("G", "V"):
            gold = int(g.get("gold", 0))
            a, b, k = gold & 255, gold >> 8, 1
        else:
            die("%s: tipo %s" % (x["id"], t))
        if not (1 <= k <= 255 and 0 <= a <= 255 and 0 <= b <= 255):
            die("%s: valori fuori da un byte" % x["id"])
        ty.append(QG[t] | c << 4)
        p1.append(a); p2.append(b); n.append(k)
        it.append(items.index(g["item"]) + 1 if g.get("item") else 0)
    L = ["; generato da tools/build/gen_qdata.py da data/quests/next/quests.yaml - non modificare",
         "QT_NUM   = %d          ; quest non ripetibili: 1..12 catena, 13..27 accessorie" % len(qs),
         "QT_CHAIN = 12"]
    L += ["QG_%-5s = %d" % (k, v) for k, v in QG.items()]
    L.append("; QID: " + ", ".join("%d %s" % (i + 1, x["id"]) for i, x in enumerate(qs)))
    for nm, v in (("qt_ty", ty), ("qt_p1", p1), ("qt_p2", p2), ("qt_n", n), ("qt_it", it)):
        L.append("%-6s .byte %s" % (nm, ", ".join(str(e) for e in v)))
    L.append('        .enc "screen"')
    for i, k in enumerate(items):
        L.append('qi_%d    .text "%s", 0' % (i + 1, q["quest_items"][k]))
    L.append('        .enc "none"')
    L.append("qi_lo  .byte 0, " + ", ".join("<qi_%d" % (i + 1) for i in range(len(items))))
    L.append("qi_hi  .byte 0, " + ", ".join(">qi_%d" % (i + 1) for i in range(len(items))))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(L) + "\n")
    print("gen_qdata: %d quest, %d oggetti di quest -> %s" % (len(qs), len(items), OUT))


if __name__ == "__main__":
    main()
