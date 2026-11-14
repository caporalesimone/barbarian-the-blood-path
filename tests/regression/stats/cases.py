"""Stat points and respec (11/11, branch feature/stat-points, src/game/charsheet.asm): the level-up gives stat points
(pl_pts) instead of raising the stats, the HUD shows an arrow + C while there are points to spend, the C screen
spends them (+/-, confirm, reset), saves on exit, and a respec token gives them all back. Respec tokens: +1 for the
final boss, a low chance in the chests of the Abyss (resp_roll), at most RESP_MAX. One VICE session, the village."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, K_RUNSTOP, K_Y, LF, RT, D, U

CHAIN = True
K_C, K_PLUS, K_MINUS = (2, 0x10), (5, 0x01), (5, 0x08)


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def avail(g):
    return g.call_keep(g.L["pts_avail"])["a"]


def hpmax_expected(g, lvl, con):
    L = g.L
    return L["PL_HP1"] + con + (lvl - 1) * (L["PL_HPL"] + (con - 10) // 2)


def set_level(g, lvl, sadd=(0, 0, 0)):
    L = g.L
    g.poke(L["c_lvl"], lvl); g.poke(L["c_sadd"], *sadd)
    g.call_keep(L["recalc_stats"]); g.call_keep(L["hp_full"])
    g.poke(L["hud_dirty"], 1); g.frames(6)


def hud_icon(g):
    L = g.L
    return g.mem(L["SCR_H"] + 800 + 120 + 6, 1)


@test("STAT-10", "level up: the stats stay the base ones, the points grow by pl_pts (1 every 2 levels, 2..18)")
def stat_levelup(ctx):
    g = ctx["g"]; L = g.L
    pts = g.mem(L["pl_pts"], 21)
    check(pts[1] == 0 and pts[2] == 1 and pts[3] == 1 and pts[18] == 9 and pts[20] == 9, "pl_pts %s" % pts)
    xp_need = g.b(L["xp_n0"]) + 256 * g.b(L["xp_n1"])       # level 1 -> 2
    g.poke(L["c_xp"], xp_need & 255, xp_need >> 8, 0)
    g.poke(L["tmp0"], 0, 0)
    g.call_keep(L["add_xp"])
    check(g.b(L["c_lvl"]) == 2, "level %d after the xp (expected 2)" % g.b(L["c_lvl"]))
    s = g.mem(L["s_str"], 3)
    check(s == [L["PL_STR0"], L["PL_DEX0"], L["PL_CON0"]], "stats %s after the level up (expected the base ones)" % s)
    check(avail(g) == 1, "points to spend %d (expected 1)" % avail(g))


@test("STAT-11", "HUD: glyph next to the level number (row 23, col 6) while there are points to spend, blank without")
def stat_hud(ctx):
    g = ctx["g"]; L = g.L
    g.frames(20)
    h = hud_icon(g)
    check(h == [L["G_LVUP"]], "HUD %s (expected the level-up glyph)" % h)
    check(g.b(0xd800 + 23 * 40 + 6) & 15 == 5, "glyph colour %d (expected green)" % (g.b(0xd800 + 23 * 40 + 6) & 15))
    g.poke(L["c_sadd"], 1); g.poke(L["hud_dirty"], 1); g.frames(20)
    h = hud_icon(g)
    check(h == [L["G_BLANK"]], "HUD %s with no points (expected blank)" % h)
    g.poke(L["c_sadd"], 0); g.poke(L["hud_dirty"], 1); g.frames(2)


@test("STAT-12", "C screen: D (+) on str, confirm: c_sadd str 1, str 17, no points left; RUN/STOP goes back without saving")
def stat_spend(ctx):
    g = ctx["g"]; L = g.L
    key(g, K_C, 3)
    check(not g.in_game(), "the C screen does not open")
    check(g.b(L["ui_cur"]) == 0, "cursor %d (expected str)" % g.b(L["ui_cur"]))
    g.frames(1, joy=RT); g.frames(2)
    check(g.mem(L["cs_pend"], 3) == [1, 0, 0], "pending %s" % g.mem(L["cs_pend"], 3))
    g.frames(1, joy=RT); g.frames(2)                                  # no points left: refused
    check(g.mem(L["cs_pend"], 3) == [1, 0, 0], "a second point without points: %s" % g.mem(L["cs_pend"], 3))
    g.poke(L["ui_cur"], 3); g.frames(1); g.press_fire()               # confirm
    check(g.mem(L["c_sadd"], 3) == [1, 0, 0] and g.b(L["s_str"]) == L["PL_STR0"] + 1,
          "after confirm: c_sadd %s str %d" % (g.mem(L["c_sadd"], 3), g.b(L["s_str"])))
    check(avail(g) == 0, "points left %d" % avail(g))
    g.watch(L["save_char"], L["sv_all"])
    g.run_stop(); g.frames(5, tmax=60)
    while not g.in_game(): g.frames(1, tmax=60)
    n = g.hits[L["save_char"]] + g.hits[L["sv_all"]]; g.unwatch()
    print("      saves on exit: %d" % n)
    check(n == 0, "the hero was saved %d times on exit (expected 0: only 'save game' saves, 11/11 evening)" % n)


@test("STAT-13", "C screen: '-' takes a pending point back, reset clears them, exit without changes does not save")
def stat_minus_reset(ctx):
    g = ctx["g"]; L = g.L
    set_level(g, 6, (1, 0, 0))                                        # 3 points, 1 spent: 2 to spend
    key(g, K_C, 3)
    g.poke(L["ui_cur"], 2); g.frames(1)
    key(g, K_PLUS, 1); key(g, K_PLUS, 1)
    check(g.mem(L["cs_pend"], 3) == [0, 0, 2], "pending %s (expected con 2)" % g.mem(L["cs_pend"], 3))
    key(g, K_MINUS, 1)
    check(g.mem(L["cs_pend"], 3) == [0, 0, 1], "after '-': %s" % g.mem(L["cs_pend"], 3))
    g.poke(L["ui_cur"], 4); g.frames(1); g.press_fire()               # reset
    check(g.mem(L["cs_pend"], 3) == [0, 0, 0] and g.mem(L["c_sadd"], 3) == [1, 0, 0],
          "after reset: pending %s spent %s" % (g.mem(L["cs_pend"], 3), g.mem(L["c_sadd"], 3)))
    g.watch(L["save_char"], L["sv_all"])
    g.run_stop(); g.frames(3)
    while not g.in_game(): g.frames(1, tmax=60)
    n = g.hits[L["save_char"]] + g.hits[L["sv_all"]]; g.unwatch()
    check(n == 0, "saved %d times without changes" % n)


@test("STAT-14", "exit with pending points: they are confirmed (dex +2); hp max follows con")
def stat_exit_applies(ctx):
    g = ctx["g"]; L = g.L
    key(g, K_C, 3)
    g.poke(L["ui_cur"], 1); g.frames(1)
    g.press_fire(); g.press_fire()                                    # Fire on a stat = +
    g.run_stop(); g.frames(3)
    while not g.in_game(): g.frames(1, tmax=60)
    check(g.mem(L["c_sadd"], 3) == [1, 2, 0], "c_sadd %s (expected [1, 2, 0])" % g.mem(L["c_sadd"], 3))
    check(g.mem(L["cs_pend"], 3) == [0, 0, 0], "pending left %s" % g.mem(L["cs_pend"], 3))
    for lvl, con in ((6, 0), (12, 2), (20, 5)):
        set_level(g, lvl, (0, 0, con))
        want = hpmax_expected(g, lvl, L["PL_CON0"] + con)
        check(g.w16(L["hpmax"]) == want, "level %d con +%d: hp max %d (expected %d)" % (lvl, con, g.w16(L["hpmax"]), want))
    set_level(g, 6, (1, 2, 0))


@test("STAT-15", "respec: no entry without tokens; with 2 tokens: yes -> all the points back, 1 token left, not saved on exit")
def stat_respec(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_resp"], 0)
    key(g, K_C, 3)                                                    # (12/11) no points, no token: no entries at all
    g.press_fire()
    check(not g.in_game() and g.mem(L["c_sadd"], 3) == [1, 2, 0], "respec without tokens changed %s" % g.mem(L["c_sadd"], 3))
    g.run_stop(); g.frames(3)
    while not g.in_game(): g.frames(1, tmax=60)
    g.poke(L["c_resp"], 2)
    key(g, K_C, 3)                                                    # (12/11) no points: "respec" is the only entry
    g.press_fire()                                                    # "use a respec token?"
    key(g, K_Y, 2)
    check(g.mem(L["c_sadd"], 3) == [0, 0, 0] and g.b(L["c_resp"]) == 1,
          "after respec: c_sadd %s tokens %d" % (g.mem(L["c_sadd"], 3), g.b(L["c_resp"])))
    check(avail(g) == 3, "points to spend after respec %d (expected 3)" % avail(g))
    g.watch(L["save_char"], L["sv_all"])
    g.run_stop(); g.frames(3)
    while not g.in_game(): g.frames(1, tmax=60)
    n = g.hits[L["save_char"]] + g.hits[L["sv_all"]]; g.unwatch()
    check(n == 0, "saved %d times after a respec (expected 0: only 'save game' saves)" % n)


@test("STAT-16", "respec tokens: resp_add stops at RESP_MAX; resp_roll never above ground nor in levels 1-20, ~2% in the Abyss")
def stat_tokens(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_resp"], L["RESP_MAX"] - 1)
    g.call_keep(L["resp_add"]); g.call_keep(L["resp_add"])
    check(g.b(L["c_resp"]) == L["RESP_MAX"], "tokens %d (expected %d)" % (g.b(L["c_resp"]), L["RESP_MAX"]))
    rr = L["resp_roll"]
    # 6502 loop at $0340: 1024 calls of resp_roll (Y x 4 rounds), then stop
    code = [0xa2, 0x04, 0xa0, 0x00, 0x98, 0x48, 0x8a, 0x48, 0x20, rr & 255, rr >> 8, 0x68, 0xaa, 0x68, 0xa8, 0x88,
            0xd0, 0xf2, 0xca, 0xd0, 0xef, 0xea]
    cur = g.b(L["cur_level"])
    for lvl, lo, hi in ((5, 0, 0), (20, 0, 0), (21, 4, 45), (200, 4, 45)):
        g.poke(L["c_resp"], 0); g.poke(L["cur_level"], lvl)
        r0 = g.regs()
        g.poke(0x0340, *code); g.brk(0x0340 + len(code) - 1); g.pc(0x0340); g.go(60); g.delbrk()
        if g.at_input: g.brk(g.RI)
        for k in ("a", "x", "y"): g.cmd("r %s=%02x" % (k, r0[k]))
        g.cmd("r pc=%04x" % r0["pc"])
        g.last = 0
        n = g.b(L["c_resp"])
        print("      level %d: %d tokens in 1024 chests" % (lvl, n))
        check(lo <= n <= hi, "level %d: %d tokens in 1024 chests (expected %d..%d)" % (lvl, n, lo, hi))
    g.poke(L["cur_level"], cur)
    g.poke(L["c_resp"], 0)
