"""Boss levels of chapters 1-3 (19/11, owner's request: every boss level has its own theme and shape, tied to its chapter;
docs/wiki/dungeon.md "Piani del boss dei capitoli 1-3"): 1 crypt (latin cross), 2 island in the middle of the swamp (ruined mill),
3 half-collapsed cave (landslide). Sources: data/maps/bosschapN.txt (tools/build/gen_bossmap.py), tiles tools/build/boss_gfx.py
on the tiles of the chapter's levels, palette data/chapters.yaml final.palette. The throne room (level 20) is not touched.
One VICE session (CHAIN); screenshots of arrival and boss in out/work/bossmaps/ (to look at, not compared)."""
import collections, os
from c64test import test, check
from lib.c64 import Game, ROOT
from lib.play import new_game
import boss_gfx as BG, gen_gfx as GG, chapters_db

CHAIN = True
SHOTS = os.path.join(ROOT, "out", "work", "bossmaps")
W = 48
PAL = {ch["id"]: ch["final"].get("palette") for ch in chapters_db.load()["chapters"] if ch.get("final")}


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    os.makedirs(SHOTS, exist_ok=True)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def source(c):
    """the map of data/maps/bosschapC.txt as tile numbers, WALL left as WALL (post_walls turns some into WALLFACE)"""
    rows = [l.rstrip("\n") for l in open(os.path.join(ROOT, "data", "maps", "bosschap%d.txt" % c)) if not l.startswith(";")]
    leg = dict({"#": "WALL", ".": "FLOOR", "<": "STAIRSU", "B": "FLOOR"}, **BG.LEGEND[c])
    return [[GG.TID[leg[ch]] for ch in r] for r in rows], rows


@test("BOSSMAP-10", "boss levels 5, 10, 15: the map of data/maps/bosschapN.txt (after post_walls), the furniture of the chapter, "
      "stairs up to the boss walkable, no stairs down, its own palette (final.palette), the tiles of GFX(2c) from boss_gfx.py")
def boss_maps(ctx):
    g = ctx["g"]; L = g.L
    T = GG.TID
    for c in (1, 2, 3):
        g.poke(L["c_chap"], c); g.poke(L["c_unl"], c)
        g.call_keep(L["change_level"], regs="a=%02x,x=00" % (5 * c), tmax=150); g.frames(3)
        check(g.b(L["lv_cboss"]) == 1, "level %d: lv_cboss %d" % (5 * c, g.b(L["lv_cboss"])))
        src, rows = source(c)
        m = g.mem(0xC000, W * W)
        tile = lambda x, y: m[y * W + x]
        bad = []
        for y in range(W):
            for x in range(W):
                s, t = src[y][x], tile(x, y)
                if s == T["WALL"]:
                    ok = t in (T["WALL"], T["WALLFACE"])
                elif s == T["FLOOR"]:
                    ok = t in (T["FLOOR"], T["FLOORB"], T["FLOORC"])
                else:
                    ok = t == s
                if not ok:
                    bad.append((x, y, s, t))
        check(not bad, "level %d: %d tiles differ from bosschap%d.txt, first %s" % (5 * c, len(bad), c, bad[:5]))
        used = {tile(x, y) for y in range(W) for x in range(W)}
        miss = [n for n in BG.LEGEND[c].values() if T[n] not in used]
        check(not miss, "level %d: furniture never on the map: %s" % (5 * c, miss))
        check(T["STAIRSD"] not in used, "level %d: stairs down on the boss level" % (5 * c))
        sx, sy, bx, by = g.mem(L["bm_hdr"], 4)
        sol = g.mem(L["solidtab"], 48)
        seen, q = {(sx, sy)}, collections.deque([(sx, sy)])
        while q:
            x, y = q.popleft()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= n[0] < W and 0 <= n[1] < W and n not in seen and not sol[tile(*n)] & 1:
                    seen.add(n); q.append(n)
        check((bx, by) in seen, "level %d: the boss (%d,%d) is not reachable from the stairs (%d,%d)" % (5 * c, bx, by, sx, sy))
        walk = {(x, y) for y in range(W) for x in range(W) if not sol[tile(x, y)] & 1}
        check(walk == seen, "level %d: %d walkable tiles not reachable from the stairs" % (5 * c, len(walk - seen)))
        exp = PAL[c]
        got = (g.b(0xD022) & 15, g.b(0xD023) & 15)
        want = (g.b(L["pal_c1"] + exp), g.b(L["pal_c2"] + exp))
        check(got == want, "level %d: colours %s, palette %d wants %s" % (5 * c, got, exp, want))
        d = open(os.path.join(ROOT, "out", "work", "gfx", "gfx%d.prg" % (2 * c)), "rb").read()[2:]
        DN = GG.DUN_NT
        for n, gr in BG.tiles(c).items():
            want_ch = GG.tile_chars(gr)
            for q_, ch in enumerate(want_ch):
                o = (q_ * DN + T[n]) * 8
                check(bytes(d[o:o + 8]) == bytes(ch), "GFX%d: tile %s, quarter %d differs from boss_gfx.py" % (2 * c, n, q_))
        g.poke(L["godmode"], 1)
        g.teleport(sx, sy); g.frames(4)
        g.screenshot(os.path.join(SHOTS, "boss%d_arrival.png" % c))
        g.teleport(bx, by + 2); g.frames(4)
        g.screenshot(os.path.join(SHOTS, "boss%d_boss.png" % c))
    g.poke(L["godmode"], 0)
    # the throne room stays as it was: red palette, the star around the boss
    g.poke(L["c_chap"], 4); g.poke(L["c_unl"], 4)
    g.call_keep(L["change_level"], regs="a=%02x,x=00" % L["MAXLEVEL"], tmax=150); g.frames(3)
    check(g.b(0xD022) & 15 == g.b(L["pal_c1"] + 4), "throne room: palette not red")
    m = g.mem(0xC000, W * W)
    check(T["GRASSA"] in m, "throne room: no star tiles")
