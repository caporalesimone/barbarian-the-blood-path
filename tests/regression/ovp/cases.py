"""Level code (19/11, docs/wiki/dungeon.md "Codice del piano"): code needed by one kind of level only travels in the tail of
the theme file of that level (tools/build/bundle.py) and gfx_tail copies it to OVP_AT ($C900, zone 1 of the MENU module: free
in the dungeon). Today: the throne room (src/game/final.asm, tail of GFX8). One VICE session (CHAIN)."""
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


def go(g, lvl, chap):
    L = g.L
    g.poke(L["c_chap"], chap); g.poke(L["c_unl"], max(chap, g.b(L["c_unl"])))
    g.call_keep(L["change_level"], regs="a=%02x,x=00" % lvl, tmax=150); g.frames(3)


@test("OVP-10", "level 20: the code of the throne room is copied from the tail of GFX8 to $C900 (ovp_ok = 1); the boss below "
      "3/4 of its life calls a wave of SUM_WAVE monsters; level 19: no level code; village: the MENU module is read again at $C900")
def ovp_final(ctx):
    g = ctx["g"]; L = g.L
    code = open(os.path.join(ROOT, "out", "work", "ovl_final.bin"), "rb").read()
    go(g, L["MAXLEVEL"], 4)
    check(g.b(L["ovp_ok"]) == 1, "level 20: ovp_ok %d" % g.b(L["ovp_ok"]))
    check(bytes(g.mem(0xC900, len(code))) == code, "level 20: $C900 differs from out/work/ovl_final.bin")
    b = g.b(L["lb_boss"]) - 1
    check(b >= 0, "level 20: no boss")
    n0 = g.b(L["lb_cnt"])
    mx = g.b(L["mhm"] + b) | g.b(L["mhmh"] + b) << 8
    hp = mx * 3 // 4 - 1
    g.poke(L["mhp"] + b, hp & 255); g.poke(L["mhph"] + b, hp >> 8)
    g.poke(L["godmode"], 1)
    g.frames(4)
    check(g.b(L["lb_cnt"]) == n0 + L["SUM_WAVE"], "wave: monsters %d -> %d (expected +%d)" % (n0, g.b(L["lb_cnt"]), L["SUM_WAVE"]))
    check(g.b(L["fb_wave"]) == 1, "fb_wave %d" % g.b(L["fb_wave"]))
    g.poke(L["godmode"], 0)
    go(g, L["MAXLEVEL"] - 1, 4)
    check(g.b(L["ovp_ok"]) == 0, "level 19: ovp_ok %d" % g.b(L["ovp_ok"]))
    g.call_keep(L["change_level"], regs="a=00,x=00", tmax=150); g.frames(3)
    check(g.b(L["ovp_ok"]) == 0 and g.b(L["ovl_cur"]) == 1, "village: ovp_ok %d, ovl_cur %d" % (g.b(L["ovp_ok"]), g.b(L["ovl_cur"])))
    menu = open(os.path.join(ROOT, "out", "work", "menu.bin"), "rb").read()     # flat image from the lowest zone (pack_menu.py)
    base = min(L["MR%d_AT" % k] for k in range(1, L["MPARTS"] + 1))
    check(bytes(g.mem(0xC900, 16)) == menu[0xC900 - base:0xC900 - base + 16], "village: $C900 is not the MENU module")


def boss_level(g, c):
    """boss level of chapter c; returns (overlay labels, boss index, boss tile)"""
    L = g.L
    go(g, 5 * c, c)
    code = open(os.path.join(ROOT, "out", "work", "ovl_boss%d.bin" % c), "rb").read()
    check(g.b(L["ovp_ok"]) == 1, "level %d: ovp_ok %d" % (5 * c, g.b(L["ovp_ok"])))
    check(bytes(g.mem(0xC900, 12)) == code[:12], "level %d: the jump table at $C900 differs from out/work/ovl_boss%d.bin" % (5 * c, c))
    # (the variables of the level code live inside it: only the jump table is compared)
    b = g.b(L["lb_boss"]) - 1
    check(b >= 0, "level %d: no boss" % (5 * c))
    _, _, bx, by = g.mem(L["bm_hdr"], 4)
    return labels("ovl_boss%d" % c), b, (bx, by)


def hp(g, b):
    L = g.L
    return g.b(L["mhp"] + b) | g.b(L["mhph"] + b) << 8, g.b(L["mhm"] + b) | g.b(L["mhmh"] + b) << 8


def set_hp(g, b, v):
    g.poke(g.L["mhp"] + b, v & 255); g.poke(g.L["mhph"] + b, v >> 8)


@test("OVP-11", "level 5, The Hollow Abbot (code in the tail of GFX2): under 2/3 of its life it stops 1 s (green) and raises "
      "2 Skeletons next to itself; while one of them lives it regenerates (1 hp every 25 frames)")
def ovp_abbot(ctx):
    g = ctx["g"]; L = g.L
    O, b, (bx, by) = boss_level(g, 1)
    g.poke(L["godmode"], 1)
    g.teleport(bx, by + 3); g.frames(4)
    n0 = g.b(L["lb_cnt"])
    h, mx = hp(g, b)
    set_hp(g, b, mx * 2 // 3 - 1)
    g.frames(3)
    check(g.b(O["ab_t"]) > 0, "no stop under 2/3 (ab_t %d, ab_wave %d)" % (g.b(O["ab_t"]), g.b(O["ab_wave"])))
    g.frames(60)
    n1 = g.b(L["lb_cnt"])
    check(n1 == n0 + 2, "skeletons raised: %d (expected 2)" % (n1 - n0))
    check(all(g.b(L["mtype"] + i) == O["AB_SKEL"] for i in range(n0, n1)), "raised monsters are not Skeletons")
    h0, _ = hp(g, b)
    g.frames(100)
    h1, _ = hp(g, b)
    check(h1 >= h0 + 3, "regeneration with the skeletons alive: %d -> %d" % (h0, h1))
    g.poke(L["godmode"], 0)


@test("OVP-12", "level 10, The Miller of BadWater (GFX4): awake, every 4 s a 1 s charge, the blow, 1.5 s uncovered (hits x2); "
      "under half life 2 Drowned once")
def ovp_miller(ctx):
    g = ctx["g"]; L = g.L
    O, b, (bx, by) = boss_level(g, 2)
    g.poke(L["godmode"], 1)
    g.teleport(bx, by + 2); g.frames(4)
    for _ in range(260):
        if g.b(O["mi_s"]) == 1: break
        g.frames(1)
    check(g.b(O["mi_s"]) == 1, "no charge within 260 frames (mi_s %d, mi_t %d)" % (g.b(O["mi_s"]), g.b(O["mi_t"])))
    for _ in range(60):
        if g.b(O["mi_s"]) == 2: break
        g.frames(1)
    check(g.b(O["mi_s"]) == 2, "not uncovered after the charge (mi_s %d)" % g.b(O["mi_s"]))
    g.poke(L["cb_dl"], 7, 0)
    g.call_keep(L["ovp_dmg"], regs="x=%02x" % b)
    check((g.b(L["cb_dl"]), g.b(L["cb_dh"])) == (14, 0), "uncovered: damage 7 -> %d (expected 14)" % g.b(L["cb_dl"]))
    n0 = g.b(L["lb_cnt"])
    _, mx = hp(g, b)
    set_hp(g, b, mx // 2 - 1)
    g.frames(4)
    n1 = g.b(L["lb_cnt"])
    check(n1 == n0 + 2 and all(g.b(L["mtype"] + i) == O["MI_DROWN"] for i in range(n0, n1)), "Drowned called: %d" % (n1 - n0))
    set_hp(g, b, mx // 3)
    g.frames(4)
    check(g.b(L["lb_cnt"]) == n1, "Drowned called twice")
    g.poke(L["godmode"], 0)


@test("OVP-13", "level 15, Varok the Oathbreaker (GFX6): aligned with the hero he stops (warning) and charges along the row; "
      "his shield halves the hero's hits, not when stunned")
def ovp_varok(ctx):
    g = ctx["g"]; L = g.L
    O, b, (bx, by) = boss_level(g, 3)
    g.poke(L["godmode"], 1)
    g.teleport(bx + 5, by); g.frames(2)
    x0 = g.b(L["mxl"] + b) | g.b(L["mxh"] + b) << 8
    seen = set()
    for _ in range(120):
        g.frames(1, joy=0)
        seen.add(g.b(O["va_s"]))
        if 2 in seen and g.b(O["va_s"]) != 2: break
    x1 = g.b(L["mxl"] + b) | g.b(L["mxh"] + b) << 8
    check(1 in seen and 2 in seen, "no warning or no charge (states %s)" % sorted(seen))
    check(x1 > x0 + 16, "the charge did not move him toward the hero: x %d -> %d" % (x0, x1))
    g.poke(O["va_s"], 0)
    g.poke(L["cb_dl"], 10, 0)
    g.call_keep(L["ovp_dmg"], regs="x=%02x" % b)
    check(g.b(L["cb_dl"]) == 5, "shield: damage 10 -> %d (expected 5)" % g.b(L["cb_dl"]))
    g.poke(O["va_s"], 3)
    g.poke(L["cb_dl"], 10, 0)
    g.call_keep(L["ovp_dmg"], regs="x=%02x" % b)
    check(g.b(L["cb_dl"]) == 10, "stunned: damage 10 -> %d (expected 10)" % g.b(L["cb_dl"]))
    g.poke(O["va_s"], 0)
    g.poke(L["godmode"], 0)
