"""Order of the lists (24/11, owner's request): equipment, pack, belt in the inventory and in the alchemist's list "yours"
(src/game/inv.asm iv_sg, src/menu/shop.asm sh_segs). Every entry of the list is resolved with sl_get (slot code sl_sl:
pack 0..7, equipment PACK_N.., belt $20+n, separator $ff): the kinds must come in that order. One VICE session, the village."""
from c64test import test, check
from lib.c64 import Game
from lib.play import new_game, key, K_I, fire_to, find

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    L = g.L
    g.poke(L["c_beltt"], L["I_POTR"], L["I_POTY"], 0, 0)
    g.poke(L["c_pack"], L["I_SCROLL"]); g.poke(L["c_packb"], 2)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def kinds(g, lst, pack_n):
    """kinds of the entries of list lst in order: 'e' equipment, 'p' pack, 'b' belt (separators skipped)"""
    L = g.L
    out = []
    for i in range(g.b(L["sl_n"] + lst)):
        r = g.call_keep(L["sl_get"], regs="a=%02x,x=%02x" % (i, lst))
        s = g.b(L["sl_sl"])
        if r["c"] or s == 0xff:
            continue
        out.append("b" if 0x20 <= s < 0x40 else "e" if s >= pack_n else "p")
    return "".join(out)


def ordered(k):
    return k == "".join(sorted(k, key="epb".index))


@test("ORDER-10", "inventory: equipment, then pack, then belt (the belt potions are the last entries)")
def inv(ctx):
    g = ctx["g"]; L = g.L
    key(g, K_I, 3)
    k = kinds(g, 0, L["PACK_N"])
    check("e" in k and "p" in k and k.endswith("bb") and ordered(k), "inventory order %r" % k)
    g.run_stop(); g.frames(3)
    check(g.in_game(), "RUN/STOP does not close the inventory")


@test("ORDER-11", "alchemist, list 'yours': rings worn, pack, belt (4 slots, last; the '>' on a belt slot when buying a potion: SHOP-BELT-10)")
def alch(ctx):
    g = ctx["g"]; L = g.L
    door = find(g, L["T_DALCH"])
    check(door, "no alchemist door on the map")
    fire_to(g, door[0][0], door[0][1] + 1)
    check(g.b(L["sh_mask"]) != 0, "the alchemist does not open")
    k = kinds(g, 1, L["PACK_N"])
    check(k.endswith("bbbb") and "p" in k and ordered(k), "alchemist order %r" % k)
    g.run_stop(); g.frames(2)
    check(g.in_game(), "RUN/STOP does not close the shop")
