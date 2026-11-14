"""Dungeon regression tests (11/11, TODO 1.12): chests (key, monster too close, full pack, full belt), minimap fog,
portal after a change of level, Frenzy and Rage, the throne room (boss, wall, epic chest, lever) and death on level
20. One VICE session (development disk), chained: the tests share the game state."""
from lib.c64 import Game, addr_after, listing
from c64test import test, check
from lib.play import (new_game, fire_to, find, alive, mpos, floor_next, clear_around, go_level, go_village, key,
                      FLOOR_D, K_M, K_5, RT, D)

CHAIN = True
K_U, K_O = (3, 0x40), (4, 0x40)                             # Rage, Frenzy


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g)
    go_level(g, 1)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def chests(g):
    """indices of the closed chests of the level: (index, x, y, type)"""
    L = g.L
    t, xs, ys = g.mem(L["ch_t"], L["CH_MAX"]), g.mem(L["cx_x"], L["CH_MAX"]), g.mem(L["cx_y"], L["CH_MAX"])
    return [(i, xs[i], ys[i], t[i]) for i in range(L["CH_MAX"]) if t[i] and not t[i] & 0x20 and g.tile(xs[i], ys[i]) == L["T_CHEST"]]


def new_chest(g, t=1):
    """a new closed chest of type t on a free floor tile (MAP + chest table): (index, x, y, type)"""
    L = g.L
    i = g.mem(L["ch_t"], L["CH_MAX"]).index(0)
    x, y = next((x, y) for y in range(3, 45) for x in range(3, 45)
                if all(g.tile(x + dx, y + dy) in FLOOR_D for dx in (-1, 0, 1) for dy in (-1, 0, 1)))
    g.poke(L["cx_x"] + i, x); g.poke(L["cx_y"] + i, y); g.poke(L["ch_t"] + i, t)
    g.poke(L["MAP"] + y * 48 + x, L["T_CHEST"])
    return i, x, y, t


def chest_with(g, i, items, counts=None):
    """chest i with a known content: bit 7 = content already generated (chest_open shows it as it is), no gold"""
    L = g.L
    g.poke(L["ch_t"] + i, (g.b(L["ch_t"] + i) & 0x43) | 0x80)
    items = list(items) + [0] * (4 - len(items))
    g.poke(L["ch_i"] + 4 * i, *items)
    g.poke(L["ch_b"] + 4 * i, *(list(counts or []) + [0] * (4 - len(counts or []))))


def away(g, x, y):
    """step off the chest (a tile change clears ch_blk), then back next to it"""
    p = floor_next(g, x, y)
    g.teleport(p[0], p[1]); g.frames(3)


def is_open(g, i):
    return bool(g.b(g.L["ch_t"] + i) & 0x20)


@test("DUNG-CHEST-10", "key chest: without a key 'it is locked' (stays closed); with a key it opens, one key used")
def chest_key(ctx):
    g, L = ctx["g"], ctx["g"].L
    i, x, y, t = chests(g)[0]
    ctx["used"] = {i}
    g.poke(L["ch_t"] + i, (t & 0xfc) | 2)                       # key chest (ch_keyr: 0, 1, 1)
    clear_around(g, x, y)
    g.poke(L["c_keys"], 0)
    fire_to(g, x, y)
    check(not g.in_game() and g.b(L["ch_msg"]) == 1, "no 'locked' screen (ch_msg %d)" % g.b(L["ch_msg"]))
    g.press_fire()
    check(g.in_game() and not is_open(g, i), "the locked chest opened or its screen stays")
    g.poke(L["c_keys"], 2)
    away(g, x, y); clear_around(g, x, y); fire_to(g, x, y)
    check(not g.in_game() and is_open(g, i), "with a key the chest does not open")
    check(g.b(L["c_keys"]) == 1, "keys %d (expected 1: one used)" % g.b(L["c_keys"]))
    g.run_stop(); g.frames(2)
    check(g.in_game(), "the chest screen does not close")


@test("DUNG-CHEST-11", "monster within 2 tiles: Fire refused, label 'monster too close!' (id 15); monster gone: it opens")
def chest_near(ctx):
    g, L = ctx["g"], ctx["g"].L
    cs = [c for c in chests(g) if c[0] not in ctx["used"]]
    check(cs, "no other closed chest on the level")
    i, x, y, t = cs[0]
    ctx["used"].add(i)
    g.poke(L["ch_t"] + i, t & 0xfc | 1)                         # normal chest (no key)
    clear_around(g, x, y)
    m = alive(g)[0]
    p = next((x + dx, y + dy) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1)) if g.tile(x + dx, y + dy) in FLOOR_D)
    g.poke(L["mxl"] + m, (p[0] * 16 + 8) & 255); g.poke(L["mxh"] + m, (p[0] * 16 + 8) >> 8)
    g.poke(L["myl"] + m, (p[1] * 16 + 8) & 255); g.poke(L["myh"] + m, (p[1] * 16 + 8) >> 8)
    g.godmode = g.b(L["godmode"]); g.poke(L["godmode"], 1)
    fire_to(g, x, y, frames=1)
    check(g.in_game() and not is_open(g, i), "the chest opened with a monster at 2 tiles")
    check(g.b(L["ch_blk"]) == 1, "ch_blk %d (expected 1)" % g.b(L["ch_blk"]))
    lab = g.call_keep(L["loc_id"])["a"]
    check(lab == 15, "label id %d on the chest (expected 15: monster too close!)" % lab)
    clear_around(g, x, y, 6)
    away(g, x, y); fire_to(g, x, y)
    check(not g.in_game() and is_open(g, i), "without monsters the chest does not open")
    g.run_stop(); g.frames(2)
    g.poke(L["godmode"], g.godmode)


@test("LOOT-10", "full pack: a weapon in a chest stays there ('pack is full'); one free slot: taken")
def loot_pack(ctx):
    g, L = ctx["g"], ctx["g"].L
    cs = [c for c in chests(g) if c[0] not in ctx["used"]] or [c for c in chests(g)]
    i, x, y, t = cs[0]
    ctx["chest"] = (i, x, y)
    g.poke(L["ch_t"] + i, t & 0xfc | 1)
    chest_with(g, i, [L["I_SWORD"]], [0])
    g.fill(L["c_pack"], L["c_pack"] + 7, L["I_DAGGER"]); g.fill(L["c_packd"], L["c_packd"] + 7, 30)
    g.fill(L["c_packm"], L["c_packm"] + 7, 40)
    clear_around(g, x, y, 6)
    fire_to(g, x, y)
    check(not g.in_game(), "the chest does not open")
    g.press_fire()                                              # take the sword
    check(g.b(L["ch_i"] + 4 * i) == L["I_SWORD"] and L["I_SWORD"] not in g.mem(L["c_pack"], 8),
          "with a full pack the sword moved (chest %d, pack %s)" % (g.b(L["ch_i"] + 4 * i), g.mem(L["c_pack"], 8)))
    check(not g.in_game(), "the chest screen closed")
    g.poke(L["c_pack"] + 7, 0)
    g.press_fire()
    check(L["I_SWORD"] in g.mem(L["c_pack"], 8), "with a free slot the sword was not taken")
    if not g.in_game(): g.run_stop(); g.frames(2)
    g.fill(L["c_pack"], L["c_pack"] + 7, 0)


@test("LOOT-11", "full belt: a potion in a chest stays there; one free belt slot: it goes to the belt, not the pack")
def loot_belt(ctx):
    g, L = ctx["g"], ctx["g"].L
    cs = [c for c in chests(g) if c[0] not in ctx["used"] and c[0] != ctx["chest"][0]] or [c for c in chests(g)]
    i, x, y, t = cs[0]
    ctx["used"].add(i)
    g.poke(L["ch_t"] + i, t & 0xfc | 1)
    chest_with(g, i, [L["I_RED"]])
    g.poke(L["c_beltt"], 14, 14, 14, 14)
    clear_around(g, x, y, 6)
    fire_to(g, x, y)
    check(not g.in_game(), "the chest does not open")
    g.press_fire()
    check(g.b(L["ch_i"] + 4 * i) == L["I_RED"] and g.mem(L["c_beltt"], 4) == [14] * 4,
          "full belt: chest %d belt %s" % (g.b(L["ch_i"] + 4 * i), g.mem(L["c_beltt"], 4)))
    g.poke(L["c_beltt"] + 1, 0)
    g.press_fire()
    check(g.mem(L["c_beltt"], 4) == [14, L["I_RED"], 14, 14], "belt %s (expected the red potion in slot 2)" % g.mem(L["c_beltt"], 4))
    check(L["I_RED"] not in g.mem(L["c_pack"], 8), "the potion went to the pack")
    if not g.in_game(): g.run_stop(); g.frames(2)


@test("DUNG-CHEST-12", "golden chest: needs a key like the key chest (ch_keyr), one key used")
def chest_gold(ctx):
    g, L = ctx["g"], ctx["g"].L
    i, x, y, t = new_chest(g, 3)                                # golden chest, content not generated yet
    clear_around(g, x, y, 6)
    g.poke(L["c_keys"], 0)
    fire_to(g, x, y)
    check(not g.in_game() and g.b(L["ch_msg"]) == 1, "golden chest without a key: no 'locked' screen")
    g.press_fire()
    check(g.in_game() and not is_open(g, i), "the golden chest opened without a key")
    g.poke(L["c_keys"], 1)
    away(g, x, y); fire_to(g, x, y)
    check(not g.in_game() and is_open(g, i) and g.b(L["c_keys"]) == 0, "golden chest with a key: open %s, keys %d" % (is_open(g, i), g.b(L["c_keys"])))
    g.run_stop(); g.frames(2)


@test("LOOT-12", "10 scrolls on the hero: a scroll in a chest stays there (max 10); with 9 it is taken (stack of 10)")
def loot_scrolls(ctx):
    g, L = ctx["g"], ctx["g"].L
    i, x, y, t = new_chest(g, 1)
    chest_with(g, i, [L["I_SCROLL"]], [1])
    g.fill(L["c_pack"], L["c_pack"] + 7, 0); g.poke(L["c_pack"], L["I_SCROLL"]); g.poke(L["c_packb"], 10)
    clear_around(g, x, y, 6)
    fire_to(g, x, y)
    check(not g.in_game(), "the chest does not open")
    g.press_fire()
    check(g.b(L["ch_i"] + 4 * i) == L["I_SCROLL"] and g.b(L["c_packb"]) == 10, "11th scroll taken (stack %d)" % g.b(L["c_packb"]))
    check(g.b(L["gv_why"]) == 2, "gv_why %d (expected 2: max scrolls)" % g.b(L["gv_why"]))
    g.poke(L["c_packb"], 9)
    g.press_fire()
    check(g.b(L["c_packb"]) == 10, "with 9 scrolls the stack is %d (expected 10)" % g.b(L["c_packb"]))
    if not g.in_game(): g.run_stop(); g.frames(2)
    g.fill(L["c_pack"], L["c_pack"] + 7, 0)


def minimap_cells(g):
    """open the minimap, return the drawn cells {(col, row)} of the map area (cols 8..31, rows 0..23) and close it"""
    key(g, K_M, 3)
    scr = g.mem(g.L["SCR_A"], 1000)
    cells = {(c, r) for r in range(24) for c in range(8, 32) if scr[r * 40 + c] not in (63, 32)}
    g.run_stop(); g.frames(3)
    return cells


@test("MAP-10", "minimap fog: nothing explored -> nothing far from the hero; all explored -> the level; half -> top half only")
def map_fog(ctx):
    g, L = ctx["g"], ctx["g"].L
    e = L["EXPL"]
    g.fill(e, e + 287, 0)
    hx, hy = g.ptile()
    near = minimap_cells(g)
    far = [p for p in near if abs(p[0] - (8 + hx // 2)) > 3 or abs(p[1] - hy // 2) > 3]
    check(not far, "fog: %d cells drawn far from the hero (%s...)" % (len(far), far[:4]))
    g.fill(e, e + 287, 0xff)
    full = minimap_cells(g)
    check(len(full) > 60 and len(full) > 4 * len(near), "all explored: only %d cells drawn (fog: %d)" % (len(full), len(near)))
    g.fill(e, e + 287, 0); g.fill(e, e + 143, 0xff)            # rows 0..23 of the level explored
    half = minimap_cells(g)
    low = [p for p in half if p[1] >= 12 and (abs(p[0] - (8 + hx // 2)) > 3 or abs(p[1] - hy // 2) > 3)]
    check(not low, "top half explored: %d cells drawn in the bottom half" % len(low))
    check(any(p[1] < 12 for p in half), "top half explored: nothing drawn in the top half")
    g.fill(e, e + 287, 0xff)


def read_scroll(g):
    L = g.L
    pk = g.mem(L["c_pack"], 8)
    if L["I_SCROLL"] not in pk:
        g.poke(L["c_pack"] + 7, L["I_SCROLL"]); g.poke(L["c_packb"] + 7, 1)
    p = floor_next(g, *find(g, L["T_STAIRSU"])[0])
    g.teleport(p[0], p[1]); g.frames(3)
    key(g, K_5, 3)


@test("PORTAL-10", "portal on level 1, then a new portal on level 2: the old one on level 1 is gone, the village one leads to 2")
def portal_change(ctx):
    g, L = ctx["g"], ctx["g"].L
    read_scroll(g)
    check(find(g, L["T_PORTAL"]), "no portal on level 1")
    go_level(g, 2)
    read_scroll(g)
    check(find(g, L["T_PORTAL"]) and g.b(L["c_retlvl"]) == 2, "level 2: portal %s, return level %d" % (bool(find(g, L["T_PORTAL"])), g.b(L["c_retlvl"])))
    fire_to(g, *find(g, L["T_STAIRSU"])[0]); g.wait_main()
    check(g.b(L["cur_level"]) == 1, "not on level 1")
    check(not find(g, L["T_PORTAL"]), "the old portal is still on level 1")
    go_village(g)
    p = find(g, L["T_PORTAL"])
    check(p, "no portal in the village")
    fire_to(g, *p[0]); g.wait_main()
    check(g.b(L["cur_level"]) == 2, "the village portal leads to level %d (expected 2)" % g.b(L["cur_level"]))
    fire_to(g, *find(g, L["T_STAIRSU"])[0]); g.wait_main()


def skill_ready(g, x):
    g.poke(g.L["sk_cdl"] + x, 0); g.poke(g.L["sk_cdh"] + x, 0)


def fire_once(g):
    """Fire held until the first attack (global cooldown), then released: attacks made in that frame"""
    L = g.L
    g.watch(L["perform_skill1"])
    for _ in range(60):
        g.frames(1, joy=0x10)
        if g.hits[L["perform_skill1"]]: break
    n = g.hits[L["perform_skill1"]]
    g.frames(20)
    g.unwatch()
    return n


@test("SKILL-10", "Frenzy (O): level 15 needed; 5 s; two attacks per Fire; run +100% = 4 px per frame; normal run after")
def frenzy(ctx):
    g, L = ctx["g"], ctx["g"].L
    T = L["tmr"]
    g.poke(L["c_lvl"], 14); skill_ready(g, 5)
    key(g, K_O, 2)
    check(g.w16(T + L["T_FZ"]) == 0, "Frenzy active at level 14")
    g.poke(L["c_lvl"], 15)
    key(g, K_O, 1)
    fz = g.w16(T + L["T_FZ"])
    check(240 <= fz <= 250, "Frenzy timer %d (expected about 250)" % fz)
    check(g.w16(L["sk_cdl"] + 5) or g.b(L["sk_cdh"] + 5), "no cooldown after Frenzy")
    row = next((x, y) for y in range(2, 46) for x in range(2, 40) if all(g.tile(x + k, y) in FLOOR_D for k in range(8)))
    g.teleport(*row); g.frames(2)                               # (not on stairs or a chest: Fire would use the place)
    clear_around(g, *g.ptile(), 8)
    n = fire_once(g)
    check(n == 2, "Frenzy: %d attacks for one Fire (expected 2)" % n)
    row = next((x, y) for y in range(2, 46) for x in range(2, 40) if all(g.tile(x + k, y) in FLOOR_D for k in range(8)))
    g.teleport(*row); g.frames(2)
    g.poke(L["fz_run"], 100)
    x0 = g.w16(L["px"]); g.frames(6, joy=RT); x1 = g.w16(L["px"])
    check(x1 - x0 >= 22, "Frenzy run: %d px in 6 frames (expected 24)" % (x1 - x0))
    g.frames(2)
    g.poke(T + L["T_FZ"], 1, 0); g.frames(3)
    check(g.b(L["fz_run"]) == 0, "fz_run %d after the end of Frenzy" % g.b(L["fz_run"]))
    g.teleport(*row); g.frames(2)
    x0 = g.w16(L["px"]); g.frames(6, joy=RT); x1 = g.w16(L["px"])
    check(10 <= x1 - x0 <= 13, "normal run: %d px in 6 frames (expected 12)" % (x1 - x0))
    n = fire_once(g)
    check(n == 1, "without Frenzy: %d attacks for one Fire (expected 1)" % n)


@test("SKILL-11", "Rage (U): level 9 needed; 6 s; damage taken halved (min 1), full damage without Rage")
def rage(ctx):
    g, L = ctx["g"], ctx["g"].L
    T = L["tmr"]
    g.poke(L["c_lvl"], 8); skill_ready(g, 4)
    key(g, K_U, 2)
    check(g.w16(T + L["T_RAGE"]) == 0, "Rage active at level 8")
    g.poke(L["c_lvl"], 9)
    key(g, K_U, 1)
    r = g.w16(T + L["T_RAGE"])
    check(290 <= r <= 300, "Rage timer %d (expected about 300)" % r)
    a_rage = addr_after(listing("game"), "mon_attack", r"T_RAGE")
    g.poke(L["godmode"], 1)
    i = alive(g)[0]
    p = floor_next(g, *mpos(g, i))
    g.teleport(p[0], p[1])

    def hits(n, rage_on):
        got = []
        g.watch(until=(a_rage, L["hurt_player"]))
        for _ in range(400):
            if rage_on: g.poke(T + L["T_RAGE"], 200, 0)
            else: g.poke(T + L["T_RAGE"], 0, 0)
            g.frames(1)
            if g.stopped == a_rage:
                pre = g.b(L["mu0"]) + 256 * g.b(L["mu1"])
                g.frames(1)
                if g.stopped == L["hurt_player"]:
                    got.append((pre, g.b(L["cb_dl"]) + 256 * g.b(L["cb_dh"])))
                    if len(got) == n: break
        g.unwatch()
        return got

    hr = hits(3, True)
    check(len(hr) == 3, "only %d monster hits with Rage" % len(hr))
    check(all(d == max(1, pre >> 1) for pre, d in hr), "Rage: (before, after) %s (expected halved, min 1)" % hr)
    hn = hits(2, False)
    check(len(hn) == 2 and all(d == max(1, pre) for pre, d in hn), "no Rage: (before, after) %s" % hn)
    g.poke(L["godmode"], 0)


def to_throne(g):
    """from anywhere to level 20: down to level 1, cur_level = 19, stairs down"""
    L = g.L
    if g.b(L["cur_level"]) == 0: go_level(g, 1)
    g.poke(L["cur_level"], 19)
    fire_to(g, *find(g, L["T_STAIRSD"])[0]); g.wait_main()


@test("DEATH-10", "death on level 20 (throne room): village, half gold, deepest level 20 kept")
def death20(ctx):
    g, L = ctx["g"], ctx["g"].L
    to_throne(g)
    check(g.b(L["cur_level"]) == 20, "not on level 20 (%d)" % g.b(L["cur_level"]))
    g.poke16(L["c_gold"], 800)
    boss = [i for i in alive(g) if g.b(L["mtype"] + i) == L["T_FINAL"]]
    check(boss, "no final boss on level 20")
    p = floor_next(g, *mpos(g, boss[0]))
    g.teleport(p[0], p[1])
    died = False
    for _ in range(120):
        g.poke16(L["c_hp"], 1); g.frames(5)
        if not g.in_game(): died = True; break
    check(died, "no death next to the final boss")
    g.press_fire(); g.wait_main()
    check(g.b(L["cur_level"]) == 0 and g.w16(L["c_gold"]) == 400, "level %d gold %d (expected the village, 400)" % (g.b(L["cur_level"]), g.w16(L["c_gold"])))
    check(g.b(L["c_maxd"]) >= 20, "deepest level %d after the death (expected 20)" % g.b(L["c_maxd"]))


@test("THRONE-10", "throne room: north wall closed, boss killed -> wall open, epic chest without key, lever -> portal")
def throne(ctx):
    g, L = ctx["g"], ctx["g"].L
    to_throne(g)
    door = g.mem(L["fin_door"], 6)
    walls = [(door[k], door[k + 1]) for k in range(0, 6, 2)]
    check(all(g.tile(*w) not in FLOOR_D for w in walls), "north wall already open: %s" % [g.tile(*w) for w in walls])
    g.poke(L["godmode"], 1)
    b = [i for i in alive(g) if g.b(L["mtype"] + i) == L["T_FINAL"]][0]
    p = floor_next(g, *mpos(g, b))
    g.teleport(p[0], p[1]); g.frames(4, joy=p[2])
    for _ in range(80):
        g.poke(L["mhp"] + b, 1); g.poke(L["mhph"] + b, 0)
        g.frames(1, fire=True); g.frames(6)
        if not g.b(L["malive"] + b): break
    check(not g.b(L["malive"] + b), "the final boss is still alive")
    g.frames(5)
    check(all(g.tile(*w) in FLOOR_D for w in walls), "north wall still closed: %s" % [g.tile(*w) for w in walls])
    epic = [c for c in chests(g) if c[3] & 0x40]
    check(epic, "no epic chest")
    g.poke(L["c_keys"], 0)
    i, x, y, t = epic[0]
    clear_around(g, x, y, 30)
    fire_to(g, x, y)
    check(not g.in_game() and is_open(g, i), "the epic chest does not open without a key")
    g.run_stop(); g.frames(2)
    lv = find(g, L["T_DHOME"])                                  # T_LEVER = T_DHOME in the throne room
    check(lv, "no lever")
    fire_to(g, *lv[0])
    check(not g.in_game(), "the lever screen does not open")
    g.frames(1, joy=D); g.frames(1); g.press_fire(settle=3)     # pull the lever
    for _ in range(10):
        if g.in_game(): break
        g.frames(3)
    check(g.b(L["c_lever"]) == 1, "c_lever %d (expected 1)" % g.b(L["c_lever"]))
    check(g.tile(L["FIN_AX"], L["FIN_AY"]) == L["T_PORTAL"], "no portal at the lever (tile %d)" % g.tile(L["FIN_AX"], L["FIN_AY"]))
    g.poke(L["godmode"], 0)
