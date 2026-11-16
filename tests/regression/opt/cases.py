"""The optimizations O1-O14 (11/11, docs/wiki/ottimizzazione.md): the shared routines called directly, at their
limits. Fast: one VICE session, the village. (Sanity of the optimization work, moved to regression on 11/11.)"""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def put_monster(g, i, dx, dy):
    L = g.L
    x, y = g.w16(L["px"]) + dx, g.w16(L["py"]) + dy
    g.poke(L["mxl"] + i, x & 255); g.poke(L["mxh"] + i, (x >> 8) & 255)
    g.poke(L["myl"] + i, y & 255); g.poke(L["myh"] + i, (y >> 8) & 255)


@test("OPT-11", "bar_far (sabs): monster off screen at |dx| >= 176 or |dy| >= 112, both signs")
def bar_far(ctx):
    g, L = ctx["g"], ctx["g"].L
    g.teleport(24, 24); g.frames(1)
    for dx, dy, far in ((175, 0, 0), (176, 0, 1), (-175, 0, 0), (-176, 0, 1), (0, 111, 0), (0, 112, 1),
                        (0, -111, 0), (0, -112, 1), (300, 0, 1), (-300, 0, 1)):
        put_monster(g, 0, dx, dy)
        r = g.call_keep(L["bar_far"], regs="x=00")
        check(r["c"] == far, "bar_far dx %d dy %d: C=%d (expected %d)" % (dx, dy, r["c"], far))


@test("OPT-12", "neg16 / sabs: -tmp0:1 and |tmp0:1| saturated at 255")
def neg_abs(ctx):
    g, L = ctx["g"], ctx["g"].L
    for v in (0, 1, 255, 256, 1000, -1, -255, -256, -1000):
        g.poke(L["tmp0"], v & 255, (v >> 8) & 255)
        g.call_keep(L["neg16"])
        got = g.b(L["tmp0"]) + 256 * g.b(L["tmp1"])
        check(got == (-v) & 0xffff, "neg16(%d) = %d" % (v, got))
        g.poke(L["tmp0"], v & 255, (v >> 8) & 255)
        a = g.call_keep(L["sabs"])["a"]
        check(a == min(abs(v), 255), "sabs(%d) = %d" % (v, a))


@test("OPT-02", "gold_total: c_gold + 10 x c_sgold (24 bit) at the limits")
def gold_total(ctx):
    g, L = ctx["g"], ctx["g"].L
    for gold, sg in ((0, 0), (9999, 0), (0, 65535), (10000, 65535), (123, 4567)):
        g.poke16(L["c_gold"], gold); g.poke16(L["c_sgold"], sg)
        g.call_keep(L["gold_total"])
        t = g.b(L["tmp0"]) + 256 * g.b(L["tmp1"]) + 65536 * g.b(L["tmp2"])
        check(t == gold + 10 * sg, "gold_total(%d, %d) = %d" % (gold, sg, t))
    g.poke16(L["c_gold"], 100); g.poke16(L["c_sgold"], 0)


@test("OPT-05", "pot_heal: itval + itdn x level for the three potions at levels 1 and 20, Abyss values (pab_*) at level 99")
def pot_heal(ctx):
    """(15/11, TODO J4) dungeon: red 20, yellow 50, violet 4L+40; Abyss (level > 20): 30, 75, 5L+28 (POT-10 reads items.tsv)"""
    g, L = ctx["g"], ctx["g"].L
    lv0 = g.b(L["c_lvl"])
    for pid, dun, aby in ((13, (20, 0), (30, 0)), (14, (50, 0), (75, 0)), (15, (40, 4), (28, 5))):
        for lv in (1, 20, 99):
            k, per = dun if lv <= 20 else aby
            g.poke(L["c_lvl"], lv)
            g.call_keep(L["pot_heal"], regs="y=%02x" % pid)
            got = g.b(L["mu0"]) + 256 * g.b(L["mu1"])
            check(got == k + per * lv, "pot_heal(%d) level %d = %d (expected %d)" % (pid, lv, got, k + per * lv))
    g.poke(L["c_lvl"], lv0)


@test("OPT-03", "set_name4 / set_name: every name of nm_tab in cmdbuf+3.., nlen = length, io_dir = 1, A = 1, X kept")
def set_name4(ctx):
    g, L = ctx["g"], ctx["g"].L
    names = {"nm_fmap": b"FMAP", "nm_lobby": b"LOBBY", "nm_menu": b"MENU", "nm_gfx": b"GFX0"}   # PETSCII
    for lab, want in names.items():
        off = L[lab] - L["nm_tab"]
        n = len(want)
        if n == 4:
            r = g.call_keep(L["set_name4"], regs="y=%02x" % off)
        else:
            r = g.call_keep(L["set_name"], regs="y=%02x, a=%02x" % (off, n))
        got = bytes(g.mem(L["cmdbuf"] + 3, n))
        check(got == want and g.b(L["nlen"]) == n and g.b(L["io_dir"]) == 1, "%s: %r nlen %d io_dir %d" % (lab, got, g.b(L["nlen"]), g.b(L["io_dir"])))
        check(r["a"] == 1, "%s: A = %d (expected 1)" % (lab, r["a"]))


@test("OPT-12B", "put_hero: the hero on tile (A, X) -> px/py = tile x 16 + 8 (centre)")
def put_hero(ctx):
    g, L = ctx["g"], ctx["g"].L
    for tx, ty in ((0, 0), (24, 24), (47, 47), (40, 43)):
        g.poke(0x0350, 0xa9, tx, 0xa2, ty, 0x4c, L["put_hero"] & 255, L["put_hero"] >> 8)   # lda #tx / ldx #ty / jmp
        g.call_keep(0x0350)
        want = (tx * 16 + 8, ty * 16 + 8)
        got = (g.w16(L["px"]), g.w16(L["py"]))
        check(got == want, "put_hero(%d, %d) -> %s" % (tx, ty, got))
    g.teleport(24, 24); g.frames(2)
