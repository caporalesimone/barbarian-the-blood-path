#!/usr/bin/env python3
"""File MENU (11/11, TODO D13; 18/11 un solo file): i menu del villaggio e gli NPC (src/menu.asm), assemblati da
tools/build/asm.sh in un'immagine piatta out/work/menu.bin che parte dalla zona piu' bassa, con MPARTS zone di codice
(src/game/stash.asm; le etichette in out/work/menu.lbl): zona k = MRk_AT .. mzk_top (al massimo MRk_END).
Ogni zona si comprime ZX0 da sola. (18/11, revisione R2) Le parti vanno in UN file, out/work/menu.prg (prima un file per
zona: ogni file costava ~0,4 s a ogni ingresso nel villaggio): intestazione (numero di parti, poi per ogni parte 4 B:
indirizzo dei dati compressi, destinazione), le parti delle zone diverse dalla zona 2, infine la zona 2. Il file finisce a
MR2_END (fine della zona 2): il gioco (src/game/stash.asm, ml_read) lo carica al suo indirizzo, nella RAM sotto il KERNAL
dopo la cache del villaggio (ML_LO), decomprime le altre zone dall'appoggio e per ultima la zona 2 sul posto. Qui si
simula tutto in una memoria di 64 KB (tools/build/pack.py mem_unpack): nessuna scrittura su dati non ancora letti, ogni
zona ricostruita byte per byte, il file sopra ML_LO.
Uscita: out/work/menu.prg e out/work/menu_zK.prg (le zone decompresse, per i test); stampa dimensioni e spazio libero."""
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


def main():
    img = open(os.path.join(OUT, "menu.bin"), "rb").read()
    G = labels("game.lbl")
    zs = zones()
    base = min(z[1] for z in zs)                           # l'immagine piatta parte dalla zona piu' bassa
    bodies = [img[at - base:end - base] for _, at, end, _ in zs]
    comps = []
    for (name, at, end, lim), body in zip(zs, bodies):
        assert end <= lim, "%s: oltre la fine della zona di %d B" % (name, end - lim)
        c, _ = pack.zx0(body, "menu_%04x" % at)
        assert zx0dec.zx0_decompress(c) == body, "%s: il flusso ZX0 non si decomprime" % name
        comps.append(c)
    last = max(range(len(zs)), key=lambda k: zs[k][1])      # la zona piu' alta (la 2, sotto il KERNAL): per ultima, sul posto
    order = [k for k in range(len(zs)) if k != last] + [last]
    hdr_len = 1 + 4 * len(zs)
    total = hdr_len + sum(len(c) for c in comps)
    fend = G["MR2_END"]
    assert zs[last][3] == fend, "la zona sul posto deve finire a MR2_END"
    load_at = fend - total
    assert load_at >= G["ML_LO"], "file MENU di %d B: scende sotto ML_LO ($%04x, fine del segmento CORE) di %d B" % (total, G["ML_LO"], G["ML_LO"] - load_at)
    hdr, data, pos = [len(zs)], b"", load_at + hdr_len
    for k in order:
        hdr += [pos & 255, pos >> 8, zs[k][1] & 255, zs[k][1] >> 8]
        data += comps[k]; pos += len(comps[k])
    f = bytes(hdr) + data
    assert len(f) == total
    mem = bytearray(65536)
    mem[load_at:fend] = f
    for k in order:                                        # come ml_read: le parti nell'ordine dell'intestazione
        i = order.index(k)
        src = mem[load_at + 1 + 4 * i] | mem[load_at + 2 + 4 * i] << 8
        dst = mem[load_at + 3 + 4 * i] | mem[load_at + 4 + 4 * i] << 8
        if k != last:
            assert not (dst < fend and dst + len(bodies[k]) > load_at), "%s: la destinazione tocca il file" % zs[k][0]
        pack.mem_unpack(mem, src, dst, fend)
    for k, body in enumerate(bodies):
        assert mem[zs[k][1]:zs[k][1] + len(body)] == body, "%s: decompressa diversa" % zs[k][0]
    open(os.path.join(OUT, "menu.prg"), "wb").write(bytes([load_at & 255, load_at >> 8]) + f)
    for old in os.listdir(OUT):                            # i file di una volta (menu1..menuN)
        if re.fullmatch(r"menu\d+\.prg", old):
            os.remove(os.path.join(OUT, old))
    for k, (z, b) in enumerate(zip(zs, bodies), 1):        # le zone decompresse, per i test (scritte dal monitor)
        open(os.path.join(OUT, "menu_z%d.prg" % k), "wb").write(bytes([z[1] & 255, z[1] >> 8]) + b)
    print("menu: " + ", ".join("%s %d -> %d B (libera %d B)" % (z[0], len(b), len(c), z[3] - z[2])
                               for z, b, c in zip(zs, bodies, comps)) +
          ", file menu: %d B da $%04x (%d blocchi, %d B sopra ML_LO)" % (total, load_at, -(-(total + 2) // 254), load_at - G["ML_LO"]))


if __name__ == "__main__":
    main()
