#!/usr/bin/env python3
"""Graphics atlas of the game: out/work/atlas/index.html (+ a lossless PNG per tile and per map, tiles.json). English (11/11).

Reads the same files the C64 reads (out/work/gfx/gfx0.prg, gfx1.prg, gfx2.prg, charset.bin, uifont.bin, out/work/title.koa) and
the palettes from src/game.asm: the rendering is identical by construction, without VICE.
Two parts (11/11): the common graphics (charset, HUD, UI font, sprites, menus from docs/screens, title, story) and one
part per chapter (data/chapters.yaml: village, dungeon themes, final map).
Sets: village (VILLG, data/town_map.txt), dungeon with the 8 palettes (DUNGA..DUNGH, data/atlas_dungeon.txt), throne
room (TRONO, map of tools/build/gen_final.py). Tile id = 5 letters of the set + the legend letter.
Groups (elements made of several tiles): data/atlas_groups.json.

Usage: python3 tools/atlas/gen_atlas.py [--check]   (--check: only the checks, for tests/run_tests.sh)"""
import json, os, random, re, sys
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build"))   # (13/11) generatori in tools/build/
from PIL import Image
import gen_gfx as G
import gen_maps as M
import gen_final as F
import atlas_names as AN

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "out", "work", "atlas")
CHECK = "--check" in sys.argv
# palette VICE "colodore" (la stessa di tools/build/gen_title.py)
PAL = [(0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189), (139, 63, 150), (85, 160, 73), (64, 49, 141),
       (191, 206, 114), (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80), (120, 120, 120), (148, 224, 137),
       (120, 105, 196), (159, 159, 159)]
CNAME = ["black", "white", "red", "cyan", "purple", "green", "blue", "yellow", "orange", "brown", "light red",
         "dark grey", "grey", "light green", "light blue", "light grey"]
errors, warns = [], []


def rd(p):
    return open(os.path.join(ROOT, p), "rb").read()


# ------------------------------------------------------------------ palette (src/game.asm)
src_main = open(os.path.join(ROOT, "src", "game.asm")).read()
pals = {}
for k in ("pal_bg", "pal_c1", "pal_c2", "pal_ram"):
    m = re.search(r"^%s\s+\.byte\s+([0-9, ]+)" % k, src_main, re.M)
    pals[k] = [int(x) for x in m.group(1).split(",")]
for v in pals["pal_ram"]:
    if v < 8:
        errors.append("pal_ram %d < 8: multicolour off" % v)


def palette(i):
    """indice di palette -> 4 colori C64 per le coppie di bit 00, 01, 10, 11"""
    return [pals["pal_bg"][i], pals["pal_c1"][i], pals["pal_c2"][i], pals["pal_ram"][i] & 7]


# ------------------------------------------------------------------ tile dai file GFXn
consts = open(os.path.join(ROOT, "out", "work", "gfx_consts.inc")).read()
NT = int(re.search(r"^GFX_NT = (\d+)", consts, re.M).group(1))
DN = int(re.search(r"^GFX_DSTRIP = (\d+)", consts, re.M).group(1)) // 8


def tiles_from(data, n):
    """GFXn file without header: 4 strips of n characters (top-left, top-right, bottom-left, bottom-right) ->
    for each tile 16 rows x 8 multicolour pixels (indices 0..3)"""
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


town_t = tiles_from(rd("out/work/gfx/gfx0.prg")[2:], NT)
dun_t = tiles_from(rd("out/work/gfx/gfx1.prg")[2:], DN)
trono_t = tiles_from(rd("out/work/gfx/gfx2.prg")[2:], DN)


def post_walls(m, rng):
    """come post_walls in src/game/dungeon.asm: WALL con sotto un tile >= 2 -> WALLFACE; FLOOR -> FLOORB / FLOORC con
    probabilita' 1/8 ciascuno (nel gioco dal generatore casuale; qui un seme fisso: la variazione e' estetica)"""
    T = G.TID
    for y in range(len(m) - 1):
        for x in range(48):
            if m[y][x] == T["WALL"] and m[y + 1][x] >= 2:
                m[y][x] = T["WALLFACE"]
    for y in range(len(m)):
        for x in range(48):
            if m[y][x] == T["FLOOR"]:
                r = rng.randrange(8)
                if r < 2:
                    m[y][x] = T["FLOORB"] + r


def read_map(path, legend_chars):
    rows = [l.rstrip("\n") for l in open(os.path.join(ROOT, path)) if l.strip() and not l.startswith(";")]
    for r in rows:
        if len(r) != 48:
            errors.append("%s: row of %d characters (48 needed)" % (path, len(r)))
    return [[legend_chars[c] for c in r] for r in rows]


# ------------------------------------------------------------------ set
TOWN_LET = {G.TTID[n]: c for n, c in M.LEGEND.items()}
DUN_LET = {G.TID[n]: c for n, c in G.DUN_LEGEND.items()}
town_map = read_map("data/town_map.txt", {c: G.TTID[n] for c, n in M.inv_legend().items()})
dmap = read_map("data/atlas_dungeon.txt", {c: G.TID[n] for n, c in G.DUN_LEGEND.items()})
post_walls(dmap, random.Random(7))
fm = [[G.TID[n] for n in r] for r in F.final_map()]
post_walls(fm, random.Random(7))
star, circ, chests = F.final_figures()
for x, y in star:
    fm[y][x] = G.TID["GRASSA"]
for x, y in circ:
    fm[y][x] = G.TID["GRASSB"]
for x, y in chests:
    fm[y][x] = G.TID["CHEST"]

# ruoli nel codice: costanti T_* usate in src/ (escluso il file generato)
srcs = "".join(open(os.path.join(dp, f)).read() for dp, _, fs in os.walk(os.path.join(ROOT, "src")) for f in fs
               if f.endswith(".asm") and f != "gfx_consts.inc")
tconst = {}
for m_ in re.finditer(r"^(T_\w+)\s*=\s*(\d+)(.*)$", consts, re.M):
    tconst.setdefault(int(m_.group(2)), []).append((m_.group(1), "villaggio" in m_.group(3)))


def roles(slot, town):
    out = []
    for name, town_only in tconst.get(slot, []):
        if town_only and not town:
            continue
        if town and not town_only and slot < len(G.TILES) and G.TILES[slot] != G.TOWN_TILES[slot]:
            continue                                    # posto del dungeon che nel villaggio ospita un altro tile
        if re.search(r"\b%s\b" % name, srcs):
            out.append(name)
    return out


SETS = []


def add_set(code, title, tiles, names, letters, pal_i, mp, used, solid_names, town, pal=None, solid_list=None, mapsrc=None):
    """pal = colori propri (villaggi dei capitoli 2..: stanno nel file TWNc, non nelle tabelle di src/game.asm);
    solid_list = posti solidi propri; mapsrc = da dove viene la mappa (testo per la pagina)"""
    if solid_list is None:
        nm = G.TOWN_TILES if town else G.TILES
        solid_list = [i for i in range(len(tiles)) if nm[i] in solid_names]
    SETS.append(dict(code=code, title=title, tiles=tiles, names=names, letters=letters, pal=pal or palette(pal_i), pal_i=pal_i,
                     solid_list=solid_list, mapsrc=mapsrc,
                     map=mp, used=used, solid=solid_names, town=town))


add_set("VILLG", "Village (GFX0, palette 0)", town_t, {i: n for i, n in enumerate(G.TOWN_TILES)}, TOWN_LET, 0,
        town_map, set(range(NT)), G.SOLID, True)
# (15/11, TODO Z2) villaggi dei capitoli 2..5: file TWNc, tile, colori, mappa e tile solidi propri (tools/build/villages.py).
# I nomi dei tile ridisegnati stanno nel modulo del villaggio (vilN_*.py) e si aggiungono qui ad AN.TILE.
import villages as VIL
for _c, _v in sorted(VIL.VILLAGES.items()):
    if not _v["tiles"]:
        continue
    _names = {}
    for _i, _n in enumerate(G.TOWN_TILES):
        _t = VIL.tile_name(_c, _n)
        if _t:
            AN.TILE["V%d:%s" % (_c, _n)] = _t
        _names[_i] = "V%d:%s" % (_c, _n) if _t else _n
    _map = read_map(_v["map"], {c: G.TTID[n] for c, n in M.inv_legend().items()})
    _sol = VIL.solid(_c, G.TOWN_TILES, G.SOLID)
    add_set("VILL%d" % _c, "%s (TWN%d, its own colours)" % (_v["name"], _c), tiles_from(rd("out/work/gfx/twn%d.prg" % _c)[2:], NT),
            _names, TOWN_LET, 0, _map, {t for r in _map for t in r} | {G.TTID["PORTAL"]}, G.SOLID, True,
            pal=list(_v["pal"]), solid_list=[i for i in range(NT) if _sol[i]], mapsrc=_v["map"])
for k in range(1, 9):
    add_set("DUNG" + "ABCDEFGH"[k - 1], "Dungeon, palette %d (GFX1)" % k, dun_t, {i: G.TILES[i] for i in range(DN)}, DUN_LET,
            k, dmap, {G.TID[n] for n in G.DUN_USED}, G.SOLID, False)
add_set("TRONO", "Throne room, level 20 (GFX2, palette 4)", trono_t,
        {i: G.TRONO_NAMES.get(G.TILES[i], G.TILES[i]) for i in range(DN)}, DUN_LET, 4, fm,
        {G.TID[n] for n in G.TRONO_USED}, G.SOLID, False)

# ------------------------------------------------------------------ controlli
# nomi e descrizioni (tools/atlas/atlas_names.py, regola del committente del 10/11: ogni tile e ogni glifo ha il suo nome)
for s in SETS:
    for i, n in s["names"].items():
        if n not in AN.TILE:
            errors.append("%s: tile %d (%s) has no name and description in tools/atlas/atlas_names.py (TILE)" % (s["code"], i, n))
ui_src = open(os.path.join(ROOT, "src", "game", "ui.asm")).read()
for m_ in re.finditer(r"^((?:CH|BOX)_\w+)\s*=\s*(\d+)", ui_src, re.M):
    k, c = m_.group(1), int(m_.group(2))
    if c not in AN.UI or AN.UI[c][1] != k:
        errors.append("UI glyph %s = %d: missing (or with another constant) in tools/atlas/atlas_names.py (UI)" % (k, c))
import gen_font as FONT
for c in FONT.ICON:
    if c not in AN.UI:
        errors.append("UI glyph %d (tools/build/gen_font.py ICON) without a name in tools/atlas/atlas_names.py (UI)" % c)
for n in G.HUD_ID:
    if n not in AN.HUD:
        errors.append("HUD glyph %s without a name in tools/atlas/atlas_names.py (HUD)" % n)
for s in SETS:
    ids = [s["code"] + s["letters"][i] for i in range(len(s["tiles"]))]
    if len(set(ids)) != len(ids):
        errors.append("%s: duplicate ids" % s["code"])
    present = {t for r in s["map"] for t in r}
    miss = s["used"] - present - {G.TID["PORTAL"], G.TID["FREE8"]}      # il portale compare solo aperto (villaggio; sala del trono: portale nero dopo la leva)
    if miss and s["code"] in ("VILLG", "DUNGA", "TRONO"):
        (errors if s["code"] == "DUNGA" else warns).append(
            "%s: tiles never on the map: %s" % (s["code"], ", ".join(s["names"][i] for i in sorted(miss))))
groups = json.load(open(os.path.join(ROOT, "data", "atlas_groups.json")))
setmap = {s["code"]: s for s in SETS}


def find(s, rows):
    let = s["letters"]
    H, W = len(rows), len(rows[0])
    for y in range(len(s["map"]) - H + 1):
        for x in range(48 - W + 1):
            if all(let[s["map"][y + j][x + i]] == rows[j][i] for j in range(H) for i in range(W) if rows[j][i] != "?"):
                return x, y
    return None


for g in groups:
    s = setmap[g["set"]]
    if "rect" in g:
        x0, y0, x1, y1 = g["rect"]
        g["rows"] = ["".join(s["letters"][s["map"][y][x]] for x in range(x0, x1 + 1)) for y in range(y0, y1 + 1)]
        g["at"] = (x0, y0)
    else:
        g["at"] = find(s, g["rows"])
        if g["at"] is None:
            warns.append("group %s/%s not found on the map" % (g["set"], g["name"]))
for w in warns:
    print("warning:", w)
if errors:
    for e in errors:
        print("ERROR:", e)
    sys.exit(1)
if CHECK:
    print("atlas: checks ok (%d sets, %d groups)" % (len(SETS), len(groups)))
    sys.exit(0)

# ------------------------------------------------------------------ PNG
os.makedirs(os.path.join(OUT, "png"), exist_ok=True)


def fname(tid):
    return "".join(c if c.isalnum() else "_%02x" % ord(c) for c in tid)


def tile_img(px, pal, sc=4):
    im = Image.new("RGB", (16 * sc, 16 * sc))
    for y in range(16):
        for x in range(8):
            c = PAL[pal[px[y][x]]]
            for yy in range(sc):
                for xx in range(2 * sc):
                    im.putpixel((x * 2 * sc + xx, y * sc + yy), c)
    return im


def map_img(s, sc=2, gap=1):
    H = len(s["map"])
    im = Image.new("RGB", (48 * (16 * sc + gap) + gap, H * (16 * sc + gap) + gap), (40, 40, 40))
    cache = {}
    for y in range(H):
        for x in range(48):
            t = s["map"][y][x]
            if t not in cache:
                cache[t] = tile_img(s["tiles"][t], s["pal"], sc)
            im.paste(cache[t], (gap + x * (16 * sc + gap), gap + y * (16 * sc + gap)))
    return im


records = []
for s in SETS:
    counts = {}
    for r in s["map"]:
        for t in r:
            counts[t] = counts.get(t, 0) + 1
    s["counts"] = counts
    for i, px in enumerate(s["tiles"]):
        tid = s["code"] + s["letters"][i]
        png = "png/%s.png" % fname(tid)
        tile_img(px, s["pal"]).save(os.path.join(OUT, png), optimize=True)
        name = s["names"][i]
        records.append(dict(id=tid, set=s["code"], tile=i, letter=s["letters"][i], name=name.lower(),
                            nome=AN.TILE[name][0], desc=AN.TILE[name][1],
                            solid=i in s["solid_list"],
                            used=i in s["used"], role=roles(i, s["town"]), palette=s["pal_i"],
                            chars=[i, 64 + i, 128 + i, 192 + i], png=png, count=counts.get(i, 0),
                            group=[g["name"] for g in groups if g["set"] == s["code"] and s["letters"][i] in "".join(g["rows"])]))
    map_img(s).save(os.path.join(OUT, "png", "%s_map.png" % s["code"]), optimize=True)
json.dump(records, open(os.path.join(OUT, "tiles.json"), "w"), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ titolo
koa = rd("out/work/title.koa")
bm, scr, col, bg = koa[:8000], koa[8000:9000], koa[9000:10000], koa[10000]
tim = Image.new("RGB", (320, 200))
used_cells, free_rows, colcount = 0, {}, {}
for cell in range(1000):
    cy, cx = divmod(cell, 40)
    cols = [bg, scr[cell] >> 4, scr[cell] & 15, col[cell] & 15]
    nonbg = False
    for y in range(8):
        b = bm[cell * 8 + y]
        for p in range(4):
            v = (b >> (6 - 2 * p)) & 3
            nonbg |= v != 0
            for xx in range(2):
                tim.putpixel((cx * 8 + p * 2 + xx, cy * 8 + y), PAL[cols[v]])
            if v:
                colcount[cols[v]] = colcount.get(cols[v], 0) + 1
    if nonbg:
        used_cells += 1
    else:
        free_rows.setdefault(cy, []).append(cx)
tim.resize((640, 400), Image.NEAREST).save(os.path.join(OUT, "png", "title.png"), optimize=True)
title_size = len(rd("out/work/title.prg")) - 2
import shutil
shutil.copy(os.path.join(ROOT, "out", "work", "gfx", "sprites.png"), os.path.join(OUT, "png", "sprites.png"))


# ------------------------------------------------------------------ mostri per capitolo (15/11): dai file GFXn che legge il C64
def _consts():
    t = open(os.path.join(ROOT, "out", "work", "gfx_consts.inc")).read()
    return {k: int(v.replace("$", "0x"), 0) for k, v in re.findall(r"^(GFX_\w+|NM_AT)\s*=\s*(\$?[0-9a-fA-F]+)", t, re.M)}


def _spr_png(d, col, path, sc=4):
    """sprite multicolor 24x21 (63 byte): 01 = MC0 marrone 9, 10 = colore dello sprite, 11 = MC1 grigio chiaro 15"""
    im = Image.new("RGB", (24 * sc, 21 * sc), (24, 24, 28))
    pal = [None, PAL[9], PAL[col], PAL[15]]
    for y in range(21):
        for bx in range(3):
            b = d[y * 3 + bx]
            for p in range(4):
                v = (b >> (6 - 2 * p)) & 3
                if v:
                    for xx in range(2 * sc):
                        for yy in range(sc):
                            im.putpixel(((bx * 4 + p) * 2 * sc + xx, y * sc + yy), pal[v])
    im.save(path, optimize=True)


def monster_sets():
    K = _consts()
    off_m = 4 * K["GFX_DSTRIP"]
    off_s, off_i = off_m + K["GFX_MONS"], off_m + K["GFX_MONS"] + K["GFX_STRONG"]
    tiers = ["base"] * 4 + ["strong"] * 4 + ["boss"]
    out = []
    for f in range(1, 2 * G.CHAPTERS + 1):
        d = rd("out/work/gfx/gfx%d.prg" % f)[2:]
        info = d[off_i:off_i + K["GFX_INFO"]]
        mons = []
        for t in range(9):
            spr = d[off_m + t * 128:off_m + t * 128 + 63] if t < 4 else d[off_s + (t - 4) * 128:off_s + (t - 4) * 128 + 63]
            a = info[9 + t] - (K["NM_AT"] & 255)
            name = "".join(chr(c + 96) if 1 <= c <= 26 else chr(c) for c in info[a:info.index(0, a)])
            png = "mon_f%d_%d.png" % (f, t + 1)
            if not CHECK:
                _spr_png(spr, info[t], os.path.join(OUT, "png", png))
            mons.append(dict(t=t + 1, name=name, col=info[t], tier=tiers[t], png=png))
        out.append(dict(file="GFX%d" % f, chapter=(f + 1) // 2, boss=f % 2 == 0, mons=mons))
    return out


def spans(xs):
    out, i = [], 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
            j += 1
        out.append("%d" % xs[i] if i == j else "%d–%d" % (xs[i], xs[j]))
        i = j + 1
    return ", ".join(out)


# ------------------------------------------------------------------ mappa dei 256 codici del charset del gioco
cs = rd("out/work/gfx/charset.bin")
codes = []
hud_inv = {c: n for n, c in G.HUD_ID.items()}
for c in range(256):
    q, i = divmod(c, 64)
    if i < NT:
        kind, lab = "tile", "tile %d, quarter %d (%s)" % (i, q, G.TOWN_TILES[i] + " / " + G.TILES[i] if G.TOWN_TILES[i] != G.TILES[i] else G.TILES[i])
    elif c in hud_inv:
        n = hud_inv[c]
        kind = "warn" if n in G.HUD_WARN else ("letter" if len(n) == 1 and n.isalpha() else "hud")
        lab = "HUD glyph %s: %s (%s)" % (n, AN.HUD[n][0], AN.HUD[n][2])
    elif c in AN.MINI and c != 63:
        kind, lab = "mini", AN.MINI[c][0] + ": " + AN.MINI[c][2]
    elif c in G.HUD_FREE:
        kind, lab = "free", "FREE"
    else:
        kind, lab = ("mini", "blank (reserved: minimap)") if c == 63 else (("free" if not any(cs[c * 8:c * 8 + 8]) else "other"), "FREE")
    codes.append(dict(c=c, k=kind, l=lab, b=list(cs[c * 8:c * 8 + 8])))
uif = list(rd("out/work/gfx/uifont.bin"))
uiglyphs = AN.ui_glyphs()
hudglyphs = [dict(c=c, n=n, name=AN.HUD[n][0], key=AN.HUD[n][1], desc=AN.HUD[n][2], b=list(cs[c * 8:c * 8 + 8]))
             for n, c in sorted(G.HUD_ID.items(), key=lambda t: t[1])]
hudglyphs += [dict(c=c, n="-", name=v[0], key=v[1], desc=v[2], b=list(cs[c * 8:c * 8 + 8])) for c, v in sorted(AN.MINI.items())]

# ------------------------------------------------------------------ HTML
DATA = dict(PAL=[list(p) for p in PAL], CNAME=CNAME, sets=[], groups=[], codes=codes, uif=uif, ui=uiglyphs, hud=hudglyphs, space=None)
for s in SETS:
    DATA["sets"].append(dict(code=s["code"], title=s["title"], pal=s["pal"], pal_i=s["pal_i"],
                             tiles=s["tiles"], names={str(i): n.lower() for i, n in s["names"].items()},
                             nomi={str(i): AN.TILE[n][0] for i, n in s["names"].items()},
                             descs={str(i): AN.TILE[n][1] for i, n in s["names"].items()},
                             letters={str(i): c for i, c in s["letters"].items()}, map=s["map"],
                             used=sorted(s["used"]), counts={str(k): v for k, v in s["counts"].items()},
                             solid=s["solid_list"], mapsrc=s["mapsrc"],
                             roles={str(i): roles(i, s["town"]) for i in range(len(s["tiles"]))},
                             free_letters="".join(chr(c) for c in range(33, 127)
                                                  if chr(c) not in s["letters"].values() and chr(c) != ";")))
for g in groups:
    s = setmap[g["set"]]
    inv = {c: i for i, c in s["letters"].items()}
    DATA["groups"].append(dict(set=g["set"], name=g["name"], label=g["label"], rows=g["rows"], at=g["at"],
                               tiles=[[inv.get(c, -1) for c in r] for r in g["rows"]]))
# ------------------------------------------------------------------ spazio: posti liberi utilizzabili e % di utilizzo
space = []
for s in SETS:
    if (s["code"].startswith("DUNG") and s["code"] != "DUNGA") or (s["code"].startswith("VILL") and s["code"] != "VILLG"):
        continue
    cap = len(s["tiles"])
    free = [i for i in range(cap) if i not in s["used"]]
    nm = {"VILLG": "Village tiles (GFX0)", "DUNGA": "Dungeon tiles (GFX1, every theme 1-7)", "TRONO": "Throne room tiles (GFX2)"}[s["code"]]
    note = ("every slot of the charset (45 = 64 codes of the quarter minus the 19 fixed HUD characters) is used by the village"
            if s["code"] == "VILLG" else
            "slots in the file: %d (DUN_NT). The free ones hold village leftovers or nothing: a new tile replaces them in the "
            "theme file at no cost. Beyond the file up to %d slots by making GFXn longer (32 B per tile)." % (cap, NT))
    space.append(dict(name=nm, used=cap - len(free), cap=cap, free=[dict(i=i, n=s["names"][i].lower(), id=s["code"] + s["letters"][i]) for i in free], note=note))
kinds = {}
for o in codes:
    kinds[o["k"]] = kinds.get(o["k"], 0) + 1
space.append(dict(name="Game charset (256 codes: tiles, HUD, minimap)", used=256 - kinds.get("free", 0), cap=256,
                  free=[dict(i=o["c"], n=o["l"], id="") for o in codes if o["k"] == "free"],
                  note="free codes for new HUD glyphs: the ones listed (the others are 4 tile quarters, HUD glyphs, minimap)"))
uf = [o for o in uiglyphs if o["kind"] == "free"]
space.append(dict(name="UI font (128 codes)", used=128 - len(uf), cap=128, free=[dict(i=o["c"], n=o["name"], id="") for o in uf],
                  note="certainly free: only the ones listed. Codes 64-127 not redrawn are the inverted letters: many never "
                       "show on a screen, but which ones is not verified, so here they count as used"))
title_info = dict(used=used_cells, free=1000 - used_cells, rows={str(k): spans(v) for k, v in sorted(free_rows.items())},
                  colors=sorted(colcount.items(), key=lambda x: -x[1]), size=title_size)
html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "atlas_template.html")).read()
DATA["space"] = space
# ------------------------------------------------------------------ chapters (data/chapters.yaml) and common menus
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chapters_db  # noqa: E402
CHAP = chapters_db.load()["chapters"]          # (11/11) local levels + global depth (docs/wiki/quests.md 3.8)
import bestiary  # noqa: E402
BEST = bestiary.load()
for ch in CHAP:
    for code in ch["atlas_sets"] + [ch["village"]["atlas_set"]] + ([ch["final"]["atlas_set"]] if ch.get("final") else []):
        if code and code not in setmap:
            errors.append("data/chapters.yaml: chapter %s: set %s unknown" % (ch["id"], code))
in_ch = {c for ch in CHAP for c in ch["atlas_sets"] + [ch["village"]["atlas_set"]] + ([ch["final"]["atlas_set"]] if ch.get("final") else []) if c}
for s in SETS:
    if s["code"] not in in_ch:
        warns.append("set %s in no chapter (data/chapters.yaml)" % s["code"])
DATA["chapters"] = [dict(id=ch["id"], name=ch["name"], implemented=ch["implemented"], village=ch["village"],
                         levels=dict(n=ch["n_levels"], first_depth=ch["first_depth"], last_depth=ch["last_depth"]),
                         bestiary=[dict(name=r["name"], tier=r["tier"], concept=r["implemented"] != "yes") for r in BEST
                                   if r["chapter"] == ch["id"]],
                         themes=ch["themes"], final=ch.get("final"),
                         sets=[c for c in [ch["village"]["atlas_set"]] + ch["atlas_sets"] + ([ch["final"]["atlas_set"]] if ch.get("final") else []) if c])
                    for ch in CHAP]
MENUS = {"menu_iniziale": ("barbarian menu", "start menu: the heroes, create new barbarian, quit the game"),
         "nuovo_barbaro": ("new barbarian", "name and seed of a new hero"), "scheda": ("barbarian details", "a saved hero: start, delete, back"),
         "badsave": ("bad save", "saves of another version: offer to delete"), "quit": ("quit", "quit the game?"),
         "menu_gioco": ("game menu", "RUN/STOP in the game: resume, save game, quit game"), "inventario": ("backpack", "inventory (I)"),
         "fabbro": ("blacksmith", "shop of the smith"), "alchimista": ("alchemist", "shop of the alchemist"),
         "locanda": ("inn", "the inn chest (OVLT/OVL2)"), "locanda_scelta": ("inn: choice", "inn: what to wear"),
         "baule": ("chest", "a level chest"), "mappa": ("minimap", "minimap (M)"), "leva": ("lever", "the lever of the throne room"),
         "morte": ("death", "the death screen"), "io_screen": ("loading", "waiting screen while loading or saving"),
         "io_generico": ("loading", "generic loading"), "io_livello": ("level loading", "loading of a level"),
         "personaggio": ("character", "C screen: pending points with the preview of the new values, respec tokens"),
         "personaggio_vuoto": ("character: no points", "C screen with no points to spend and no respec tokens"),
         "trucchi": ("cheats", "debug and test builds only (CHEATS=1): the cheat menu, entry 'cheats' of the game menu")}
scr_dir = os.path.join(ROOT, "docs", "screens")
DATA["menus"] = [dict(file=f, title=MENUS.get(f[:-4], (f[:-4], ""))[0], desc=MENUS.get(f[:-4], ("", "(no description: add it in tools/atlas/gen_atlas.py MENUS)"))[1])
                 for f in sorted(os.listdir(scr_dir)) if f.endswith(".png") and f != "tutti_i_menu.png"]
DATA["monsters"] = monster_sets()
html = html.replace("/*DATA*/null", json.dumps(DATA, separators=(",", ":")))
html = html.replace("/*TITLE*/null", json.dumps(title_info))
open(os.path.join(OUT, "index.html"), "w").write(html)
print("atlas: out/work/atlas/index.html (%d sets, %d tiles, %d groups, %d chapters)" % (len(SETS), len(records), len(groups), len(DATA["chapters"])))
