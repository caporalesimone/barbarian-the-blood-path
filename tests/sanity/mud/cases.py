"""Mud of the Drowned (24/11, AI of chapter 2, src/game/ovl_decor.asm DK_CHAP 2): with a Drowned (type 1) alive and awake within
DW_R pixels on both axes the hero moves at half speed (ovp_slow, update_player: still one frame in two). Only on the generated
levels of chapter 2 (code in the tail of GFX3). One VICE session, level 7 of chapter 2, god mode."""
from c64test import test, check
from lib.c64 import Game, labels
from lib.play import new_game, alive, mpos, floor_next, FLOOR_D, RT

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    L = g.L
    g.poke(L["godmode"], 1)
    g.poke(L["c_chap"], 2); g.poke(L["c_unl"], 2)
    g.call_keep(L["change_level"], regs="a=07,x=00", tmax=150); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def run_right(g, n=24):
    """px gained holding right for n frames"""
    L = g.L
    x0 = g.w16(L["px"])
    for _ in range(n):
        g.frames(1, joy=RT)
    return g.w16(L["px"]) - x0


def lane(g, mx, my):
    """a tile next to (mx, my) with 3 floor tiles to its right"""
    for dx, dy in ((-1, 0), (0, 1), (0, -1), (-2, 0)):
        x, y = mx + dx, my + dy
        if all(g.tile(x + k, y) in FLOOR_D for k in range(0, 4)):
            return x, y
    return None


@test("MUD-10", "chapter 2: a Drowned awake next to the hero -> ovp_slow, the hero covers about half the distance; the Drowned "
      "dead (or asleep) -> normal speed")
def mud(ctx):
    g = ctx["g"]; L = g.L
    ms = [i for i in alive(g) if i + 1 != g.b(L["lb_boss"])]
    check(ms, "no monster on level 7")
    i = ms[0]
    for j in ms[1:]:                                       # one Drowned only, still (stunned), the others away
        g.poke(L["malive"] + j, 0)
    g.poke(L["mtype"] + i, 1); g.poke(L["mwake"] + i, 1)
    mx, my = mpos(g, i)
    p = lane(g, mx, my)
    check(p is not None, "no free lane next to the monster at %s" % ((mx, my),))
    g.teleport(*p); g.frames(2)
    g.poke(L["mstun"] + i, 200)
    g.frames(5)
    check(g.b(L["ovp_slow"]) != 0, "ovp_slow 0 next to an awake Drowned")
    slow = run_right(g, 12)
    g.poke(L["malive"] + i, 0)
    g.teleport(*p); g.frames(5)
    check(g.b(L["ovp_slow"]) == 0, "ovp_slow %d with the Drowned dead" % g.b(L["ovp_slow"]))
    fast = run_right(g, 12)
    check(fast > 0 and slow * 10 <= fast * 7, "distance with mud %d, without %d (expected about half)" % (slow, fast))
