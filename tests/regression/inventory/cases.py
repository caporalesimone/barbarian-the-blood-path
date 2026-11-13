"""Inventory regression tests (11/11, from the code review): drop with DEL (y/n), two-handed weapon and shield, take off
an item, the weapon cannot be taken off, full pack. Inventory cursor (ui_cur): 0..7 pack, 8..11 weapon, armor, shield,
ring. One VICE session, the village."""
from lib.c64 import Game
from lib.runner import test, check
from lib.play import new_game, key, K_I, K_DEL, K_Y, K_N

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    L = g.L
    cat, fl = g.mem(L["itcat"], 64), g.mem(L["itfl"], 64)
    ctx["two"] = next(i for i in range(1, 64) if cat[i] == L["CAT_WEAPON"] and fl[i] & 1)
    ctx["one"] = next(i for i in range(1, 64) if cat[i] == L["CAT_WEAPON"] and not fl[i] & 1)
    ctx["shield"] = next(i for i in range(1, 64) if cat[i] == L["CAT_SHIELD"])
    ctx["armor"] = next(i for i in range(1, 64) if cat[i] == L["CAT_ARMOR"])


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def pack(g, *ids):
    L = g.L
    ids = list(ids) + [0] * (8 - len(ids))
    g.poke(L["c_pack"], *ids)
    g.poke(L["c_packd"], *[30 if i else 0 for i in ids]); g.poke(L["c_packm"], *[40 if i else 0 for i in ids])
    g.poke(L["c_packb"], *[0] * 8)


def equip(g, slot, item):
    L = g.L
    g.poke(L["c_eq"] + slot, item); g.poke(L["c_eqd"] + slot, 30 if item else 0); g.poke(L["c_eqm"] + slot, 40 if item else 0)
    g.poke(L["c_eqb"] + slot, 0)


def open_inv(g):
    key(g, K_I, 3)
    check(not g.in_game(), "the inventory does not open")


def at(g, cur):
    g.poke(g.L["ui_cur"], cur); g.frames(1)


def close(g):
    g.run_stop(); g.frames(2)
    check(g.in_game(), "the inventory does not close")


@test("INV-DROP-10", "DEL on a pack item: N keeps it, Y drops it; DEL on an empty slot asks nothing")
def inv_drop(ctx):
    g, L = ctx["g"], ctx["g"].L
    pack(g, ctx["armor"])
    open_inv(g); at(g, 0)
    key(g, K_DEL, 1); key(g, K_N, 1)
    check(g.b(L["c_pack"]) == ctx["armor"], "N: the item was dropped")
    key(g, K_DEL, 1); key(g, K_Y, 1)
    check(g.mem(L["c_pack"], 8) == [0] * 8, "Y: pack %s (expected empty)" % g.mem(L["c_pack"], 8))
    key(g, K_DEL, 2)                                            # empty slot: no question, the screen is the same
    check(not g.in_game(), "DEL on an empty slot closed the inventory")
    close(g)


@test("INV-2H-10", "two-handed weapon with a shield on: the shield goes back to the pack; full pack: refused")
def inv_two_hands(ctx):
    g, L = ctx["g"], ctx["g"].L
    w0 = g.b(L["c_eq"])
    equip(g, 2, ctx["shield"]); pack(g, ctx["two"])
    open_inv(g); at(g, 0); g.press_fire()
    check(g.b(L["c_eq"]) == ctx["two"] and g.b(L["c_eq"] + 2) == 0, "weapon %d shield %d" % (g.b(L["c_eq"]), g.b(L["c_eq"] + 2)))
    pk = g.mem(L["c_pack"], 8)
    check(ctx["shield"] in pk and w0 in pk, "pack %s (expected the shield and the old weapon)" % pk)
    close(g)
    equip(g, 0, ctx["one"]); equip(g, 2, ctx["shield"])
    pack(g, ctx["two"], *[ctx["armor"]] * 7)                     # full pack: no room for the shield
    open_inv(g); at(g, 0); g.press_fire()
    check(g.b(L["c_eq"]) == ctx["one"] and g.b(L["c_eq"] + 2) == ctx["shield"], "full pack: the two-handed weapon was equipped")
    close(g)


@test("INV-2H-11", "shield with a two-handed weapon on: refused")
def inv_shield(ctx):
    g, L = ctx["g"], ctx["g"].L
    equip(g, 0, ctx["two"]); equip(g, 2, 0); pack(g, ctx["shield"])
    open_inv(g); at(g, 0); g.press_fire()
    check(g.b(L["c_eq"] + 2) == 0 and g.b(L["c_pack"]) == ctx["shield"], "the shield was equipped with a two-handed weapon")
    close(g)


@test("INV-UNEQ-10", "take off the armor (to the pack); full pack: refused; the weapon cannot be taken off")
def inv_unequip(ctx):
    g, L = ctx["g"], ctx["g"].L
    equip(g, 0, ctx["one"]); equip(g, 1, ctx["armor"]); pack(g)
    open_inv(g); at(g, 9); g.press_fire()
    check(g.b(L["c_eq"] + 1) == 0 and ctx["armor"] in g.mem(L["c_pack"], 8), "armor not taken off")
    at(g, 8); g.press_fire()
    check(g.b(L["c_eq"]) == ctx["one"], "the weapon was taken off")
    close(g)
    equip(g, 1, ctx["armor"]); pack(g, *[ctx["shield"]] * 8)
    open_inv(g); at(g, 9); g.press_fire()
    check(g.b(L["c_eq"] + 1) == ctx["armor"], "full pack: the armor was taken off")
    close(g)
    pack(g)
