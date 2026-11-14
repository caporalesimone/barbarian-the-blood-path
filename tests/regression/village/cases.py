"""Village regression tests (11/11): the module MENU (inn and shops) loaded once and never again (from tools/ovl2_count.py,
removed: it measured, now it checks; until 11/11 the inn module OVL2 was overwritten by the theme prefetch), the
fountain. One VICE session, development disk."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, fire_to, find, INN_DOOR, SMITH_DOOR, go_level, go_village

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def visit(g, door):
    """enter a village screen (fire below the door), count the reads of the file MENU (ml_read), leave with RUN/STOP;
    returns the number of reads"""
    L = g.L
    g.teleport(*door); g.frames(3)
    g.watch(L["ml_read"])
    g.frames(1, fire=True); g.frames(8, tmax=60)
    n = g.hits[L["ml_read"]]
    opened = not g.in_game()
    g.unwatch()
    check(opened, "the screen did not open")
    g.run_stop(); g.frames(3)
    check(g.in_game(), "RUN/STOP does not close the screen")
    return n


@test("VIL-MENU-10", "inn and smith right after the start, again after walking around: no read of the file MENU inside the same village visit")
def menu_start(ctx):
    g = ctx["g"]
    n = [visit(g, INN_DOOR), visit(g, SMITH_DOOR)]
    x, y = INN_DOOR
    for dx in range(1, 12):                                    # (until 11/11 after 8 tiles the prefetch overwrote OVL2)
        g.teleport(x + dx, y); g.frames(2)
    n += [visit(g, INN_DOOR), visit(g, SMITH_DOOR)]
    check(n == [0, 0, 0, 0], "reads of the file MENU: %s (expected none)" % n)


@test("VIL-MENU-11", "after level 1 and back (the module MENU is read again at the village entry): inn and smith without further reads")
def menu_after_level(ctx):
    g = ctx["g"]
    go_level(g, 1); g.frames(20); go_village(g)
    n = [visit(g, INN_DOOR), visit(g, SMITH_DOOR)]
    check(n == [0, 0], "reads of the file MENU after level 1: %s (expected none)" % n)


@test("FOUNT-10", "fountain: walking on it heals to full hp")
def fountain(ctx):
    g, L = ctx["g"], ctx["g"].L
    f = find(g, L["T_FOUNTAIN"])
    check(f, "no fountain tile on the village map")
    hm = g.w16(L["hpmax"])
    g.teleport(f[0][0], f[0][1] + 3); g.frames(2)
    g.poke16(L["c_hp"], 1)
    g.teleport(*f[0]); g.frames(3)
    check(g.w16(L["c_hp"]) == hm, "hp %d after the fountain (max %d)" % (g.w16(L["c_hp"]), hm))


@test("INN-GOLD-11", "inn: Fire on the chest gold row does nothing (no withdrawal since 10/11), the screen stays open")
def inn_gold_row(ctx):
    g, L = ctx["g"], ctx["g"].L
    g.poke16(L["c_gold"], 1234); g.poke16(L["c_sgold"], 500)
    g.teleport(*INN_DOOR); g.frames(3); g.press_fire(); g.frames(5, tmax=60)
    check(not g.in_game(), "the inn did not open")
    g.poke(L["ui_cur"], 14); g.frames(1)                        # entry 14 = chest gold (src/menu/inn.asm)
    g.press_fire()
    check((g.w16(L["c_gold"]), g.w16(L["c_sgold"])) == (1234, 500), "gold %d chest %d (expected 1234, 500)" % (g.w16(L["c_gold"]), g.w16(L["c_sgold"])))
    check(not g.in_game(), "the inn closed")
    g.run_stop(); g.frames(3)
    check(g.in_game(), "RUN/STOP does not close the inn")
