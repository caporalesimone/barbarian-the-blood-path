"""C screen reworked on 15/11 (TODO Z5, owner's request; src/game/charsheet.asm): nothing about respec while there are
no tokens, pending points movable between the stats until a definitive confirmation ("confirm" asks; RUN/STOP with
pending points asks and "no" gives them back), preview "current -> new" of the derived stats, hint of the stat under
the cursor, "next point at level N" when there are no points. One VICE session, the village; the screen memory is
checked, not only the variables."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, K_Y, K_N, LF, RT, D

CHAIN = True
K_C, K_PLUS, K_MINUS = (2, 0x10), (5, 0x01), (5, 0x08)
UC_PEND = 5


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    lvl(g, 6, (1, 2, 0))                                           # level 6: 3 points, all spent


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def lvl(g, level, sadd, resp=0):
    L = g.L
    g.poke(L["c_lvl"], level); g.poke(L["c_sadd"], *sadd); g.poke(L["c_resp"], resp)
    g.call_keep(L["recalc_stats"]); g.call_keep(L["hp_full"]); g.frames(3)


def addr(g, y):
    L = g.L
    return g.b(L["scrrow_lo"] + y) | g.b(L["scrrow_hi"] + y) << 8


def row(g, y):
    """text of a UI row (screen codes: letters 1-26, '>' $3e; anything else '.')"""
    return "".join(chr(c + 96) if 1 <= c <= 26 else chr(c) if 32 <= c < 64 else "." for c in g.mem(addr(g, y), 40))


def screen(g):
    return "\n".join(row(g, y) for y in range(25))


def avail(g):
    return g.call_keep(g.L["pts_avail"])["a"]


def pend(g):
    return g.mem(g.L["cs_pend"], 3)


def open_c(g):
    key(g, K_C, 3)
    check(not g.in_game(), "the C screen does not open")


def back(g):
    g.run_stop(); g.frames(3)
    while not g.in_game(): g.frames(1, tmax=60)


def at(g, cur):
    g.poke(g.L["ui_cur"], cur); g.frames(1)


def cur_to(g, cur):
    """cursor on entry cur with a real move (down from the entry above): the screen is redrawn"""
    g.poke(g.L["ui_cur"], (cur - 1) % g.b(g.L["ui_n"])); g.frames(1, joy=D); g.frames(1)


@test("CS-10", "no points, no token: nothing about respec on the screen, no entries, 'no points to spend.', next point at level 8")
def cs_view(ctx):
    g = ctx["g"]; L = g.L
    open_c(g)
    s = screen(g)
    check("respec" not in s and "token" not in s, "respec shown with 0 tokens:\n%s" % s)
    check(">" not in "".join(row(g, y) for y in range(2, 22)), "an entry cursor is shown:\n%s" % s)
    check("actions" not in s and "confirm" not in s, "the actions box is shown without entries:\n%s" % s)
    check(row(g, 13)[3:22] == "no points to spend.", "row 13: %r" % row(g, 13))
    check(row(g, 14)[3:24].rstrip() == "next point at level 8", "row 14: %r" % row(g, 14))
    check(row(g, 24)[1:14] == "run/stop:back", "row 24: %r" % row(g, 24))
    g.press_fire(); g.frames(2)
    check(not g.in_game() and g.mem(L["c_sadd"], 3) == [1, 2, 0], "fire changed something")
    back(g)
    lvl(g, 20, (5, 2, 2))                                            # all 9 points spent: no next point
    open_c(g)
    check("next point" not in row(g, 14), "row 14 at level 20: %r" % row(g, 14))
    back(g)
    lvl(g, 6, (1, 2, 0))


@test("CS-11", "no points, 1 token: token count shown, only 'respec' (row 17); yes: points back, full menu without respec")
def cs_respec(ctx):
    g = ctx["g"]; L = g.L
    lvl(g, 6, (1, 2, 0), resp=1)
    open_c(g)
    check(row(g, 2)[22:35] == "respec tokens" and row(g, 2)[36:39].strip() == "1", "row 2: %r" % row(g, 2))
    check(row(g, 17)[2:10] == "> respec", "row 17: %r" % row(g, 17))
    check(row(g, 24)[1:22] == "fire:ok run/stop:back", "row 24: %r" % row(g, 24))
    g.press_fire()
    check("use a respec token?" in row(g, 23), "row 23: %r" % row(g, 23))
    key(g, K_Y, 3)
    check(g.mem(L["c_sadd"], 3) == [0, 0, 0] and g.b(L["c_resp"]) == 0, "respec not done: %s" % g.mem(L["c_sadd"], 3))
    s = screen(g)
    check("confirm" in row(g, 17) and "undo" in row(g, 18), "after the respec the full menu is not back:\n%s" % s)
    check("respec" not in s and "token" not in s, "respec still shown with 0 tokens:\n%s" % s)
    check(g.b(L["ui_n"]) == 5, "entries %d (expected 5: no respec entry)" % g.b(L["ui_n"]))
    back(g)


@test("CS-12", "points, no token: entries str/dex/con/confirm/undo only, 'points to spend 3', no respec anywhere")
def cs_points(ctx):
    g = ctx["g"]; L = g.L
    lvl(g, 6, (0, 0, 0))
    open_c(g)
    s = screen(g)
    check(g.b(L["ui_n"]) == 5 and "respec" not in s and "token" not in s, "respec with 0 tokens:\n%s" % s)
    check(row(g, 13)[3:20] == "points to spend 3" and "pending" not in row(g, 13), "row 13: %r" % row(g, 13))
    check(row(g, 24)[1:37] == "a/d -/+:points fire:ok run/stop:back", "row 24: %r" % row(g, 24))
    back(g)


@test("CS-13", "before confirming, points move freely: D/+ add, A/- take back, between str/dex/con; undo takes all back")
def cs_move(ctx):
    g = ctx["g"]; L = g.L
    open_c(g)
    g.frames(1, joy=RT); g.frames(2); g.frames(1, joy=RT); g.frames(2)  # str +2
    key(g, K_MINUS, 1)                                                  # str -1
    at(g, 2); key(g, K_PLUS, 1)                                         # con +1
    check(pend(g) == [1, 0, 1], "pending %s (expected [1, 0, 1])" % pend(g))
    check(row(g, 13)[3:20] == "points to spend 1" and row(g, 13)[23:32] == "pending 2", "row 13: %r" % row(g, 13))
    g.frames(1, joy=LF); g.frames(2)                                    # con -1 (A)
    at(g, 1); g.press_fire()                                            # dex +1 (fire)
    check(pend(g) == [1, 1, 0], "pending %s (expected [1, 1, 0])" % pend(g))
    check(g.mem(L["c_sadd"], 3) == [0, 0, 0], "points spent before the confirmation: %s" % g.mem(L["c_sadd"], 3))
    at(g, 0); key(g, K_PLUS, 1)                                         # str +1: all 3 pending
    key(g, K_PLUS, 1)                                                   # no points left: refused
    check(pend(g) == [2, 1, 0] and "no points." in row(g, 23), "pending %s, row 23 %r" % (pend(g), row(g, 23)))
    at(g, 4); g.press_fire()                                            # undo
    check(pend(g) == [0, 0, 0] and avail(g) == 3, "after undo: pending %s, points %d" % (pend(g), avail(g)))
    check("pending" not in row(g, 13), "row 13 after undo: %r" % row(g, 13))


@test("CS-14", "preview: con +1 shows 'hp N -> N+6' and 'mod +2 -> +3' (new values green); hint of the stat under the cursor")
def cs_preview(ctx):
    g = ctx["g"]; L = g.L
    for y in range(3, 7):
        check(L["CH_ARROW"] not in g.mem(addr(g, y), 40), "arrow on row %d without pending points: %r" % (y, row(g, y)))
    hp0, c0 = g.w16(L["hpmax"]), g.b(L["s_con"])
    m0, m1 = (c0 - 10) // 2, (c0 - 9) // 2
    at(g, 2); key(g, K_PLUS, 1)                                         # con +1 (15 -> 16: mod +2 -> +3)
    want = "hp   %d . %d" % (hp0, hp0 + 1 + 5 * (m1 - m0))              # level 6: +1 con, mod change x 5 levels
    check(row(g, 3)[2:2 + len(want)] == want, "row 3: %r (expected %r)" % (row(g, 3), want))
    a = addr(g, 3) + 2 + want.index(".")
    check(g.b(a) == L["CH_ARROW"], "no arrow glyph on row 3")
    col = g.b(0xd800 + (a - addr(g, 0)) + 2) & 15
    check(col == UC_PEND, "new hp value colour %d (expected %d, green)" % (col, UC_PEND))
    w1, w2 = "con %d . %d" % (c0, c0 + 1), "mod +%d" % m0 + (" . +%d" % m1 if m1 != m0 else "")
    check(row(g, 11)[3:3 + len(w1)] == w1 and row(g, 11)[18:18 + len(w2)] == w2, "row 11: %r (%r %r)" % (row(g, 11), w1, w2))
    for y in (4, 5):
        check(L["CH_ARROW"] not in g.mem(addr(g, y), 40), "row %d changed by con: %r" % (y, row(g, y)))
    hints = {0: "attack, damage, battle cry", 1: "armor class (armor may cap it)", 2: "hit points, for every level"}
    for c, h in hints.items():
        cur_to(g, c)
        check(row(g, 14)[3:3 + len(h)] == h, "hint for entry %d: %r" % (c, row(g, 14)))
    cur_to(g, 4)                                                        # cursor on undo: no hint
    check(row(g, 14)[3:38].strip() == "", "hint on an action: %r" % row(g, 14))
    at(g, 4); g.press_fire()                                            # undo
    for y in range(3, 7):
        check(L["CH_ARROW"] not in g.mem(addr(g, y), 40), "arrow left on row %d after undo: %r" % (y, row(g, y)))


@test("CS-15", "confirm asks 'spend 2 points for good?': no = keep editing, yes = spent and 'no points to spend.' if none left")
def cs_confirm(ctx):
    g = ctx["g"]; L = g.L
    at(g, 3); g.press_fire()                                            # confirm without pending points: refused
    check("no points." in row(g, 23) and g.mem(L["c_sadd"], 3) == [0, 0, 0], "row 23: %r" % row(g, 23))
    at(g, 0); key(g, K_PLUS, 1); key(g, K_PLUS, 1)
    at(g, 3); g.press_fire()
    check(row(g, 23)[1:25] == "spend 2 points for good?", "row 23: %r" % row(g, 23))
    key(g, K_N, 3)
    check(pend(g) == [2, 0, 0] and g.mem(L["c_sadd"], 3) == [0, 0, 0], "'no' changed something: %s" % pend(g))
    check(not g.in_game() and row(g, 23).strip() == "", "after 'no': row 23 %r" % row(g, 23))
    at(g, 2); key(g, K_PLUS, 1)                                         # still editable: con +1
    at(g, 3); g.press_fire()
    check(row(g, 23)[1:25] == "spend 3 points for good?", "row 23: %r" % row(g, 23))
    key(g, K_Y, 3)
    check(g.mem(L["c_sadd"], 3) == [2, 0, 1] and pend(g) == [0, 0, 0], "after yes: c_sadd %s" % g.mem(L["c_sadd"], 3))
    check(g.b(L["s_str"]) == L["PL_STR0"] + 2, "str %d" % g.b(L["s_str"]))
    check(row(g, 13)[3:22] == "no points to spend.", "row 13 after the confirmation: %r" % row(g, 13))
    back(g)


@test("CS-16", "RUN/STOP with pending points asks 'spend 1 point before leaving?': no = points given back, yes = spent")
def cs_leave(ctx):
    g = ctx["g"]; L = g.L
    lvl(g, 6, (1, 1, 0))                                                # 1 point to spend
    open_c(g)
    at(g, 1); g.press_fire()                                            # dex +1
    g.run_stop()
    check(row(g, 23)[1:30] == "spend 1 point before leaving?", "row 23: %r" % row(g, 23))
    key(g, K_N, 3)
    while not g.in_game(): g.frames(1, tmax=60)
    check(g.mem(L["c_sadd"], 3) == [1, 1, 0] and pend(g) == [0, 0, 0], "spent %s pending %s" % (g.mem(L["c_sadd"], 3), pend(g)))
    check(avail(g) == 1, "points to spend after leaving without spending: %d (expected 1)" % avail(g))
    open_c(g)
    check(row(g, 13)[3:20] == "points to spend 1", "the point is not back on the screen: %r" % row(g, 13))
    at(g, 1); g.press_fire()
    g.run_stop(); key(g, K_Y, 3)
    while not g.in_game(): g.frames(1, tmax=60)
    check(g.mem(L["c_sadd"], 3) == [1, 2, 0] and avail(g) == 0, "after yes: spent %s" % g.mem(L["c_sadd"], 3))
    open_c(g); back(g)                                                  # no pending points: RUN/STOP leaves at once
