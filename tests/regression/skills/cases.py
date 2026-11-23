"""Skills regression tests (11/11, from the code review): selection by level (H J K L), Whirlwind hits every monster
around, Battle Cry stuns, Smash hits the monsters in its area, cooldowns. Frenzy and Rage: regression/dungeon
(SKILL-10/11). Hits are counted on hit_one (one attack roll per monster). One VICE session, level 1, godmode."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, go_level, key, alive, clear_around, floor_next, find, FLOOR_D

CHAIN = True
K_H, K_J, K_K, K_L = (3, 0x20), (4, 0x04), (4, 0x20), (5, 0x04)


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g)
    go_level(g, 1)
    g.poke(g.L["godmode"], 1)
    g.poke(g.L["q_step"], 12)                                   # (23/11, Q15) chain done: only the level decides


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def open_room(g):
    """a floor tile with floor all around (3x3) far from the stairs"""
    for y in range(3, 45):
        for x in range(3, 45):
            if all(g.tile(x + dx, y + dy) in FLOOR_D for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)):
                return x, y
    return None


def surround(g, n, d=16):
    """n monsters alive around the hero at d pixels (the others far): returns their indices"""
    L = g.L
    px, py = g.w16(L["px"]), g.w16(L["py"])
    m = alive(g)
    off = [(d, 0), (-d, 0), (0, d), (0, -d), (d, d), (-d, -d)]
    used = m[:n]
    for k, i in enumerate(used):
        x, y = px + off[k][0], py + off[k][1]
        g.poke(L["mxl"] + i, x & 255); g.poke(L["mxh"] + i, x >> 8); g.poke(L["myl"] + i, y & 255); g.poke(L["myh"] + i, y >> 8)
        g.poke(L["mhp"] + i, 250); g.poke(L["mhph"] + i, 0); g.poke(L["mstun"] + i, 0)
    for i in m[n:]:
        g.poke(L["malive"] + i, 0)
    return used


def use_skill(g, idx, keyk, lvl):
    """skill idx selected with its key at level lvl, cooldown zero, Fire held until the skill is used (global cooldown),
    then released: returns (hit_one calls, perform calls)"""
    L = g.L
    g.poke(L["c_lvl"], lvl); g.poke(L["sk_cdl"] + idx, 0); g.poke(L["sk_cdh"] + idx, 0)
    key(g, keyk, 1)
    g.watch(L["hit_one"], L["perform_skill1"])
    for _ in range(40):
        g.frames(1, joy=0x10)
        if g.hits[L["perform_skill1"]]: break
    g.frames(12)
    h, p = g.hits[L["hit_one"]], g.hits[L["perform_skill1"]]
    g.unwatch()
    return h, p


def in_area(g, used, hw, hh):
    """monsters of used inside the skill area around the hero (half width hw, half height hh, pixels)"""
    L = g.L
    px, py = g.w16(L["px"]), g.w16(L["py"])
    return sum(1 for i in used if g.b(L["malive"] + i) or True
               if abs(g.b(L["mxl"] + i) + 256 * g.b(L["mxh"] + i) - px) < hw
               and abs(g.b(L["myl"] + i) + 256 * g.b(L["myh"] + i) - py) < hh)


@test("SKILL-12", "skill keys: J/K/L refused below levels 3/6/12, accepted at the level (c_skill)")
def skill_select(ctx):
    g, L = ctx["g"], ctx["g"].L
    for k, idx, lvl in ((K_J, 1, 3), (K_K, 2, 6), (K_L, 3, 12)):
        key(g, K_H, 1)
        g.poke(L["c_lvl"], lvl - 1); key(g, k, 1)
        check(g.b(L["c_skill"]) == 0, "skill %d selected at level %d" % (idx, lvl - 1))
        g.poke(L["c_lvl"], lvl); key(g, k, 1)
        check(g.b(L["c_skill"]) == idx, "skill %d not selected at level %d (c_skill %d)" % (idx, lvl, g.b(L["c_skill"])))
    key(g, K_H, 1)


@test("SKILL-13", "Whirlwind: one attack roll on each of the 3 monsters around, 2 s cooldown")
def whirlwind(ctx):
    g, L = ctx["g"], ctx["g"].L
    p = open_room(g)
    check(p, "no open room on the level")
    g.teleport(*p); g.frames(2)
    used = surround(g, 3)
    h, n = use_skill(g, 1, K_J, 3)
    want = in_area(g, used, 26, 26)
    check(n == 1 and h == want == 3, "Whirlwind: %d attack rolls, %d uses (expected 3 = monsters in the area %d, 1)" % (h, n, want))
    cd = g.w16(L["sk_cdl"] + 1) if False else g.b(L["sk_cdl"] + 1) + 256 * g.b(L["sk_cdh"] + 1)
    check(80 <= cd <= 100, "Whirlwind cooldown %d frames (expected about 100)" % cd)


@test("SKILL-14", "Battle Cry: one saving throw per monster in its area (hit_one), the failed ones stunned; 15 s cooldown")
def battle_cry(ctx):
    g, L = ctx["g"], ctx["g"].L
    stunned = 0
    for _ in range(4):                                           # a saving throw can spare a monster: a few tries
        used = surround(g, 4, 32)
        h, n = use_skill(g, 2, K_K, 6)
        want = in_area(g, used, 80, 64)
        check(n == 1 and h == want >= 3, "Battle Cry: %d saving throws, %d uses (expected %d = monsters in the area, 1)" % (h, n, want))
        stunned += sum(1 for i in used if g.b(L["mstun"] + i))
        if stunned: break
    check(stunned, "no monster stunned by Battle Cry in 4 tries")
    cd = g.b(L["sk_cdl"] + 2) + 256 * g.b(L["sk_cdh"] + 2)
    check(700 <= cd <= 750, "Battle Cry cooldown %d frames (expected about 750)" % cd)


@test("SKILL-15", "Smash: one attack roll on each monster within 44 px, 6 s cooldown")
def smash(ctx):
    g, L = ctx["g"], ctx["g"].L
    used = surround(g, 4, 16)
    h, n = use_skill(g, 3, K_L, 12)
    want = in_area(g, used, 44, 44)
    check(n == 1 and h == want >= 3, "Smash: %d attack rolls, %d uses (expected %d = monsters in the area, 1)" % (h, n, want))
    cd = g.b(L["sk_cdl"] + 3) + 256 * g.b(L["sk_cdh"] + 3)
    check(280 <= cd <= 300, "Smash cooldown %d frames (expected about 300)" % cd)
    key(g, K_H, 1)
