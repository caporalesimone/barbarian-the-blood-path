"""Belt of 8 (24/11, TODO F1, docs/wiki/quests.md: reward of chain step 6, QB_BELT): 4 slots in front (keys 1-4), 4 behind
(slot j+4 behind slot j). Before step 6 is handed in only the front row exists (belt_cap 4); after it the potions fill the
front row and then the back row; a potion drunk from the front lets the one behind move up (belt_up, also when the HUD is
drawn after a menu). HUD row 23: the back row (dark grey dashes while it does not exist). One VICE session, the village."""
from c64test import test, check
from lib.c64 import Game
from lib.play import new_game, key, BELT_KEYS, fire_to, find

CHAIN = True
ROW23 = 0xd800 + 23 * 40 + 23                                # colour of back slot j: ROW23 + 2 j (hud_p3, row 23 from column 23)


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    L = g.L
    g.poke16(L["hpmax"], 100); g.poke16(L["c_hp"], 50)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def give(g, item):
    """give_item of a potion: True if taken"""
    r = g.call_keep(g.L["give_item"], regs="a=%02x" % item)
    return not r["c"]


def hud(g):
    """the whole HUD drawn again (hud_dirty: one panel per frame, hud_step)"""
    g.poke(g.L["hud_dirty"], 1); g.frames(8)


@test("BELT-20", "before step 6 (q_step 5): 4 slots, a fifth potion is refused and row 23 has dark grey dashes; step 6 handed in "
      "(q_step 6): the fifth potion goes to slot 5 (behind slot 1), its colour in row 23")
def cap(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["q_step"], L["QB_BELT"] - 1)
    g.poke(L["c_beltt"], *([L["I_POTR"]] * 4 + [0] * 4))
    check(not give(g, L["I_POTY"]), "fifth potion taken with the belt of 4")
    hud(g)
    check([g.b(ROW23 + 2 * j) & 15 for j in range(4)] == [11] * 4, "row 23 colours %s, expected dark grey" % [g.b(ROW23 + 2 * j) & 15 for j in range(4)])
    g.poke(L["q_step"], L["QB_BELT"])
    check(give(g, L["I_POTY"]), "fifth potion refused with the belt of 8")
    check(g.mem(L["c_beltt"], 8) == [L["I_POTR"]] * 4 + [L["I_POTY"], 0, 0, 0], "belt %s" % g.mem(L["c_beltt"], 8))
    hud(g)
    yel = g.b(L["itfl"] + L["I_POTY"])
    cols = [g.b(ROW23 + 2 * j) & 15 for j in range(4)]
    check(cols == [yel & 15, 6, 6, 6], "row 23 colours %s, expected %d then blue" % (cols, yel & 15))


@test("BELT-21", "key 1 with slot 1 and slot 5 full: the potion of slot 1 is drunk, the one of slot 5 moves up to slot 1")
def up(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["tmr"] + L["T_POT"], 0, 0)
    g.poke16(L["c_hp"], 20)
    key(g, BELT_KEYS[0], 3)
    b = g.mem(L["c_beltt"], 8)
    check(b[0] == L["I_POTY"] and b[4] == 0, "belt %s after key 1 (expected the yellow one in slot 1)" % b)
    check(g.w16(L["c_hp"]) > 20, "nothing drunk (hp %d)" % g.w16(L["c_hp"]))


@test("BELT-22", "a front slot emptied elsewhere (shop, inventory): the next HUD drawing moves the potion behind it up")
def align(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_beltt"], 0, L["I_POTR"], 0, L["I_POTR"], 0, 0, L["I_POTV"], 0)
    hud(g)
    b = g.mem(L["c_beltt"], 8)
    check(b == [0, L["I_POTR"], L["I_POTV"], L["I_POTR"], 0, 0, 0, 0], "belt %s after the HUD" % b)
