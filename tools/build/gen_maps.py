#!/usr/bin/env python3
"""Mappe fisse disegnate a mano (file di testo in data/): villaggio. Una lettera per casella (48x48).
Uscita: out/work/town.map (RLE). Formato RLE: byte b < $C0 = tile; b >= $C0 = ripeti il byte successivo (b & $3F) + 2 volte.
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
# (12/11, TODO M1; 15/11 Z2) caselle speciali generiche: una lettera in piu' che nella mappa diventa un tile normale ma la
# cui posizione va nell'intestazione del file del villaggio (town_k, src/game/levels.asm): "=" = uscita del capitolo
# (sentiero, 2 caselle), "E" = ingresso (sentiero), "P" = posto del portale (selciato; la casella sotto e' l'arrivo).
# (19/11) "F" = traghetto (posto BRIDGE, calpestabile): 0 o 2 caselle; salendo su una si arriva sull'altra (tile_trigger,
# tk_boat). Il tile ha la barriera per gli NPC (solidtab bit 1, campo "solido" = "npc" in vilN_*.py): mai un NPC sopra.
ALIASES = {"=": "PATH", "E": "PATH", "P": "COBBLE", "F": "BRIDGE"}
EXITS = "="
CH.update({c: G.TTID[n] for c, n in ALIASES.items()})
def inv_legend():
    """lettera -> nome del tile, alias compresi (per chi legge data/town_map.txt)"""
    d = {c: n for n, c in LEGEND.items()}
    d.update(ALIASES)
    return d
TK_NAME = 25                     # nome del luogo di cura con lo 0 finale
NSEC = 16                        # (17/11) settori degli NPC vaganti per villaggio (x, y, larghezza, altezza: 4 byte l'uno)
NFIX = 3                         # (21/11) NPC fissi oltre a quello della piazza: x, y, settore (1..NSEC), disegno
FIX_NAME = 16                    # (21/11) nome di un NPC fisso (etichetta della barra), con lo 0 finale (tabella fix_nm, GAME)
TK_LEN = 20 + TK_NAME + 4 * NSEC + 2 + 4 + 2 * NFIX + 1   # intestazione del file TWNc: town_k in levels.asm

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
    import villages as V
    msg = []
    for c, v in sorted(V.VILLAGES.items()):
        r, k = build(c, v)
        open(os.path.join(ROOT, "out", "work", "town%d.map" % c), "wb").write(k + r)
        msg.append("%d: %d" % (c, len(k) + len(r)))
    with open(os.path.join(ROOT, "out", "work", "town_places.inc"), "w") as f:
        f.write("; generato da tools/build/gen_maps.py: intestazione dei file dei villaggi (TWNc), copiata in town_k\n")
        f.write("TK_LEN = %d\nTK_NAME = %d\nTK_SOLID = %d\nTX_EXIT_N = 2\nNVIL = %d\nNSEC = %d\nNFIX = %d\n"
                % (TK_LEN, TK_NAME, TK_SOLID, len(V.VILLAGES), NSEC, NFIX))
        # (21/11) nomi degli NPC fissi di tutti i villaggi, uno dopo l'altro (codici schermo, 0 finale): l'etichetta della barra
        # (QL_ID) punta al nome tk_fnb + k (npc_here1, src/menu/npc_here.asm)
        names = [n for c in sorted(V.FIXED) for n, _, _ in V.FIXED[c]]
        offs, o = [], 0
        for n in names:
            offs.append(o)
            o += len(n) + 1
        # (22/11) colori dei vestiti degli NPC: 4 per villaggio (villages.py NPC_COL), letti da npc_colr (quest.asm)
        f.write("npc_col .byte " + ", ".join(str(x) for c in sorted(V.VILLAGES) for x in V.NPC_COL[c]) + "\n")
        f.write("fix_nm  .byte " + ", ".join(str(b) for n in names for b in text(n) + b"\0") + "\n")
        f.write("fix_lo  .byte " + ", ".join("<(fix_nm+%d)" % x for x in offs) + "\n")
        f.write("fix_hi  .byte " + ", ".join(">(fix_nm+%d)" % x for x in offs) + "\n")
        # (23/11, committente) nome del villaggio di ogni capitolo (villages.py NAME) nella minimappa del villaggio: vil_lo/vil_hi
        # indicizzati da c_chap - 1. Non nell'intestazione TWNc: il file del villaggio 1 e' gia' a TOWN_MAX
        vn = [V.VILLAGES[c]["name"].lower() for c in sorted(V.VILLAGES)]
        for n in vn:
            assert 0 < len(n) <= 21 and all(ch in "abcdefghijklmnopqrstuvwxyz '" for ch in n), "nome del villaggio per la minimappa (max 21): %r" % n
        vo, o = [], 0
        for n in vn:
            vo.append(o)
            o += len(n) + 1
        f.write("vil_nm  .byte " + ", ".join(str(b) for n in vn for b in text(n) + b"\0") + "\n")
        f.write("vil_lo  .byte " + ", ".join("<(vil_nm+%d)" % x for x in vo) + "\n")
        f.write("vil_hi  .byte " + ", ".join(">(vil_nm+%d)" % x for x in vo) + "\n")
    print("villaggi: intestazione + RLE in byte (max %d): %s" % (TOWN_MAX, ", ".join(msg)))
    print("settori NPC (al massimo in una finestra di gioco; sprite liberi: 5): " + ", ".join("%d: %d (%d)" % (c, n, w) for c, (n, w) in sorted(SEC_REPORT.items())))
    print("NPC fissi (nome, casella, settore, distanza dal punto): " + "; ".join("%d: %s" % (c, ", ".join("%s (%d,%d) s%d d%d" % e for e in v))
                                                                            for c, v in sorted(FIX_REPORT.items())))


TOWN_MAX = 0x760                 # intestazione + RLE: fino a GFX_DUN_AT (src/game.asm)
TK_SOLID = 48


def text(t):
    """testo in codici schermo (come .enc "screen" di 64tass: a-z = 1-26)"""
    return bytes(ord(ch) - 96 if "a" <= ch <= "z" else ord(ch) for ch in t)


def rows_of(path):
    return [l.rstrip("\n") for l in open(path) if not l.startswith(";")]


SEC_REPORT = {}                  # villaggio -> (settori, massimo in una finestra): lo stampa main()


def sectors(c, m, walk):
    """(17/11) settori degli NPC vaganti: NSEC voci di 4 byte (x, y, larghezza, altezza in caselle; larghezza 0 = voce non usata).
    Ogni settore sta nella mappa, e' abbastanza grande e ha abbastanza caselle percorribili; il numero di settori in una
    finestra di gioco (21 x 13 caselle) e' quello che viene stampato (oltre 5 NPC visibili non si disegna)."""
    import villages as V
    secs = V.SECTORS[c]
    assert len(secs) <= NSEC, "villaggio %d: al massimo %d settori" % (c, NSEC)
    ok = lambda x, y: 0 <= x < W and 0 <= y < H and m[y * W + x] in walk
    for (x, y, w, h) in secs:
        assert 8 <= w <= 63 and 5 <= h <= 63 and x + w <= W and y + h <= H, "villaggio %d: settore %s fuori misura" % (c, (x, y, w, h))
        n = sum(ok(a, b) for a in range(x, x + w) for b in range(y, y + h))
        assert n >= 20, "villaggio %d: settore %s con solo %d caselle percorribili" % (c, (x, y, w, h), n)
    worst = max(sum(1 for (x, y, w, h) in secs
                    if any(ok(a, b) for a in range(max(x, wx), min(x + w, wx + 21)) for b in range(max(y, wy), min(y + h, wy + 13))))
                for wx in range(W - 20) for wy in range(H - 12))
    SEC_REPORT[c] = (len(secs), worst)
    out = b"".join(bytes(s) for s in secs)
    return out + bytes(4 * (NSEC - len(secs)))


def giver(c, m, walk, seen, pl, need):
    """(17/11) casella di chi da' la quest: nella piazza della fontana (2 byte: x, y). La piu' vicina al centro della fontana a
    distanza 3 o piu' (poi 2, poi 1 se la piazza e' stretta), raggiungibile, con le 8 caselle attorno percorribili (non
    sbarra niente) e lontana almeno 3 caselle dalle porte, dal portale e dall'ingresso del sotterraneo."""
    F = [(i % W, i // W) for i in range(W * H) if m[i] == G.TTID["FOUNTAIN"]]
    cx, cy = sum(x for x, _ in F) / len(F), sum(y for _, y in F) / len(F)
    avoid = [(i % W, i // W + 1) for i in pl] + [need["arrivo dal portale"], need["cripta"], need["uscita"], need["uscita 2"]] + \
        [q for n, q in need.items() if n.startswith("traghetto")]
    for dmin in (3, 2, 1):
        cand = [(max(abs(x - cx), abs(y - cy)), x, y) for y in range(H) for x in range(W)
                if (x, y) in seen and m[y * W + x] != G.TTID["FOUNTAIN"] and max(abs(x - cx), abs(y - cy)) >= dmin
                and all(m[(y + dy) * W + x + dx] in walk for dx in (-1, 0, 1) for dy in (-1, 0, 1) if 0 <= x + dx < W and 0 <= y + dy < H)
                and all(max(abs(x - a), abs(y - b)) >= 3 for a, b in avoid)]
        if cand:
            d, x, y = min(cand)
            assert d <= 7, "villaggio %d: nessuna casella libera vicino alla fontana per chi da' la quest" % c
            return bytes([x, y])
    raise AssertionError("villaggio %d: nessuna casella per chi da' la quest" % c)


def fixed(c, m, walk, seen, pl, need, g):
    """(21/11) NPC fissi (villages.FIXED), 2 * NFIX + 1 byte: per ognuno oltre a quello della piazza (casella g) settore (1..NSEC,
    bit 0-4) + disegno (bit 5-6) e casella dentro il settore (x - x0 nei bit 0-3, y - y0 nei bit 4-7; 0, 0 = voce non usata),
    poi l'indice del primo nome nella tabella fix_nm (town_places.inc, GAME). Ogni NPC fisso: in un settore (che non ha piu' il
    suo vagante) diverso da quello degli altri, a meno di 16 caselle dall'angolo del settore, raggiungibile, con le 8 caselle
    attorno percorribili, ad almeno 3 caselle da porte, portale, sotterraneo, uscite e traghetto, ad almeno 8 caselle dagli altri
    NPC fissi (pochi sprite e "!" insieme), il piu' vicino possibile al suo punto (al massimo 18 caselle). Per il villaggio 1 lo
    spazio e' contato: intestazione + mappa RLE al massimo TOWN_MAX."""
    import villages as V
    fx = V.FIXED[c]
    assert 1 <= len(fx) <= 1 + NFIX, "villaggio %d: da 1 a %d NPC fissi" % (c, 1 + NFIX)
    assert fx[0][1] is None, "villaggio %d: il primo NPC fisso sta nella piazza (punto None)" % c
    secs = V.SECTORS[c]
    avoid = [(i % W, i // W) for i in pl] + [(i % W, i // W + 1) for i in pl] + \
        [need["arrivo dal portale"], need["portale"], need["cripta"], need["uscita"], need["uscita 2"]] + \
        [q for n, q in need.items() if n.startswith("traghetto")]
    sec_of = lambda x, y: next((k + 1 for k, (sx, sy, sw, sh) in enumerate(secs)
                                if sx <= x < sx + min(sw, 16) and sy <= y < sy + min(sh, 16)), 0)
    placed, used, ent = [(g[0], g[1])], set(), b""
    for name, anchor, look in fx[1:]:
        kind = anchor[0]
        if kind == "tile":
            T = [(i % W, i // W) for i in range(W * H) if m[i] == G.TTID[anchor[1]]]
            assert T, "villaggio %d: nessun tile %s per %s" % (c, anchor[1], name)
            ax, ay = sum(x for x, _ in T) / len(T), sum(y for _, y in T) / len(T)
        elif kind == "door":
            ax, ay = need["davanti a " + anchor[1]]
        elif kind == "crypt":
            ax, ay = need["cripta"]
        elif kind == "boat":
            ax, ay = need["traghetto 1"]
        else:
            raise AssertionError("villaggio %d: punto %r sconosciuto" % (c, anchor))
        cand = [(max(abs(x - ax), abs(y - ay)), x, y) for y in range(1, H - 1) for x in range(1, W - 1)
                if (x, y) in seen and sec_of(x, y) and sec_of(x, y) not in used
                and all(m[(y + dy) * W + x + dx] in walk for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                and all(max(abs(x - a), abs(y - b)) >= 3 for a, b in avoid)
                and all(max(abs(x - a), abs(y - b)) >= 8 for a, b in placed)]
        assert cand, "villaggio %d: nessuna casella per %s" % (c, name)
        d, x, y = min(cand)
        assert d <= 18, "villaggio %d: %s a %d caselle dal suo punto (max 18)" % (c, name, d)
        s_ = sec_of(x, y)
        sx, sy = secs[s_ - 1][:2]
        assert 1 <= s_ <= 31 and 0 <= look <= 3 and (x - sx, y - sy) != (0, 0)
        used.add(s_)
        placed.append((x, y))
        ent += bytes([s_ | look << 5, (x - sx) | (y - sy) << 4])
        FIX_REPORT.setdefault(c, []).append((name, x, y, s_, d))
    for name, _, _ in fx:
        assert 0 < len(name) < FIX_NAME and name == name.lower() and all(ch in "abcdefghijklmnopqrstuvwxyz '" for ch in name), name
    first = sum(len(V.FIXED[k]) for k in sorted(V.FIXED) if k < c)
    return ent.ljust(2 * NFIX, b"\0") + bytes([first])


FIX_REPORT = {}


def build(c, v):
    import villages as V
    """mappa RLE e intestazione (TK_LEN byte) del villaggio c, con i controlli"""
    path = os.path.join(ROOT, v["map"])
    m = read_txt(path)
    rows = rows_of(path)
    where = lambda ch: [(x, y) for y, r in enumerate(rows) for x, t in enumerate(r) if t == ch]
    one = lambda ch, what: (where(ch) if len(where(ch)) == 1 else sys.exit("%s: serve una sola casella %s (%s)" % (path, ch, what)))[0]
    sol = V.solid(c, G.TOWN_TILES, G.SOLID)
    walk = {i for i in range(len(G.TOWN_TILES)) if not sol[i] & 1}
    for n in ("DSMITH", "DALCH", "DHOME"):
        assert m.count(G.TTID[n]) == 1, "%s: serve una sola porta %s" % (path, n)
        i = m.index(G.TTID[n]); dx, dy = i % W, i // W
        if not v["tiles"]:
            # villaggio 1: niente arredi (lampioni, cespugli, fiori, bancarelle, pozzo, alberi) entro 3 caselle dalle porte
            # dei negozi e della locanda: si entra facilmente (06/11; 10/11: botti e fieno non ci sono piu')
            dec = {G.TTID[t] for t in ("LAMP", "BUSH", "FLOWERS", "STALL", "WELL", "TREE")}
            bad = [(x, y) for y in range(max(0, dy - 3), min(H, dy + 4)) for x in range(max(0, dx - 3), min(W, dx + 4))
                   if m[y * W + x] in dec]
            assert not bad, f"{path}: arredi entro 3 caselle dalla porta {n} ({dx},{dy}): {bad}"
        # tutti: le due caselle davanti alla porta (a sud) sono percorribili (Fire apre da 1 o 2 caselle davanti)
        assert all(m[(dy + k) * W + dx] in walk for k in (1, 2)), "%s: davanti alla porta %s (%d,%d) servono 2 caselle libere" % (path, n, dx, dy)
    px, py = one("P", "portale"); nx, ny = one("E", "ingresso"); sx, sy = one(">", "cripta")
    ex = where("=")
    assert len(ex) == 2, "%s: uscita del capitolo: 2 caselle (=)" % path
    assert m.count(G.TTID["FOUNTAIN"]) >= 1, "%s: manca la fontana" % path
    # (15/11) tutto raggiungibile dall'ingresso: porte (dalla casella davanti), cripta, fontana, uscita, portale e il suo arrivo
    # (19/11) anche con il traghetto: dalla casella F di una barca si arriva su quella dell'altra
    boats = where("F")
    hop = {boats[0]: boats[1], boats[1]: boats[0]} if len(boats) == 2 else {}
    seen, todo = {(nx, ny)}, [(nx, ny)]
    while todo:
        x, y = todo.pop()
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) + ((hop[(x, y)],) if (x, y) in hop else ()):
            if q not in seen and 0 <= q[0] < W and 0 <= q[1] < H and m[q[1] * W + q[0]] in walk:
                seen.add(q); todo.append(q)
    need = {"portale": (px, py), "arrivo dal portale": (px, py + 1), "cripta": (sx, sy), "uscita": ex[0], "uscita 2": ex[1]}
    for n in ("DSMITH", "DALCH", "DHOME"):
        i = m.index(G.TTID[n]); need["davanti a " + n] = (i % W, i // W + 1)
    need["fontana"] = next((i % W, i // W) for i in range(W * H) if m[i] == G.TTID["FOUNTAIN"])
    assert len(boats) in (0, 2), "%s: traghetto: 0 o 2 caselle F" % path
    for k, q in enumerate(boats):
        need["traghetto %d" % (k + 1)] = q
        assert sol[G.TTID["BRIDGE"]] == 2, "%s: il tile del traghetto (BRIDGE) deve avere la barriera per gli NPC" % path
    for what, q in need.items():
        assert q in seen, "%s: %s %s non raggiungibile dall'ingresso" % (path, what, q)
    lost = [(i % W, i // W) for i in range(W * H) if m[i] in walk and (i % W, i // W) not in seen]
    assert not lost, "%s: caselle percorribili isolate: %s" % (path, lost[:12])
    pl = [m.index(G.TTID[n]) for n in ("DSMITH", "DALCH", "DHOME")]
    bg, c1, c2, acc = v["pal"]
    assert 0 <= acc <= 7, "accento: colore 0..7 (colore dei caratteri in multicolor)"
    heal = v["heal"]
    assert 0 < len(heal) < TK_NAME and heal == heal.lower() and all(ch in "abcdefghijklmnopqrstuvwxyz '" for ch in heal), heal
    k = bytes([px, py, sx, sy, nx, ny, bg, c1, c2, 8 | acc] + [t for i in pl for t in (i % W, i // W)]
              + [ex[0][0], ex[1][0], ex[0][1], ex[1][1]]) + text(heal).ljust(TK_NAME, b"\0")
    gv = giver(c, m, walk, seen, pl, need)
    k += sectors(c, m, walk) + gv
    k += bytes([t for q in boats for t in q]).ljust(4, b"\0")    # (19/11) tk_boat: x1, y1, x2, y2 (0 = nessun traghetto)
    k += fixed(c, m, walk, seen, pl, need, gv)                     # (21/11) tk_fix, tk_fnm
    npc = V.NPC_COL[c]                                             # (22/11) colori dei vestiti degli NPC (npc_col in town_places.inc)
    assert len(npc) == 4 and not set(npc) & {bg, c1, c2, 9, 15}, "villaggio %d: colori degli NPC %s uguali al terreno o ai multicolor degli sprite" % (c, npc)
    assert len(k) == TK_LEN
    k += bytes(sol + [0] * (TK_SOLID - len(sol)))          # tile solidi del villaggio (solidtab)
    r = rle(m)
    assert len(k) + len(r) <= TOWN_MAX, "%s: mappa troppo grande: %d + %d B (max %d)" % (path, len(k), len(r), TOWN_MAX)
    return r, k


if __name__ == "__main__":
    main()
