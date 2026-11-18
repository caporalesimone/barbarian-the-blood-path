#!/usr/bin/env python3
"""Quest (17/11, concept; 18/11 elenco e dettaglio): data/quests.yaml -> out/work/quests.inc (GAME), out/work/quests_m.inc
(modulo MENU) e, con --files (dopo src/qpage.asm), i file del disco. Copyright 2026 - Simone Caporale

File QST0 (letto da GAME a QBUF = SCR_B ed eseguito, src/game/quest.asm ui_quest): codice della pagina (out/work/qpage.bin,
  src/qpage.asm) + indice: per ogni quest 1..Q_N il capitolo (1 byte) e il titolo (0 finale).
File QSTn, n = 1..Q_N (letto dalla pagina a QTXT = $B000 quando se ne apre il dettaglio): premio 0, numero di righe dello stato
  (1 byte), righe dello stato e poi del testo (ciascuna 0 finale), $FF. Codici dello schermo (font della UI).
quests.inc (GAME): Q_N e q_gvr1 (nome di Hilde: etichetta dell'NPC 0 nel villaggio).
quests_m.inc (MENU, src/menu/npc.asm): q_ch = capitolo di ogni quest (gli NPC che vagano offrono quelle del capitolo o prima)."""
import os, sys, textwrap
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "work")
W = 36                    # colonne del testo nel riquadro del dettaglio
QBUF, QTXT = 0xBC00, 0xB000
QBUF_MAX, QTXT_MAX = 1024, 1024     # QST0: tutto lo schermo B (i puntatori degli sprite li riscrive l'IRQ, spento nella UI); QSTn: $B000-$B3FF


def scr(s):
    """testo -> codici dello schermo del font della UI (lettere minuscole 1..26, il resto come ASCII 32..63)"""
    out = bytearray()
    for c in s.lower():
        o = ord(c)
        if "a" <= c <= "z":
            out.append(o - 96)
        elif 32 <= o <= 63:
            out.append(o)
        else:
            sys.exit("gen_quests: carattere non disponibile nel font: %r in %r" % (c, s))
    return bytes(out)


def wrap(s):
    return textwrap.wrap(" ".join(str(s).split()), W)


def main():
    qs = yaml.safe_load(open(os.path.join(ROOT, "data", "quests.yaml")))["quests"]
    files = "--files" in sys.argv[1:]
    if not 1 <= len(qs) <= 8:
        sys.exit("gen_quests: da 1 a 8 quest (c_qst e' una maschera di 8 bit)")
    index = bytearray()
    for n, q in enumerate(qs, 1):
        if q["id"] != n:
            sys.exit("gen_quests: id %s fuori ordine (attesi 1..N)" % q["id"])
        for k, lim in (("giver", 16), ("title", 24), ("reward", 36)):
            if len(q[k]) > lim:
                sys.exit("gen_quests: quest %d: %s piu' lungo di %d caratteri" % (n, k, lim))
        if not 1 <= q["chapter"] <= 9:
            sys.exit("gen_quests: quest %d: capitolo %s (1..9)" % (n, q["chapter"]))
        if (n == 1) != (q["giver"] == "hilde"):
            sys.exit("gen_quests: la quest 1 e solo lei e' di hilde (NPC 0); le altre le offrono gli NPC che vagano")
        index += bytes([q["chapter"]]) + scr(q["title"]) + b"\0"
        st, tx = wrap(q["status"]), wrap(q["text"])
        data = bytearray(scr(q["reward"]) + b"\0" + bytes([len(st)]))
        for ln in st + tx:
            data += scr(ln) + b"\0"
        data.append(0xff)
        if len(data) > QTXT_MAX:
            sys.exit("gen_quests: quest %d: %d B, oltre i %d B di QTXT" % (n, len(data), QTXT_MAX))
        if files:
            open(os.path.join(OUT, "qst%d.prg" % n), "wb").write(bytes([QTXT & 255, QTXT >> 8]) + bytes(data))
    if files:
        page = open(os.path.join(OUT, "qpage.bin"), "rb").read()
        d = page + bytes(index)
        if len(d) > QBUF_MAX:
            sys.exit("gen_quests: QST0 di %d B (pagina %d + indice %d), oltre i %d B di QBUF" % (len(d), len(page), len(index), QBUF_MAX))
        open(os.path.join(OUT, "qst0.prg"), "wb").write(bytes([QBUF & 255, QBUF >> 8]) + d)
        print("quest: %d (qst0 %d B: pagina %d + indice %d; qst1..qst%d)" % (len(qs), len(d), len(page), len(index), len(qs)))
        return
    inc = ["; generato da tools/build/gen_quests.py (data/quests.yaml): non modificare", "Q_N = %d" % len(qs),
           "q_gvr1 .text %s, 0" % ", ".join(str(b) for b in scr(qs[0]["giver"]))]
    open(os.path.join(OUT, "quests.inc"), "w").write("\n".join(inc) + "\n")
    open(os.path.join(OUT, "quests_m.inc"), "w").write(
        "; generato da tools/build/gen_quests.py (data/quests.yaml): capitolo di ogni quest (indice = quest - 1)\n"
        "q_ch .byte %s\n" % ", ".join(str(q["chapter"]) for q in qs))
    print("quest: %d" % len(qs))


if __name__ == "__main__":
    main()
