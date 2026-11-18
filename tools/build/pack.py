#!/usr/bin/env python3
"""Compressione ZX0 dei file che START (src/start.asm) legge all'avvio (chiamato da tools/build/asm.sh).

Oggi: GAME (out/work/game.prg, $0400-...) -> out/work/game.zx0, decompresso SUL POSTO da START (src/common/zx0.inc) appena il file
e' stato letto. Il file compresso si carica in modo che il suo ultimo byte stia "delta" byte sopra l'ultimo byte del
gioco (regola di ZX0 per la decompressione sul posto) e sotto $A000 (corpo di START).
Scrive anche out/work/pack.inc (indirizzi per START) e verifica in Python (tools/build/zx0dec.py) che la decompressione
sul posto in una memoria di 64 KB ricostruisca il gioco byte per byte.

Compressore: il programma C originale (Einar Saukas, BSD-3, compilato dai sorgenti in Lab64: build-scripts/sources.conf di Lab64), compilato nella build dell'immagine
lab64-tools (stage zx0-build: il compilatore resta fuori dall'immagine) e messo nel PATH (/opt/c64/bin/zx0, 13/11).
Modo rapido (-q, ~1,5 s) di norma; ZX0_BEST=1 (tools/build/release.sh) per il modo ottimo (~20 s, ~1,2 KB in meno).
Cache in out/cache/zx0/: se il gioco non cambia non si ricomprime."""
import hashlib, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zx0dec

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
CACHE = os.path.join(ROOT, "out", "cache", "zx0")
LOADER_AT = 0xA000                      # corpo di START (src/start.asm): il file compresso deve finire sotto
BEST = os.environ.get("ZX0_BEST") == "1"


def compressor():
    """zx0 nel PATH di lab64-tools (compilato dai sorgenti nella build dell'immagine, build-scripts/sources.conf di Lab64)"""
    z = shutil.which("zx0")
    if not z:
        sys.exit("pack: manca zx0: gira nel container lab64-tools (lab64 run ...)")
    return z


def zx0(data, tag):
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.sha1(data + (b"best" if BEST else b"quick")).hexdigest()[:16]
    cf, cd = os.path.join(CACHE, h + ".zx0"), os.path.join(CACHE, h + ".delta")
    if os.path.exists(cf) and os.path.exists(cd):
        return open(cf, "rb").read(), int(open(cd).read())
    raw = os.path.join(CACHE, tag + ".bin")
    open(raw, "wb").write(data)
    out = subprocess.run([compressor(), "-f"] + ([] if BEST else ["-q"]) + [raw, cf],
                         capture_output=True, text=True, check=True).stdout
    delta = int(re.search(r"delta (\d+)", out).group(1))
    open(cd, "w").write(str(delta))
    return open(cf, "rb").read(), delta


def mem_unpack(mem, src, dest, file_end):
    """(18/11) decompressione ZX0 in una memoria di 64 KB condivisa (stessa logica di zx0dec): legge da src, scrive da dest;
    errore se scrive su dati del file non ancora letti (fra il punto di lettura e file_end). Ritorna (fine scritta, fine letta)"""
    st = {"src": src, "dst": dest, "mask": 0, "val": 0, "back": False, "last": 0}

    def byte():
        b = mem[st["src"]]
        st["src"] += 1
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

    def put(b):
        if st["dst"] >= st["src"] and st["dst"] < file_end:
            raise AssertionError("la decompressione sul posto sovrascrive dati non ancora letti")
        mem[st["dst"]] = b
        st["dst"] += 1

    def copy(off, n):
        for _ in range(n):
            put(mem[st["dst"] - off])

    last, state = 1, "lit"
    while True:
        if state == "lit":
            for _ in range(elias(0)):
                put(byte())
            if bit():
                state = "new"
                continue
            copy(last, elias(0))
            state = "new" if bit() else "lit"
        else:
            m = elias(1)
            if m == 256:
                break
            last = m * 128 - (byte() >> 1)
            st["back"] = True
            copy(last, elias(0) + 1)
            state = "new" if bit() else "lit"
    return st["dst"], st["src"]


def inplace_check(comp, load_at, dest, orig):
    """decompressione sul posto in una memoria di 64 KB: stessa logica di zx0dec ma su memoria condivisa"""
    mem = bytearray(65536)
    mem[load_at:load_at + len(comp)] = comp
    mem_unpack(mem, load_at, dest, load_at + len(comp))
    assert mem[dest:dest + len(orig)] == orig, "decompressione sul posto: risultato diverso"


def main():
    g = open(os.path.join(ROOT, "out", "work", "game.prg"), "rb").read()
    dest, body = g[0] | g[1] << 8, g[2:]
    comp, delta = zx0(body, "game")
    assert zx0dec.zx0_decompress(comp) == body, "zx0: il flusso non si decomprime nel gioco"
    last = dest + len(body) - 1                 # ultimo byte del gioco
    load_at = last + delta - len(comp) + 1      # ultimo byte compresso = ultimo byte del gioco + delta
    assert load_at + len(comp) <= LOADER_AT, "GAME compresso oltre $9FFF: tocca il corpo di START"
    assert load_at > dest, "GAME compresso: indirizzo di carico sotto la destinazione"
    inplace_check(comp, load_at, dest, body)
    open(os.path.join(ROOT, "out", "work", "game.zx0"), "wb").write(bytes([load_at & 255, load_at >> 8]) + comp)
    with open(os.path.join(ROOT, "out", "work", "pack.inc"), "w") as f:
        f.write("; generato da tools/build/pack.py - non modificare\n")
        f.write(f"GAME_ZX_AT  = ${load_at:04x}         ; GAME compresso (ZX0) caricato qui\n")
        f.write(f"GAME_ZX_DST = ${dest:04x}         ; e decompresso sul posto qui (delta {delta})\n")
        f.write(f"GAME_ZX_LEN = {len(comp)}\nGAME_RAW_LEN = {len(body)}\n")
    print(f"pack: GAME {len(body)} -> {len(comp)} B ZX0 ({'ottimo' if BEST else 'rapido'}, -{100 - 100 * len(comp) // len(body)}%),"
          f" carico a ${load_at:04x}, delta {delta}")


if __name__ == "__main__":
    main()
