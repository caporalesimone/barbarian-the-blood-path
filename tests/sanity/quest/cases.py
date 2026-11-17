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


NPC_N = 9           # the quest giver + one walker per sector (NSEC = 8, tools/build/gen_maps.py)


def npcs_now(g, L):
    """[(index, tx, ty)] of the NPCs that are in the village"""
    xl, xh, yl, yh = (g.mem(L[n], NPC_N) for n in ("npc_xl", "npc_xh", "npc_yl", "npc_yh"))
    return [(i, ((xh[i] << 8) | xl[i]) >> 4, ((yh[i] << 8) | yl[i]) >> 4) for i in range(NPC_N) if xh[i] != 0xff]


def sector(g, L, i):
    x, y, w, h = g.mem(L["tk_sec"] + 4 * (i - 1), 4)
    return x, y, w, h


def with_walkers(g, L):
    """walkers present at random (3/4 per sector): a new game until there is at least one (8 sectors: 1 time in 65536 there is none)"""
    for _ in range(6):
        w = [n for n in npcs_now(g, L) if n[0]]
        if w:
            return w
        new_game(g); g.frames(4)
    check(False, "no walker in 6 new games")


def inside(sec, tx, ty):
    x, y, w, h = sec
    return x <= tx < x + w and y <= ty < y + h


@test("QUEST-10", "village: the NPCs are placed (quest giver + at most one walker per sector, each inside its sector, on free tiles)")
def npcs(ctx):
    g, L = ctx["g"], ctx["L"]
    new_game(g)
    g.frames(4)
    now = npcs_now(g, L)
    check(now and now[0][0] == 0, "no quest giver: %s" % now)
    for i, tx, ty in now:
        check(g.tile(tx, ty) != 0xff and not (g.mem(L["solidtab"] + g.tile(tx, ty), 1)[0] & 1), "NPC %d on a solid tile (%d,%d)" % (i, tx, ty))
        if i:
            check(inside(sector(g, L, i), tx, ty), "walker %d (%d,%d) outside its sector %s" % (i, tx, ty, sector(g, L, i)))
    ctx["now"] = now


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


@test("QUEST-13", "the walkers move (slowly, the hero near), stay inside their sector and never stand on the hero's tile")
def walkers(ctx):
    g, L = ctx["g"], ctx["L"]
    walk = with_walkers(g, L)
    i, tx, ty = walk[0]
    sec = sector(g, L, i)
    # the hero next to the walker (any free neighbour tile)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
        if g.tile(tx + dx, ty + dy) != 0xff and not (g.mem(L["solidtab"] + g.tile(tx + dx, ty + dy), 1)[0] & 1):
            break
    g.teleport(tx + dx, ty + dy); g.frames(6)
    seen = {(tx, ty)}
    for _ in range(40):
        g.frames(20)
        now = {n[0]: n for n in npcs_now(g, L)}
        check(i in now, "walker %d disappeared" % i)
        _, wx, wy = now[i]
        check(inside(sec, wx, wy), "walker %d left its sector %s: (%d,%d)" % (i, sec, wx, wy))
        check((wx, wy) != (g.b(L["ptx"]), g.b(L["pty"])), "walker %d on the hero's tile" % i)
        seen.add((wx, wy))
    check(len(seen) > 1, "walker %d did not move in 800 frames with the hero next to it" % i)
    check(npcs_now(g, L)[0][1:] == (g.b(L["npc_tx0"]), g.b(L["npc_ty0"])), "the quest giver moved")


@test("QUEST-14", "the visible NPCs get the free sprites 3..7 (never the hero's, never more than 5)")
def sprites(ctx):
    g, L = ctx["g"], ctx["L"]
    with_walkers(g, L)
    now = npcs_now(g, L)
    for i, tx, ty in now[:6]:
        g.teleport(tx, ty + 1 if g.tile(tx, ty + 1) != 0xff and not (g.mem(L["solidtab"] + g.tile(tx, ty + 1), 1)[0] & 1) else ty - 1); g.frames(4)
        en = g.b(L["sh_en"])
        cx = g.b(L["camx"]) | (g.b(L["camx"] + 1) << 8)
        cy = g.b(L["camy"]) | (g.b(L["camy"] + 1) << 8)
        near = [n for n in npcs_now(g, L) if cx + 16 <= n[1] * 16 + 8 <= cx + 300 and cy + 16 <= n[2] * 16 + 8 <= cy + 176]
        n_on = bin(en & 0xF8).count("1")
        check(en & 0x06 == 0, "sprites 1/2 on in the village: %02x" % en)
        check(n_on >= min(len(near), 5), "%d NPCs well inside the screen but %d sprites (sh_en %02x)" % (len(near), n_on, en))
