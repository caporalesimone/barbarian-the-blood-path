"""Quest concept (17/11, src/game/quest.asm, src/qpage.asm, src/menu/npc.asm): the NPCs of the village; (18/11) several quests
taken together: the list (Q) and the detail of a quest (title, chapter, yellow status placeholder, text that scrolls, reward),
the "!" over who has a quest to give, walkers that offer a quest ("quest giver") and stop with the hero near, the attack cadence
from DEX. One VICE session, a new barbarian in the village."""
import os
from c64test import test, check
from lib.c64 import Game, OUT
from lib.play import new_game, D

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


NPC_N = 17          # the quest giver + one walker per sector (NSEC = 16, tools/build/gen_maps.py)


def npcs_now(g, L):
    """[(index, tx, ty)] of the NPCs that are in the village"""
    xl, xh, yl, yh = (g.mem(L[n], NPC_N) for n in ("npc_xl", "npc_xh", "npc_yl", "npc_yh"))
    return [(i, ((xh[i] << 8) | xl[i]) >> 4, ((yh[i] << 8) | yl[i]) >> 4) for i in range(NPC_N) if xh[i] != 0xff]


def sector(g, L, i):
    x, y, w, h = g.mem(L["tk_sec"] + 4 * (i - 1), 4)
    return x, y, w, h


def with_walkers(g, L):
    """walkers present at random (7/8 per sector): a new game until there is at least one (16 sectors: practically always)"""
    for _ in range(6):
        w = [n for n in npcs_now(g, L) if n[0]]
        if w:
            return w
        new_game(g); g.frames(4)
    check(False, "no walker in 6 new games")


COLRAM = 0xD800
BANG_PTR = 0x30     # sprite of the "!" ($8C00, zone 5 of the MENU module)


def free(g, L, tx, ty):
    return g.tile(tx, ty) != 0xff and not (g.mem(L["solidtab"] + g.tile(tx, ty), 1)[0] & 1)


def next_to(g, L, tx, ty, dist=1):
    """a free tile at distance dist (on one axis, or diagonal for 1) from (tx, ty)"""
    for dx, dy in ((dist, 0), (-dist, 0), (0, dist), (0, -dist), (dist, dist), (-dist, -dist), (dist, -dist), (-dist, dist)):
        if free(g, L, tx + dx, ty + dy):
            return tx + dx, ty + dy
    check(False, "no free tile at distance %d from (%d,%d)" % (dist, tx, ty))


def bangs(g, L):
    """[(sprite, x, y)] of the "!" on (sprites 1-2 with the pointer of the "!")"""
    en = g.b(L["sh_en"])
    return [(s, g.b(L["sh_x"] + s), g.b(L["sh_y"] + s)) for s in (1, 2) if en & (1 << s) and g.b(L["sh_ptr"] + s) == BANG_PTR]


def npc_sprite(g, L, i):
    """(x, y) of the sprite of NPC i if it is drawn (pointer of its design, colour npc_c)"""
    en = g.b(L["sh_en"])
    g_, c = g.b(L["npc_g"] + i), g.b(L["npc_c"] + i)
    for s in range(3, 8):
        if en & (1 << s) and (g.b(L["sh_ptr"] + s) - 0x8C) // 2 == g_ and g.b(L["sh_col"] + s) & 15 == c:
            return g.b(L["sh_x"] + s), g.b(L["sh_y"] + s)
    return None


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
    check(now[0][1:] == tuple(g.mem(L["tk_g"], 2)), "the quest giver is not on its tile of the fountain square (tk_g %s): %s" % (list(g.mem(L["tk_g"], 2)), now[0]))
    for i, tx, ty in now:
        check(g.tile(tx, ty) != 0xff and not (g.mem(L["solidtab"] + g.tile(tx, ty), 1)[0] & 1), "NPC %d on a solid tile (%d,%d)" % (i, tx, ty))
        if i:
            check(inside(sector(g, L, i), tx, ty), "walker %d (%d,%d) outside its sector %s" % (i, tx, ty, sector(g, L, i)))
    q = g.mem(L["npc_q"], NPC_N)
    check(q[0] == 0, "hilde (22/11: QGIV, nothing before step 1) has a mark: npc_q %s" % q)
    given = [q[i] for i, _, _ in now if i and q[i] and q[i] < 0x80]
    check(len(given) == len(set(given)) and all(2 <= x <= L["Q_N"] for x in given), "walkers' quests wrong or repeated: %s" % given)
    ctx["now"] = now


@test("QUEST-11", "Q with no quest taken: the list (file QST0) says 'talk to the villagers', RUN/STOP goes back to the game")
def page_none(ctx):
    g, L = ctx["g"], ctx["L"]
    g.frames(1, keys={7: 0x40}); g.frames(20)
    t = screen_text(g)
    g.screenshot(os.path.join(OUT, "quest_none.png"))
    check("quests" in t and "talk to the villagers" in t, "no empty list on the screen")
    g.frames(1, keys={7: 0x80}); g.frames(3)
    check(g.b(L["cur_level"]) == 0 and g.b(L["c_qst"]) == 0, "not back in the village")


@test("QUEST-12", "Hilde: name in the bar next to her (22/11: Fire opens the quest module QGIV, tests/sanity/qgiv); concept quest 1 marked taken for the list tests below")
def page_quest(ctx):
    g, L = ctx["g"], ctx["L"]
    tx, ty = g.b(L["npc_tx0"]), g.b(L["npc_ty0"])
    g.teleport(*next_to(g, L, tx, ty)); g.frames(20)
    check(g.b(L["bar_lab"]) == L["QL_ID"], "bar label %d (expected the quest giver %d)" % (g.b(L["bar_lab"]), L["QL_ID"]))
    g.screenshot(os.path.join(OUT, "quest_npc.png"))
    g.poke(L["c_qst"], g.b(L["c_qst"]) | 1)


@test("QUEST-13", "the walkers move (slowly, the hero 4 tiles away), stay inside their sector, never stand on the hero's tile; with the hero next to them they stop")
def walkers(ctx):
    g, L = ctx["g"], ctx["L"]
    walk = with_walkers(g, L)
    i, tx, ty = walk[0]
    sec = sector(g, L, i)
    g.teleport(*next_to(g, L, tx, ty, 4)); g.frames(6)
    seen = {(tx, ty)}
    for _ in range(40):
        g.frames(20)
        now = {n[0]: n for n in npcs_now(g, L)}
        check(i in now, "walker %d disappeared" % i)
        _, wx, wy = now[i]
        check(inside(sec, wx, wy), "walker %d left its sector %s: (%d,%d)" % (i, sec, wx, wy))
        check((wx, wy) != (g.b(L["ptx"]), g.b(L["pty"])), "walker %d on the hero's tile" % i)
        seen.add((wx, wy))
        if len(seen) > 1: break
    check(len(seen) > 1, "walker %d did not move in 800 frames with the hero 4 tiles away" % i)
    check(npcs_now(g, L)[0][1:] == (g.b(L["npc_tx0"]), g.b(L["npc_ty0"])), "the quest giver moved")
    _, wx, wy = {n[0]: n for n in npcs_now(g, L)}[i]
    g.teleport(*next_to(g, L, wx, wy)); g.frames(20)
    _, wx, wy = {n[0]: n for n in npcs_now(g, L)}[i]
    for _ in range(20):
        g.frames(20)
        check({n[0]: n for n in npcs_now(g, L)}[i][1:] == (wx, wy), "walker %d moved with the hero next to it" % i)


@test("QUEST-14", "the visible NPCs get the free sprites 3..7 (never the hero's, never more than 5)")
def sprites(ctx):
    g, L = ctx["g"], ctx["L"]
    with_walkers(g, L)
    now = npcs_now(g, L)
    for i, tx, ty in now[:6]:
        g.teleport(tx, ty + 1 if g.tile(tx, ty + 1) != 0xff and not (g.mem(L["solidtab"] + g.tile(tx, ty + 1), 1)[0] & 1) else ty - 1); g.frames(14)
        en = g.b(L["sh_en"])
        cx = g.b(L["camx"]) | (g.b(L["camx"] + 1) << 8)
        cy = g.b(L["camy"]) | (g.b(L["camy"] + 1) << 8)
        near = [n for n in npcs_now(g, L) if cx + 16 <= n[1] * 16 + 8 <= cx + 300 and cy + 24 <= n[2] * 16 + 8 <= cy + 150]
        n_on = bin(en & 0xF8).count("1")
        check(all(g.b(L["sh_ptr"] + k) == BANG_PTR for k in (1, 2) if en & (1 << k)), "sprites 1/2 on in the village, not as '!': %02x" % en)
        check(n_on >= min(len(near), 5), "%d NPCs well inside the screen but %d sprites (sh_en %02x)" % (len(near), n_on, en))


@test("QUEST-15", "a walker with a quest ('quest giver' in the bar, '!'): Fire = quest taken, the walker gives it no more; long text scrolls with S; the list has 2 quests")
def walker_quest(ctx):
    g, L = ctx["g"], ctx["L"]
    i, tx, ty = with_walkers(g, L)[0]
    c = g.b(L["c_qst"]) & ~2
    g.poke(L["c_qst"], c); g.poke(L["npc_q"] + i, 2)
    g.teleport(*next_to(g, L, tx, ty)); g.frames(20)
    _, tx, ty = {n[0]: n for n in npcs_now(g, L)}[i]
    g.teleport(*next_to(g, L, tx, ty)); g.frames(36)
    check(g.b(L["bar_lab"]) == L["QL_GV"], "bar label %d (expected 'quest giver' %d)" % (g.b(L["bar_lab"]), L["QL_GV"]))
    ws = npc_sprite(g, L, i)
    check(ws is not None and [x for x in bangs(g, L) if x[1] == ws[0] and x[2] < ws[1]], "no '!' over the walker %d" % i)
    g.screenshot(os.path.join(OUT, "quest_giver.png"))
    g.press_fire(); g.frames(25)
    check(g.b(L["c_qst"]) & 2, "quest 2 not taken: c_qst %02x" % g.b(L["c_qst"]))
    check(g.b(L["npc_q"] + i) == 0, "the walker still offers a quest")
    t = screen_text(g)
    check("rats in the cellar" in t and " more " in t, "detail of quest 2 without its title or without ' more '")
    first = t[5 * 40:6 * 40]
    for _ in range(3):
        g.frames(1, joy=D); g.frames(2)
    t = screen_text(g)
    g.screenshot(os.path.join(OUT, "quest_scroll.png"))
    check(t[5 * 40:6 * 40] != first and " up " in t, "the text did not scroll down")
    g.run_stop(); g.frames(4)
    t = screen_text(g)
    check("the widow's son" in t and "rats in the cellar" in t, "the list does not show 2 quests")
    g.run_stop(); g.frames(20)
    check(g.in_game(), "not back in the game")


@test("QUEST-16", "attack cadence (s_rate): weapon + max(0, slow - per_dex x mod DEX): new hero (dagger, DEX 13) slower, DEX 18 = the weapon's")
def cadence(ctx):
    g, L = ctx["g"], ctx["L"]
    import yaml
    from lib.c64 import ROOT
    a = yaml.safe_load(open(os.path.join(ROOT, "data", "rules.yaml")))["player"]["attack_speed"]
    w = g.b(L["itrate"] + g.b(L["c_eq"]))
    sad = g.b(L["c_sadd"] + 1)
    g.call_keep(L["recalc_stats"])
    dex = g.b(L["s_dex"])
    exp = w + max(0, a["slow"] - a["per_dex"] * ((dex - 10) // 2))
    check(g.b(L["s_rate"]) == exp, "s_rate %d, expected %d (weapon %d, DEX %d)" % (g.b(L["s_rate"]), exp, w, dex))
    g.poke(L["c_sadd"] + 1, sad + 18 - dex)
    g.call_keep(L["recalc_stats"])
    check(g.b(L["s_dex"]) == 18 and g.b(L["s_rate"]) == w, "DEX %d: s_rate %d, expected the weapon's %d" % (g.b(L["s_dex"]), g.b(L["s_rate"]), w))
    g.poke(L["c_sadd"] + 1, sad)
    g.call_keep(L["recalc_stats"])
