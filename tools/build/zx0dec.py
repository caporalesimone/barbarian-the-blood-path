#!/usr/bin/env python3
"""Decompressore di riferimento ZX0 v2 (stesso algoritmo di dzx0.c di Einar Saukas, licenza BSD-3): e' la
specifica esatta del flusso che legge il decompressore 6502 (src/common/zx0.inc). Il flusso lo produce il compressore C
in lab64-tools (compilato dai sorgenti, sources.conf di Lab64; usato da tools/build/pack.py), formato v2 in avanti.

Formato (bit letti MSB per primo da un byte dei bit che si ricarica quando e' esaurito; byte e bit nello stesso flusso):
  elias(inv): v = 1; finche' bit() == 0: v = v*2 + (bit() XOR inv); il bit 1 chiude
  LETTERALI: n = elias(0); n byte copiati; bit 1 -> NUOVO OFFSET; bit 0 -> COPIA DALL'ULTIMO OFFSET
  COPIA DALL'ULTIMO OFFSET: n = elias(0); copia n byte da out - offset; bit 0 -> LETTERALI; bit 1 -> NUOVO OFFSET
  NUOVO OFFSET: m = elias(1) (bit di valore invertiti); m == 256 -> FINE; b = byte; offset = m*128 - (b >> 1);
     il bit 0 di b e' il PRIMO bit letto dall'elias(0) della lunghezza ("backtrack"); n = elias(0) + 1; copia;
     bit 1 -> NUOVO OFFSET; bit 0 -> LETTERALI
  offset iniziale = 1.
Decompressione sul posto (README di ZX0): l'ultimo byte compresso deve stare almeno "delta" byte sopra l'ultimo
byte decompresso (delta lo stampa il compressore).

Uso: python3 tools/build/zx0dec.py file.zx0 [out.bin]"""
import sys


def zx0_decompress(src):
    out = bytearray()
    st = {"pos": 0, "mask": 0, "val": 0, "back": False, "last": 0}

    def byte():
        b = src[st["pos"]]
        st["pos"] += 1
        st["last"] = b
        return b

    def bit():
        if st["back"]:
            st["back"] = False
            return st["last"] & 1
        st["mask"] >>= 1
        if st["mask"] == 0:
            st["mask"] = 128
            st["val"] = byte()
        return 1 if st["val"] & st["mask"] else 0

    def elias(inv):
        v = 1
        while not bit():
            v = v << 1 | (bit() ^ inv)
        return v

    def copy(off, n):
        if off > len(out):
            raise ValueError("offset fuori dal decompresso")
        for _ in range(n):
            out.append(out[-off])

    last = 1
    state = "lit"
    while True:
        if state == "lit":
            n = elias(0)
            for _ in range(n):
                out.append(byte())
            if bit():
                state = "new"
                continue
            copy(last, elias(0))
            state = "new" if bit() else "lit"
        else:
            m = elias(1)
            if m == 256:
                if st["pos"] != len(src):
                    raise ValueError("dati dopo la fine del flusso")
                return bytes(out)
            last = m * 128 - (byte() >> 1)
            st["back"] = True
            copy(last, elias(0) + 1)
            state = "new" if bit() else "lit"


if __name__ == "__main__":
    d = zx0_decompress(open(sys.argv[1], "rb").read())
    if len(sys.argv) > 2:
        open(sys.argv[2], "wb").write(d)
    print(len(d))
