"""Potions and belt (11/11, TODO 1.12): every potion type, every belt slot, empty slots, full hp, cooldown, belt colour
in the HUD, save/load, death, buying with a full belt. One VICE session (development disk), the village (no monsters).
BELT_SLOTS = 4 today: with the 8-slot belt (TODO 3.1) the tests follow the constant and the keys of lib.play."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, BELT_KEYS, fire_to, find, alive, mpos, floor_next, go_level, go_village, K_RUNSTOP

BELT_SLOTS = 4
CHAIN = True                                                # (one session: after a failure the game state is unknown)
HUD_BELT = 0xd800 + 22 * 40 + 29                           # colour of belt slot j: HUD_BELT + 2 j (hud_p3)
HEAL = {13: (20, 0), 14: (60, 0), 15: (40, 4)}              # potion id -> (fixed, per level): docs/oggetti.md
COLOUR = {13: 2, 14: 7, 15: 4}                              # red, yellow, violet; 6 (blue) while cooling down
CD = {13: 250, 14: 350, 15: 500}                            # cooldown in frames (itrate x 2): 5, 7, 10 s


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g)
    g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def belt(g, *ids):
    ids = list(ids) + [0] * (BELT_SLOTS - len(ids))
    g.poke(g.L["c_beltt"], *ids)


def cool_off(g):
    g.poke(g.L["tmr"] + g.L["T_POT"], 0, 0)


def hp_setup(g, hp, hpmax=1000):
    """hp and a large maximum (so that a heal is never capped unless asked)"""
    g.poke16(g.L["hpmax"], hpmax); g.poke16(g.L["c_hp"], hp)


def drink_check(g, pid, lvl):
    L = g.L
    g.poke(L["c_lvl"], lvl)
    cool_off(g); belt(g, pid); hp_setup(g, 1)
    key(g, BELT_KEYS[0], 3)
    want = 1 + HEAL[pid][0] + HEAL[pid][1] * lvl
    hp = g.w16(L["c_hp"])
    check(hp == want, "potion %d level %d: hp %d (expected %d)" % (pid, lvl, hp, want))
    check(g.b(L["c_beltt"]) == 0, "potion %d: the belt slot is not freed" % pid)
    cd = g.w16(L["tmr"] + L["T_POT"])
    check(CD[pid] - 10 <= cd <= CD[pid], "potion %d: cooldown %d frames (expected about %d)" % (pid, cd, CD[pid]))
    belt(g, 0, pid); g.poke(L["hud_dirty"], 1); g.frames(6)                                # second potion at once: refused (cooldown), blue in the HUD
    col = g.b(HUD_BELT + 2) & 15
    key(g, BELT_KEYS[1], 2)
    check(g.w16(L["c_hp"]) == hp and g.b(L["c_beltt"] + 1) == pid, "potion %d: drunk during the cooldown" % pid)
    check(col == 6, "potion %d: HUD colour %d during the cooldown (expected 6, blue)" % (pid, col))
    cool_off(g); g.poke(L["hud_dirty"], 1); g.frames(6)
    col = g.b(HUD_BELT + 2) & 15
    check(col == COLOUR[pid], "potion %d: HUD colour %d (expected %d)" % (pid, col, COLOUR[pid]))
    hp_setup(g, 990)                                             # cap at the maximum
    key(g, BELT_KEYS[1], 2)
    check(g.w16(L["c_hp"]) == 1000, "potion %d: hp %d over the cap (max 1000)" % (pid, g.w16(L["c_hp"])))
    cool_off(g)


@test("POTION-10", "minor healing (red): +20, 5 s cooldown, red in the belt, capped at max hp")
def potion_red(ctx):
    drink_check(ctx["g"], 13, 1)


@test("POTION-11", "healing potion (yellow): +60, 7 s cooldown, yellow in the belt, capped at max hp")
def potion_yellow(ctx):
    drink_check(ctx["g"], 14, 1)


@test("POTION-12", "greater healing (violet): +40 + 4 x level at levels 1, 10, 50, 99; 10 s cooldown, violet")
def potion_violet(ctx):
    for lvl in (1, 10, 50, 99):
        drink_check(ctx["g"], 15, lvl)
    ctx["g"].poke(ctx["g"].L["c_lvl"], 1)


@test("BELT-11", "every belt slot: its key drinks only that slot; the key of an empty slot does nothing")
def belt_slots(ctx):
    g, L = ctx["g"], ctx["g"].L
    for i in range(BELT_SLOTS):
        ids = [0] * BELT_SLOTS; ids[i] = 13
        cool_off(g); belt(g, *ids); hp_setup(g, 1)
        key(g, BELT_KEYS[i], 2)
        check(g.w16(L["c_hp"]) > 1, "key %d: no heal" % (i + 1))
        check(g.mem(L["c_beltt"], BELT_SLOTS) == [0] * BELT_SLOTS, "key %d: belt %s" % (i + 1, g.mem(L["c_beltt"], BELT_SLOTS)))
    for i in range(BELT_SLOTS):                                  # slot i empty, all the others full
        ids = [14] * BELT_SLOTS; ids[i] = 0
        cool_off(g); belt(g, *ids); hp_setup(g, 1)
        gold = g.w16(L["c_gold"])
        key(g, BELT_KEYS[i], 2)
        check(g.w16(L["c_hp"]) == 1, "empty slot %d: hp changed to %d" % (i + 1, g.w16(L["c_hp"])))
        check(g.mem(L["c_beltt"], BELT_SLOTS) == ids, "empty slot %d: belt %s (expected %s)" % (i + 1, g.mem(L["c_beltt"], BELT_SLOTS), ids))
        check(g.w16(L["tmr"] + L["T_POT"]) == 0, "empty slot %d: cooldown started" % (i + 1))
        check(g.w16(L["c_gold"]) == gold, "empty slot %d: gold changed" % (i + 1))


@test("BELT-12", "full hp: the potion is not drunk (stays in the belt, no cooldown)")
def belt_full_hp(ctx):
    g, L = ctx["g"], ctx["g"].L
    cool_off(g); belt(g, 13, 14, 15); hp_setup(g, 500, 500)
    for i in range(3):
        key(g, BELT_KEYS[i], 2)
    check(g.mem(L["c_beltt"], 3) == [13, 14, 15], "belt %s after the keys with full hp" % g.mem(L["c_beltt"], 3))
    check(g.w16(L["tmr"] + L["T_POT"]) == 0, "cooldown started with full hp")


@test("SHOP-BELT-10", "alchemist: potion with a full belt refused (gold kept); one free slot: chosen, the potion goes there")
def shop_belt(ctx):
    g, L = ctx["g"], ctx["g"].L
    g.poke(L["c_lvl"], 1); g.poke16(L["hpmax"], 100); g.poke16(L["c_hp"], 100)
    g.poke16(L["c_gold"], 5000)
    belt(g, 13, 13, 13, 13)
    door = find(g, L["T_DALCH"])
    check(door, "no alchemist door on the map")
    fire_to(g, door[0][0], door[0][1] + 1)
    check(g.b(L["sh_mask"]) != 0, "the alchemist does not open")
    ids = g.mem(L["l8_id"], 8)
    pot = [i for i, v in enumerate(ids) if v in (13, 14, 15)]
    if not pot:                                                  # random stock without potions: put one in the first entry
        g.poke(L["l8_id"], 14); pot = [0]
    k = pot[0]; pid = g.b(L["l8_id"] + k)
    for _ in range(10):                                          # ui_lc: 12..19 = wares (l8_id), 20..23 belt
        if g.b(L["ui_lc"]) == 12 + k: break
        g.frames(1, joy=2 if g.b(L["ui_lc"]) < 12 + k else 1); g.frames(1)
    check(g.b(L["ui_lc"]) == 12 + k, "cursor on entry %d, not on the potion (%d)" % (g.b(L["ui_lc"]), 12 + k))
    price = g.w16(L["itprice"] + 2 * pid)
    g.press_fire()                                              # buy (potions: no y/n question, shop_buy)
    check(g.w16(L["c_gold"]) == 5000 and g.mem(L["c_beltt"], 4) == [13] * 4,
          "full belt: gold %d belt %s" % (g.w16(L["c_gold"]), g.mem(L["c_beltt"], 4)))
    belt(g, 13, 13, 0, 13)
    g.press_fire()                                              # buy -> slot choice ('>' on the free slot)
    check(g.b(g.MN["sh_slot"]) == 2, "slot choice on %d (expected the free slot 2)" % g.b(g.MN["sh_slot"]))
    g.press_fire()                                              # put
    check(g.mem(L["c_beltt"], 4) == [13, 13, pid, 13], "belt %s (expected the potion in slot 3)" % g.mem(L["c_beltt"], 4))
    check(g.w16(L["c_gold"]) == 5000 - price, "gold %d (expected %d)" % (g.w16(L["c_gold"]), 5000 - price))
    g.run_stop(); g.frames(2)
    check(g.in_game(), "RUN/STOP does not close the shop")


@test("SHOP-SELL-11", "alchemist: sell a belt potion (slot freed) and one scroll of a stack, at half price")
def shop_sell_belt(ctx):
    g, L = ctx["g"], ctx["g"].L
    belt(g, 14, 0, 0, 0)
    g.fill(L["c_pack"], L["c_pack"] + 7, 0); g.poke(L["c_pack"], L["I_SCROLL"]); g.poke(L["c_packb"], 3)
    g.poke16(L["c_gold"], 1000)
    door = find(g, L["T_DALCH"])
    fire_to(g, door[0][0], door[0][1] + 1)
    check(g.b(L["sh_mask"]) != 0, "the alchemist does not open")
    for want, what in ((20, "belt slot 1"), (24, "scroll")):
        for _ in range(30):
            if g.b(L["ui_lc"]) == want: break
            g.frames(1, joy=2); g.frames(1)
        check(g.b(L["ui_lc"]) == want, "cursor never on the %s (ui_lc %d)" % (what, g.b(L["ui_lc"])))
        item = 14 if want == 20 else L["I_SCROLL"]
        g0 = g.w16(L["c_gold"])
        g.press_fire(); g.press_fire()                              # sell, confirm
        check(g.w16(L["c_gold"]) == g0 + g.w16(L["itprice"] + 2 * item) // 2, "%s: gold %d (expected %d)" % (what, g.w16(L["c_gold"]), g0 + g.w16(L["itprice"] + 2 * item) // 2))
    check(g.b(L["c_beltt"]) == 0, "the belt slot was not freed")
    check(g.b(L["c_packb"]) == 2, "scroll stack %d (expected 2)" % g.b(L["c_packb"]))
    g.run_stop(); g.frames(2)
    check(g.in_game(), "RUN/STOP does not close the shop")


@test("BELT-13", "save from the game menu, belt wiped in RAM, hero loaded from disk: same belt")
def belt_save(ctx):
    g, L = ctx["g"], ctx["g"].L
    belt(g, 15, 0, 14, 13)
    g.run_stop(); g.frames(2)                                   # game menu: resume, save, quit
    g.frames(1, joy=2); g.frames(1)
    g.press_fire(settle=2)                                      # save game
    for _ in range(20):
        if g.in_game(): break
        g.frames(5, tmax=60)
    check(g.in_game(), "after 'save game' the game does not resume")
    belt(g, 0, 0, 0, 0)
    g.call_keep(L["load_char"], tmax=60)
    check(g.mem(L["c_beltt"], 4) == [15, 0, 14, 13], "belt after loading %s (expected [15, 0, 14, 13])" % g.mem(L["c_beltt"], 4))


@test("BELT-14", "death keeps the belt (no potion lost)")
def belt_death(ctx):
    g, L = ctx["g"], ctx["g"].L
    go_level(g, 1)
    belt(g, 13, 0, 15, 0)
    died = False
    for i in alive(g):
        p = floor_next(g, *mpos(g, i))
        if not p: continue
        g.teleport(p[0], p[1])
        for _ in range(80):
            g.poke16(L["c_hp"], 1); g.poke(L["c_beltt"], 13); g.poke(L["c_beltt"] + 2, 15)
            cool_off(g)
            g.frames(5)
            if not g.in_game(): died = True; break
        if died: break
    check(died, "no death")
    g.press_fire(); g.wait_main()
    check(g.b(L["cur_level"]) == 0, "not in the village after dying")
    check(g.mem(L["c_beltt"], 4) == [13, 0, 15, 0], "belt after death %s" % g.mem(L["c_beltt"], 4))
