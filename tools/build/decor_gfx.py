"""Arredi dei piani generati dei capitoli 1-4 (19/11, richiesta del committente: "elementi decorativi a tema in tutti i
dungeon"; docs/wiki/dungeon.md "Arredi dei piani"). Tile: tools/build/gen_gfx.py li mette nei file del tema dei piani
GFX(2c-1) nei posti liberi FREE9, FREE10, FREE11 (solidi) e GRASSA, GRASSB (calpestabili); FREE25, FREE26 e (fuori dalla
palude) PATH restano liberi. Dove vanno: la passata degli arredi del codice del piano (src/game/ovl_decor.asm, OVJ_DECOR,
subito dopo la generazione); decorate() qui sotto e' la stessa passata in Python (atlante, controlli).
Classi dei pixel multicolor come nei temi: 0 sfondo, 1 pal_c1, 2 pal_c2, 3 colore della RAM. Nelle righe '.' = la base."""
W, H = 8, 16
CHAPTERS = (1, 2, 3, 4)


def art(base, rows):
    assert len(rows) == H and all(len(r) == W for r in rows), rows
    return [[base[y][x] if ch == "." else int(ch) for x, ch in enumerate(r)] for y, r in enumerate(rows)]


def decor(c, floor):
    """floor = pavimento base del tema del capitolo (griglia)"""
    t = {}
    if c == 1:                                           # sotterraneo di mattoni (palette 1-8: classe 3 = giallo, ciano nella 3)
        t["FREE9"] = ("urn", "funeral urn (solid, against a wall)", art(floor, [
            "........", "..2222..", "...22...", "..2222..", ".222222.", "22232222", "22333222", "22232222",
            "22222222", ".222222.", ".222222.", "..2222..", "..1111..", ".111111.", "........", "........"]))
        t["FREE10"] = ("coffin", "wooden coffin standing against the wall (solid)", art(floor, [
            "..0000..", ".022220.", "02222220", "02211220", "02211220", "02111120", "02211220", "02211220",
            "02211220", "02222220", ".022220.", ".022220.", ".022220.", "..0220..", "..0000..", "........"]))
        t["FREE11"] = ("brazier", "iron brazier with a fire (solid, free standing)", art(floor, [
            "...3....", "..33.3..", "..3333..", ".333333.", ".323323.", "02222220", "01222210", ".011110.",
            "..0110..", "...11...", "...11...", "..1111..", ".11..11.", ".1....1.", "00....00", "........"]))
        t["GRASSA"] = ("bones", "bones and a skull on the floor (walkable)", art(floor, [
            "........", "........", "..22....", ".2222...", ".2020...", ".2222...", "..22..2.", ".....2..",
            "....2...", "...2..2.", "..2....2", ".....22.", "........", "........", "........", "........"]))
        t["GRASSB"] = ("cracked slab", "cracked floor slab (walkable)", art(floor, [
            "........", "...1....", "...1....", "..11....", "..1.....", "..11....", "...11...", "....1...",
            "....11..", "..111...", "..1..1..", ".1...1..", ".....11.", "......1.", "........", "........"]))
    elif c == 2:                                         # palude (palette 12: fango marrone = classe 1)
        t["FREE9"] = ("stump", "rotten tree stump (solid, free standing)", art(floor, [
            "........", "........", ".000000.", "01111110", "01000010", "01011010", "01000010", "01111110",
            "00000000", "01101110", "01110110", "01101110", "00111100", ".000000.", "........", "........"]))
        t["FREE10"] = ("fetish pole", "a pole with a skull and charms: the dollmaker's mark (solid, free standing)", art(floor, [
            "..0000..", ".022220.", ".020020.", ".022220.", "..0220..", "..0110..", "02011020", "02011020",
            "00011000", "..0110..", "..0110..", "..0110..", "..0110..", ".001100.", ".022220.", ".000000."]))
        t["FREE11"] = ("reed clump", "thick reeds on the shore (solid, against the water)", art(floor, [
            "..2...2.", "..2.0.2.", ".02.2.2.", ".22.2.20", ".22.2.22", ".22.2222", ".222.222", ".222.222",
            ".2222222", "22222222", "22222222", "22222222", "02222220", ".022220.", "..0000..", "........"]))
        t["GRASSA"] = ("puddle", "black puddle with a lily (walkable)", art(floor, [
            "........", "........", "...000..", "..00000.", ".0002000", ".0022200", ".0002000", "..00000.",
            "...000..", "........", "........", ".....2..", "........", "........", "........", "........"]))
        t["GRASSB"] = ("toadstools", "pale toadstools in the mud (walkable)", art(floor, [
            "........", "........", "..22....", ".2222...", ".2222...", "..00....", "..00..2.", ".....222",
            ".....222", "......0.", "........", "..2.....", ".222....", "..0.....", "........", "........"]))
    elif c == 3:                                         # grotte (palette 9, 11: 3 = blu; 10: 3 = nero)
        t["FREE9"] = ("stalagmite", "tall stalagmite (solid, free standing)", art(floor, [
            "...2....", "...2....", "..122...", "..122...", "..1222..", "..1222..", ".11222..", ".11222..",
            ".112222.", ".112222.", "1112222.", "11122222", "11112222", ".111122.", "..3333..", "........"]))
        t["FREE10"] = ("boulder", "fallen boulder (solid, free standing)", art(floor, [
            "........", "........", "..2222..", ".222222.", "22222212", "22222112", "22221122", "22211222",
            "12222221", "12222211", "11222111", ".111111.", "..3333..", "........", "........", "........"]))
        t["FREE11"] = ("crystals", "cluster of crystals / icicles (solid, against a wall)", art(floor, [
            "....2...", "...22...", "...221..", ".2.221..", ".2.221.2", "22.221.2", "221221.2", "22122122",
            "22122122", "22112122", "12112112", "11111111", ".111111.", "..3333..", "........", "........"]))
        t["GRASSA"] = ("scree", "loose gravel (walkable)", art(floor, [
            "........", ".2...1..", "....2...", "..1.....", ".....22.", ".22.....", "....1...", "..2...2.",
            ".....1..", ".1.2....", "......2.", "...22...", ".1......", ".....2..", "..2.....", "........"]))
        t["GRASSB"] = ("old bones", "the bones of someone who did not get out (walkable)", art(floor, [
            "........", "........", "....22..", "...2222.", "...2121.", "...2222.", "....22..", ".2......",
            "..2..2..", "...22...", "..2..2..", ".2....2.", "........", "........", "........", "........"]))
    elif c == 4:                                         # cittadella (mattoni, palette 1-8)
        t["FREE9"] = ("armour", "empty suit of armour on a plinth (solid, free standing)", art(floor, [
            "...22...", "..2222..", "..2112..", "..2222..", ".222222.", "22222222", "2.2222.2", "2.2332.2",
            "2.2222.2", "..2222..", "..2..2..", "..2..2..", ".22..22.", "01111110", "01111110", "00000000"]))
        t["FREE10"] = ("banner", "the banner of the Lord of Ruin on a stand (solid, against a wall)", art(floor, [
            "11111111", ".333333.", ".322223.", ".323323.", ".322223.", ".323323.", ".322223.", ".333333.",
            "..3333..", "...33...", "...11...", "...11...", "...11...", "..1111..", ".111111.", "........"]))
        t["FREE11"] = ("weapon rack", "rack of spears and halberds (solid, against a wall)", art(floor, [
            "........", "2..2..2.", "2..2..2.", "2..2.222", "2.222.2.", "2..2..2.", "11111111", "2..2..2.",
            "2..2..2.", "2..2..2.", "2..2..2.", "11111111", "1......1", "1......1", "11....11", "........"]))
        t["GRASSA"] = ("seal", "the seal of the citadel inlaid in the floor (walkable)", art(floor, [
            "........", "...33...", "..3..3..", ".3.33.3.", ".3.33.3.", "3.3..3.3", "3.3..3.3", "3.3..3.3",
            "3.3..3.3", ".3.33.3.", ".3.33.3.", "..3..3..", "...33...", "........", "........", "........"]))
        t["GRASSB"] = ("broken shield", "a broken shield and rubble (walkable)", art(floor, [
            "........", "........", "..2222..", ".223322.", ".232232.", ".223322.", "..2222..", "...22..1",
            "......11", ".1......", "11...2..", "....22..", "........", "........", "........", "........"]))
    return t


def tiles(c, floor):
    """{posto: griglia} degli arredi del capitolo c sul pavimento floor (griglia del tile FLOOR del tema)"""
    return {n: g for n, (_, _, g) in decor(c, floor).items()}


def names(c):
    """{posto: (nome, descrizione)} per l'atlante"""
    flat = [[0] * W for _ in range(H)]
    return {n: (a, b) for n, (a, b, _) in decor(c, flat).items()}


# Regole della passata (src/game/ovl_decor.asm): per ogni casella di pavimento (FLOOR..FLOORC) h = rand(); h < DK_ANY: arredo;
# h < DK_W calpestabile WALK[h & 1]; altrimenti solido: regola B (le 8 vicine pavimento: isolato) SOLID_B[h & 1], regola A
# (muro a nord, O, E, SO, S, SE pavimento: contro il muro) SOLID_A[h & 1]. Capitolo 4 (cittadella, simmetrica): colonne 1..22 e
# la stessa h sulla casella specchiata (47 - x); le colonne 23 e 24 (l'asse) restano senza arredi: due caselle vicine si
# guarderebbero a vicenda e lo specchio non sarebbe esatto.
SOLID_A = {1: ("FREE9", "FREE10"), 2: ("FREE11", "FREE11"), 3: ("FREE11", "FREE9"), 4: ("FREE10", "FREE11")}
SOLID_B = {1: ("FREE11", "FREE11"), 2: ("FREE9", "FREE10"), 3: ("FREE9", "FREE10"), 4: ("FREE9", "FREE9")}
WALK = ("GRASSA", "GRASSB")
DK_W = {1: 12, 2: 12, 3: 12, 4: 6}
DK_ANY = {1: 40, 2: 40, 3: 40, 4: 48}
MIRROR = {4}


def write_inc(path, tid):
    """costanti e tabelle per src/game/ovl_decor.asm (una sezione per capitolo, scelta con DK_CHAP)"""
    with open(path, "w") as f:
        f.write("; generato da tools/build/decor_gfx.py: regole degli arredi dei piani (ovl_decor.asm)\n")
        for c in CHAPTERS:
            f.write(".if DK_CHAP == %d\n" % c)
            f.write("DK_W = %d\nDK_ANY = %d\nDK_XEND = %d\nDK_MIRROR = %d\n" % (DK_W[c], DK_ANY[c], 23 if c in MIRROR else 47, int(c in MIRROR)))
            f.write("dk_wt .byte %d, %d\n" % tuple(tid[n] for n in WALK))
            f.write("dk_bt .byte %d, %d\n" % tuple(tid[n] for n in SOLID_B[c]))
            f.write("dk_at .byte %d, %d\n" % tuple(tid[n] for n in SOLID_A[c]))
            f.write(".endif\n")


def rand(s):
    """xorshift16 del gioco (src/game.asm rand): s = [lo, hi], ritorna il byte alto"""
    lo, hi = s
    c = hi & 1
    a = (lo >> 1) | (c << 7)
    c = lo & 1
    hi = a ^ hi
    lo = (c << 7) ^ lo
    lo = (hi >> 1) ^ lo
    hi = lo ^ hi
    s[0], s[1] = lo, hi
    return hi


def decorate(m, c, rnd, tid, floor=(2, 4)):
    """la passata in Python, uguale al 6502: m = lista di 2304 tile (cambiata sul posto), rnd = (lo, hi) del generatore
    casuale a fine generazione. Ritorna (solidi, calpestabili)."""
    f0, f1 = floor
    s = [rnd[0], rnd[1] | 0x80]
    fl = lambda x, y: f0 <= m[y * 48 + x] <= f1
    cnt = [0, 0]

    def try_at(x, y, h):
        if not fl(x, y):
            return
        if h < DK_W[c]:
            m[y * 48 + x] = tid[WALK[h & 1]]; cnt[1] += 1
            return
        if not all(fl(x + dx, y + dy) for dx, dy in ((-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))):
            return
        if all(fl(x + dx, y - 1) for dx in (-1, 0, 1)):
            m[y * 48 + x] = tid[SOLID_B[c][h & 1]]; cnt[0] += 1
        elif m[(y - 1) * 48 + x] < f0:
            m[y * 48 + x] = tid[SOLID_A[c][h & 1]]; cnt[0] += 1
    for y in range(1, len(m) // 48 - 1):              # (nel gioco 1..46; l'atlante passa mappe d'esempio piu' basse)
        for x in range(1, 23 if c in MIRROR else 47):
            if not fl(x, y):
                continue
            h = rand(s)
            if h >= DK_ANY[c]:
                continue
            try_at(x, y, h)
            if c in MIRROR:
                try_at(47 - x, y, h)
    return tuple(cnt)
