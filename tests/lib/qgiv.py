"""Helpers of the quest module QGIV (src/qgiv.asm): talk to a fixed NPC of the village, read the screen, close
(tests/regression/qgiv, tests/sanity/qreward)."""
import os
from c64test import check
from lib.c64 import OUT

SCR_A = 0xB400
NPC_N = 17


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
