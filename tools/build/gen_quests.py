#!/usr/bin/env python3
"""Quest (17/11, concept): data/quests.yaml -> out/work/quests.inc (prima di GAME) e, con --files (dopo src/qpage.asm),
out/work/qstN.prg: un file per quest, QSTn sul disco, piu' QST0 ("no quest"). Copyright 2026 - Simone Caporale

File QSTn (letto da GAME a QBUF = SCR_B ed eseguito, solo mentre la pagina della quest e' aperta, src/game/quest.asm):
  codice della pagina (out/work/qpage.bin, src/qpage.asm), poi il testo: nome di chi la da' 0, titolo 0, premio 0, righe del
  testo (ciascuna 0), $FF. Codici dello schermo (font della UI). QST0 = codice + $FF.
quests.inc (GAME e LOBBY): Q_N = numero di quest, q_ttl_lo/q_ttl_hi + titoli (lobby, pagina del barbaro), q_gvr_lo/q_gvr_hi
+ nomi (etichetta dell'NPC nel villaggio)."""
import os, sys, textwrap
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out", "work")
W, LINES = 36, 11


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


def main():
    qs = yaml.safe_load(open(os.path.join(ROOT, "data", "quests.yaml")))["quests"]
    files = "--files" in sys.argv[1:]
    page = open(os.path.join(OUT, "qpage.bin"), "rb").read() if files else b""
    inc = ["; generato da tools/build/gen_quests.py (data/quests.yaml): non modificare", "Q_N = %d" % len(qs)]
    if files:
        open(os.path.join(OUT, "qst0.prg"), "wb").write(bytes([0x00, 0xbc]) + page + b"\xff")
    for n, q in enumerate(qs, 1):
        if q["id"] != n:
            sys.exit("gen_quests: id %s fuori ordine (attesi 1..N)" % q["id"])
        for k, lim in (("giver", 16), ("title", 30), ("reward", 36)):
            if len(q[k]) > lim:
                sys.exit("gen_quests: quest %d: %s piu' lungo di %d caratteri" % (n, k, lim))
        lines = textwrap.wrap(" ".join(str(q["text"]).split()), W)
        if len(lines) > LINES:
            sys.exit("gen_quests: quest %d: testo di %d righe (massimo %d)" % (n, len(lines), LINES))
        data = bytearray(page)
        for s_ in (q["giver"], q["title"], q["reward"]):
            data += scr(s_) + b"\0"
        for ln in lines:
            data += scr(ln) + b"\0"
        data.append(0xff)
        if len(data) > 1000:
            sys.exit("gen_quests: quest %d: %d B, oltre i 1000 B di QBUF (codice della pagina + testo)" % (n, len(data)))
        if files:
            open(os.path.join(OUT, "qst%d.prg" % n), "wb").write(bytes([0x00, 0xbc]) + bytes(data))
        inc.append("q_ttl%d .text %s, 0" % (n, ", ".join(str(b) for b in scr(q["title"]))))
        inc.append("q_gvr%d .text %s, 0" % (n, ", ".join(str(b) for b in scr(q["giver"]))))
    inc.append("q_ttl_lo .byte 0" + "".join(", <q_ttl%d" % n for n in range(1, len(qs) + 1)))
    inc.append("q_ttl_hi .byte 0" + "".join(", >q_ttl%d" % n for n in range(1, len(qs) + 1)))
    if not files:
        open(os.path.join(OUT, "quests.inc"), "w").write("\n".join(inc) + "\n")
    print("quest: %d%s" % (len(qs), (" (qst0..qst%d.prg, pagina %d B)" % (len(qs), len(page))) if files else ""))


if __name__ == "__main__":
    main()
