"""Village module of the quests (22/11, owner's decisions D3, D13, D18; src/qgiv.asm, file "qstg" at CORE_AT, texts QTXc at
QTX): Fire next to a fixed NPC of the village (k of villages.FIXED: 0 hilde, 1 father osric, 2 grom, 3 the gravedigger) gives
or takes back its quest. One VICE session, a new barbarian in the village of chapter 1; the steps follow each other."""
import os
from c64test import test, check
from lib.c64 import Game, OUT
from lib.play import new_game, key, K_M, D

CHAIN = True
SCR_A = 0xB400
NPC_N = 17


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(4)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def screen_text(g):
    return "".join(chr(b + 96) if 1 <= b <= 26 else chr(b) if 32 <= b < 64 else " " for b in g.mem(SCR_A, 1000))


def free(g, L, tx, ty):
    return g.tile(tx, ty) != 0xff and not (g.mem(L["solidtab"] + g.tile(tx, ty), 1)[0] & 1)


def talk(g, k, shot=None):
    """teleport next to the fixed NPC k, Fire: the screen of QGIV as text (then Fire again: back in the village)"""
    L = g.L
    d = g.mem(L["npc_d"], NPC_N)
    i = next(i for i in range(NPC_N) if d[i] & 0x80 and (d[i] >> 4) & 3 == k and g.b(L["npc_xh"] + i) != 0xff)
    x = ((g.b(L["npc_xh"] + i) << 8) | g.b(L["npc_xl"] + i)) >> 4
    y = ((g.b(L["npc_yh"] + i) << 8) | g.b(L["npc_yl"] + i)) >> 4
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        if free(g, L, x + dx, y + dy):
            break
    g.teleport(x + dx, y + dy); g.frames(10)
    g.press_fire()
    t = wait_screen(g)
    if shot:
        g.screenshot(os.path.join(OUT, shot))
    return t


def wait_screen(g, n=60):
    """frames until the disk wait screen ('please wait') is gone and the module has drawn (at most n x 10 frames)"""
    for _ in range(n):
        g.frames(10)
        t = screen_text(g)
        if "please wait" not in t and t.strip():
            g.frames(5)
            return screen_text(g)
    return screen_text(g)


def close(g):
    g.press_fire()
    for _ in range(60):
        g.frames(10)
        if g.in_game():
            break
    check(g.b(g.L["cur_level"]) == 0 and g.in_game(), "not back in the village")


@test("QGIV-10", "father osric (k 1): step 1 taken at once (q_flag 1), its title, the yellow goal 'slay the fallen: 0/8', the text and the reward on screen; hilde (k 0): nothing yet; (22/11) text with a blank row between lines, scroll bar on column 39 (CH_THUMB), S scrolls one line")
def qg_offer(ctx):
    g = ctx["g"]; L = g.L
    t = talk(g, 0)
    check("nothing for you now" in t, "hilde has something before step 1: %r" % t[400:480])
    close(g)
    t = talk(g, 1, "qgiv_offer.png")
    check(g.b(L["q_flag"]) == 1 and g.b(L["q_step"]) == 0, "q_flag %d q_step %d" % (g.b(L["q_flag"]), g.b(L["q_step"])))
    check("a sword for the crypt" in t and "slay the fallen: 0/8" in t and "the crypt door stands open" in t and "reward: 120 gold" in t,
          "screen: %r" % t[:200])
    row = lambda r: t[r * 40 + 1:r * 40 + 38]
    check(row(5).strip() and not row(6).strip() and row(7).strip(), "no blank row between the text lines: %r / %r / %r" % (row(5), row(6), row(7)))
    bar = [g.b(SCR_A + r * 40 + 39) for r in range(5, 17)]
    check(bar[0] == 78 and 30 in bar, "scroll bar on column 39: %s" % bar)
    l2 = row(7).strip()
    g.frames(1, joy=D); g.frames(2)
    t2 = screen_text(g)
    check(t2[5 * 40 + 1:5 * 40 + 38].strip() == l2, "S: the second line does not go up (%r, expected %r)" % (t2[5 * 40 + 1:5 * 40 + 38], l2))
    close(g)


@test("QGIV-11", "step 1 reached (8 fallen): father osric takes it back: +120 gold, osric's cudgel in the pack, q_step 1, purse step (q_flag $10), the 'done' text")
def qg_turnin(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["q_flag"], 3); g.poke(L["q_cnt"], 8)
    g0 = g.w16(L["c_gold"])
    t = talk(g, 1, "qgiv_done.png")
    check(g.b(L["q_step"]) == 1 and g.b(L["q_flag"]) == 0x10 and g.b(L["q_cnt"]) == 0, "state %s" % g.mem(L["q_step"], 3))
    check(g.w16(L["c_gold"]) == g0 + 120, "gold %d -> %d" % (g0, g.w16(L["c_gold"])))
    p, s = g.mem(L["c_pack"], 8), g.mem(L["c_packs"], 8)
    check(0x80 in s and p[s.index(0x80)] == g.b(L["un_base"]), "osric's cudgel not in the pack: %s %s" % (p, s))
    check("eight less to drag us down" in t and "reward:" in t, "done text missing")
    close(g)


@test("QGIV-12", "hilde gives step 2 (the amulet, from father osric); grom gives a1.1 (side, q_side slot 0 = id 1) after step 1 of the chapter")
def qg_side(ctx):
    g = ctx["g"]; L = g.L
    t = talk(g, 0)
    check(g.b(L["q_flag"]) & 1 and "the widow's son" in t, "step 2 not taken: flag %d" % g.b(L["q_flag"]))
    close(g)
    t = talk(g, 2)
    check(g.mem(L["q_side"], 2) == [1, 0] and "grom's old hammer" in t, "q_side %s" % g.mem(L["q_side"], 8))
    close(g)


@test("QGIV-13", "a1.1 reached, back to grom: a magic sword; then a1.2 (G: 300 gold) offered; Fire again: 'give 300 gold?' yes -> -300 gold, the gravedigger, q_sdone bits 0-1")
def qg_gold(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["q_side"], 0x81, 1)
    talk(g, 2); close(g)
    check(g.b(L["q_sdone"]) == 1 and g.mem(L["q_side"], 2) == [0, 0], "a1.1 not delivered: q_sdone %d q_side %s" % (g.b(L["q_sdone"]), g.mem(L["q_side"], 2)))
    check(L["I_SWORD"] in g.mem(L["c_pack"], 8), "no sword in the pack: %s" % g.mem(L["c_pack"], 8))
    t = talk(g, 2); close(g)
    check(g.mem(L["q_side"], 2) == [2, 0] and "iron for the forge" in t, "a1.2 not taken: %s" % g.mem(L["q_side"], 2))
    g.poke16(L["c_gold"], 400)
    t = talk(g, 2)
    check("give 300 gold" in t, "no question: %r" % t[400:480])
    g.press_fire(); t = wait_screen(g)
    check(g.w16(L["c_gold"]) == 100 and g.b(L["q_sdone"]) == 3, "gold %d q_sdone %d" % (g.w16(L["c_gold"]), g.b(L["q_sdone"])))
    u = next(i for i, l in enumerate(open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "items", "next", "uniques.tsv"))) if l.startswith("gravedigger")) - 1
    check(0x80 + u in g.mem(L["c_packs"], 8), "the gravedigger not in the pack: %s" % g.mem(L["c_packs"], 8))
    close(g)


@test("QGIV-14", "Q12: pack full, step 2 reached: father osric says 'no room' and the step stays to be taken back (q_step 1, q_flag bit 1)")
def qg_full(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["q_flag"], 0x13); g.poke(L["q_cnt"], 1)
    g.poke(L["c_pack"], *([L["I_DAGGER"]] * 8))
    t = talk(g, 1)
    check("no room" in t, "no message: %r" % t[400:480])
    check(g.b(L["q_step"]) == 1 and g.b(L["q_flag"]) == 0x13, "state changed: %s" % g.mem(L["q_step"], 3))
    close(g)


def fixed_index(g, k):
    L = g.L
    d = g.mem(L["npc_d"], NPC_N)
    return next(i for i in range(NPC_N) if d[i] & 0x80 and (d[i] >> 4) & 3 == k and g.b(L["npc_xh"] + i) != 0xff)


@test("QGIV-15", "D12, marks of the fixed NPCs (q_marks, npc_q): yellow $87 who has a quest to give, green $85 who takes one back, 0 nobody; the '!' sprite has that colour")
def qg_marks(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_pack"], 0, 0, 0, 0, 0, 0, 0, 0)
    g.poke(L["q_step"], 1, 0x13, 1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0)     # step 2 reached (to osric); a1.1, a1.2 done
    g.call_keep(L["MENU_QMARK"])
    q = [g.b(L["npc_q"] + fixed_index(g, k)) for k in range(4)]
    check(q == [0, 0x85, 0, 0x87], "npc_q of hilde, osric, grom, gravedigger: %s (expected 0, $85, 0, $87)" % [hex(x) for x in q])
    i = fixed_index(g, 1)
    x = ((g.b(L["npc_xh"] + i) << 8) | g.b(L["npc_xl"] + i)) >> 4
    y = ((g.b(L["npc_yh"] + i) << 8) | g.b(L["npc_yl"] + i)) >> 4
    g.teleport(x - 3 if free(g, L, x - 3, y) else x + 3, y)
    cols = set()
    for _ in range(12):
        g.frames(3)
        en = g.b(L["sh_en"])
        cols |= {g.b(L["sh_col"] + s) & 15 for s in (1, 2) if en & (1 << s) and g.b(L["sh_ptr"] + s) == 0x30}
    g.screenshot(os.path.join(OUT, "qgiv_marks.png"))
    check(5 in cols and 7 not in cols, "colours of the '!': %s (expected green 5, and white 1 when up)" % sorted(cols))


@test("QGIV-18", "town minimap (M): a '!' over each fixed NPC with a mark (sprites 3..5 = k 1..3, mm_qmark): osric green, the gravedigger yellow, grom none; glyph block MG_B+3 (mq_gl, double size), x = 82 + 4 col, y = 34 + 4 row")
def qg_minimap(ctx):
    g = ctx["g"]; L = g.L
    key(g, K_M, 3)
    check(not g.in_game(), "the minimap does not open")
    g.watch(until=(L["mm_wait"],)); g.frames(2); g.unwatch()        # after mm_icons, before the text group
    g.screenshot(os.path.join(OUT, "qgiv_minimap.png"))
    en, msb = g.b(0xd015), g.b(0xd010)
    why = []
    for k, col in ((1, 5), (2, None), (3, 7)):
        s = 2 + k
        if col is None:
            if en & (1 << s): why.append("sprite %d on (k %d has no mark)" % (s, k))
            continue
        i = fixed_index(g, k)
        tx = ((g.b(L["npc_xh"] + i) << 8) | g.b(L["npc_xl"] + i)) >> 4
        ty = ((g.b(L["npc_yh"] + i) << 8) | g.b(L["npc_yl"] + i)) >> 4
        sx = g.b(0xd000 + 2 * s) + (256 if msb & (1 << s) else 0)
        sy = g.b(0xd001 + 2 * s)
        got = (bool(en & (1 << s)), g.b(0xd027 + s) & 15, sx, sy, g.b(L["SCR_A"] + 0x3f8 + s))
        exp = (True, col, 82 + 4 * tx, 34 + 4 * ty, 0xc3)
        if got != exp: why.append("k %d: on/colour/x/y/pointer %s, expected %s" % (k, got, exp))
    if list(g.mem(0xb0c0, 24)[0::3]) != [0x18] * 5 + [0, 0x18, 0]: why.append("no wide '!' glyph in block $B0C0")
    if g.b(0xd01d) & g.b(0xd017) & 0x28 != 0x28: why.append("the '!' sprites are not double size")
    g.run_stop(); g.frames(3)
    check(not why and g.in_game(), "; ".join(why) or "RUN/STOP does not close the minimap")


@test("QGIV-16", "page Q (key Q, module QGIV with q_k $ff): step 2 and the side a1.3 taken -> 2 rows with their titles; Fire on the first: its text and the goal; RUN/STOP back")
def qg_page(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["q_step"], 1, 0x11, 0, 3, 0, 3, 0, 0, 0, 0, 0, 0, 0)       # step 2 taken; a1.3 (id 3) taken
    g.frames(1, keys={7: 0x40})
    t = wait_screen(g)
    g.screenshot(os.path.join(OUT, "qgiv_page.png"))
    check("quests" in t and "the widow's son" in t and "a name on the stone" in t, "list: %r" % t[:400])
    g.press_fire(); t = wait_screen(g)
    check("find tam's amulet on level 3" in t and "my son tam" in t, "detail: %r" % t[:300])
    g.run_stop(); g.frames(10)
    g.run_stop()
    for _ in range(40):
        g.frames(10)
        if g.in_game():
            break
    check(g.in_game(), "not back in the game")


@test("QGIV-17", "page Q in a dungeon (level 1, no MENU module): the list, RUN/STOP back in the game; the stairs down still work (theme and CORE read again)")
def qg_page_dungeon(ctx):
    from lib.play import go_level
    g = ctx["g"]; L = g.L
    go_level(g, 1); g.frames(10)
    g.frames(1, keys={7: 0x40})
    t = wait_screen(g)
    check("the widow's son" in t, "list in the dungeon: %r" % t[:300])
    g.run_stop()
    for _ in range(40):
        g.frames(10)
        if g.in_game():
            break
    check(g.in_game() and g.b(L["cur_level"]) == 1, "not back on level 1")
    go_level(g, 2); g.frames(10)
    check(g.b(L["cur_level"]) == 2 and g.in_game(), "stairs to level 2 after the page")
