"""Riscrive la catena dei settori della directory (traccia 18) di un d64 con un altro interleave (18/11, PERF-12).

Uso: d64_dirilv.py disco.d64 K. Il contenuto dei settori non cambia, cambia solo dove stanno sulla traccia 18 e i loro
collegamenti; il primo settore resta l'1 (lo cerca il DOS) e la BAM della traccia 18 segue i settori usati. Krill legge la
directory un settore dopo l'altro: cc1541 la scrive con interleave 3, con 2 Krill la legge piu' in fretta (misure nella
pagina docs/wiki/FastLoader.md, sezione 7.2)."""
import sys

SPT18 = 19
T18 = sum(21 for _ in range(17)) * 256          # offset della traccia 18 (tracce 1-17 da 21 settori)


def relink(d, k):
    sec = lambda s: T18 + s * 256
    chain, t, s = [], 18, 1
    while t == 18:
        if s in chain or len(chain) >= SPT18 - 1:
            raise SystemExit("d64_dirilv: catena della directory non valida")
        chain.append(s)
        t, s = d[sec(s)], d[sec(s) + 1]
    end = (t, s)                                # ultimo settore: 00 ff
    new = [1]
    while len(new) < len(chain):
        c = (new[-1] + k) % SPT18
        while c == 0 or c in new:
            c = (c + 1) % SPT18
        new.append(c)
    body = [bytes(d[sec(s) + 2:sec(s) + 256]) for s in chain]
    for s in chain:
        d[sec(s):sec(s) + 256] = bytes(256)
    for i, s in enumerate(new):
        nt, ns = (18, new[i + 1]) if i + 1 < len(new) else end
        d[sec(s)], d[sec(s) + 1] = nt, ns
        d[sec(s) + 2:sec(s) + 256] = body[i]
    bam = sec(0) + 4 + 17 * 4                   # voce della traccia 18 nella BAM
    m = 0
    for s in range(SPT18):
        if s != 0 and s not in new:
            m |= 1 << s
    d[bam], d[bam + 1], d[bam + 2], d[bam + 3] = bin(m).count("1"), m & 255, (m >> 8) & 255, m >> 16
    return chain, new


if __name__ == "__main__":
    path, k = sys.argv[1], int(sys.argv[2])
    d = bytearray(open(path, "rb").read())
    old, new = relink(d, k)
    open(path, "wb").write(d)
    print("d64_dirilv: directory %s -> %s (interleave %d)" % (old, new, k))
