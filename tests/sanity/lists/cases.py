"""(23/11, owner's request, prototype on the branch liste-compatte) Scrolling lists without the empty slots of the pack and of
the inn chest (sl_vis / sl_map, src/game/ui.asm): the entries of those segments are only the occupied slots, in order;
equipment (5 fixed slots), belt (slots 1-4) and wares keep every slot. One VICE session, a new barbarian in the village."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, K_I, K_RUNSTOP, INN_DOOR

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def entries(g):
    """every entry of every list of the screen: (list, entry, sl_sl), separators left out"""
    L = g.L
    out = []
    for l in range(g.b(L["sl_nl"])):
        for c in range(g.b(L["sl_n"] + l)):
            r = g.call_keep(L["sl_get"], regs="a=%02x,x=%02x" % (c, l))
            if not r["c"]:
                out.append((l, c, g.b(L["sl_sl"])))
    return out


def check_lists(g, what):
    L = g.L
    pack, chest = g.mem(L["c_pack"], 8), g.mem(L["st_id"], 24)
    e = entries(g)
    ps = [s for _, _, s in e if s < 8]
    cs = [s - 0x40 for _, _, s in e if 0x40 <= s < 0x40 + 24]
    want_p = [i for i in range(8) if pack[i]]
    check(ps == want_p, "%s: pack entries %s, occupied slots %s" % (what, ps, want_p))
    return cs, [i for i in range(24) if chest[i]]


@test("LIST-C-10", "inventory, pack with 3 items of 8: the pack entries are the 3 occupied slots (no '-' rows); equipment and belt keep every slot")
def inv_compact(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_pack"], 2, 3, 4, 0, 0, 0, 0, 0)            # 3 items in the first slots (the new barbarian has none)
    g.poke(L["c_packd"], 50, 50, 50); g.poke(L["c_packm"], 50, 50, 50)
    key(g, K_I, 3)
    check(not g.in_game(), "the inventory does not open")
    check_lists(g, "inventory")
    e = entries(g)
    check(sum(1 for _, _, s in e if 8 <= s < 13) == 5 and sum(1 for _, _, s in e if 0x20 <= s < 0x24) == 4,
          "equipment or belt not whole: %s" % [s for _, _, s in e])
    key(g, K_RUNSTOP, 3)


@test("LIST-C-11", "inn: the chest with 2 items of 24 shows 2 entries, the pack only its items")
def inn_compact(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["st_id"], *([0] * 24)); g.poke(L["st_id"], 3, 5)
    g.teleport(*INN_DOOR); g.frames(3)
    g.press_fire(settle=3)
    for _ in range(20):
        if g.b(L["sl_nl"]) == 2 and not g.in_game(): break
        g.frames(5, tmax=60)
    cs, want = check_lists(g, "inn")
    check(cs == want == [0, 1], "chest entries %s, occupied %s" % (cs, want))


@test("LIST-C-12", "inn: a pack item to the empty chest (1 entry), back to the pack (chest empty again): the cursor goes back to the pack list; D on the empty chest list does nothing")
def inn_empty(ctx):
    from lib.play import RT
    g = ctx["g"]; L = g.L
    key(g, K_RUNSTOP, 3)
    for _ in range(20):
        if g.in_game(): break
        g.frames(5)
    g.poke(L["st_id"], *([0] * 24))
    g.poke(L["c_pack"], 2, 0, 0, 0, 0, 0, 0, 0); g.poke(L["c_packd"], 50); g.poke(L["c_packm"], 50)
    g.press_fire(settle=3)
    for _ in range(20):
        if not g.in_game(): break
        g.frames(5, tmax=60)
    check(not g.in_game() and g.b(L["sl_l"]) == 0, "the inn does not open on the pack list")
    g.frames(1, joy=RT); g.frames(2)
    check(g.b(L["sl_l"]) == 0, "D moved the cursor to the empty chest list")
    g.press_fire(settle=5)                               # the pack item (cursor on it) to the chest
    cs, want = check_lists(g, "after pack -> chest")
    check(cs == want == [0] and g.b(L["sl_l"]) == 0, "chest entries %s (occupied %s), cursor list %d" % (cs, want, g.b(L["sl_l"])))
    g.frames(1, joy=RT); g.frames(2)
    check(g.b(L["sl_l"]) == 1, "D does not reach the chest list with 1 entry")
    g.press_fire(settle=5)                               # back to the pack: the chest list is empty
    cs, want = check_lists(g, "after chest -> pack")
    check(cs == want == [] and g.b(L["sl_l"]) == 0 and not g.in_game(),
          "chest %s, cursor list %d (expected the pack list 0)" % (cs, g.b(L["sl_l"])))
