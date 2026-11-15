"""Villages of the chapters (15/11, TODO Z2, docs/villaggio.md): every chapter has its own village file TWNc with its own tiles,
map, colours, solid tiles, name of the healing place and positions (portal, way down, entry, exit, doors). The game copies
the header of the file into town_k / solidtab (gfx_install) and reads everything from there. One VICE session (CHAIN).
The expected values come from the same sources as the build (data/town_map*.txt, tools/build/villages.py)."""
import os
from c64test import test, check
from lib.c64 import Game, ROOT
from lib.play import new_game, find, fire_to
import gen_gfx as GG, gen_maps as GM, villages as V

CHAIN = True
SHOTS = os.path.join(ROOT, "out", "work", "villages")


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    os.makedirs(SHOTS, exist_ok=True)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def header(c):
    """(header bytes, solid list) of village c, as the build writes them"""
    v = V.VILLAGES[c]
    _, k = GM.build(c, v)
    return k[:GM.TK_LEN], list(k[GM.TK_LEN:])


def village(g, c):
    """travel to the village of chapter c as from the previous chapter (spawn mode 4: the entry)"""
    L = g.L
    g.poke(L["c_chap"], c); g.poke(L["c_unl"], c)
    g.call_keep(L["change_level"], regs="a=00,x=04", tmax=150)
    g.frames(3)


def check_village(g, c):
    L = g.L
    k, sol = header(c)
    px, py, sx, sy, nx, ny = k[:6]
    check(bytes(g.mem(L["town_k"], GM.TK_LEN)) == bytes(k), "town_k differs from the header of TWN%d" % c)
    check(g.mem(L["solidtab"], 48) == sol, "solidtab differs from the solid tiles of village %d" % c)
    check(g.ptile() == (nx, ny), "hero at %s, not at the entry %s" % (g.ptile(), (nx, ny)))
    bg, c1, c2, acc = V.VILLAGES[c]["pal"]
    got = [g.b(L["bg_cur"]), g.b(0xd022) & 15, g.b(0xd023) & 15, g.b(0xd800) & 15]
    check(got == [bg, c1, c2, 8 | acc], "colours %s, expected %s" % (got, [bg, c1, c2, 8 | acc]))
    m = GM.read_txt(os.path.join(ROOT, V.VILLAGES[c]["map"]))
    check(bytes(g.mem(L["MAP"], 48 * 48)) == bytes(m), "MAP differs from %s" % V.VILLAGES[c]["map"])
    return k


for _c in sorted(V.VILLAGES):
    def _mk(c):
        @test("VIL-TWN-%d" % (10 + c), "village %d (%s): header in town_k, solid tiles, colours, map, hero at the entry" % (c, V.VILLAGES[c]["name"]))
        def t(ctx):
            g = ctx["g"]
            if c > 1:
                village(g, c)
            check_village(g, c)
            g.frames(30)
            g.screenshot(os.path.join(SHOTS, "shot%d_entry.png" % c))
        return t
    _mk(_c)


@test("VIL-TWN-20", "village 3: the healing place heals and has its own name; portal arrival below the portal tile; the way down leads to level 11 and back onto it")
def places(ctx):
    g = ctx["g"]; L = g.L
    village(g, 3)
    k, _ = header(3)
    px, py, sx, sy = k[:4]
    name = bytes(g.mem(L["ls_fount"], GM.TK_NAME)).split(b"\0")[0]
    check(name == GM.text(V.VILLAGES[3]["heal"]), "name of the healing place: %r" % name)
    g.poke16(L["c_hp"], 1)
    g.teleport(*find(g, L["T_FOUNTAIN"])[0]); g.frames(6)
    check(g.w16(L["c_hp"]) == g.w16(L["hpmax"]), "the healing place did not heal: hp %d" % g.w16(L["c_hp"]))
    check((g.tile(sx, sy), find(g, L["T_TSTAIRS"])) == (L["T_TSTAIRS"], [(sx, sy)]), "the way down is not at (%d,%d)" % (sx, sy))
    fire_to(g, sx, sy); g.wait_main(); g.frames(2)
    check(g.b(L["cur_level"]) == 11, "way down -> level %d" % g.b(L["cur_level"]))
    fire_to(g, *find(g, L["T_STAIRSU"])[0]); g.wait_main(); g.frames(2)
    check(g.b(L["cur_level"]) == 0 and g.ptile() == (sx, sy), "back from level 11: level %d at %s" % (g.b(L["cur_level"]), g.ptile()))
    g.call_keep(L["change_level"], regs="a=00,x=02", tmax=150); g.frames(3)
    check(g.ptile() == (px, py + 1), "portal arrival at %s, expected %s" % (g.ptile(), (px, py + 1)))


@test("VIL-TWN-21", "village 5 (City of the Abyss, prototype): the Maw does not lead anywhere yet")
def maw(ctx):
    g = ctx["g"]; L = g.L
    village(g, 5)
    fire_to(g, *find(g, L["T_TSTAIRS"])[0]); g.frames(10)
    check(g.b(L["cur_level"]) == 0 and g.in_game(), "the Maw changed level: %d" % g.b(L["cur_level"]))


@test("VIL-BOSS-10", "boss levels of chapters 1-3: the boss is drawn with its own sprite colour (cb_col), in the slot of the final boss")
def cboss(ctx):
    g = ctx["g"]; L = g.L
    import monsters as MO
    for c in (1, 2, 3):
        g.poke(L["c_chap"], c)
        g.call_keep(L["change_level"], regs="a=%02x,x=00" % (5 * c), tmax=150); g.frames(3)
        sx, sy, bx, by = g.mem(L["bm_hdr"], 4)
        check(g.b(L["lv_cboss"]) == 1 and g.b(L["lb_boss"]) > 0, "level %d: no chapter boss" % (5 * c))
        g.poke(L["godmode"], 1)
        g.teleport(bx, by + 2); g.frames(4)
        cols = [g.b(0xd027 + i) & 15 for i in range(1, 8)]
        check(MO.CBOSS_COL[c - 1] in cols, "chapter %d: sprite colours %s, expected %d" % (c, cols, MO.CBOSS_COL[c - 1]))
        g.screenshot(os.path.join(SHOTS, "boss%d.png" % c))
    g.poke(L["godmode"], 0)


@test("VIL-TWN-22", "villages 2-5: fire one tile below the doors opens smith, alchemist and inn; RUN/STOP closes them")
def doors(ctx):
    g = ctx["g"]; L = g.L
    for c in (2, 3, 4, 5):
        village(g, c)
        for t in ("T_DSMITH", "T_DALCH", "T_DHOME"):
            x, y = find(g, L[t])[0]
            g.teleport(x, y + 1); g.frames(3)
            g.frames(1, fire=True); g.frames(8, tmax=60)
            check(not g.in_game(), "village %d: %s did not open" % (c, t))
            g.run_stop(); g.frames(3)
            check(g.in_game(), "village %d: RUN/STOP does not close %s" % (c, t))


@test("VIL-TWN-23", "village 4 with chapter 5 unlocked (final boss killed): the exit in the crater leads to the City of the Abyss, hero saved at its entry")
def to_abyss(ctx):
    g = ctx["g"]; L = g.L
    village(g, 4)
    g.poke(L["c_unl"], 5)
    k4, _ = header(4)
    g.teleport(k4[16], k4[18])                         # first exit tile (tx_exit_x, tx_exit_y)
    g.frames(3)
    check(g.call_keep(L["loc_id"])["a"] == 19, "no travel label on the exit of village 4")
    g.frames(1)
    g.press_fire(1); g.wait_main(tmax=120); g.frames(3)
    k5, _ = header(5)
    check(g.b(L["c_chap"]) == 5 and g.ptile() == (k5[4], k5[5]), "chapter %d at %s" % (g.b(L["c_chap"]), g.ptile()))
    check(bytes(g.mem(L["town_k"], GM.TK_LEN)) == bytes(k5), "town_k is not the header of TWN5")
    g.poke(L["c_chap"], 9)
    g.call_keep(L["load_char"], tmax=60)
    check(g.b(L["c_chap"]) == 5, "hero on the disk: c_chap %d" % g.b(L["c_chap"]))
