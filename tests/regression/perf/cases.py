"""Performance (11/11): the game must keep its frame rate in every situation. Frame = cycles between two reads of the
input in the main loop (lib.c64.Game.frames, cycle counter of the C64: warp mode does not change it); a frame is
"lost" when it lasts more than 1.5 PAL frames (19656 cycles). Thresholds = the values measured on 11/11 (v1.164,
docs/wiki/prestazioni.md) plus a margin: a test fails when the game gets slower than today, not when it is not perfect.
Also: time to change level, to open the inventory, the shops and the inn, to save (emulated seconds, 985248 cycles per
second); every level 1..19 and the throne room boss fight; the level generator on every level 1..255 (the Abyss levels
21..255 too: the generator is the only part of the Abyss that exists in the code today)."""
from lib.c64 import Game, FRAME
from c64test import test, check
from c64test import Skip
from lib.play import (new_game, go_level, alive, mpos, floor_next, fire_to, find, key, K_I, K_RUNSTOP, U, D, LF, RT,
                      INN_DOOR, SMITH_DOOR)

CHAIN = True
CPS = 985248
DIRS = (RT, D, LF, U, RT | D, LF | U, RT | U, LF | D)


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g)
    g.poke(g.L["godmode"], 1)                                   # (the hero must not die while we measure)
    g.frames(5)
    ctx["res"] = {}


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def walk(g, n=240, near_monsters=False):
    """n frames of walking: a direction until the hero stops moving, then the next one; returns the frame lengths"""
    L = g.L
    durs, k, last, still = [], 0, None, 0
    for i in range(n // 4):
        if near_monsters and i % 15 == 0:
            m = alive(g)
            if m:
                p = floor_next(g, *mpos(g, m[i // 15 % len(m)]))
                if p: g.teleport(p[0], p[1]); g.frames(1)
        durs += g.frames(4, joy=DIRS[k % len(DIRS)])
        pos = (g.w16(L["px"]), g.w16(L["py"]))
        still = still + 1 if pos == last else 0
        last = pos
        if still >= 1: k += 1; still = 0
    return durs[1:]


def lost(durs):
    return sum(1 for d in durs if d > 1.5 * FRAME) / max(1, len(durs))


def worst(durs):
    return max(durs) / FRAME if durs else 0


def check_walk(ctx, name, durs, max_lost, max_worst):
    lo, wo = lost(durs), worst(durs)
    ctx["res"][name] = (lo, wo)
    print("      %s: %d frames, lost %.1f%%, worst %.2f frames" % (name, len(durs), 100 * lo, wo))
    check(lo <= max_lost, "%s: %.1f%% lost frames (threshold %.0f%%)" % (name, 100 * lo, 100 * max_lost))
    check(wo <= max_worst, "%s: worst frame %.2f frames (threshold %.1f)" % (name, wo, max_worst))


@test("PERF-10", "village: walking in 8 directions, lost frames <= 2%, worst frame <= 2")
def perf_village(ctx):
    g = ctx["g"]
    g.teleport(24, 24); g.frames(3)
    check_walk(ctx, "village", walk(g, 320), 0.02, 2.0)


@test("PERF-11", "inventory open within 0.3 s, minimap within 0.5 s; back in the game within 0.3 s")
def perf_ui(ctx):
    g, L = ctx["g"], ctx["g"].L
    def settle(d):
        """cycles until the first normal frame: the screen is drawn between some input reads"""
        tot = sum(d)
        for _ in range(20):
            x = g.frames(1)[0]
            if x < 1.2 * FRAME: return tot
            tot += x
        return tot

    for name, k, mx in (("inventory", K_I, 0.3), ("minimap", (4, 0x10), 0.5)):     # 11/11: 0.10 s, 0.64 s; 15/11 (TODO D2, class table + row pointers): minimap 0.26 s, limit ~2x
        t_open = settle(g.frames(1, keys={k[0]: k[1]})) / CPS
        t_back = settle(g.frames(1, keys={K_RUNSTOP[0]: K_RUNSTOP[1]})) / CPS
        print("      %s: open %.2f s, back %.2f s" % (name, t_open, t_back))
        check(t_open <= mx and t_back <= 0.3, "%s: open %.2f s (max %.1f), back to the game %.2f s (max 0.3)" % (name, t_open, mx, t_back))
        check(g.in_game(), "%s: not back in the game" % name)


def settle_open(g, k=None, fire=False, tmax=60):
    """emulated seconds from the key/Fire to the first normal frame of the screen that opens"""
    d = g.frames(1, fire=fire, keys=({k[0]: k[1]} if k else None), tmax=tmax)
    tot = sum(d)
    for _ in range(400):
        x = g.frames(1, tmax=tmax)[0]
        if x < 1.2 * FRAME: return tot / CPS
        tot += x
    return tot / CPS


@test("PERF-19", "village screens with the module MENU in memory (loaded at the village entry, 11/11): smith, inn, inn again <= 0.5 s, back <= 0.5 s")
def perf_shops(ctx):
    g, L = ctx["g"], ctx["g"].L
    for name, door, mx in (("smith", SMITH_DOOR, 0.5), ("inn", INN_DOOR, 0.5), ("inn again", INN_DOOR, 0.5)):   # 11/11: 0.12, 0.14, 0.14 s (before: inn first time 9.18 s)
        g.teleport(*door); g.frames(3)
        t = settle_open(g, fire=True)
        check(not g.in_game(), "%s: the screen did not open" % name)
        tb = settle_open(g, K_RUNSTOP)
        print("      %s: open %.2f s, back %.2f s" % (name, t, tb))
        check(g.in_game(), "%s: not back in the game" % name)
        check(t <= mx and tb <= 0.5, "%s: open %.2f s (max %.1f), back %.2f s (max 0.5)" % (name, t, mx, tb))
        g.teleport(24, 24); g.frames(2)


def level_time(g, target):
    """seconds (emulated) from the Fire on the stairs to the first frame of the new level"""
    L = g.L
    t = L["T_TSTAIRS"] if g.b(L["cur_level"]) == 0 else (L["T_STAIRSD"] if target > g.b(L["cur_level"]) else L["T_STAIRSU"])
    g.teleport(*find(g, t)[0]); g.frames(3)
    c0 = g.last
    g.frames(1, fire=True)
    while g.b(L["cur_level"]) != target or not g.in_game():
        g.frames(1, tmax=60)
    return (g.last - c0) / CPS


@test("PERF-12", "change of level (stairs, Krill): village -> 1 <= 5 s, 1 -> 2 <= 13 s, 2 -> 1 <= 13 s (the level left is saved: whole hero file)")
def perf_level(ctx):
    g = ctx["g"]
    bad = []                                                        # (18/11) all three measured, then the verdict: same sequence pass or fail
    for a, b, mx in ((0, 1, 5.0), (1, 2, 13.0), (2, 1, 13.0)):      # 11/11 KERNAL without cache: 11.1, 13.8, 15.8 s; Krill: 3.1, 10.2, 11.4
        t = level_time(g, b)
        print("      level %d -> %d: %.2f s" % (a, b, t))
        if t > mx:
            bad.append("level %d -> %d: %.2f s (max %.0f s)" % (a, b, t, mx))
    check(not bad, "; ".join(bad))


@test("PERF-13", "dungeon level 1: walking (corridors, rooms), lost frames <= 6%, worst frame <= 2.5")
def perf_dungeon(ctx):
    g = ctx["g"]
    check_walk(ctx, "level 1", walk(g, 320), 0.06, 2.5)             # 11/11: 1.9%, 2.00


@test("PERF-14", "dungeon level 1: walking among the monsters (they wake up and follow), lost <= 10%, worst <= 2.5")
def perf_monsters(ctx):
    g, L = ctx["g"], ctx["g"].L
    check_walk(ctx, "level 1 + monsters", walk(g, 320, near_monsters=True), 0.10, 2.5)   # 11/11: 4.4%, 2.07


@test("PERF-15", "Frenzy run (+100%) among the monsters: lost frames <= 40%, worst frame <= 3")
def perf_frenzy(ctx):
    g, L = ctx["g"], ctx["g"].L
    durs = []
    for _ in range(4):
        g.poke(L["tmr"] + L["T_FZ"], 250, 0); g.poke(L["fz_run"], 100)
        durs += walk(g, 80, near_monsters=True)
    check_walk(ctx, "Frenzy", durs, 0.40, 3.0)                      # 11/11: 26.9%, 2.07


@test("PERF-16", "combat in a crowd: attacking with 4+ monsters awake around, lost <= 15%, worst <= 3")
def perf_combat(ctx):
    g, L = ctx["g"], ctx["g"].L
    g.poke(L["tmr"] + L["T_FZ"], 0, 0); g.poke(L["fz_run"], 0); g.frames(2)   # (fz_run: normal run again)
    m = alive(g)
    check(len(m) >= 4, "only %d monsters alive" % len(m))
    p = floor_next(g, *mpos(g, m[0]))
    g.teleport(p[0], p[1]); g.frames(1)
    for i in m[1:5]:                                            # the others next to the hero
        g.poke(L["mxl"] + i, g.b(L["mxl"] + m[0])); g.poke(L["mxh"] + i, g.b(L["mxh"] + m[0]))
        g.poke(L["myl"] + i, g.b(L["myl"] + m[0])); g.poke(L["myh"] + i, g.b(L["myh"] + m[0]))
    durs = []
    for _ in range(40):
        for i in m: g.poke(L["mhp"] + i, 200); g.poke(L["mhph"] + i, 0)
        durs += g.frames(1, joy=p[2], fire=True) + g.frames(5, joy=p[2])
    check_walk(ctx, "combat", durs[1:], 0.15, 3.0)                  # 11/11: 7.9%, 2.02


@test("PERF-17", "game menu 'save game' within 10 s (Krill: read + rewrite of the whole hero file, 9 blocks)")
def perf_save(ctx):
    g, L = ctx["g"], ctx["g"].L
    key(g, K_RUNSTOP, 1); g.frames(1, joy=D); g.frames(1)
    c0 = g.last
    g.frames(1, fire=True)
    while not g.in_game(): g.frames(1, tmax=60)
    t = (g.last - c0) / CPS
    print("      save: %.2f s" % t)
    check(t <= 10.0, "save game: %.2f s (max 10 s)" % t)            # 11/11: REL 3.2 s; Krill 8.6 s (provisional, docs/wiki/FastLoader.md)


def to_level(g, lv):
    """change_level to lv (spawn on the stairs up), then back to an input read"""
    g.call_keep(g.L["change_level"], regs="a=%02x,x=00" % lv, tmax=150)
    g.frames(2)


@test("PERF-18", "levels 5, 10, 15, 20 (other themes, throne room): walking, lost <= 5/6/10/5%, worst <= 2.5 (20: 4)")
def perf_themes(ctx):
    g, L = ctx["g"], ctx["g"].L
    if g.b(L["cur_level"]) == 0: go_level(g, 1)
    g.poke(L["fz_run"], 0)
    for lv, mx, wmax in ((5, 0.05, 2.5), (10, 0.06, 2.5), (15, 0.10, 2.5), (20, 0.05, 4.0)):   # 11/11: 0%, 0.8%, 3.8%, 0.4%
        to_level(g, lv)                     # (12/11: 5, 10, 15 are chapter boss levels, without stairs down)
        check(g.b(L["cur_level"]) == lv, "not on level %d" % lv)
        check_walk(ctx, "level %d" % lv, walk(g, 240), mx, wmax)        # (level 20: worst frame 2.95)


@test("PERF-20", "final boss fight in the throne room (boss + summons around): lost <= 25%, worst <= 4")
def perf_boss(ctx):
    g, L = ctx["g"], ctx["g"].L
    check(g.b(L["cur_level"]) == 20, "not on level 20")
    m = alive(g)
    check(m, "no monster on level 20")
    boss = max(m, key=lambda i: g.b(L["mhph"] + i) * 256 + g.b(L["mhp"] + i))
    p = floor_next(g, *mpos(g, boss))
    check(p, "no floor next to the boss")
    g.teleport(p[0], p[1]); g.frames(1)
    durs = []
    for _ in range(40):
        g.poke(L["mhp"] + boss, 255); g.poke(L["mhph"] + boss, 3)
        durs += g.frames(1, joy=p[2], fire=True) + g.frames(5, joy=p[2])
    check_walk(ctx, "final boss", durs[1:], 0.25, 4.0)


@test("PERF-21", "every dungeon level 1..19 (change_level): walking, lost <= 20%, worst <= 3")
def perf_all_levels(ctx):
    g, L = ctx["g"], ctx["g"].L
    if g.b(L["cur_level"]) == 20:                # the throne room has no stairs down: up to 19 first
        fire_to(g, *find(g, L["T_STAIRSU"])[0]); g.wait_main()
    rows = []
    for lv in range(1, 20):
        to_level(g, lv)                           # (12/11: change_level; the chapter boss levels have no stairs down)
        check(g.b(L["cur_level"]) == lv, "not on level %d" % lv)
        d = walk(g, 160)
        rows.append((lv, lost(d), worst(d)))
        ctx["res"]["level %d" % lv] = (lost(d), worst(d))
    for lv, lo, wo in rows:
        print("      level %2d: lost %4.1f%%, worst %.2f" % (lv, 100 * lo, wo))
    bad = [(lv, lo, wo) for lv, lo, wo in rows if lo > 0.20 or wo > 3.0]   # 11/11: max 14.5% (level 14), worst 2.03
    check(not bad, "levels over the thresholds: %s" % ", ".join("%d (%.1f%%, %.2f)" % (a, 100 * b, c) for a, b, c in bad))


@test("PERF-22", "Abyss levels 21..255: walking (when the Abyss exists)")
def perf_abyss_walk(ctx):
    raise Skip("the Abyss is not in the game yet (TODO): its levels cannot be entered; PERF-23 measures the generator")


def gen_cycles(g, lvl):
    """cycles of gen_dungeon for level lvl (called between two input reads, like the stairs do)"""
    L = g.L
    g.poke(L["cur_level"], lvl)
    r0 = g.regs()
    c0 = g.last
    g.poke(0x0340, 0x20, L["gen_dungeon"] & 255, L["gen_dungeon"] >> 8, 0xea)
    g.brk(0x0343); g.pc(0x0340)
    c1 = g.go(60)
    g.delbrk()
    if g.at_input: g.brk(g.RI)
    for b in list(g.hits) + list(g.until): g.brk(b)
    for k in ("pc", "a", "x", "y"): g.cmd("r %s=%02x" % (k, r0[k]) if k != "pc" else "r pc=%04x" % r0["pc"])
    g.last = c1                                  # (counter at the generator's return: the next call/frame starts here)
    return c1 - c0


@test("PERF-23", "level generator on EVERY level 1..19 and on every Abyss level 21..255: <= 1.5 s each, up stairs present")
def perf_gen(ctx):
    g, L = ctx["g"], ctx["g"].L
    cur = g.b(L["cur_level"])
    res = {}
    for lv in [x for x in range(1, 256) if x != L["MAXLEVEL"]]:
        c = gen_cycles(g, lv)
        m = g.mem(L["MAP"], L["MAPW"] * L["MAPH"])
        res[lv] = (c / CPS, m.count(L["T_STAIRSU"]), m.count(L["T_STAIRSD"]))
    g.poke(L["cur_level"], cur)
    ts = [t for t, _, _ in res.values()]
    dun = [res[x][0] for x in range(1, 20)]
    ab = [res[x][0] for x in range(21, 256)]
    print("      levels 1-19: %.2f-%.2f s (avg %.2f); Abyss 21-255: %.2f-%.2f s (avg %.2f)" % (
        min(dun), max(dun), sum(dun) / len(dun), min(ab), max(ab), sum(ab) / len(ab)))
    slow_l = [x for x, (t, _, _) in res.items() if t > 1.5]          # 11/11: 0.34-0.84 s, avg 0.58
    check(not slow_l, "generator over 1.5 s on levels %s" % slow_l[:10])
    nost = [x for x, (_, u, _) in res.items() if u != 1]
    check(not nost, "levels without exactly one up stairs: %s" % nost[:10])
    nodn = [x for x in range(1, 20) if res[x][2] != 1]
    check(not nodn, "dungeon levels without exactly one down stairs: %s" % nodn)
    ctx["res"]["generator"] = (max(ts), 0)


@test("PERF-24", "every village 1..5: walking from next to each wandering NPC (they walk too), lost <= 1.5%, worst <= 2.1 "
      "(19/11: before 3-4% near the NPCs)")
def perf_village_npc(ctx):
    """The wandering NPCs (npc_tick, their sprites in build_sprites, the place label) on top of a full redraw of the screen
    made the frame too long: since 19/11 that work waits one frame when maybe_redraw redraws (redraw_due). Start 3 tiles from
    each NPC, 100 frames of walking, turning as soon as the hero stops (2 frames): with the PERF walk (4 frames per
    step) the old code lost only 0-0.6%, with this one 1.8-4.4%."""
    g, L = ctx["g"], ctx["g"].L
    n = L["npc_xh"] - L["npc_xl"]
    rows = []
    for c in (1, 2, 3, 4, 5):
        g.poke(L["c_chap"], c); g.poke(L["c_unl"], max(c, g.b(L["c_unl"])))
        g.call_keep(L["change_level"], regs="a=00,x=04", tmax=150); g.frames(5)
        sol = {i for i, v in enumerate(g.mem(L["solidtab"], 48)) if v}
        xl, xh, yl, yh = (g.mem(L[k], n) for k in ("npc_xl", "npc_xh", "npc_yl", "npc_yh"))
        durs = []
        for i in [i for i in range(n) if xh[i] != 0xff]:
            nx, ny = (xl[i] + 256 * xh[i]) >> 4, (yl[i] + 256 * yh[i]) >> 4
            for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3)):
                if g.tile(nx + dx, ny + dy) not in sol and 2 < nx + dx < 45 and 2 < ny + dy < 45:
                    g.teleport(nx + dx, ny + dy); g.frames(2)
                    k, still, last, d = len(durs), 0, None, []
                    for _ in range(100):            # a turn as soon as the hero stops (2 frames): the walk of a player
                        d += g.frames(1, joy=DIRS[k % len(DIRS)])   # bumping into the NPCs, many full redraws
                        pos = (g.w16(L["px"]), g.w16(L["py"]))
                        still = still + 1 if pos == last else 0
                        last = pos
                        if still >= 2: k += 1; still = 0
                    durs += d[1:]
                    break
        lo, wo = lost(durs), worst(durs)
        rows.append((c, lo, wo))
        print("      village %d: %d frames, lost %.1f%%, worst %.2f" % (c, len(durs), 100 * lo, wo))
    bad = [(c, lo, wo) for c, lo, wo in rows if lo > 0.015 or wo > 2.1]
    check(not bad, "villages over the thresholds: %s" % ", ".join("%d (%.1f%%, %.2f)" % (c, 100 * a, b) for c, a, b in bad))
