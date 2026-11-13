"""C screen without points to spend (12/11, committente, src/game/charsheet.asm): no menu entries, the sentence
"no points to spend.", RUN/STOP goes back. With a respec token the only entry is "respec" (my exception, to be
confirmed: otherwise a respec could never be used once all the points are spent). One VICE session, the village."""
from lib.c64 import Game
from lib.runner import test, check
from lib.play import new_game, key, K_Y

CHAIN = True
K_C = (2, 0x10)


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    L = g.L
    g.poke(L["c_lvl"], 6); g.poke(L["c_sadd"], 1, 2, 0)          # level 6: 3 points, all spent
    g.call_keep(L["recalc_stats"]); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def row(g, y):
    """text of a UI row (screen codes: letters 1-26, '>' $3e)"""
    L = g.L
    a = g.b(L["scrrow_lo"] + y) | g.b(L["scrrow_hi"] + y) << 8
    return "".join(chr(c + 96) if 1 <= c <= 26 else chr(c) if 32 <= c < 64 else "." for c in g.mem(a, 40))


def back(g):
    g.run_stop(); g.frames(3)
    while not g.in_game(): g.frames(1, tmax=60)


@test("CS-10", "no points, no respec token: no entries (no '>'), 'no points to spend.', RUN/STOP back to the game")
def cs_view(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_resp"], 0)
    key(g, K_C, 3)
    rows = [row(g, y) for y in range(8, 20)]
    check(not any(">" in r for r in rows), "an entry cursor is shown: %s" % [r for r in rows if ">" in r])
    check("no points to spend." in row(g, 18), "row 18: %r" % row(g, 18))
    check("confirm" not in "".join(rows) and "respec" not in row(g, 16), "menu entries shown")
    g.press_fire(); g.frames(2)
    check(not g.in_game() and g.mem(L["c_sadd"], 3) == [1, 2, 0], "fire changed something")
    back(g)
    check(g.in_game(), "RUN/STOP did not go back")


@test("CS-11", "no points, 1 respec token: only 'respec' (cursor on row 16); fire + yes: points back, all the entries again")
def cs_respec(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_resp"], 1)
    key(g, K_C, 3)
    check(row(g, 16)[2:10] == ">.respec".replace(".", " "), "row 16: %r" % row(g, 16))
    g.press_fire(); key(g, K_Y, 3)
    check(g.mem(L["c_sadd"], 3) == [0, 0, 0] and g.b(L["c_resp"]) == 0, "respec not done: %s" % g.mem(L["c_sadd"], 3))
    check("confirm" in row(g, 16) and "no points" not in row(g, 18), "after the respec the full menu is not back: %r" % row(g, 16))
    back(g)
