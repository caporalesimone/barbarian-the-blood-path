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
import re
import sys
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "out", "work", "qtab.inc")
QTX = 0xEC00            # testi del capitolo nel gioco (qengine.asm QTX, D2): fino a MR2_AT ($F4E0, zona 2 del MENU)
QTX_MAX = 0xF4E0 - QTX
WRAP = 36
T5X = "0123456789?-+!,'()>%$"          # (22/11) '$' = la moneta del font della UI (CH_COIN, d5_t2 in ui.asm)
COL = {"red": 1, "yellow": 2, "violet": 3}
QG = {"K": 1, "B": 2, "P": 3, "IM": 4, "IC": 5, "C": 6, "G": 7, "V": 8}
CH_LV = 5


def die(m):
    sys.exit("gen_qdata: " + m)


def t5(s):
    """testo a 5 bit del gioco (macro t5, src/common/macros.inc; d5_get in ui.asm): 1-26 lettere, 27 spazio, 28 ':', 29 '.',
    30 '/', 31 + indice in T5X; 0 finale; 3 simboli in una parola di 16 bit, byte alto prima"""
    y = []
    for ch in s:
        if "a" <= ch <= "z":
            y.append(ord(ch) - 96)
        elif ch in " :./":
            y.append(27 + " :./".index(ch))
        elif ch in T5X:
            y += [31, T5X.index(ch)]
        else:
            die("carattere %r fuori dalla tabella a 5 bit in %r" % (ch, s))
    y.append(0)
    while len(y) % 3:
        y.append(0)
    out = bytearray()
    for i in range(0, len(y), 3):
        w = y[i] * 1024 + y[i + 1] * 32 + y[i + 2]
        out += bytes([w >> 8, w & 255])
    return bytes(out)


def wrap(s):
    lines, cur = [], ""
    for w in s.split():
        if cur and len(cur) + 1 + len(w) > WRAP:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        lines.append(cur)
    return lines


def block(lines):
    if len(lines) > 255:
        die("troppe righe")
    return bytes([len(lines)]) + b"".join(t5(l) for l in lines)


def reward(x, uq, ids):
    """premio: 4 byte (oro/10, unico $80+u, oggetto magico: base I_* o $FF = qualsiasi, pozioni e segni) + testo"""
    r = x["reward"]
    gold = int(r.get("gold", 0))
    if gold % 10 or gold > 2550:
        die("%s: oro %d (multiplo di 10, al massimo 2550)" % (x["id"], gold))
    u = 0x80 + uq.index(r["unique"]) if r.get("unique") else 0
    it = 0
    if r.get("item"):
        b = r["item"].get("base")
        it = ("I_" + ids[b].upper()) if b else "$ff"
    pot = 0
    words = []
    if gold:
        words.append("%d gold" % gold)
    if r.get("unique"):
        words.append(r["unique"])
    if r.get("item"):
        words.append("a magic " + (r["item"].get("base") or "item"))
    for p in r.get("potions") or []:
        (c, n), = p.items()
        pot = COL[c] | n << 2
        words.append("%d %s potions" % (n, c))
    if r.get("respec"):
        pot |= 0x20
        words.append("a respec token")
    if r.get("purse"):
        pot |= 0x40
        words.append("purse: upgrade $%d" % r["purse"])      # (22/11, committente: "a purse of N" sembrava oro)
    if r.get("belt"):
        pot |= 0x80
        words.append("a belt of %d" % r["belt"])
    if r.get("skill"):
        words.append("the skill " + r["skill"])
    if r.get("relic"):
        words.append(r["relic"])
    rl = wrap("reward: " + ", ".join(words))
    if len(rl) > 3:                                     # (22/11) il riquadro del premio di QGIV ha 3 righe (QG_RY)
        die("premio di %s su %d righe (al massimo 3): %r" % (x.get("id"), len(rl), rl))
    return [gold // 10, u, it, pot], rl


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
    uq = [u["name"] for u in csv.DictReader(open(os.path.join(ROOT, "data", "items", "next", "uniques.tsv")), delimiter="\t")]
    ids = {b["name"]: b["id"] for b in csv.DictReader(open(os.path.join(ROOT, "data", "items", "next", "bases.tsv")), delimiter="\t")}
    ids.update({k: k for k in list(ids.values())})
    vil = {}
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import villages
    for c, fx in villages.FIXED.items():
        for k, f in enumerate(fx):
            vil[(c, f[0])] = k
    qs = [x for x in q["quests"] if x["kind"] == "chain"] + [x for x in q["quests"] if x["kind"] == "side"]
    if [x["id"] for x in qs[:12]] != list(range(1, 13)) or len(qs) != 27:
        die("servono 12 passi della catena e 15 accessorie")
    ty, p1, p2, n, it, npc, rw = [], [], [], [], [], [], []
    texts = {c: [] for c in range(1, 5)}
    for i, x in enumerate(qs):
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
        gv = vil.get((c, x["giver"]))
        tn = vil.get((c, x.get("turn_in", x["giver"])))
        if gv is None or tn is None:
            die("%s: NPC %s / %s non fisso nel villaggio %d (villages.FIXED)" % (x["id"], x["giver"], x.get("turn_in"), c))
        prev = x.get("after")
        if prev and qs[i - 1]["id"] != prev:
            die("%s: after %s deve essere la quest precedente nel file" % (x["id"], prev))
        npc.append(gv | tn << 2 | (0x80 if prev else 0))
        b, rl = reward(x, uq, ids)
        rw.append(b)
        gt = x["goal_text"]
        cnt = "{n}" in gt
        gt = gt.split("{n}")[0]
        e = t5(x["title"]) + t5(re.sub(r"\{\w\}", "", gt)) + bytes([1 if cnt else 0])
        e += block(wrap(x["text"])) + block(wrap(x["done"])) + block(rl)
        texts[c].append((i, e))
    L = ["; generato da tools/build/gen_qdata.py da data/quests/next/quests.yaml - non modificare",
         "QT_NUM   = %d          ; quest non ripetibili: 1..12 catena, 13..27 accessorie" % len(qs),
         "QT_CHAIN = 12"]
    L += ["QG_%-5s = %d" % (k, v) for k, v in QG.items()]
    L.append("; QID: " + ", ".join("%d %s" % (i + 1, x["id"]) for i, x in enumerate(qs)))
    L.append("; qt_np: bit 0-1 NPC fisso che la da' (k di villages.FIXED), bit 2-3 chi la ritira, bit 7 = prima serve la quest precedente")
    L.append("QTX      = $%04x      ; testi del capitolo (file QTXc, D2)" % QTX)
    for nm, v in (("qt_ty", ty), ("qt_p1", p1), ("qt_p2", p2), ("qt_n", n), ("qt_it", it), ("qt_np", npc)):
        L.append("%-6s .byte %s" % (nm, ", ".join(str(e) for e in v)))
    L.append('        .enc "screen"')
    for i, k in enumerate(items):
        L.append('qi_%d    .text "%s", 0' % (i + 1, q["quest_items"][k]))
    L.append('        .enc "none"')
    L.append("qi_lo  .byte 0, " + ", ".join("<qi_%d" % (i + 1) for i in range(len(items))))
    L.append("qi_hi  .byte 0, " + ", ".join(">qi_%d" % (i + 1) for i in range(len(items))))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(L) + "\n")
    # premi (modulo QGIV, src/qgiv.asm): 4 byte per quest
    open(os.path.join(os.path.dirname(OUT), "qgiv_rw.inc"), "w").write(
        "; generato da tools/build/gen_qdata.py - premi delle quest: oro/10, unico $80+u, oggetto magico (base, $ff qualsiasi),\n"
        "; pozioni (bit 0-1 colore 1 rossa 2 gialla 3 viola, bit 2-4 quante) + bit 5 gettone, 6 borsello, 7 cintura a 8\n"
        + "\n".join("        .byte %s" % ", ".join(str(v) for v in b) for b in rw) + "\n")
    # testi dei capitoli: n, n x (QID-1, indirizzo), poi le voci (titolo, obiettivo, contatore si/no, testo, consegna, premio)
    for c, ent in texts.items():
        head = 1 + 3 * len(ent)
        d, addr = bytearray([len(ent)]), QTX + head
        body = bytearray()
        for qi, e in ent:
            d += bytes([qi, (addr + len(body)) & 255, (addr + len(body)) >> 8])
            body += e
        d += body
        if len(d) > QTX_MAX:
            die("testi del capitolo %d: %d B (al massimo %d)" % (c, len(d), QTX_MAX))
        open(os.path.join(os.path.dirname(OUT), "qtx%d.prg" % c), "wb").write(bytes([QTX & 255, QTX >> 8]) + bytes(d))
        print("gen_qdata: capitolo %d, %d quest, %d B" % (c, len(ent), len(d)))
    print("gen_qdata: %d quest, %d oggetti di quest -> %s" % (len(qs), len(items), OUT))


if __name__ == "__main__":
    main()
