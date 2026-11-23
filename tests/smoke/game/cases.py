"""Game smoke tests: one VICE session (development disk), the happy path of a game played in sequence.
Speed shortcuts: the hero is teleported (px/py) next to doors, stairs, chests and monsters; keys are written at the
exit of read_input (lib/c64.py). Everything else is the real game (menus, shops, inn, levels, UI).
CHAIN: if a step fails the following ones are skipped (they depend on the game state)."""
from lib.c64 import Game
from c64test import test, check
from lib.play import (NAME, SEED, SOLID_V, FLOOR_D, U, D, LF, RT, GG, find, mpos, alive, fire_to,  # noqa: F401
                      minimap, new_game, key, clear_around, floor_next, SMITH_DOOR, K_5, list_to, K_R)

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    ctx["L"], ctx["M"] = g.L, g.M


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


@test("PG-NEW-01", "new barbarian: name, seed, game starts in the village")
def pg_new(ctx):
    g, L, M = ctx["g"], ctx["L"], ctx["M"]
    new_game(g)
    check(g.b(L["cur_level"]) == 0, "not in the village (cur_level %d)" % g.b(L["cur_level"]))
    check(g.mem(L["c_name"], 12) == NAME, "name %s" % g.mem(L["c_name"], 12))
    check(g.b(L["c_lvl"]) == 1 and g.w16(L["c_gold"]) == 100, "level %d, gold %d (expected 1, 100)" % (g.b(L["c_lvl"]), g.w16(L["c_gold"])))
    hp, hm = g.w16(L["c_hp"]), g.w16(L["hpmax"])
    check(hp == hm > 0, "hp %d/%d" % (hp, hm))
    check(g.b(L["c_eq"]) != 0, "no starting weapon")


@test("VIL-MOVE-01", "village: walk without glitches (tiles, VIC registers, frames)")
def vil_move(ctx):
    g, L = ctx["g"], ctx["L"]
    scr = {((L["SCR_A"] & 0x3fff) >> 10), ((L["SCR_B"] & 0x3fff) >> 10)}      # double buffer: d018 switches between the two
    def vic():
        d18 = g.b(0xd018)
        return [g.b(0xd011) & 0x78, g.b(0xd016) & 0xf8, d18 & 0x0e, (d18 >> 4) in scr, g.b(0xdd00) & 3]
    g.frames(2)
    v0, p0 = vic(), g.ptile()
    durs, path = [], [p0]
    for joy, n in ((U, 50), (RT, 40), (U, 30), (LF, 30), (D, 30)):
        for k in range(n // 10):
            durs += g.frames(10, joy=joy)
            p = g.ptile(); path.append(p)
            t = g.tile(*p)
            check(t not in SOLID_V, "hero on a solid tile %s = %s" % (p, GG.TILES[t]))
            v = vic()
            check(v == v0, "VIC registers changed: %s -> %s (pos %s)" % (v0, v, p))
    moved = len(set(path))
    check(moved >= 8, "the hero moved too little: %d different tiles" % moved)
    lost = sum(1 for d in durs if d > 1.5 * 19656)
    check(lost <= len(durs) * 0.02, "%d lost frames out of %d" % (lost, len(durs)))


@test("MAP-01", "minimap in the village: hero marker on the hero's position")
def map_village(ctx):
    why = minimap(ctx["g"])
    check(not why, why)


@test("SHOP-BUY-01", "smith: buy the first ware (gold carried + inn chest); the bought ware leaves the list (22/11)")
def shop_buy(ctx):
    g, L = ctx["g"], ctx["L"]
    g.poke16(L["c_gold"], 50); g.poke16(L["c_sgold"], 100)
    fire_to(g, 39, 12)                                       # below the smith's door
    check(g.b(L["sh_mask"]) != 0, "the shop did not open")
    item = g.b(L["l8_id"])
    price = g.w16(L["itprice"] + 2 * item)
    n0, w0 = g.b(g.MN["shp_cnt"]), g.mem(L["l8_id"], 8)
    g.press_fire(); g.press_fire()                          # buy, confirm
    n1, w1 = g.b(g.MN["shp_cnt"]), g.mem(L["l8_id"], 8)
    check(n1 == n0 - 1 and list(w1) == list(w0[1:n0]) + [0] * (9 - n0), "wares %s (%d) -> %s (%d): the bought one must leave the list" % (list(w0), n0, list(w1), n1))
    pk, gd, sg = g.mem(L["c_pack"], 8), g.w16(L["c_gold"]), g.w16(L["c_sgold"])
    if price <= 50: want = (50 - price, 100)                 # (the stock is random: the price may fit in the purse)
    else: need = price - 50; dec = -(-need // 10); want = (dec * 10 - need, 100 - dec)
    check(item in pk, "item %d not in the pack %s" % (item, pk))
    check((gd, sg) == want, "gold %d chest %d (expected %d, %d; price %d)" % (gd, sg, want[0], want[1], price))
    ctx["bought"] = (item, price)


@test("SHOP-SELL-01", "smith: sell the bought item at price >> SELL_SHIFT (a quarter since 20/11)")
def shop_sell(ctx):
    g, L = ctx["g"], ctx["L"]
    item, price = ctx["bought"]
    check(list_to(g, 1, "ui_lc", 0), "cursor not on the first pack slot (ui_lc %d)" % g.b(L["ui_lc"]))   # list 1 = gear
    g0 = g.w16(L["c_gold"])
    g.press_fire(); g.press_fire()
    check(item not in g.mem(L["c_pack"], 8), "the item is still in the pack")
    exp = g0 + (price >> L["SELL_SHIFT"])
    check(g.w16(L["c_gold"]) == exp, "gold %d (expected %d)" % (g.w16(L["c_gold"]), exp))
    g.run_stop()
    check(g.b(L["sh_mask"]) == 0 and g.in_game(), "RUN/STOP does not close the shop")


@test("SHOP-REPAIR-01", "smith: repair the worn weapon (durability back to max - 1, gold paid)")
def shop_repair(ctx):
    g, L = ctx["g"], ctx["g"].L
    w = g.b(L["c_eq"])
    g.poke(L["c_packd"] + 8, 10); g.poke(L["c_packm"] + 8, 60)     # equipment = entries 8..11 after the 8 pack slots
    g.poke16(L["c_gold"], 1000)
    fire_to(g, *SMITH_DOOR)
    check(g.b(L["sh_mask"]) != 0, "the smith does not open")
    check(list_to(g, 1, "ui_lc", 8), "cursor not on the weapon (ui_lc %d)" % g.b(L["ui_lc"]))   # ui_lc 8 = equipped weapon
    cost = g.w16(L["itprice"] + 2 * w) * L["REPAIR_PC"] // 100
    key(g, K_R); g.press_fire()                                    # R: repair, fire: confirm
    check(g.b(L["c_packd"] + 8) == 59 and g.b(L["c_packm"] + 8) == 59, "durability %d/%d (expected 59/59)" % (g.b(L["c_packd"] + 8), g.b(L["c_packm"] + 8)))
    check(g.w16(L["c_gold"]) == 1000 - cost, "gold %d (expected %d, cost %d)" % (g.w16(L["c_gold"]), 1000 - cost, cost))
    g.run_stop(); g.frames(2)
    check(g.in_game(), "RUN/STOP does not close the smith")


@test("INN-CHEST-01", "inn: an item from the pack to the chest")
def inn_put(ctx):
    g, L = ctx["g"], ctx["L"]
    g.poke(L["c_pack"], 2); g.poke(L["c_packd"], 50); g.poke(L["c_packm"], 60)
    fire_to(g, 40, 43); g.frames(5)                         # below the inn's door (OVLT from disk)
    check(not g.in_game(), "the inn chest did not open")
    check(list_to(g, 0, "ui_cur", 0), "cursor not on the first pack slot")   # (21/11) list 0 = yours
    g.press_fire()
    check(g.b(L["c_pack"]) == 0 and 2 in g.mem(L["st_id"], 24), "pack %s, chest %s" % (g.mem(L["c_pack"], 8), g.mem(L["st_id"], 8)))


@test("INN-CHEST-02", "inn: the item from the chest back to the pack")
def inn_take(ctx):
    g, L = ctx["g"], ctx["L"]
    check(list_to(g, 1, "ui_cur", 0x40), "cursor not on the first chest slot")   # list 1 = chest ($40 + slot)
    g.press_fire()
    check(2 in g.mem(L["c_pack"], 8) and 2 not in g.mem(L["st_id"], 24), "pack %s, chest %s" % (g.mem(L["c_pack"], 8), g.mem(L["st_id"], 8)))


@test("INN-GOLD-01", "inn: entering, the carried gold goes into the chest (in tens)")
def inn_gold(ctx):
    g, L = ctx["g"], ctx["L"]
    g.run_stop(); g.frames(3)
    check(g.in_game(), "RUN/STOP does not close the inn")
    g.poke16(L["c_gold"], 1234)
    g0, s0 = g.w16(L["c_gold"]), g.w16(L["c_sgold"])
    fire_to(g, 40, 43); g.frames(5)                         # (21/11) the deposit is made entering the inn
    check(not g.in_game(), "the inn does not open again")
    gd, sg = g.w16(L["c_gold"]), g.w16(L["c_sgold"])
    check((gd, sg) == (g0 % 10, s0 + g0 // 10), "carried %d chest %d (expected %d, %d)" % (gd, sg, g0 % 10, s0 + g0 // 10))
    g.run_stop(); g.frames(3)
    check(g.in_game(), "RUN/STOP does not close the inn")


@test("LVL-IN-01", "crypt: enter level 1")
def lvl_in(ctx):
    g, L = ctx["g"], ctx["L"]
    fire_to(g, *find(g, L["T_TSTAIRS"])[0]); g.wait_main()
    check(g.b(L["cur_level"]) == 1, "level %d (expected 1)" % g.b(L["cur_level"]))
    check(g.tile(*g.ptile()) in FLOOR_D + (L["T_STAIRSU"],), "hero off the floor: tile %d" % g.tile(*g.ptile()))
    check(len(alive(g)) > 0, "no monsters on the level")


@test("FIGHT-01", "combat: a monster killed, experience gained")
def fight(ctx):
    g, L = ctx["g"], ctx["L"]
    hm, xp0 = g.w16(L["hpmax"]), g.w16(L["c_xp"])
    for i in alive(g):
        mx, my = mpos(g, i)
        for dx, dy, j in ((0, 1, U), (0, -1, D), (1, 0, LF), (-1, 0, RT)):
            if g.tile(mx + dx, my + dy) in FLOOR_D: break
        else:
            continue
        g.teleport(mx + dx, my + dy); g.frames(4, joy=j)
        for _ in range(60):
            g.poke16(L["c_hp"], hm)
            g.frames(1, fire=True); g.frames(6)
            if not g.b(L["malive"] + i): break
        check(not g.b(L["malive"] + i), "monster %d still alive after 60 attacks" % i)
        check(g.w16(L["c_xp"]) > xp0, "experience did not grow (%d)" % xp0)
        return
    check(False, "no reachable monster")


@test("PG-LEVEL-01", "level up: experience over the threshold -> level + 1, more hp, Whirlwind selectable at level 3 (with step 2 of the chain)")
def pg_level(ctx):
    g, L = ctx["g"], ctx["g"].L
    lv, hm = g.b(L["c_lvl"]), g.w16(L["hpmax"])
    while g.b(L["c_lvl"]) < 3:
        n = g.b(L["c_lvl"])
        thr = g.b(L["xp_n0"] + n - 1) + 256 * g.b(L["xp_n1"] + n - 1) + 65536 * g.b(L["xp_n2"] + n - 1)
        g.poke(L["c_xp"], (thr - 2) & 255, ((thr - 2) >> 8) & 255, (thr - 2) >> 16)
        g.poke(L["tmp0"], 1, 0); g.call_keep(L["add_xp"])               # one point short: no level
        check(g.b(L["c_lvl"]) == n, "level %d one point below the threshold %d" % (g.b(L["c_lvl"]), thr))
        g.poke(L["tmp0"], 1, 0); g.call_keep(L["add_xp"])               # threshold reached: next level
        check(g.b(L["c_lvl"]) == n + 1, "level %d at the threshold %d (expected %d)" % (g.b(L["c_lvl"]), thr, n + 1))
    check(g.w16(L["hpmax"]) > hm, "max hp %d did not grow (was %d)" % (g.w16(L["hpmax"]), hm))
    check(g.w16(L["c_hp"]) == g.w16(L["hpmax"]), "hp not full after the level up")
    g.frames(2)
    g.poke(L["q_step"], 2)                                         # (23/11, Q15) and step 2 of the chain handed in
    key(g, (4, 0x04), 2)                                           # J: Whirlwind (level 3)
    check(g.b(L["c_skill"]) == 1, "Whirlwind not selected at level 3 (c_skill %d)" % g.b(L["c_skill"]))
    key(g, (3, 0x20), 2)                                           # H: back to Slash


@test("MAP-02", "minimap on level 1: hero marker on the hero's position")
def map_level(ctx):
    why = minimap(ctx["g"])
    check(not why, why)


@test("POTION-01", "potion: key 1 drinks the first belt slot, hp grows, slot freed")
def potion(ctx):
    g, L = ctx["g"], ctx["L"]
    hm = g.w16(L["hpmax"])
    g.poke(L["c_beltt"], L["I_RED"]); g.poke16(L["c_hp"], 1)
    g.frames(1, keys={7: 0x01}); g.frames(2)                # 1: first belt slot
    hp = g.w16(L["c_hp"])
    check(hp > 1, "hp did not grow (%d)" % hp)
    check(g.b(L["c_beltt"]) == 0, "the belt slot is not free")
    g.poke16(L["c_hp"], hm)


@test("DUNG-CHEST-01", "level chest: opens, gold and item taken")
def dung_chest(ctx):
    g, L = ctx["g"], ctx["L"]
    cx, cy = find(g, L["T_CHEST"])[0]
    for i in alive(g):                                       # no monsters within 2 tiles (chest_blocked)
        mx, my = mpos(g, i)
        if max(abs(mx - cx), abs(my - cy)) < 3: g.poke(L["malive"] + i, 0)
    g0, p0 = g.w16(L["c_gold"]), sum(1 for x in g.mem(L["c_pack"], 8) if x)
    fire_to(g, cx, cy)
    opened = not g.in_game()
    if opened: g.press_fire()                                # take the entry under the cursor
    if not g.in_game(): g.run_stop()
    p1 = sum(1 for x in g.mem(L["c_pack"], 8) if x)
    check(opened, "the chest does not open")
    check(g.w16(L["c_gold"]) > g0 or p1 > p0, "no loot: gold %d -> %d, items %d -> %d" % (g0, g.w16(L["c_gold"]), p0, p1))
    check(g.in_game(), "the chest screen does not close")


@test("EQUIP-01", "inventory: change weapon")
def equip(ctx):
    g, L = ctx["g"], ctx["L"]
    g.fill(L["c_pack"], L["c_pack"] + 7, 0)
    w0 = g.b(L["c_eq"])
    new = 2 if w0 != 2 else 1
    g.poke(L["c_pack"], new); g.poke(L["c_packd"], 50); g.poke(L["c_packm"], 60)
    g.frames(1, keys={4: 2}); g.frames(3)                    # I: inventory (22/11: the cursor starts on the weapon)
    check(not g.in_game(), "the inventory does not open")
    check(g.b(L["sl_cur"]) == 0 and g.b(L["sl_top"]) == 0, "cursor %d, window from %d (expected the weapon, 0/0)" % (g.b(L["sl_cur"]), g.b(L["sl_top"])))
    check(list_to(g, 0, "ui_cur", 0), "the cursor does not reach the first pack slot")
    g.press_fire()
    check(g.b(L["c_eq"]) == new and w0 in g.mem(L["c_pack"], 8), "weapon %d, pack %s (expected %d and the old %d in the pack)" % (g.b(L["c_eq"]), g.mem(L["c_pack"], 8), new, w0))
    if not g.in_game(): g.run_stop(); g.frames(2)
    check(g.in_game(), "the inventory does not close")


@test("LVL-DOWN-01", "stairs down to level 2 and up again to level 1")
def lvl_down(ctx):
    g, L = ctx["g"], ctx["L"]
    fire_to(g, *find(g, L["T_STAIRSD"])[0]); g.wait_main()
    check(g.b(L["cur_level"]) == 2, "level %d (expected 2)" % g.b(L["cur_level"]))
    check(g.tile(*g.ptile()) in FLOOR_D + (L["T_STAIRSU"],), "hero off the floor: tile %d" % g.tile(*g.ptile()))
    fire_to(g, *find(g, L["T_STAIRSU"])[0]); g.wait_main()
    check(g.b(L["cur_level"]) == 1, "back up: level %d (expected 1)" % g.b(L["cur_level"]))


@test("SCROLL-01", "a portal scroll taken from a level chest goes to the pack (stack)")
def scroll_chest(ctx):
    g, L = ctx["g"], ctx["g"].L
    pk = g.mem(L["c_pack"], 8)
    for k, v in enumerate(pk):
        if v == L["I_SCROLL"]: g.poke(L["c_pack"] + k, 0)
    t = g.mem(L["ch_t"], L["CH_MAX"])
    cs = [i for i in range(L["CH_MAX"]) if t[i] and not t[i] & 0x20]
    check(cs, "no closed chest left on the level")
    i = cs[0]; x, y = g.b(L["cx_x"] + i), g.b(L["cx_y"] + i)
    g.poke(L["ch_t"] + i, (t[i] & 0x40) | 0x81)                   # normal chest, content already generated: 2 scrolls
    g.poke(L["ch_i"] + 4 * i, L["I_SCROLL"], 0, 0, 0); g.poke(L["ch_b"] + 4 * i, 2, 0, 0, 0)
    clear_around(g, x, y, 6)
    fire_to(g, x, y)
    check(not g.in_game(), "the chest does not open")
    g.press_fire()
    if not g.in_game(): g.run_stop(); g.frames(2)
    pk = g.mem(L["c_pack"], 8)
    check(L["I_SCROLL"] in pk, "no scroll in the pack %s" % pk)
    check(g.b(L["c_packb"] + pk.index(L["I_SCROLL"])) == 2, "scroll stack %d (expected 2)" % g.b(L["c_packb"] + pk.index(L["I_SCROLL"])))


@test("PORTAL-01", "scroll: portal on the level, back to the village")
def portal_out(ctx):
    g, L = ctx["g"], ctx["L"]
    up = find(g, L["T_STAIRSU"])[0]
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        if g.tile(up[0] + dx, up[1] + dy) in FLOOR_D: break
    g.teleport(up[0] + dx, up[1] + dy); g.frames(3)
    if L["I_SCROLL"] not in g.mem(L["c_pack"], 8):            # (SCROLL-01 put one in the pack)
        g.poke(L["c_pack"] + 7, L["I_SCROLL"]); g.poke(L["c_packb"] + 7, 1)
    key(g, K_5, 3)                                            # 5: scroll
    p = find(g, L["T_PORTAL"])
    check(p, "no portal after reading the scroll")
    fire_to(g, *p[0]); g.wait_main()
    check(g.b(L["cur_level"]) == 0 and g.b(L["c_retlvl"]) == 1, "level %d, return %d (expected 0 and 1)" % (g.b(L["cur_level"]), g.b(L["c_retlvl"])))


@test("PORTAL-02", "village: the portal leads back to the level")
def portal_back(ctx):
    g, L = ctx["g"], ctx["L"]
    fire_to(g, *find(g, L["T_PORTAL"])[0]); g.wait_main()
    check(g.b(L["cur_level"]) == 1, "level %d (expected 1)" % g.b(L["cur_level"]))


@test("LVL-OUT-01", "stairs up: back to the village")
def lvl_out(ctx):
    g, L = ctx["g"], ctx["L"]
    fire_to(g, *find(g, L["T_STAIRSU"])[0]); g.wait_main()
    check(g.b(L["cur_level"]) == 0, "level %d (expected the village)" % g.b(L["cur_level"]))


@test("DEATH-01", "death: screen, village, half gold, full hp")
def death(ctx):
    g, L = ctx["g"], ctx["L"]
    fire_to(g, *find(g, L["T_TSTAIRS"])[0]); g.wait_main()
    g.poke16(L["c_gold"], 1000)
    d0 = g.w16(L["c_deaths"])
    died = False
    for i in alive(g):
        mx, my = mpos(g, i)
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if g.tile(mx + dx, my + dy) in FLOOR_D: break
        else:
            continue
        g.teleport(mx + dx, my + dy)
        for _ in range(80):
            g.poke16(L["c_hp"], 1)
            g.frames(5)
            if not g.in_game(): died = True; break
        if died: break
    check(died, "no death (monsters do not hit?)")
    g.press_fire(); g.wait_main()
    check(g.b(L["cur_level"]) == 0, "not in the village after dying")
    check(g.w16(L["c_gold"]) == 500 and g.w16(L["c_deaths"]) == d0 + 1, "gold %d (expected 500), deaths %d" % (g.w16(L["c_gold"]), g.w16(L["c_deaths"])))
    check(g.w16(L["c_hp"]) == g.w16(L["hpmax"]), "hp not full")


@test("PG-SAVE-01", "game menu 'save game': back in the game; the hero on disk equals the one in RAM")
def pg_save(ctx):
    g, L = ctx["g"], ctx["g"].L
    snap = lambda: (g.mem(L["c_name"], 12), g.w16(L["c_xp"]), g.w16(L["c_gold"]), g.mem(L["c_eq"], 4), g.mem(L["c_pack"], 8))
    s0 = snap()
    g.run_stop(); g.frames(2); g.frames(1, joy=D); g.frames(1)
    g.press_fire(settle=2)                                   # save game
    for _ in range(20):
        if g.in_game(): break
        g.frames(5, tmax=60)
    check(g.in_game(), "after 'save game' the game does not resume")
    g.fill(L["c_lvl"], L["c_sgold"] + 1, 0)
    g.call_keep(L["load_char"], tmax=60)
    check(snap() == s0, "hero from disk %s, before %s" % (snap(), s0))


@test("PG-LOAD-01", "save game, change the gold, quit (no save): the barbarian loads back as saved")
def pg_load(ctx):
    g, L = ctx["g"], ctx["L"]
    snap = lambda: (g.mem(L["c_name"], 12), g.w16(L["c_xp"]), g.w16(L["c_gold"]), g.w16(L["c_sgold"]), g.mem(L["c_eq"], 4),
                    g.w16(L["c_deaths"]))
    g.call_keep(L["gm_save"], tmax=150)
    s0 = snap()
    g.poke16(L["c_gold"], (g.w16(L["c_gold"]) + 77) & 0xffff)     # not saved: lost with the quit (11/11 evening)
    g.run_stop(); g.frames(2, joy=0)                       # game menu: resume, save, quit
    g.frames(1, joy=D); g.frames(1); g.frames(1, joy=D); g.frames(1)
    g.press_fire(settle=2)                                  # quit -> "quit game? unsaved progress will be lost"
    g.frames(1, keys={3: 0x02}, tmax=60)                    # Y: back to the menu without saving
    g.fill(L["c_lvl"], L["c_sgold"] + 1, 0)                 # wipe the hero in RAM: it must come back from disk
    g.frames(3); g.press_fire(settle=3)                     # first barbarian of the list -> details
    g.press_fire(settle=1)                                  # start
    g.wait_main(90)
    s1 = snap()
    check(s1 == s0, "after loading %s, saved %s" % (s1, s0))
