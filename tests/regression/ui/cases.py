"""UI (sanity of 10/11 and 11/11, moved to regression on 11/11): the key or the Fire that closes a screen must not act in
the game too. Closing the inventory or the minimap with RUN/STOP must not open the game menu (found by smoke EQUIP-01);
"resume" / "save game" of the game menu in front of a door must not open the shop or the inn (found by BELT-13: ui_exit
clears joynew/keynew). Real game from the development disk, keys written at the exit of read_input."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, fire_to, key, SMITH_DOOR, INN_DOOR, K_RUNSTOP, D, U, RT, LF


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(2)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def open_close(g, row, mask):
    g.frames(1, keys={row: mask}); g.frames(3)
    opened = not g.in_game()
    g.run_stop(); g.frames(3)
    return opened, g.in_game()


@test("UI-INV-10", "inventory: RUN/STOP closes it and returns to the game (no game menu)")
def inv(ctx):
    opened, back = open_close(ctx["g"], 4, 0x02)          # I
    check(opened, "the inventory does not open")
    check(back, "not back in the game after RUN/STOP (game menu open?)")


@test("UI-MAP-10", "minimap: RUN/STOP closes it and returns to the game (no game menu)")
def minimap(ctx):
    opened, back = open_close(ctx["g"], 4, 0x10)          # M
    check(opened, "the minimap does not open")
    check(back, "not back in the game after RUN/STOP (game menu open?)")


def menu_pick(g, n):
    """game menu (RUN/STOP), n times down, Fire: 0 resume, 1 save game"""
    key(g, K_RUNSTOP, 2)
    for _ in range(n): g.frames(1, joy=D); g.frames(1)
    g.watch(g.MN["enter_shop"])
    g.press_fire(settle=3)
    for _ in range(10):
        if g.in_game(): break
        g.frames(5, tmax=60)
    n_shop = g.hits[g.MN["enter_shop"]]
    g.unwatch()
    return n_shop


@test("UI-SHOP-10", "shop closed with RUN/STOP: back in the game, no game menu")
def shop_close(ctx):
    g = ctx["g"]
    fire_to(g, *SMITH_DOOR)
    check(g.b(g.L["sh_mask"]) != 0, "the smith does not open")
    g.run_stop(); g.frames(2)
    check(g.in_game(), "not back in the game after RUN/STOP")


@test("UI-MENU-10", "game menu 'resume' with Fire in front of a shop door: the shop does not open")
def menu_resume(ctx):
    g = ctx["g"]
    n = menu_pick(g, 0)
    check(n == 0 and g.in_game(), "the shop opened after 'resume' (%d times)" % n)


@test("UI-MENU-11", "game menu 'save game' with Fire in front of the inn: the inn does not open")
def menu_save(ctx):
    g = ctx["g"]
    g.teleport(*INN_DOOR); g.frames(3)
    g.watch(g.L["ovl_town"])
    key(g, K_RUNSTOP, 2); g.frames(1, joy=D); g.frames(1); g.press_fire(settle=3)
    for _ in range(10):
        if g.in_game(): break
        g.frames(5, tmax=60)
    n = g.hits[g.L["ovl_town"]]
    g.unwatch()
    check(n == 0 and g.in_game(), "the inn opened after 'save game' (%d times)" % n)


@test("UI-LIST-10", "(22/11, owner) two lists as one (smith): down past the last ware -> first entry of 'gear', up from the first ware -> last of 'gear', down past the last of 'gear' -> first ware; D/A -> first entry of the other list")
def list_cont(ctx):
    g = ctx["g"]; L = g.L
    fire_to(g, *SMITH_DOOR)
    check(g.b(L["sh_mask"]) != 0, "the smith does not open")
    st = lambda: (g.b(L["sl_l"]), g.b(L["sl_cur"] + g.b(L["sl_l"])))
    mv = lambda j: (g.frames(1, joy=j), g.frames(1), st())[2]
    n0, n1 = g.mem(L["sl_n"], 2)
    why = []
    s = st()
    for _ in range(n0 - 1): s = mv(D)
    if s != (0, n0 - 1): why.append("not on the last ware: %s" % (s,))
    s = mv(D)
    if s != (1, 0): why.append("down from the last ware: %s (expected list 1, entry 0)" % (s,))
    s = mv(U)
    if s != (0, n0 - 1): why.append("up from the first of gear: %s (expected the last ware %d)" % (s, n0 - 1))
    for _ in range(n0 - 1): s = mv(U)
    s = mv(U)
    if s[0] != 1 or s[1] < n1 - 2: why.append("up from the first ware: %s (expected the last of gear, %d entries)" % (s, n1))
    s = mv(D)
    if s != (0, 0): why.append("down from the last of gear: %s (expected the first ware)" % (s,))
    mv(D); mv(D)
    s = mv(RT)
    if s != (1, 0): why.append("D: %s (expected list 1, entry 0)" % (s,))
    mv(D)
    s = mv(LF)
    if s != (0, 0): why.append("A: %s (expected list 0, entry 0)" % (s,))
    g.run_stop(); g.frames(2)
    check(not why, "; ".join(why))
