"""Monster stats of the chapters (24/11, TODO M9, docs/wiki/bestiario.md): a chapter with own_stats (data/chapters.yaml,
today chapter 2) gives its monster types 1..8 their own life, AC, attack, damage bonus, save, speed, xp and loot level bonus
(tools/build/mon_stats.py: the bestiary of the chapter around the mean of chapter 1, same mean difficulty). The theme file
carries the block at its end, gfx_install copies it to mt_ch. Expected values from the same function as the build.
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
