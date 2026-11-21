"""The Hollow Abbot (chapter 1 boss, level 5; 21/11, owner's request; src/game/ovl_boss1.asm): besides raising the dead (2/3,
1/3, OVP-11) under 30% of its life it rages: red border, faster attacks (attack recharge at most AB_RCD frames) and every
2 x AB_CD frames the censer: AB_WARN frames of white blinking, then the incense cloud takes 1/8 of the hero's max life if he is
within AB_R pixels. One VICE session (CHAIN)."""
import os
from c64test import test, check
from lib.c64 import Game, ROOT, labels
from lib.play import new_game

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def boss5(g):
    L = g.L
    g.poke(L["c_chap"], 1)
    g.call_keep(L["change_level"], regs="a=05,x=00", tmax=150); g.frames(3)
    check(g.b(L["ovp_ok"]) == 1, "level 5: ovp_ok %d" % g.b(L["ovp_ok"]))
    b = g.b(L["lb_boss"]) - 1
    check(b >= 0, "level 5: no boss")
    _, _, bx, by = g.mem(L["bm_hdr"], 4)
    return labels("ovl_boss1"), b, (bx, by)


def hpm(g, b):
    L = g.L
    return g.b(L["mhm"] + b) | g.b(L["mhmh"] + b) << 8


@test("BOSS1-10", "level 5: over 30% of its life the Abbot does not rage; under 30% it rages (red border, attack recharge <= AB_RCD)")
def rage(ctx):
    g = ctx["g"]; L = g.L
    O, b, (bx, by) = boss5(g)
    ctx["O"], ctx["b"], ctx["bxy"] = O, b, (bx, by)
    g.poke(L["godmode"], 1)
    g.teleport(bx, by + 6); g.frames(4)
    mx = hpm(g, b)
    v = mx * 32 // 100
    g.poke(L["mhp"] + b, v & 255); g.poke(L["mhph"] + b, v >> 8)
    g.frames(5)
    check(g.b(O["abx_rage"]) == 0, "rage at 32%% of its life (%d of %d)" % (v, mx))
    v = mx * 28 // 100
    g.poke(L["mhp"] + b, v & 255); g.poke(L["mhph"] + b, v >> 8)
    g.frames(5)
    check(g.b(O["abx_rage"]) == 1, "no rage at 28%% of its life")
    g.poke(L["mcd"] + b, 45); g.frames(2)
    check(g.b(L["mcd"] + b) <= O["AB_RCD"], "attack recharge %d (expected <= %d)" % (g.b(L["mcd"] + b), O["AB_RCD"]))


@test("BOSS1-11", "raging Abbot: the censer warns (white blinking) and then the cloud takes hpmax/8 from the hero next to it (far away: not checked, the boss walks)")
def censer(ctx):
    g = ctx["g"]; L = g.L
    O, b, (bx, by) = ctx["O"], ctx["b"], ctx["bxy"]
    g.poke(L["godmode"], 0)
    hpmax = g.w16(L["hpmax"])
    g.poke16(L["c_hp"], hpmax)
    g.poke(O["abx_w"], 0); g.poke(O["abx_cd"], 1)                 # the censer now
    for _ in range(4):
        g.frames(1)
        if g.b(O["abx_w"]): break
    check(g.b(O["abx_w"]) > 0, "no warning (abx_w %d, abx_cd %d)" % (g.b(O["abx_w"]), g.b(O["abx_cd"])))
    for _ in range(O["AB_WARN"] + 4):                          # a first censer goes by (life restored every frame)
        g.poke(L["mcd"] + b, 40)                                # (no melee hit during the test)
        g.poke16(L["c_hp"], hpmax)
        g.frames(1)
    # next to the boss: a second censer
    g.poke(O["abx_cd"], 1)
    for _ in range(4):
        g.frames(1)
        if g.b(O["abx_w"]): break
    for _ in range(O["AB_WARN"] - 2):
        g.poke(L["mcd"] + b, 40)
        bxs, bys = g.b(L["mxl"] + b) | g.b(L["mxh"] + b) << 8, g.b(L["myl"] + b) | g.b(L["myh"] + b) << 8
        g.poke16(L["px"], bxs + 16); g.poke16(L["py"], bys)
        g.poke16(L["c_hp"], hpmax)
        g.frames(1)
    for _ in range(6):
        g.poke(L["mcd"] + b, 40)
        g.frames(1)
        if g.w16(L["c_hp"]) < hpmax: break
    os.makedirs(os.path.join(ROOT, "out", "work", "ovp"), exist_ok=True)
    g.screenshot(os.path.join(ROOT, "out", "work", "ovp", "abbot_censer.png"))
    lost = hpmax - g.w16(L["c_hp"])
    check(lost == max(1, hpmax // 8), "cloud damage %d (expected hpmax/8 = %d)" % (lost, hpmax // 8))
    g.poke(L["godmode"], 1)
