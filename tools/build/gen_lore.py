#!/usr/bin/env python3
"""Dati della lore (programma LORE): data/lore.txt + immagini -> out/work/ldat.prg (ZX0), out/work/lore.inc, anteprime.

Il programma LORE (src/start.asm con LORE=1 + src/lore/scroll.asm) carica LDAT mentre disegna il titolo, lo decomprime sul
posto in LD_DST ($2000) e lo fa scorrere dal basso verso l'alto nel modo testo multicolore (banco VIC 0).
Formato completo: docs/intro.md. In breve, l'immagine decompressa e':
  $2000  charset (2 KB): codici 0-63 = font del gioco (out/work/gfx/uifont.bin), 64-254 = forme delle immagini, caricate
         durante lo scorrimento negli "slot" liberi (eventi SHAPES); 255 non si usa (e' l'escape dell'RLE)
  $2800  sprite (fino a 16 x 64 B): mostri del gioco, 2 fotogrammi l'uno (tools/build/monsters.py)
  $2C00  forme delle immagini (8 B per carattere), poi le righe:
         riga = nev, nev eventi, poi 80 byte in RLE (40 caratteri + 40 colori; $FF n v = v ripetuto n volte)
         eventi: 0 SHAPES idx cnt lo hi | 1 SPRITE hw ptr xlo xhi col dy anim | 2 SPLIT mc1 mc2 | 3 STOP riga
         nev = $FE: fine del flusso (righe vuote)
Immagini: (1) ritagli della copertina (data/title_src.png) convertiti con i due colori multicolore comuni scelti per
immagine (registri $D022/$D023 cambiati da un raster IRQ alla riga in cui l'immagine comincia: evento SPLIT);
(2) scene vere del gioco (mappa del villaggio, sala del trono) dai tile; (3) sprite dei mostri raddoppiati.
I caratteri uguali si riusano; le immagini che non sono mai sullo schermo insieme riusano gli stessi codici.
Uscite: out/work/ldat.prg, out/work/ldat_raw.bin (immagine decompressa, per il test), out/work/lore.inc, out/work/lore_preview.png,
out/work/atlas/lore.png (atlante grafico)."""
import itertools, os, re, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_gfx as G
import gen_maps as M
import gen_final as F
import monsters as MON
import pack
import zx0dec

PAL = np.array([(0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189), (139, 63, 150), (85, 160, 73),
                (64, 49, 141), (191, 206, 114), (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80),
                (120, 120, 120), (148, 224, 137), (120, 105, 196), (159, 159, 159)], float)   # come tools/build/gen_title.py
LD_DST = 0x2000
CHARSET = 0x2000
SPR_AT = 0x2800
SPR_MAX = 16
DATA_AT = 0x2C00
LD_END = 0xA000                    # corpo di START/LORE (src/start.asm)
FIRST_SLOT, LAST_SLOT = 64, 254    # codici per le forme; 255 = escape RLE
SPR_MC = (9, 15)                   # $D025/$D026 come nel gioco (marrone, grigio chiaro)
WIDTH, MARGIN = 36, 2              # testo: colonne 2..37
TXT_COL, HI_COL = 1, 7             # bianco, giallo (< 8: caratteri in alta risoluzione)
HOLD_FRAMES = 250                  # @hold: 5 s fermo (fire salta)
SPR_BUSY = 31                      # righe per cui uno sprite raddoppiato resta acceso (247+dy -> sotto 12, piu' margine)


# ------------------------------------------------------------------ conversione di un'immagine RGB in caratteri
def dist(a, p):
    """distanza "redmean" (come tools/build/gen_title.py)"""
    rm = (a[..., None, 0] + p[None, :, 0]) / 2
    d = a[..., None, :] - p[None, :, :]
    return (2 + rm / 256) * d[..., 0] ** 2 + 4 * d[..., 1] ** 2 + (2 + (255 - rm) / 256) * d[..., 2] ** 2


def cells_of(a):
    h, w = a.shape[0] // 8, a.shape[1] // 4
    return a.reshape(h, 8, w, 4, 3).transpose(0, 2, 1, 3, 4).reshape(h * w, 32, 3), (w, h)


def convert(a, max_chars, fixed=None, ccs=range(8)):
    """a: immagine (h*8, w*4, 3) a risoluzione multicolore. Sfondo nero; per ogni cella un colore proprio 0-7;
    mc1/mc2 comuni scelti per l'immagine (o fixed). Ritorna dict con w, h, mc, celle [(forma, cc)], forme."""
    C, (w, h) = cells_of(a)
    D = dist(C, PAL)                                            # celle x 32 x 16

    def solve(m1, m2):
        cand = D[:, :, [0, m1, m2]]                             # n x 32 x 3
        best = None
        for cc in ccs:
            full = np.concatenate([cand, D[:, :, cc:cc + 1]], 2)  # n x 32 x 4
            err = full.min(2).sum(1)
            idx = full.argmin(2)
            if best is None:
                best = [err, np.full(len(C), cc), idx]
            else:
                m = err < best[0]
                best[0] = np.where(m, err, best[0])
                best[1] = np.where(m, cc, best[1])
                best[2] = np.where(m[:, None], idx, best[2])
        return best

    if fixed:
        mc = fixed
    else:
        mc = min(((solve(m1, m2)[0].sum(), (m1, m2)) for m1, m2 in itertools.combinations(range(1, 16), 2)))[1]
    err, ccs, idx = solve(*mc)
    pats = [tuple(int(v) for v in r) for r in idx]
    # riduzione delle forme diverse a max_chars: si fondono le forme meno costose da sostituire (errore di resa)
    uniq = sorted(set(p for p in pats if any(p)))
    if len(uniq) > max_chars:
        pal_c = [np.array([0, mc[0], mc[1], int(cc)]) for cc in ccs]
        cost = np.zeros((len(C), len(uniq)))                   # errore della cella c resa con la forma u
        for c in range(len(C)):
            dc = D[c][:, pal_c[c]]                             # 32 x 4
            for u, p in enumerate(uniq):
                cost[c, u] = dc[np.arange(32), list(p)].sum()
        use = {u: [c for c in range(len(C)) if pats[c] == uniq[u]] for u in range(len(uniq))}
        alive = set(range(len(uniq)))
        while len(alive) > max_chars:
            al = sorted(alive)
            best = None
            for u in al:                                       # togliere u: le sue celle vanno alla forma migliore
                cells = use[u]
                sub = cost[np.ix_(cells, [v for v in al if v != u])] if cells else None
                if cells:
                    d = sub.min(1).sum() - cost[cells, u].sum()
                else:
                    d = 0
                if best is None or d < best[0]:
                    best = (d, u)
            u = best[1]
            others = [v for v in al if v != u]
            for c in use[u]:
                v = others[int(cost[c, others].argmin())]
                use[v].append(c)
                pats[c] = uniq[v]
            use[u] = []
            alive.discard(u)
    shapes = sorted(set(p for p in pats if any(p)))
    return dict(w=w, h=h, mc=mc, cells=[(pats[i], int(ccs[i])) for i in range(len(C))], shapes=shapes)


def shape_bytes(p):
    out = []
    for y in range(8):
        v = 0
        for x in range(4):
            v = (v << 2) | p[y * 4 + x]
        out.append(v)
    return out


# ------------------------------------------------------------------ sorgenti: copertina e scene del gioco
_src = None


def cover(x, y, w, h):
    """ritaglio della copertina: x, y in pixel C64 (320x200), w x h caratteri"""
    global _src
    if _src is None:
        _src = Image.open(os.path.join(ROOT, "data", "title_src.png")).convert("RGB")
    sx, sy = _src.size[0] / 320, _src.size[1] / 200
    c = _src.crop((round(x * sx), round(y * sy), round((x + w * 8) * sx), round((y + h * 8) * sy)))
    return np.asarray(c.resize((w * 4, h * 8), Image.LANCZOS), float)


def logo():
    """il logo della copertina senza quello che lo tocca: artigli e corna del demone sopra le lettere (rossi, nella
    meta' alta delle lettere che e' grigia), le spade ai lati e le pietre viola sotto. Coordinate C64 (320x200)."""
    global _src
    if _src is None:
        _src = Image.open(os.path.join(ROOT, "data", "title_src.png")).convert("RGB")
    X0, Y0, W, H = 55, 60, 27, 6                    # ritaglio (caratteri)
    LX0, LX1, LY0, LY1, UP = 57, 266, 61.5, 103, 80  # lettere: x, y; sopra UP le lettere sono grigie
    sx, sy = _src.size[0] / 320, _src.size[1] / 200
    a = np.asarray(_src.crop((round(X0 * sx), round(Y0 * sy), round((X0 + W * 8) * sx), round((Y0 + H * 8) * sy))),
                   float).copy()
    hy = Y0 + np.arange(a.shape[0])[:, None] / sy               # coordinate C64 di ogni pixel
    hx = X0 + np.arange(a.shape[1])[None, :] / sx
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 110) & (g < 0.6 * r)
    off = (hx < LX0) | (hx > LX1) | (hy < LY0) | (hy > LY1) | ((hy < UP) & red) | (b > r + 20)
    a[off] = 0
    return np.asarray(Image.fromarray(a.astype(np.uint8)).resize((W * 4, H * 8), Image.LANCZOS), float)


def _pals():
    src = open(os.path.join(ROOT, "src", "game.asm")).read()
    p = {}
    for k in ("pal_bg", "pal_c1", "pal_c2", "pal_ram"):
        p[k] = [int(v) for v in re.search(r"^%s\s+\.byte\s+([0-9, ]+)" % k, src, re.M).group(1).split(",")]
    return lambda i: [p["pal_bg"][i], p["pal_c1"][i], p["pal_c2"][i], p["pal_ram"][i] & 7]


def _tiles(path, n):
    data = open(os.path.join(ROOT, path), "rb").read()[2:]
    out = []
    for i in range(n):
        px = []
        for y in range(16):
            row = []
            for half in (0, 1):
                q = (0 if y < 8 else 2) + half
                b = data[q * n * 8 + i * 8 + y % 8]
                row += [(b >> (6 - 2 * p)) & 3 for p in range(4)]
            px.append(row)
        out.append(px)
    return out


_scn = {}


def post_walls(m):
    """come post_walls (src/game/gen_io.asm, copia in tools/atlas/gen_atlas.py): WALL con sotto un tile >= 2 -> WALLFACE;
    FLOOR -> FLOORB / FLOORC 1/8 ciascuno (qui con un seme fisso, come l'atlante)"""
    import random
    rng, T = random.Random(7), G.TID
    for y in range(len(m) - 1):
        for x in range(len(m[0])):
            if m[y][x] == T["WALL"] and m[y + 1][x] >= 2:
                m[y][x] = T["WALLFACE"]
    for y in range(len(m)):
        for x in range(len(m[0])):
            if m[y][x] == T["FLOOR"]:
                r = rng.randrange(8)
                if r < 2:
                    m[y][x] = T["FLOORB"] + r


def scene(which, x, y, w, h):
    """scena del gioco: x, y, w, h in tile (16x16 pixel, 2x2 caratteri) della mappa"""
    if not _scn:
        consts = open(os.path.join(ROOT, "out", "work", "gfx_consts.inc")).read()
        nt = int(re.search(r"^GFX_NT = (\d+)", consts, re.M).group(1))
        dn = int(re.search(r"^GFX_DSTRIP = (\d+)", consts, re.M).group(1)) // 8
        pal = _pals()
        rows = [l.rstrip("\n") for l in open(os.path.join(ROOT, "data", "town_map.txt")) if l.strip() and not l.startswith(";")]
        inv = M.inv_legend()
        tmap = [[G.TTID[inv[c]] for c in r] for r in rows]
        fm = [[G.TID[n] for n in r] for r in F.final_map()]
        star, circ, chests = F.final_figures()
        for fx, fy in star:
            fm[fy][fx] = G.TID["GRASSA"]
        for fx, fy in circ:
            fm[fy][fx] = G.TID["GRASSB"]
        for fx, fy in chests:
            fm[fy][fx] = G.TID["CHEST"]
        drows = [l.rstrip("\n") for l in open(os.path.join(ROOT, "data", "atlas_dungeon.txt")) if l.strip() and not l.startswith(";")]
        dinv = {c: n for n, c in G.DUN_LEGEND.items()}
        dm = [[G.TID[dinv[c]] for c in r] for r in drows]
        post_walls(dm)
        _scn["town"] = (tmap, _tiles("out/work/gfx/gfx0.prg", nt), pal(0))
        _scn["dungeon"] = (dm, _tiles("out/work/gfx/gfx1.prg", dn), pal(4))      # tema rosso (palette 4), come la copertina
        _scn["final"] = (fm, _tiles("out/work/gfx/gfx2.prg", dn), pal(4))
    mp, tiles, pal = _scn[which]
    a = np.zeros((h * 16, w * 8, 3))
    for ty in range(h):
        for tx in range(w):
            t = np.array(tiles[mp[y + ty][x + tx]])
            a[ty * 16:ty * 16 + 16, tx * 8:tx * 8 + 8] = PAL[np.array(pal)[t]]
    return a


def compose(w, h, parts):
    """tela nera w x h caratteri con piu' ritagli: parts = [(array, colonna, riga)]"""
    a = np.zeros((h * 8, w * 4, 3))
    for p, cx, cy in parts:
        a[cy * 8:cy * 8 + p.shape[0], cx * 4:cx * 4 + p.shape[1]] = p
    return a


# nome -> (funzione che produce l'immagine, massimo di forme, sprite sopra l'immagine [(nome, x, riga, dy)])
IMAGES = {
    "logo": (logo, 140, [], (0, 1, 2, 7)),      # niente specchi viola o verdi fra le lettere
    "crypt": (lambda: scene("town", 2, 3, 18, 5), 50, []),   # 11/11: 50 forme (villaggio nuovo: 61, non entravano con il logo)
    "lord": (lambda: cover(100, 0, 15, 8), 120, []),
    "fountain": (lambda: scene("town", 11, 26, 10, 6), 80, []),
    "torches": (lambda: (lambda t: compose(36, 5, [(t, 0, 0), (t[:, ::-1], 31, 0)]))(cover(28, 108, 5, 5)), 40, []),
    "hero": (lambda: cover(128, 110, 11, 11), 125, []),
    "stairs": (lambda: scene("dungeon", 30, 16, 16, 6), 60, [("hero", 128, 4, 0)]),
}


def _mon(m):
    return (G.mc_bytes(m[1][0]), G.mc_bytes(m[1][1]), m[2])


def _sprites():
    hero = G.hero_sprites()
    return {"fallen": _mon(MON.BASE[0]), "skeleton": _mon(MON.BASE[1]), "zombie": _mon(MON.BASE[2]),
            "demon": _mon(MON.BASE[3]), "lord": _mon(MON.FINAL),
            "hero": (hero[2], hero[3], 10)}                # il barbaro di spalle (colore pelle 10, come nel gioco)


SPRITES = _sprites()


# ------------------------------------------------------------------ testo
def scr_code(ch):
    if "a" <= ch <= "z":
        return ord(ch) - 96
    if ch in "0123456789 !',-./:?()":
        return ord(ch)
    raise SystemExit("gen_lore: carattere non ammesso nel testo: %r" % ch)


def styled(text):
    """'[parola]' -> giallo: ritorna [(carattere, colore)]"""
    out, col = [], TXT_COL
    for ch in text:
        if ch == "[":
            col = HI_COL
        elif ch == "]":
            col = TXT_COL
        else:
            out.append((ch, col))
    return out


def wrap(text):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        vis = len(re.sub(r"[\[\]]", "", cur + " " + wd if cur else wd))
        if vis > WIDTH:
            lines.append(cur)
            cur = wd
        else:
            cur = cur + " " + wd if cur else wd
    if cur:
        lines.append(cur)
    # le parentesi di colore che restano aperte a fine riga continuano nella riga seguente
    fixed, open_ = [], False
    for ln in lines:
        s = ("[" if open_ else "") + ln
        open_ = s.count("[") > s.count("]")
        fixed.append(s + ("]" if open_ else ""))
    return fixed


# ------------------------------------------------------------------ impaginazione
class Row:
    def __init__(self):
        self.ch = [32] * 40
        self.co = [0] * 40
        self.img = [None] * 40          # (immagine, forma) per i caratteri delle immagini (codice dopo l'allocazione)
        self.ev = []                    # eventi (tipo, dati) - SHAPES aggiunti dopo


def text_row(styled_chars, col0):
    r = Row()
    for i, (ch, c) in enumerate(styled_chars):
        r.ch[col0 + i] = scr_code(ch)
        r.co[col0 + i] = c
    return r


def build():
    rows, images, sprites_used, hold, stop = [], [], [], False, None
    lines = [l.rstrip("\n") for l in open(os.path.join(ROOT, "data", "lore.txt"))]
    para = []

    def flush():
        if para:
            for ln in wrap(" ".join(para)):
                rows.append(text_row(styled(ln), MARGIN))
            para.clear()

    def spr_use(name):
        if name not in sprites_used:
            sprites_used.append(name)
        return sprites_used.index(name)

    for ln in lines:
        if ln.startswith(";"):
            continue
        if not ln.strip():
            flush()
            if rows and not (rows[-1].ev or any(c != 32 for c in rows[-1].ch)) and getattr(rows[-1], "para_gap", False):
                continue
            r = Row()
            r.para_gap = True
            rows.append(r)
            continue
        if not ln.startswith("@"):
            para.append(ln.strip())
            continue
        flush()
        cmd, _, arg = ln[1:].partition(" ")
        if cmd == "gap":
            rows += [Row() for _ in range(int(arg))]
        elif cmd == "hold":
            hold = True
        elif cmd == "title" or cmd == "center":
            st = styled(arg if cmd == "center" else "[" + arg + "]")
            rows.append(text_row(st, (40 - len(st)) // 2))
        elif cmd == "stop":
            stop = (len(rows), int(arg))
        elif cmd == "spr":
            names = arg.split()
            n = len(names)
            x0 = 24 + (320 - (n * 48 + (n - 1) * 16)) // 2
            r0 = len(rows)
            rows += [Row() for _ in range(6)]
            for i, nm in enumerate(names):
                rows[r0].ev.append(("spr", nm, x0 + i * 64, 0))
                spr_use(nm)
        elif cmd == "img":
            name, _, over = arg.partition(" ")
            fn, mx, spr = IMAGES[name][:3]
            im = convert(fn(), mx, ccs=IMAGES[name][3] if len(IMAGES[name]) > 3 else range(8))
            im["name"] = name
            col0 = (40 - im["w"]) // 2
            r0 = len(rows)
            rows += [Row() for _ in range(im["h"])]
            for i, (p, cc) in enumerate(im["cells"]):
                cy, cx = divmod(i, im["w"])
                r = rows[r0 + cy]
                if any(p):
                    r.img[col0 + cx] = (len(images), p)
                    r.co[col0 + cx] = 8 + cc
            rows[r0].ev.append(("split", im["mc"]))
            im["r0"], im["r1"] = r0, r0 + im["h"] - 1
            images.append(im)
            if over:                                    # testo sopra l'immagine (riga centrale, colonne libere)
                st = styled("[" + over + "]")
                r = rows[r0 + im["h"] // 2]
                c0 = (40 - len(st)) // 2
                for i, (ch, c) in enumerate(st):
                    assert r.img[c0 + i] is None, "testo sopra l'immagine %s: colonna occupata" % name
                    r.ch[c0 + i] = scr_code(ch)
                    r.co[c0 + i] = c
            for nm, x, ry, dy in spr:
                rows[r0 + ry].ev.append(("spr", nm, x, dy))
                spr_use(nm)
        else:
            raise SystemExit("gen_lore: comando sconosciuto @" + cmd)
    flush()
    if stop is None:
        raise SystemExit("gen_lore: manca @stop")
    rows[stop[0]].ev.append(("stop", stop[1]))
    for r in rows:
        r.para_gap = False
    return rows, images, sprites_used, hold


# ------------------------------------------------------------------ allocazione dei codici (forme) e degli sprite
def allocate(rows, images):
    """codici 64..254 per le forme: un'immagine occupa i suoi codici dalla riga r0 (quando la sua prima riga entra in
    fondo allo schermo) finche' la sua ultima riga r1 e' uscita in alto (r1 + 25, piu' 1 di margine)."""
    busy = []                                           # (inizio, fine, primo codice, n)
    for k, im in enumerate(images):
        n = len(im["shapes"])
        t0, t1 = im["r0"], im["r1"] + 26
        for s in range(FIRST_SLOT, LAST_SLOT + 2 - n):
            if all(not (s < b[2] + b[3] and b[2] < s + n and t0 <= b[1] and b[0] <= t1) for b in busy):
                break
        else:
            raise SystemExit("gen_lore: niente codici liberi per l'immagine %s (%d forme): allontanarla dalle "
                             "immagini vicine o ridurne le forme" % (im["name"], n))
        busy.append((t0, t1, s, n))
        im["slot"] = s
        im["code"] = {p: s + i for i, p in enumerate(im["shapes"])}
    for r in rows:
        for c in range(40):
            if r.img[c] is not None:
                k, p = r.img[c]
                r.ch[c] = images[k]["code"][p]


def alloc_sprites(rows):
    busy = [-1] * 8                                     # ultima riga occupata per ogni sprite hardware
    for i, r in enumerate(rows):
        evs = []
        for e in r.ev:
            if e[0] == "spr":
                for hw in range(8):
                    if busy[hw] < i:
                        busy[hw] = i + SPR_BUSY
                        evs.append(("spr", e[1], e[2], e[3], hw))
                        break
                else:
                    raise SystemExit("gen_lore: piu' di 8 sprite sullo schermo alla riga %d" % i)
            else:
                evs.append(e)
        r.ev = evs


# ------------------------------------------------------------------ codifica
def rle(data):
    out, i = bytearray(), 0
    while i < len(data):
        j = i
        while j < len(data) and data[j] == data[i] and j - i < 255:
            j += 1
        n = j - i
        if n >= 4 or data[i] == 0xFF:
            out += bytes([0xFF, n, data[i]])
        else:
            out += bytes(data[i:j])
        i = j
    return out


def encode(rows, images, sprites_used):
    font = open(os.path.join(ROOT, "out", "work", "gfx", "uifont.bin"), "rb").read()[:64 * 8]
    charset = bytearray(font) + bytearray(2048 - len(font))
    spr = bytearray()
    sprp = {}
    for nm in sprites_used:
        f0, f1, _ = SPRITES[nm]
        sprp[nm] = (SPR_AT + len(spr)) // 64 & 255
        spr += bytes(f0) + bytes(f1)
    assert len(spr) <= SPR_MAX * 64, "troppi sprite"
    spr += bytearray(DATA_AT - SPR_AT - len(spr))
    shapes = bytearray()
    sh_at = {}
    for k, im in enumerate(images):
        sh_at[k] = DATA_AT + len(shapes)
        for p in im["shapes"]:
            shapes += bytes(shape_bytes(p))
    rows_at = DATA_AT + len(shapes)
    stream = bytearray()
    for i, r in enumerate(rows):
        evs = bytearray()
        n = 0
        for k, im in enumerate(images):                 # forme dell'immagine: nella riga in cui comincia
            if im["r0"] == i and im["shapes"]:
                a = sh_at[k]
                evs += bytes([0, im["slot"], len(im["shapes"]), a & 255, a >> 8])
                n += 1
        for e in r.ev:
            if e[0] == "split":
                evs += bytes([2, e[1][0], e[1][1]])
            elif e[0] == "spr":
                _, nm, x, dy, hw = e
                evs += bytes([1, hw, sprp[nm], x & 255, x >> 8, SPRITES[nm][2], dy, 1])
            elif e[0] == "stop":
                evs += bytes([3, e[1]])
            n += 1
        assert all(0 <= c < 255 for c in r.ch)
        stream += bytes([n]) + evs + rle(bytes(r.ch) + bytes(r.co))
    stream += bytes([0xFE])
    raw = bytes(charset) + bytes(spr) + bytes(shapes) + bytes(stream)
    return raw, rows_at


# ------------------------------------------------------------------ anteprima: decodifica dal flusso codificato
def preview(raw, rows_at, scale=2):
    mem = bytearray(65536)
    mem[LD_DST:LD_DST + len(raw)] = raw
    cs = bytearray(mem[CHARSET:CHARSET + 2048])
    p = rows_at
    out_rows, splits, sprs = [], [], []
    mc = (0, 0)
    while mem[p] != 0xFE:
        n = mem[p]
        p += 1
        for _ in range(n):
            t = mem[p]
            if t == 0:
                idx, cnt, a = mem[p + 1], mem[p + 2], mem[p + 3] | mem[p + 4] << 8
                cs[idx * 8:(idx + cnt) * 8] = mem[a:a + cnt * 8]
                p += 5
            elif t == 1:
                sprs.append((len(out_rows), mem[p + 2], mem[p + 3] | mem[p + 4] << 8, mem[p + 5], mem[p + 6]))
                p += 8
            elif t == 2:
                mc = (mem[p + 1], mem[p + 2])
                p += 3
            elif t == 3:
                p += 2
        data = bytearray()
        while len(data) < 80:
            b = mem[p]
            if b == 0xFF:
                data += bytes([mem[p + 2]]) * mem[p + 1]
                p += 3
            else:
                data.append(b)
                p += 1
        assert len(data) == 80, "RLE oltre la riga"
        out_rows.append((bytes(data[:40]), bytes(data[40:]), bytes(cs), mc))
    H = len(out_rows) * 8
    img = np.zeros((H, 320, 3))
    for ry, (ch, co, chs, (m1, m2)) in enumerate(out_rows):
        for cx in range(40):
            g = chs[ch[cx] * 8:ch[cx] * 8 + 8]
            col = co[cx]
            for y in range(8):
                b = g[y]
                if col < 8:
                    for x in range(8):
                        img[ry * 8 + y, cx * 8 + x] = PAL[col] if b & (128 >> x) else PAL[0]
                else:
                    for x in range(4):
                        v = (b >> (6 - 2 * x)) & 3
                        img[ry * 8 + y, cx * 8 + 2 * x:cx * 8 + 2 * x + 2] = PAL[(0, m1, m2, col & 7)[v]]
    for r, ptr, x, col, dy in sprs:
        d = mem[ptr * 64:ptr * 64 + 63]
        for y in range(21):
            for bx in range(3):
                b = d[y * 3 + bx]
                for q in range(4):
                    v = (b >> (6 - 2 * q)) & 3
                    if v:
                        c = PAL[(0, SPR_MC[0], col, SPR_MC[1])[v]]
                        X = x - 24 + (bx * 4 + q) * 4
                        Y = r * 8 + dy + y * 2
                        if 0 <= X < 316 and Y + 2 <= H:
                            img[Y:Y + 2, X:X + 4] = c
    im = Image.fromarray(img.astype(np.uint8))
    return im.resize((320 * scale, H * scale), Image.NEAREST), len(out_rows)


def write_logo(im):
    """il logo per il menu del loader BARBARIAN (src/barbarian.asm): forme ai codici 64.., celle, colori -> out/work/logo.inc"""
    code = {p: 64 + i for i, p in enumerate(im["shapes"])}
    ch = [code[p] if any(p) else 32 for p, cc in im["cells"]]
    co = [(8 + cc) if any(p) else 0 for p, cc in im["cells"]]
    L = ["; generato da tools/build/gen_lore.py - non modificare (logo della copertina per il menu del loader)",
         "LOGO_W = %d" % im["w"], "LOGO_H = %d" % im["h"], "LOGO_N = %d" % len(im["shapes"]),
         "LOGO_MC1 = %d" % im["mc"][0], "LOGO_MC2 = %d" % im["mc"][1], "logo_cs"]
    sb = [b for p in im["shapes"] for b in shape_bytes(p)]
    for i in range(0, len(sb), 16):
        L.append("        .byte " + ", ".join("$%02x" % b for b in sb[i:i + 16]))
    for name, arr in (("logo_ch", ch), ("logo_co", co)):
        L.append(name)
        for i in range(0, len(arr), im["w"]):
            L.append("        .byte " + ", ".join("%d" % b for b in arr[i:i + im["w"]]))
    open(os.path.join(ROOT, "out", "work", "logo.inc"), "w").write("\n".join(L) + "\n")


def main():
    rows, images, sprites_used, hold = build()
    write_logo(next(i for i in images if i["name"] == "logo"))
    allocate(rows, images)
    alloc_sprites(rows)
    raw, rows_at = encode(rows, images, sprites_used)
    assert LD_DST + len(raw) <= LD_END
    comp, delta = pack.zx0(raw, "ldat")
    assert zx0dec.zx0_decompress(comp) == raw
    last = LD_DST + len(raw) - 1
    load_at = last + delta - len(comp) + 1
    assert load_at > LD_DST and load_at + len(comp) <= LD_END
    pack.inplace_check(comp, load_at, LD_DST, raw)
    out = os.path.join(ROOT, "out", "work")
    open(os.path.join(out, "ldat.prg"), "wb").write(bytes([load_at & 255, load_at >> 8]) + comp)
    open(os.path.join(out, "ldat_raw.bin"), "wb").write(raw)
    with open(os.path.join(out, "lore.inc"), "w") as f:
        f.write("; generato da tools/build/gen_lore.py - non modificare\n")
        f.write(f"LD_AT    = ${load_at:04x}         ; LDAT compresso (ZX0) caricato qui\n")
        f.write(f"LD_DST   = ${LD_DST:04x}         ; e decompresso sul posto qui (delta {delta})\n")
        f.write(f"LD_LEN   = {len(comp)}\nLD_RAW   = {len(raw)}\n")
        f.write(f"LR_ROWS  = ${rows_at:04x}         ; prima riga del flusso\n")
        f.write(f"LR_NROWS = {len(rows)}\n")
        f.write(f"LR_HOLD  = {HOLD_FRAMES if hold else 0}            ; fotogrammi di pausa sulla prima schermata\n")
    im, n = preview(raw, rows_at)
    im.save(os.path.join(out, "lore_preview.png"))
    gd = os.path.join(ROOT, "out", "work", "atlas")
    os.makedirs(gd, exist_ok=True)
    im.save(os.path.join(gd, "lore.png"))
    blocks = (len(comp) + 2 + 253) // 254
    print(f"gen_lore: {len(rows)} righe, {len(images)} immagini ({', '.join('%s %d' % (i['name'], len(i['shapes'])) for i in images)} forme),"
          f" sprite {', '.join(sprites_used)}; dati {len(raw)} B -> {len(comp)} B ZX0 ({blocks} blocchi), carico a ${load_at:04x}")


if __name__ == "__main__":
    main()
