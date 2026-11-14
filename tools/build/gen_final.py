#!/usr/bin/env python3
"""Genera out/work/final_map.inc: mappa fissa dell'ultimo piano (sala del trono del boss finale).
Corridoio da sud (arrivo dalle scale) alla sala del trono, con il pentacolo (stella + cerchio) e il boss.
Alla morte del boss si apre il muro a nord: corridoio verso una grande stanza con 4 bauli epici e
"a suspicious lever" (tirata, al suo posto compare il portale per The Endless Abyss).
Le figure sono simmetriche rispetto alla colonna CX.

Dal 06/11 la mappa non si costruisce piu' nel gioco: questo script scrive anche il file FMAP del disco
(out/work/fmap.prg, RLE come la mappa del villaggio) con la mappa di BASE del piano 20, cioe' com'era in gen_final prima di
post_walls: rettangoli di pavimento, porte chiuse, scale, leva; le caselle della stella e del cerchio sono
"marcatori" = $80 | tile (post_walls le conta come pavimento, consuma il caso come per il pavimento e scrive il tile
della figura): cosi' la mappa finale e il generatore casuale sono identici alla versione che disegnava le figure
con il codice (stesso contenuto dei bauli, stessi mostri)."""
import math, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "out", "work", "final_map.inc")
FMAP = os.path.join(ROOT, "out", "work", "fmap.prg")
# cache sotto il KERNAL (src/game/disk.asm, fin_load). 10/11: in fondo alla cache, dopo il posto di OVL2 / precaricamento
# ($F500-$FCDF) e prima dei vettori ($FFFA). Prima stava dopo la mappa del villaggio (fino a $ECFF): con il villaggio
# nuovo (v1.145) restavano 178 B e il file (~400 B) veniva troncato alla lettura.
FIN_AT = 0xFD00                                # = PF_END: il precaricamento non scrive mai da qui in su
FIN_END = 0xFFFA
CX, CY, R = 24, 25, 8                          # centro e raggio della stella (in caselle)
RECTS = [(13, 15, 35, 35),                     # sala del trono
         (23, 36, 25, 45),                     # corridoio da sud (arrivo)
         (23, 8, 25, 13),                      # corridoio a nord (chiuso fino alla morte del boss)
         (14, 1, 34, 6)]                       # stanza dei tesori
DOORS = [(23, 14), (24, 14), (25, 14)]         # muro nord della sala: si apre alla morte del boss
STAIRS = (24, 45)
CHESTS = [(17, 4), (21, 4), (27, 4), (31, 4)]  # 4 bauli epici
ABYSS = (24, 2)                                # la leva (poi il portale per The Endless Abyss)

pts = [(round(CX + R * math.sin(2 * math.pi * k / 5)), round(CY - R * math.cos(2 * math.pi * k / 5))) for k in range(5)]
star = set()
for k in range(5):
    a, b = pts[k], pts[(k + 2) % 5]
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
    for i in range(n + 1):
        star.add((round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)))
circ = set()
for d in range(0, 360, 2):
    p = (round(CX + (R + 1) * math.sin(math.radians(d))), round(CY - (R + 1) * math.cos(math.radians(d))))
    if p not in star: circ.add(p)
star.discard((CX, CY)); circ.discard((CX, CY))
def half(s):                                       # meta' sinistra; verifica la simmetria
    for x, y in s: assert (2 * CX - x, y) in s, "figura non simmetrica"
    return sorted((x, y) for x, y in s if x <= CX)
def pairs(name, lst):
    body = ", ".join(f"{x},{y}" for x, y in lst)
    return f"{name} .byte {body}\n{name.upper()}_N = {len(lst)}\n"


def final_map():
    """Mappa 48x48 del piano 20 come la costruisce gen_final (src/game/dungeon.asm) PRIMA della morte del boss, in nomi
    di tile del tema 8: per l'atlante grafico (tools/atlas/gen_atlas.py). post_walls e' applicato da chi la usa."""
    m = [["WALL"] * 48 for _ in range(48)]
    for x0, y0, x1, y1 in RECTS:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                m[y][x] = "FLOOR"
    for x, y in DOORS:                             # muro nord della sala: chiuso finche' il boss e' vivo
        m[y][x] = "WALL"
    m[STAIRS[1]][STAIRS[0]] = "STAIRSU"
    m[ABYSS[1]][ABYSS[0]] = "DHOME"                # la leva sta nello slot della porta di casa (tema 8)
    return m


def final_figures():
    """stella e cerchio (coordinate intere, simmetriche) e bauli epici: da applicare dopo post_walls"""
    return sorted(star), sorted(circ), CHESTS


def tile_ids():
    """id dei tile da out/work/gfx_consts.inc (generato da tools/build/gen_gfx.py)"""
    t = {m.group(1): int(m.group(2)) for m in re.finditer(r"^T_(\w+)\s*=\s*(\d+)", open(os.path.join(ROOT, "out", "work", "gfx_consts.inc")).read(), re.M)}
    t.setdefault("WALL", 0)
    return t


def base_map():
    """mappa di base del piano 20 (48*48 byte) come la scrive il file FMAP"""
    T = tile_ids()
    m = [[T[n] for n in r] for r in final_map()]
    half(star), half(circ)                         # verifica la simmetria
    for x, y in star:
        m[y][x] = 0x80 | T["GRASSA"]               # T_FSTAR (src/game/dungeon.asm)
    for x, y in circ:
        m[y][x] = 0x80 | T["GRASSB"]               # T_FCIRC
    for x, y in list(star) + list(circ):
        assert final_map()[y][x] == "FLOOR", "figura fuori dal pavimento"
    return bytes(b for r in m for b in r)


def rle(b):
    """come rle_unpack (src/game.asm): b < $C0 tile; $C0+n ripete il byte seguente n+2 volte (n <= 63)"""
    o, i = [], 0
    while i < len(b):
        j = i
        while j < len(b) and b[j] == b[i] and j - i < 65:
            j += 1
        if j - i >= 2:
            o += [0xC0 | (j - i - 2), b[i]]
        else:
            assert b[i] < 0xC0
            o.append(b[i])
        i = j
    return bytes(o)


def main():
    with open(OUT, "w") as f:
        f.write("; generato da tools/build/gen_final.py - non modificare\n")
        f.write(f"FIN_CX = {CX}\nFIN_CY = {CY}\nFIN_SX = {STAIRS[0]}\nFIN_SY = {STAIRS[1]}\nFIN_AX = {ABYSS[0]}\nFIN_AY = {ABYSS[1]}\n")
        f.write(f"FIN_R_PX = {(R + 1) * 16 + 8}        ; raggio del cerchio in pixel (risveglio del boss)\n")
        f.write(f"FIN_AT = ${FIN_AT:04X}           ; file FMAP (mappa di base, RLE) in fondo alla cache sotto il KERNAL (11/11)\n")
        f.write(f"FIN_END = ${FIN_END:04X}\n")
        f.write(pairs("fin_door", DOORS))
        f.write(pairs("fin_chest", CHESTS))
        f.write(pairs("fin_tip", pts))
    r = rle(base_map())
    assert FIN_AT + len(r) <= FIN_END, "FMAP troppo grande: il fondo della cache ($%04X-$FFF9) e' di %d B" % (FIN_AT, FIN_END - FIN_AT)
    os.makedirs(os.path.dirname(FMAP), exist_ok=True)
    open(FMAP, "wb").write(bytes([FIN_AT & 255, FIN_AT >> 8]) + r)
    print(OUT, FMAP, "%d B" % len(r))


if __name__ == "__main__":
    main()
