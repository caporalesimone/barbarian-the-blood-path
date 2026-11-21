#!/usr/bin/env python3
"""(21/11) Generatore dei piani compresso nel PRG di GAME (src/game.asm, GENPASS): legge dalla prima passata (GENPASS=1) i byte
del generatore (etichette gen_raw..gen_raw_end, messi dopo CODE2 solo per questo), li comprime ZX0 (tools/build/pack.py) e
scrive out/work/gen_img.zx0, che la seconda passata (GENPASS=2) include al posto del codice non compresso; copy_gfx lo
decomprime all'avvio a GEN_AT (RAM sotto l'I/O). Controlla che il flusso si decomprima uguale.
Uso: gen_imgz.py PRG_PASSATA1 LBL_PASSATA1 [USCITA]"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack, zx0dec

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def main():
    prg, lbl = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "out", "work", "gen_img.zx0")
    L = {m.group(1): int(m.group(2)[1:], 16) if m.group(2)[0] == "$" else int(m.group(2))
         for m in re.finditer(r"^(\w+)\s*=\s*(\$[0-9a-fA-F]+|\d+)\s*$", open(lbl).read(), re.M)}
    d = open(prg, "rb").read()
    load = d[0] | d[1] << 8
    a, b = L["gen_raw"], L["gen_raw_end"]
    raw = d[2 + a - load:2 + b - load]
    assert len(raw) == b - a, "gen_imgz: PRG della prima passata troppo corto"
    c, _ = pack.zx0(raw, "gen_img")
    assert zx0dec.zx0_decompress(c) == raw, "gen_imgz: il flusso ZX0 non si decomprime"
    open(out, "wb").write(c)
    print("generatore: %d -> %d B (ZX0)" % (len(raw), len(c)))


if __name__ == "__main__":
    main()
