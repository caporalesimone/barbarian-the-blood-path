"""Dungeon performance, simple optimizations (sanity moved to regression on 11/11; 11/11, docs/wiki/prestazioni.md "Dungeon: analisi dell'11/11"): mark_explored
writes one or two bytes per row with masks instead of one bit at a time (same map of the explored cells), and the HUD
redraws only the panel that changed (hit taken: HP row; experience: XP row; skill ready: row 23) instead of all four.
One VICE session, the village (EXPL is saved and restored: in the village it holds the inn chest)."""
import random
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu(); new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def expected(tx, ty):
    rows = [[0] * 6 for _ in range(48)]
    for y in range(max(0, ty - 3), min(47, ty + 3) + 1):
        for x in range(max(0, tx - 4), min(47, tx + 4) + 1):
            rows[y][x >> 3] |= 1 << (x & 7)
    return [b for r in rows for b in r]


@test("PERF-OPT-10", "mark_explored: the explored map equals the reference (9 x 7 cells around the hero) at the edges and inside")
def mark_explored(ctx):
    g = ctx["g"]; L = g.L
    E = L["EXPL"]
    saved = g.mem(E, 288)
    rnd = random.Random(11)
    pts = [(0, 0), (47, 47), (0, 47), (47, 0), (3, 46), (44, 2), (7, 7), (8, 8), (15, 20), (16, 3)] + \
          [(rnd.randrange(48), rnd.randrange(48)) for _ in range(20)]
    try:
        for tx, ty in pts:
            g.fill(E, E + 287, 0)
            g.poke(L["ptx"], tx); g.poke(L["pty"], ty)
            g.call_keep(L["mark_explored"])
            got = g.mem(E, 288)
            check(got == expected(tx, ty), "hero at %d,%d: explored map differs from the reference" % (tx, ty))
    finally:
        g.poke(E, *saved)


@test("PERF-OPT-11", "HUD: a hit taken redraws only the HP panel, experience only the XP panel (hud_pend), not the whole HUD")
def hud_panels(ctx):
    g = ctx["g"]; L = g.L
    g.frames(10)                                            # HUD idle
    g.poke(L["godmode"], 0)
    g.poke(L["hud_pend"], 0); g.poke(L["hud_dirty"], 0)
    g.poke(L["cb_dl"], 1, 0)
    g.call_keep(L["hurt_player"])
    check(g.b(L["hud_dirty"]) == 0 and g.b(L["hud_pend"]) == 1, "hit: hud_dirty %d hud_pend %d (expected 0, 1)" % (g.b(L["hud_dirty"]), g.b(L["hud_pend"])))
    g.poke(L["hud_pend"], 0)
    g.poke(L["tmp0"], 1, 0)
    g.call_keep(L["add_xp"])
    check(g.b(L["hud_dirty"]) == 0 and g.b(L["hud_pend"]) == 2, "xp: hud_dirty %d hud_pend %d (expected 0, 2)" % (g.b(L["hud_dirty"]), g.b(L["hud_pend"])))
    g.frames(4)
    hp = g.w16(L["c_hp"])
    txt = g.mem(L["SCR_H"] + 800 + 40 + 4, 3)
    check(g.b(L["hud_pend"]) == 0, "panels still pending after 4 frames: %02x" % g.b(L["hud_pend"]))
    check(txt[0] != L["G_BLANK"], "HP row not drawn")
