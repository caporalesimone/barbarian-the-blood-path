#!/usr/bin/env python3
"""Mappe fisse disegnate a mano (file di testo in data/): villaggio. Una lettera per casella (48x48).
Uscita: out/town.map (RLE). Formato RLE: byte b < $C0 = tile; b >= $C0 = ripeti il byte successivo (b & $3F) + 2 volte.
Uso: python3 tools/build/gen_maps.py [--from-bin map.bin]   (--from-bin: crea data/town_map.txt da un dump della mappa)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
import gen_gfx as G
W = H = 48
LEGEND = {"GRASSA": ".", "GRASSB": ",", "GRASSC": "`", "PATH": ":", "DIRT": "d", "COBBLE": "+", "BRIDGE": "x",
          "BWALL": "W", "BROOF": "R", "BROOFA": "r", "BROOFL": "l", "DSMITH": "S", "DALCH": "L",
          "DHOME": "H", "HDOOR": "D", "SIGNS": "5", "SIGNL": "7",
          "FOUNTAIN": "~", "FOUNT0": "1", "FOUNT1": "2", "FOUNT2": "3", "FOUNT3": "4", "PORTAL": "O", "TREE": "T",
          "TSTAIRS": ">", "CRYPTA": "/", "CRYPTB": "@", "CRYPTC": "\\", "CRYPTL": "[", "CRYPTR": "]",
          "GRAVE": "t", "GRAVE2": "Y", "WATER": "%", "WATERL": "(", "WATERR": ")",
          "FLOWERS": "*", "WELL": "w", "FENCE": "|", "LAMP": "i", "BUSH": "B", "STALL": "s",
          "WINDOW": "o", "CHIMNEY": "c", "FENCEV": "v", "SPIRE": "A"}
assert len(set(LEGEND.values())) == len(LEGEND) and set(LEGEND) == set(G.TTID), "legenda incompleta"
CH = {c: G.TTID[n] for n, c in LEGEND.items()}
# (12/11, TODO M1) caselle speciali generiche: una lettera in piu' che nella mappa diventa un tile normale ma la cui
# posizione va in out/town_places.inc. "=" = uscita del capitolo (sentiero): tx_exit, TX_EXIT_N.
ALIASES = {"=": "PATH"}
EXITS = "="
CH.update({c: G.TTID[n] for c, n in ALIASES.items()})
def inv_legend():
    """lettera -> nome del tile, alias compresi (per chi legge data/town_map.txt)"""
    d = {c: n for n, c in LEGEND.items()}
    d.update(ALIASES)
    return d
# luoghi (porte) per la minimappa: tools/build/gen_maps.py scrive out/town_places.inc
PLACES = [("DSMITH", "tp_smith"), ("DALCH", "tp_alch"), ("DHOME", "tp_home"), ("TSTAIRS", "tp_crypt")]

def rle(data):
    out, i = bytearray(), 0
    while i < len(data):
        j = i
        while j < len(data) and data[j] == data[i] and j - i < 65: j += 1
        n = j - i
        if n >= 2: out += bytes([0xC0 | (n - 2), data[i]])
        else: out.append(data[i])
        i = j
    return bytes(out)

def read_txt(path):
    rows = [l.rstrip("\n") for l in open(path) if not l.startswith(";")]
    assert len(rows) == H and all(len(r) == W for r in rows), f"{path}: servono {H} righe da {W} caratteri"
    return bytes(CH[c] for r in rows for c in r)

def exits(path):
    """caselle di uscita (lettera in EXITS): [(x, y)]"""
    rows = [l.rstrip("\n") for l in open(path) if not l.startswith(";")]
    return [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c in EXITS]

def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--from-bin":
        d = open(sys.argv[2], "rb").read()[2:2 + W * H]
        inv = {G.TTID[n]: c for n, c in LEGEND.items()}
        with open(os.path.join(ROOT, "data", "town_map.txt"), "w") as f:
            f.write("; Mappa del villaggio (48x48). Una lettera per casella. Legenda:\n")
            items = sorted(LEGEND.items(), key=lambda x: G.TTID[x[0]])
            for k in range(0, len(items), 8):
                f.write("; " + "  ".join(f"{c}={n.lower()}" for n, c in items[k:k + 8]) + "\n")
            for y in range(H):
                f.write("".join(inv[d[y * W + x]] for x in range(W)) + "\n")
        return
    m = read_txt(os.path.join(ROOT, "data", "town_map.txt"))
    # niente arredi (lampioni, cespugli, fiori, bancarelle, pozzo, alberi) entro 3 caselle dalle porte dei negozi e
    # della locanda: si entra facilmente (06/11; 10/11: botti e fieno non ci sono piu')
    dec = {G.TTID[n] for n in ("LAMP", "BUSH", "FLOWERS", "STALL", "WELL", "TREE")}
    for n in ("DSMITH", "DALCH", "DHOME"):
        i = m.index(G.TTID[n]); dx, dy = i % W, i // W
        bad = [(x, y) for y in range(max(0, dy - 3), min(H, dy + 4)) for x in range(max(0, dx - 3), min(W, dx + 4))
               if m[y * W + x] in dec]
        assert not bad, f"arredi entro 3 caselle dalla porta {n} ({dx},{dy}): {bad}"
    with open(os.path.join(ROOT, "out", "town_places.inc"), "w") as f:
        f.write("; generato da tools/build/gen_maps.py: colonna e riga delle porte del villaggio (minimappa)\n")
        for n, lab in PLACES:
            i = m.index(G.TTID[n])
            f.write(f"{lab:<10}.byte {i % W}, {i // W}\n")
        ex = exits(os.path.join(ROOT, "data", "town_map.txt"))
        assert 1 <= len(ex) <= 4, "uscite del capitolo: da 1 a 4 caselle (=)"
        f.write("; uscita del capitolo (=): colonne e righe (12/11, TODO M1)\n")
        f.write("tx_exit_x .byte " + ", ".join(str(x) for x, _ in ex) + "\n")
        f.write("tx_exit_y .byte " + ", ".join(str(y) for _, y in ex) + "\n")
        f.write(f"TX_EXIT_N = {len(ex)}\n")
    r = rle(m)
    open(os.path.join(ROOT, "out", "town.map"), "wb").write(r)
    print(f"villaggio: {len(r)} byte RLE (da {len(m)})")

if __name__ == "__main__":
    main()
