"""Fixed quest-giver NPCs (21/11, owner's request; src/menu/npc_here.asm npc_fix, tools/build/gen_maps.py fixed,
tools/build/villages.py FIXED): every village has its fixed NPCs (Aldric's Hollow: hilde in the square, father osric near the
church, grom near the smithy, the gravedigger near the crypt); each one takes the place of the walker of its sector, never moves,
and shows its name in the bar. One VICE session, a new barbarian in village 1."""
import os
from c64test import test, check
from lib.c64 import Game, OUT
from lib.play import new_game

CHAIN = True
NPC_N = 17          # NPC 0 (the square) + one per sector (NSEC = 16)
NFIX = 3
NAMES = ["hilde", "father osric", "grom", "the gravedigger"]   # tools/build/villages.py FIXED[1]


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    ctx["L"] = g.L


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def npcs_now(g, L):
    xl, xh, yl, yh = (g.mem(L[n], NPC_N) for n in ("npc_xl", "npc_xh", "npc_yl", "npc_yh"))
    return {i: (((xh[i] << 8) | xl[i]) >> 4, ((yh[i] << 8) | yl[i]) >> 4) for i in range(NPC_N) if xh[i] != 0xff}


def fixed_spec(g, L):
    """[(npc, tx, ty, design)] from the village header (tk_fix: sector | design << 5, (x - x0) | (y - y0) << 4)"""
    out = []
    raw = g.mem(L["tk_fix"], 2 * NFIX)
    for k in range(NFIX):
        a, b = raw[2 * k], raw[2 * k + 1]
        if not a:
            continue
        s = a & 31
        x0, y0 = g.mem(L["tk_sec"] + 4 * (s - 1), 2)
        out.append((s, x0 + (b & 15), y0 + (b >> 4), a >> 5))
    return out


def text_at(g, addr):
    """a 0-terminated screen-code string in memory"""
    s = ""
    while True:
        c = g.b(addr + len(s))
        if c == 0 or len(s) > 20:
            return s
        s += chr(c + 96) if 1 <= c <= 26 else chr(c)


@test("NPCFIX-10", "village 1: the fixed NPCs are on their tiles (header tk_fix), with their design, still, npc_q = the D12 mark (0, $85, $87); nobody else in their sectors")
def placed(ctx):
    g, L = ctx["g"], ctx["L"]
    new_game(g)
    g.frames(4)
    spec = fixed_spec(g, L)
    check(len(spec) == NFIX, "village 1 has %d fixed NPCs in the header (expected %d): %s" % (len(spec), NFIX, spec))
    now = npcs_now(g, L)
    d, q, gg = g.mem(L["npc_d"], NPC_N), g.mem(L["npc_q"], NPC_N), g.mem(L["npc_g"], NPC_N)
    for k, (i, tx, ty, look) in enumerate(spec, 1):
        check(now.get(i) == (tx, ty), "fixed NPC %d (%s) at %s, expected (%d,%d)" % (i, NAMES[k], now.get(i), tx, ty))
        check(d[i] == 0x80 | k << 4 and q[i] in (0, 0x85, 0x87) and gg[i] == look, "NPC %d: npc_d %02x npc_q %d design %d" % (i, d[i], q[i], gg[i]))
    check(d[0] == 0x80 and q[0] == 0, "NPC 0 (hilde, nothing before step 1, D12): npc_d %02x npc_q %d" % (d[0], q[0]))
    ctx["spec"], ctx["now"] = spec, now
    g.frames(300)                                               # walkers move; the fixed ones never
    later = npcs_now(g, L)
    for i, tx, ty, _ in spec:
        check(later.get(i) == (tx, ty), "fixed NPC %d moved to %s" % (i, later.get(i)))


@test("NPCFIX-11", "next to each fixed NPC the bar shows its name (22/11: Fire opens the quest module QGIV, tests/sanity/qgiv)")
def names(ctx):
    g, L = ctx["g"], ctx["L"]
    for k, (i, tx, ty, _) in enumerate(ctx["spec"], 1):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
            t = g.tile(tx + dx, ty + dy)
            if t != 0xff and not (g.b(L["solidtab"] + t) & 1):
                break
        g.teleport(tx + dx, ty + dy); g.frames(20)
        check(g.b(L["bar_lab"]) == L["QL_ID"], "%s: bar label %d (expected %d)" % (NAMES[k], g.b(L["bar_lab"]), L["QL_ID"]))
        ptr = g.b(L["loc_lo"] + L["QL_ID"]) | g.b(L["loc_hi"] + L["QL_ID"]) << 8
        check(text_at(g, ptr) == NAMES[k], "name %r (expected %r)" % (text_at(g, ptr), NAMES[k]))
        if k == 1:
            g.screenshot(os.path.join(OUT, "npc_fixed.png"))
