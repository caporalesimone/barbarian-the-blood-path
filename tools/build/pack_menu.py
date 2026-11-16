#!/usr/bin/env python3
"""File MENU (11/11, TODO D13): i menu del villaggio (locanda e negozi, src/menu.asm), assemblati da tools/build/asm.sh in
un'immagine piatta out/work/menu.bin che parte dalla zona piu' bassa, con MPARTS zone di codice (src/game/stash.asm; le
etichette in out/work/menu.lbl): zona k = MRk_AT .. mzk_top (al massimo MRk_END).
Ogni zona si comprime ZX0 da sola, in un file suo (docs/wiki/FORMATO_DATI.md). Il gioco (src/game/stash.asm,
ovl_town) legge ogni zona in fondo al suo posto (fino a MRk_END) e la decomprime sul posto all'inizio:
qui si verifica in una memoria di 64 KB (tools/build/pack.py inplace_check) che la decompressione non scavalchi i dati
compressi ancora da leggere e ricostruisca le zone byte per byte.
Uscita (11/11, Krill): out/work/menu1.prg .. menuN.prg, una zona compressa per file, con indirizzo di carico = fine
zona - lunghezza (il gioco li carica li' e ne legge l'inizio da Krill), e out/work/menu_zK.prg, le zone decompresse per i test); stampa dimensioni e spazio libero."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack, zx0dec

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "out", "work")


def labels(name):
    t = open(os.path.join(OUT, name)).read()
    return {m.group(1): int(m.group(2)[1:], 16) if m.group(2)[0] == "$" else int(m.group(2))
            for m in re.finditer(r"^(\w+)\s*=\s*(\$[0-9a-f]+|\d+)\s*$", t, re.M)}


def zones():
    """[(nome, inizio, fine del codice, fine della zona)] dalle etichette del gioco e del modulo"""
    G, M = labels("game.lbl"), labels("menu.lbl")
    return [("zona %d" % k, G["MR%d_AT" % k], M["mz%d_top" % k], G["MR%d_END" % k]) for k in range(1, G["MPARTS"] + 1)]


def part(img, base, name, at, end, lim):
    body = img[at - base:end - base]
    comp, delta = pack.zx0(body, "menu_%04x" % at)
    assert zx0dec.zx0_decompress(comp) == body, "%s: il flusso ZX0 non si decomprime" % name
    load_at = lim - len(comp)
    assert load_at >= at, "%s: zona troppo piccola per i dati compressi" % name
    assert end + delta <= lim, "%s: decompressione sul posto: mancano %d B (delta %d)" % (name, end + delta - lim, delta)
    pack.inplace_check(comp, load_at, at, body)
    return body, comp


def main():
    img = open(os.path.join(OUT, "menu.bin"), "rb").read()
    zs = zones()
    base = min(z[1] for z in zs)                           # l'immagine piatta parte dalla zona piu' bassa
    parts = [part(img, base, *z) for z in zs]
    blocks = 0
    for k, (z, (b, c)) in enumerate(zip(zs, parts), 1):     # (11/11, Krill) un file per zona: menu1..menuN,
        load_at = z[3] - len(c)                             # indirizzo = fondo della zona - lunghezza compressa
        open(os.path.join(OUT, "menu%d.prg" % k), "wb").write(bytes([load_at & 255, load_at >> 8]) + c)
        blocks += -(-(len(c) + 2) // 254)
    for k, (z, (b, c)) in enumerate(zip(zs, parts), 1):      # le zone decompresse, per i test (scritte dal monitor)
        open(os.path.join(OUT, "menu_z%d.prg" % k), "wb").write(bytes([z[1] & 255, z[1] >> 8]) + b)
    print("menu: " + ", ".join("%s %d -> %d B (libera %d B)" % (z[0], len(b), len(c), z[3] - z[2])
                               for z, (b, c) in zip(zs, parts)) +
          ", file menu1..%d: %d blocchi" % (len(parts), blocks))


if __name__ == "__main__":
    main()
