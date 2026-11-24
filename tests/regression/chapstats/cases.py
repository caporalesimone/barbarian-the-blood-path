"""Monster stats of the chapters (24/11, TODO M9, docs/wiki/bestiario.md): the bestiary formulas (data/monsters/bestiary.tsv,
tools/build/mon_stats.py) become per type A and B coefficients (value = A + ((B x P + 8) >> 4)); a chapter with own_stats
(data/chapters.yaml, today chapter 2) has its own rows as types 1..8. The theme file carries the block at its end, gfx_install
copies it to mt_ch, floor_types computes the values. Expected values from the same functions as the build.
One VICE session (CHAIN)."""
from c64test import test, check
from lib.c64 import Game
from lib.play import new_game, alive
import mon_stats as MS

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    g.poke(g.L["godmode"], 1)
    ctx["R"], ctx["B"] = MS.load()


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def enter(g, c, lvl):
    L = g.L
    g.poke(L["c_chap"], c); g.poke(L["c_unl"], c)
    g.call_keep(L["change_level"], regs="a=%02x,x=00" % lvl, tmax=150); g.frames(3)
    check(g.b(L["cur_level"]) == lvl, "level %d, expected %d" % (g.b(L["cur_level"]), lvl))


def block_is(ctx, c, src):
    g = ctx["g"]; L = g.L
    exp = MS.block(ctx["R"], ctx["B"], src)
    got = bytes(g.mem(L["mt_ch"], len(exp)))
    for k, f in enumerate(MS.CH_FIELDS):
        check(got[10 * k:10 * k + 10] == exp[10 * k:10 * k + 10], "chapter %d: %s %s, expected %s (chapter %d)" % (
            c, f, list(got[10 * k:10 * k + 10]), list(exp[10 * k:10 * k + 10]), src))


@test("CHST-10", "chapter 2 level 7: mt_ch = the stats of chapter 2 (mon_stats.py), different from chapter 1; "
      "the level has its monsters")
def ch2(ctx):
    g = ctx["g"]; L = g.L
    check(MS.block(ctx["R"], ctx["B"], 2) != MS.block(ctx["R"], ctx["B"], 1), "chapter 2 has the stats of chapter 1")
    enter(g, 2, 7)
    block_is(ctx, 2, 2)
    check(alive(g), "no monster on level 7")


@test("CHST-11", "back to chapter 1 (level 2): mt_ch = chapter 1; chapter 3 (no own_stats): chapter 1 too; chapter 2 boss level (10): chapter 2")
def back(ctx):
    g = ctx["g"]
    enter(g, 1, 2)
    block_is(ctx, 1, 1)
    enter(g, 3, 12)
    block_is(ctx, 3, 1)
    enter(g, 2, 10)
    block_is(ctx, 2, 2)


def ft_is(ctx, c, lvl):
    """(24/11) floor_types del C64 = mon_stats.values (formule del bestiario) per i tipi 1..9 al piano lvl"""
    g = ctx["g"]; L = g.L
    R, B = ctx["R"], ctx["B"]
    rows = MS.type_rows(c if c in MS.own_chapters() else 1)
    nf = R["dungeon"]["floors"]
    rd = lambda name: g.mem(L[name], 10)
    hl, hh, ac, att, dk, sv, xl, xh = (rd(n) for n in ("ft_hpl", "ft_hph", "ft_ac", "ft_att", "ft_dk", "ft_sv", "ft_xpl", "ft_xph"))
    for x, r in enumerate(rows, 1):
        v = MS.values(MS.coef(r, nf, B.get("monster_speed_percent", 100)), lvl, nf)
        got = dict(hp=hl[x] + 256 * hh[x], ac=ac[x], att=att[x], dk=dk[x], sv=sv[x], xp=xl[x] + 256 * xh[x])
        exp = {k: v[k] for k in got}
        check(got == exp, "chapter %d level %d type %d %s: C64 %s, formulas %s" % (c, lvl, x, r["id"], got, exp))


@test("CHST-12", "floor_types (C64) = the bestiary formulas (mon_stats.values) for types 1..9 on levels 1, 4, 7, 9, 12, 17")
def formulas(ctx):
    g = ctx["g"]
    for c, lvl in ((1, 1), (1, 4), (2, 7), (2, 9), (3, 12), (4, 17)):
        enter(g, c, lvl)
        ft_is(ctx, c, lvl)


@test("CHST-13", "base_n (which base types spawn, from mt_fmin of the theme file): chapter 1 levels 1-5, chapter 2 levels 6-10 "
      "(Will-o'-Wisp from level 6), chapter 3 levels 11-15 (types of chapter 1)")
def base_types(ctx):
    g = ctx["g"]; L = g.L
    for c, lvl in ((1, 2), (2, 7), (3, 12)):
        enter(g, c, lvl)
        rows = MS.type_rows(c if c in MS.own_chapters() else 1)[:4]
        for f in range(5 * c - 4, 5 * c + 1):
            exp = max(1, max([i + 1 for i, r in enumerate(rows) if r["floor"] <= f], default=1))
            r = g.call_keep(L["base_n"], regs="a=%02x" % f)
            check(r["a"] == exp, "chapter %d level %d: base_n %d, expected %d" % (c, f, r["a"], exp))
