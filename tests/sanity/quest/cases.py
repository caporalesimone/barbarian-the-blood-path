"""Quest concept (17/11, src/game/quest.asm, src/qpage.asm): the page of the quest (Q, Fire next to the quest giver), the NPCs of
the village. One VICE session, a new barbarian in the village."""
import os
from c64test import test, check
from lib.c64 import Game, OUT
from lib.play import new_game

CHAIN = True
SCR_A = 0xB400


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    ctx["L"], ctx["M"] = g.L, g.M


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def screen_text(g):
    """the UI screen as text (screen codes 1..26 = a..z)"""
    return "".join(chr(b + 96) if 1 <= b <= 26 else chr(b) if 32 <= b < 64 else " " for b in g.mem(SCR_A, 1000))


@test("QUEST-10", "village: the NPCs are placed (quest giver + walkers on free tiles)")
def npcs(ctx):
    g, L = ctx["g"], ctx["L"]
    new_game(g)
    g.frames(4)
    xh = g.mem(L["npc_xh"], 4)
    check(xh[0] != 0xff, "no quest giver (npc_xh %s)" % xh)
    check(sum(1 for b in xh if b != 0xff) >= 3, "fewer than 3 NPCs: %s" % xh)


@test("QUEST-11", "Q with no quest read: the page (file QST0) says 'no quest', RUN/STOP goes back to the game")
def page_none(ctx):
    g, L = ctx["g"], ctx["L"]
    g.frames(1, keys={7: 0x40}); g.frames(20)
    t = screen_text(g)
    g.screenshot(os.path.join(OUT, "quest_none.png"))
    check("no quest" in t, "no 'no quest' on the screen")
    g.frames(1, keys={7: 0x80}); g.frames(3)
    check(g.b(L["cur_level"]) == 0 and g.b(L["c_qst"]) == 0, "not back in the village")


@test("QUEST-12", "next to the quest giver: name in the bar, Fire = quest read (c_qst 1) and its page (giver, title, text)")
def page_quest(ctx):
    g, L = ctx["g"], ctx["L"]
    tx, ty = g.b(L["npc_tx0"]), g.b(L["npc_ty0"])
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
        if g.tile(tx + dx, ty + dy) not in (0xff,) and not (g.mem(L["solidtab"] + g.tile(tx + dx, ty + dy), 1)[0] & 1):
            break
    g.teleport(tx + dx, ty + dy); g.frames(6)
    check(g.b(L["bar_lab"]) == L["QL_ID"], "bar label %d (expected the quest giver %d)" % (g.b(L["bar_lab"]), L["QL_ID"]))
    g.screenshot(os.path.join(OUT, "quest_npc.png"))
    g.press_fire(); g.frames(20)
    t = screen_text(g)
    g.screenshot(os.path.join(OUT, "quest_page.png"))
    check(g.b(L["c_qst"]) == 1, "c_qst %d (expected 1)" % g.b(L["c_qst"]))
    check("hilde" in t and "widow" in t and "lorem ipsum" in t, "giver, title or text missing on the page")
    g.frames(1, keys={7: 0x80}); g.frames(3)


@test("QUEST-13", "the walkers move (slowly, the hero near) and never stand on the hero's tile")
def walkers(ctx):
    g, L = ctx["g"], ctx["L"]
    p0 = [g.mem(L["npc_xl"], 4), g.mem(L["npc_yl"], 4)]
    g.frames(400)
    p1 = [g.mem(L["npc_xl"], 4), g.mem(L["npc_yl"], 4)]
    moved = sum(1 for i in range(1, 4) if (p0[0][i], p0[1][i]) != (p1[0][i], p1[1][i]))
    check(moved >= 1, "no walker moved in 400 frames")
    check(g.mem(L["npc_xl"], 1) == p0[0][:1], "the quest giver moved")
