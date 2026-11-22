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
      "3/4 of its life calls a wave of SUM_WAVE monsters; level 19: the decor code of chapter 4 (with the citadel); village: the MENU "
      "module is read again at $C900")
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
    go(g, L["MAXLEVEL"] - 1, 4)                           # (19/11) piani generati: il codice degli arredi (capitolo 4 + cittadella)
    dec = open(os.path.join(ROOT, "out", "work", "ovl_decor4.bin"), "rb").read()
    check(g.b(L["ovp_ok"]) == 1 and bytes(g.mem(0xC900, 21)) == dec[:21], "level 19: the decor code of chapter 4 is not at $C900")
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
      "a Skeleton next to itself (2 until 22/11); while it lives it regenerates (1 hp every 50 frames since 22/11)")
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
    check(n1 == n0 + 1, "skeletons raised: %d (expected 1)" % (n1 - n0))
    check(all(g.b(L["mtype"] + i) == O["AB_SKEL"] for i in range(n0, n1)), "raised monsters are not Skeletons")
    h0, _ = hp(g, b)
    g.frames(100)
    h1, _ = hp(g, b)
    check(h1 >= h0 + 1, "regeneration with the skeleton alive: %d -> %d" % (h0, h1))
    g.poke(L["godmode"], 0)


@test("OVP-12", "level 10, Mother Stitch (GFX4): awake, a rite (1 s still) plants 2 fetishes (type 8, still, life = her max / 16); "
      "while one stands the hero's hits are halved and she regenerates; the last one down leaves her open (hits x2); "
      "under 2/3 a second rite; a fetish killed gives no loot")
def ovp_stitch(ctx):
    g = ctx["g"]; L = g.L
    O, b, (bx, by) = boss_level(g, 2)
    g.poke(L["godmode"], 1)
    g.teleport(bx, by + 3); g.frames(4)
    for _ in range(60):
        if g.b(O["dm_t"]): break
        g.frames(1)
    check(g.b(O["dm_t"]) > 0 and g.b(O["dm_wave"]) == 1, "no first rite once awake (ms_t %d, ms_wave %d)" % (g.b(O["dm_t"]), g.b(O["dm_wave"])))
    n0 = g.b(L["lb_cnt"])
    g.frames(60)
    n1 = g.b(L["lb_cnt"])
    fets = list(range(n0, n1))
    check(len(fets) == 2 and all(g.b(L["mtype"] + i) == O["DM_TYPE"] for i in fets), "fetishes planted: %d" % len(fets))
    _, mx = hp(g, b)
    check(all(hp(g, i) == (max(1, mx // 16),) * 2 for i in fets), "fetish life %s, expected %d" % ([hp(g, i) for i in fets], mx // 16))
    pos = [(g.b(L["mxl"] + i), g.b(L["myl"] + i)) for i in fets]
    os.makedirs(os.path.join(ROOT, "out", "work", "ovp"), exist_ok=True)
    g.screenshot(os.path.join(ROOT, "out", "work", "ovp", "stitch_fetishes.png"))   # to look at, not compared
    g.frames(40)
    check([(g.b(L["mxl"] + i), g.b(L["myl"] + i)) for i in fets] == pos, "the fetishes moved")
    check(g.b(O["dm_sh"]) == 1, "not protected with the fetishes standing")
    g.poke(L["cb_dl"], 10, 0)
    g.call_keep(L["ovp_dmg"], regs="x=%02x" % b)
    check(g.b(L["cb_dl"]) == 5, "protected: damage 10 -> %d (expected 5)" % g.b(L["cb_dl"]))
    set_hp(g, b, mx * 3 // 4)
    h0, _ = hp(g, b)
    g.frames(60)
    h1, _ = hp(g, b)
    check(h1 >= h0 + 2, "no regeneration while protected: %d -> %d" % (h0, h1))
    k = L["ovp_kill"]                                     # carry of ovp_kill in A: jsr ovp_kill / lda #0 / rol / rts
    g.poke(0x0350, 0x20, k & 255, k >> 8, 0xA9, 0, 0x2A, 0x60)
    check(g.call_keep(0x0350, regs="x=%02x" % fets[0])["a"] == 1, "a fetish killed: loot not suppressed (ovp_kill C=0)")
    check(g.call_keep(0x0350, regs="x=%02x" % b)["a"] == 0, "the boss killed: loot suppressed (ovp_kill C=1)")
    for i in fets:                                        # the last one down: open
        g.poke(L["malive"] + i, 0)
    g.frames(3)
    check(g.b(O["dm_open"]) > 0, "not open after the last fetish (ms_open %d)" % g.b(O["dm_open"]))
    g.poke(L["cb_dl"], 7, 0)
    g.call_keep(L["ovp_dmg"], regs="x=%02x" % b)
    check((g.b(L["cb_dl"]), g.b(L["cb_dh"])) == (14, 0), "open: damage 7 -> %d (expected 14)" % g.b(L["cb_dl"]))
    g.frames(110)
    check(g.b(O["dm_open"]) == 0, "still open after 2 s")
    set_hp(g, b, mx * 2 // 3 - 1)
    g.frames(3)
    check(g.b(O["dm_wave"]) == 2 and g.b(O["dm_t"]) > 0, "no second rite under 2/3 (ms_wave %d)" % g.b(O["dm_wave"]))
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
