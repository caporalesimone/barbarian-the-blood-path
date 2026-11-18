"""Tile della palude (18/11, TODO M11, docs/wiki/dungeon.md "Palude"): acqua, riva, fango ed erba, passerelle e cancelli per i
temi dei capitoli con `map: {style: swamp}` (data/chapters.yaml); li usa tools/build/gen_gfx.py nel file del tema dei piani.

Classi dei pixel multicolor con la palette 12 (src/game.asm): 0 nero, 1 marrone (fango, legno: pal_c1), 2 verde (liquame,
erba: pal_c2), 3 ciano (riflessi sull'acqua: colore della RAM). L'acqua e' nero e verde a scacchiera (verde scuro) con qualche
riflesso. Posti: WALL = acqua (solida), WALLFACE = riva (acqua sopra un'isola o una passerella: canne in basso), FLOOR/B/C =
fango ed erba, STAIRSU/STAIRSD = cancello di legno (si passa al piano vicino), PATH = passerella di assi (posto 14:
calpestabile e mai usato nei dungeon; FREE8 no, e' il portale nero della sala del trono).
Generatore casuale proprio: gli altri tile e file non cambiano."""
import random

W, H = 8, 16


def _water(r):
    """liquame verde scuro: nero con un pixel verde ogni due su righe alterne (25%), increspature verdi, qualche riflesso"""
    g = [[(2 if (y % 2 == 0 and (x + y // 2) % 2 == 0) else 0) for x in range(W)] for y in range(H)]
    for _ in range(2):
        x, y = r.randrange(0, W - 2), r.randrange(1, H - 1)
        g[y][x] = g[y][x + 1] = 2
    x, y = r.randrange(0, W - 1), r.randrange(0, H)
    g[y][x] = 3
    return g


def _mud(r, grass=0.18):
    g = [[1] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            v = r.random()
            if v < grass:
                g[y][x] = 2
            elif v < grass + 0.10:
                g[y][x] = 0
    return g


def _gate(r, open_side):
    """cancello di legno fra due pali, visto di fronte: pali e traverse marroni con il bordo nero, fra le assi l'acqua scura"""
    g = [[0] * W for _ in range(H)]
    for y in range(0, H):
        for x in (0, 1, 6, 7):
            g[y][x] = 1                                  # pali (2 pixel)
        g[y][2] = g[y][5] = 0
    for y in (2, 3, 11, 12):
        for x in range(1, 7):
            g[y][x] = 1                                  # traverse
    for x in (3, 4):
        for y in range(4, 11):
            g[y][x] = 1                                  # asse centrale
    for x in (0, 7):
        g[0][x] = 3                                      # cime dei pali (riflesso)
    g[7][5 if open_side else 2] = 3                      # anello: a destra (verso il piano dopo) o a sinistra
    for x in range(W):
        g[H - 1][x] = 1                                  # soglia di assi
    return g


def _plank(r):
    g = [[1] * W for _ in range(H)]
    for y in (3, 7, 11, 15):
        for x in range(W):
            g[y][x] = 0                                  # fughe fra le assi
    for y0 in (0, 4, 8, 12):
        g[y0 + 1][r.randrange(1, W - 1)] = 0             # nodi del legno
    return g


def tiles():
    """{nome del tile: griglia 8x16 di classi 0..3}"""
    r = random.Random(1806)
    out = {"WALL": _water(r)}
    g = _water(r)                                        # riva: acqua sopra, fango e canne in basso
    for y in range(11, H):
        for x in range(W):
            g[y][x] = 1 if r.random() < 0.7 else 0
    for x in range(0, W, 2):
        for y in range(r.randrange(6, 10), 12):
            g[y][x] = 2                                  # canne
    out["WALLFACE"] = g
    out["FLOOR"] = _mud(r)
    g = _mud(r)                                          # ciuffo d'erba alta
    for (x, y) in ((2, 4), (3, 3), (3, 5), (4, 2), (4, 4), (5, 3), (5, 5), (3, 6), (4, 6)):
        g[y][x] = 2
    out["FLOORB"] = g
    g = _mud(r)                                          # pozza
    for y in range(6, 11):
        for x in range(1, 6):
            if (x - 3) ** 2 / 6.5 + (y - 8) ** 2 / 5.0 <= 1:
                g[y][x] = 2 if (x + y) % 2 else 0
    out["FLOORC"] = g
    out["PATH"] = _plank(r)
    out["STAIRSD"] = _gate(r, True)
    out["STAIRSU"] = _gate(r, False)
    return out
