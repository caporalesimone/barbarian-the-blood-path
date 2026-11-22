"""(22/11, owner's request) The named boss of a level ALWAYS leaves its chest: also when the hero is 4 or more levels above
it (no loot for weaker monsters, km_nl) and when it dies on a tile that is not floor (stairs, door, furniture: the chest goes
on a floor tile next to it, adj_floor). Level 2 of chapter 1, kill_monster called on the boss. One VICE session (CHAIN)."""
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


def boss_chests(g):
    L = g.L
    t = g.mem(L["ch_t"], L["CH_MAX"])
    return [(g.b(L["cx_x"] + i), g.b(L["cx_y"] + i)) for i in range(L["CH_MAX"]) if t[i] & 8]


def kill_boss(g, tile=None):
    """the boss of the level dies (at tile, if given); returns its index and the chests left by monsters after it"""
    L = g.L
    b = g.b(L["lb_boss"]) - 1
    check(b >= 0, "no boss on the level")
    if tile:
        x, y = tile
        g.poke(L["mxl"] + b, (x * 16) & 255); g.poke(L["mxh"] + b, (x * 16) >> 8)
        g.poke(L["myl"] + b, (y * 16) & 255); g.poke(L["myh"] + b, (y * 16) >> 8)
    n0 = len(boss_chests(g))
    g.call_keep(L["kill_monster"], regs="x=%02x" % b)
    for _ in range(20):
        g.frames(2)
        if len(boss_chests(g)) > n0: break
    return b, boss_chests(g)[n0:]


@test("LOOT-BOSS-10", "the hero 6 levels above the boss of level 2 (no loot for weaker monsters): the boss still leaves its chest")
def over(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_chap"], 1)
    g.call_keep(L["change_level"], regs="a=02,x=00", tmax=150); g.frames(3)
    g.poke(L["c_lvl"], 9)
    _, new = kill_boss(g)
    check(len(new) == 1, "chests left: %s" % new)
    g.poke(L["c_lvl"], 1)


@test("LOOT-BOSS-11", "the boss of level 3 dies on the stairs down (column >= 16: the high byte of its x is not 0): its chest is on a floor tile next to them (22/11: kill_monster took the row of the loot from the wrong monster)")
def stairs(ctx):
    g = ctx["g"]; L = g.L
    g.call_keep(L["change_level"], regs="a=03,x=00", tmax=150); g.frames(3)
    m = g.mem(L["MAP"], 48 * 48)
    sd = next((i % 48, i // 48) for i, v in enumerate(m) if v == L["T_STAIRSD"])
    _, new = kill_boss(g, sd)
    check((g.b(L["loot_x"]), g.b(L["loot_y"])) == sd or new, "loot position %s (expected the stairs %s)" % ((g.b(L["loot_x"]), g.b(L["loot_y"])), sd))
    check(len(new) == 1 and max(abs(new[0][0] - sd[0]), abs(new[0][1] - sd[1])) == 1 and new[0] != sd,
          "stairs at %s, chests left %s" % (sd, new))
