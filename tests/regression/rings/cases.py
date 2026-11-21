"""Two ring slots (21/11, TODO #391: equipment of 5 slots, c_eq[EQ_RING], c_eq[EQ_RING+1]) and the ring bought from the
alchemist with its stat (before: bonus 0, no effect). One VICE session, the village; the inventory and the shop are the
real screens (scrolling lists), keys written at the exit of read_input."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, K_I, list_to, fire_to, find

CHAIN = True
R1 = 3                                          # EQ_RING: first ring slot (c_eq + 3), the second is c_eq + 4


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def sx(g, item, stat):
    """(21/11 evening, affixes) the suffix of a ring of that metal and stat (1 STR, 2 DEX, 3 CON): ring_sx"""
    L = g.L
    return L["RSX_%d%d" % (stat, g.b(L["itval"] + item))] if item and stat else 0


def ring(g, slot, item, stat):
    g.poke(g.L["c_eq"] + slot, item); g.poke(g.L["c_eqb"] + slot, 0); g.poke(g.L["c_eqs"] + slot, sx(g, item, stat))


def wear_from_pack(g, item, stat):
    """the ring in pack slot 0, inventory, fire on it, close"""
    L = g.L
    g.fill(L["c_pack"], L["c_pack"] + 7, 0); g.poke(L["c_pack"], item); g.poke(L["c_packb"], 0); g.poke(L["c_packs"], sx(g, item, stat))
    key(g, K_I, 3)
    check(not g.in_game(), "the inventory does not open")
    check(list_to(g, 0, "ui_cur", 0), "cursor not on pack slot 0 (ui_cur %d)" % g.b(L["ui_cur"]))
    g.press_fire(); g.frames(2)
    scr = "".join(chr(b + 96) if 1 <= b <= 26 else chr(b) if 32 <= b < 64 else " " for b in g.mem(0xB400 + 23 * 40, 40))
    g.run_stop(); g.frames(2)
    return scr


@test("RING-10", "inventory: with one ring on, a second ring goes to the free ring slot; both rings add their stat (recalc_stats)")
def ring_second(ctx):
    g = ctx["g"]; L = g.L
    ring(g, R1, L["I_SILVER"], 1); ring(g, R1 + 1, 0, 0)
    s0 = g.b(L["s_dex"])
    wear_from_pack(g, L["I_COPPER"], 2)
    eq = g.mem(L["c_eq"] + R1, 2)
    check(eq == [L["I_SILVER"], L["I_COPPER"]], "ring slots %s (expected silver, copper)" % eq)
    check(g.b(L["c_pack"]) == 0, "the copper ring is still in the pack")
    check(g.b(L["s_dex"]) == s0 + 2 * g.b(L["itval"] + L["I_COPPER"]), "DEX %d (before %d): the second ring does not count" % (g.b(L["s_dex"]), s0))


@test("RING-11", "inventory: with both rings on, a new ring replaces the one of lower value (it goes to the pack, message 'replaced')")
def ring_replace(ctx):
    g = ctx["g"]; L = g.L
    ring(g, R1, L["I_SILVER"], 1); ring(g, R1 + 1, L["I_COPPER"], 2)
    scr = wear_from_pack(g, L["I_GOLD"], 3)
    eq = g.mem(L["c_eq"] + R1, 2)
    low = R1 + 1 if g.b(L["itval"] + L["I_COPPER"]) <= g.b(L["itval"] + L["I_SILVER"]) else R1
    want = [L["I_SILVER"], L["I_GOLD"]] if low == R1 + 1 else [L["I_GOLD"], L["I_COPPER"]]
    check(eq == want, "ring slots %s (expected %s)" % (eq, want))
    gone = L["I_COPPER"] if low == R1 + 1 else L["I_SILVER"]
    check(gone in g.mem(L["c_pack"], 8), "the replaced ring is not in the pack %s" % g.mem(L["c_pack"], 8))
    check("replaced" in scr, "no 'replaced' message (row 23: %r)" % scr.strip())


@test("RING-12", "alchemist: a ring among the wares has affixes (af_gen) and the bought ring keeps its suffix")
def ring_shop(ctx):
    g = ctx["g"]; L = g.L
    g.fill(L["c_pack"], L["c_pack"] + 7, 0); g.poke16(L["c_gold"], 9000)
    door = find(g, L["T_DALCH"])
    check(door, "no alchemist door on the map")
    fire_to(g, door[0][0], door[0][1] + 1)
    check(g.b(L["sh_mask"]) != 0, "the alchemist does not open")
    ids, ss = g.mem(L["l8_id"], 8), g.mem(L["l8_s"], 8)
    cat = g.mem(L["itcat"], L["N_ITEMS"])
    bad = [i for i, b, p in zip(ids, ss, g.mem(L["l8_b"], 8)) if i and cat[i] == L["CAT_RING"] and not (b or p)]
    check(not bad, "rings in the wares without affixes: %s" % bad)
    want = sx(g, L["I_COPPER"], 2)
    g.poke(L["l8_id"], L["I_COPPER"]); g.poke(L["l8_b"], 0); g.poke(L["l8_s"], want)   # ware 0: copper ring of dexterity
    check(list_to(g, 0, "ui_lc", L["LC_W"]), "cursor not on ware 0")
    g.press_fire(); g.press_fire()                                     # buy, confirm
    pk = g.mem(L["c_pack"], 8)
    check(L["I_COPPER"] in pk, "the ring is not in the pack %s" % pk)
    k = pk.index(L["I_COPPER"])
    check(g.b(L["c_packs"] + k) == want, "bought ring with suffix %d (expected %d: of dexterity)" % (g.b(L["c_packs"] + k), want))
    g.run_stop(); g.frames(2)
    check(g.in_game(), "RUN/STOP does not close the shop")


@test("RING-13", "alchemist: the second worn ring has its own ui_lc (PACK_N + 4 = 12, wares from LC_W): Fire on it buys nothing")
def ring_shop_second(ctx):
    g = ctx["g"]; L = g.L
    check(L["LC_W"] > L["PACK_N"] + 4, "LC_W %d overlaps the second ring slot" % L["LC_W"])
    ring(g, R1, L["I_SILVER"], 1); ring(g, R1 + 1, L["I_COPPER"], 2)
    g.fill(L["c_pack"], L["c_pack"] + 7, 0); g.poke16(L["c_gold"], 9000)
    door = find(g, L["T_DALCH"])
    fire_to(g, door[0][0], door[0][1] + 1)
    check(g.b(L["sh_mask"]) != 0, "the alchemist does not open")
    check(list_to(g, 1, "ui_lc", L["PACK_N"] + 4), "cursor never on the second ring (ui_lc %d)" % g.b(L["ui_lc"]))
    g0 = g.w16(L["c_gold"])
    g.press_fire(); g.press_fire()
    check(g.w16(L["c_gold"]) == g0 and not any(g.mem(L["c_pack"], 8)), "Fire on the second ring bought something (gold %d -> %d, pack %s)" % (g0, g.w16(L["c_gold"]), g.mem(L["c_pack"], 8)))
    g.run_stop(); g.frames(2)
    check(g.in_game(), "RUN/STOP does not close the shop")
