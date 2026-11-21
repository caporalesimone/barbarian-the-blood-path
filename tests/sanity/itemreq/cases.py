"""STR requirements of the items (21/11, owner's decision O6; data/items/items.tsv column min_str -> itreq): with less STR
(s_str, ring included) an item is not equipped (inventory and inn) and its box shows "str N". One VICE session, the village."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, K_I

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


@test("REQ-10", "inventory: a weapon whose STR requirement is above s_str stays in the pack ('str N' in its box); with enough STR it is equipped")
def req_inv(ctx):
    g = ctx["g"]; L = g.L
    req, cat = g.mem(L["itreq"], L["N_ITEMS"]), g.mem(L["itcat"], L["N_ITEMS"])
    heavy = max((i for i in range(1, L["N_ITEMS"]) if cat[i] == L["CAT_WEAPON"]), key=lambda i: req[i])
    check(req[heavy] >= 17, "no weapon with a STR requirement >= 17 (itreq %s)" % req)
    w0 = g.b(L["c_eq"])
    g.poke(L["c_pack"], heavy, 0, 0, 0, 0, 0, 0, 0); g.poke(L["c_packd"], 30); g.poke(L["c_packm"], 40); g.poke(L["c_packb"], 0)
    key(g, K_I, 3)
    check(not g.in_game(), "the inventory does not open")
    g.poke(L["s_str"], req[heavy] - 1)
    g.poke(L["ui_cur"], 1); g.frames(2); g.poke(L["ui_cur"], 0); g.frames(3)     # redraw the box of the entry
    scr = "".join(chr(b + 96) if 1 <= b <= 26 else chr(b) if 32 <= b < 64 else " " for b in g.mem(0xB400, 1000))
    check("str %d" % req[heavy] in scr, "no 'str %d' on the screen" % req[heavy])
    g.press_fire(); g.frames(2)
    check(g.b(L["c_eq"]) == w0 and g.b(L["c_pack"]) == heavy, "equipped with STR %d < %d" % (req[heavy] - 1, req[heavy]))
    g.poke(L["s_str"], req[heavy])
    g.press_fire(); g.frames(2)
    check(g.b(L["c_eq"]) == heavy, "not equipped with STR = requirement (weapon %d)" % g.b(L["c_eq"]))
    g.run_stop(); g.frames(2)
