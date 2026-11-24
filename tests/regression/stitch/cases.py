"""Mother Stitch (24/11, D16: the proposal of 20/11 in the code, src/game/ovl_boss2.asm): fixed type and life (rules.yaml
chapter_bosses, CB2_TYPE / CB2_HP), the hex (warning, then the Slash cadence x1.625 for DM_HT frames if the hero is within DM_HR
pixels: ovp_rate) and the rotten fetishes (DM_ROT x 4 frames after the rite they become Drowned, type 1, awake, no opening).
One VICE session (CHAIN), level 10 of chapter 2."""
from c64test import test, check
from lib.c64 import Game, labels
from lib.play import new_game

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    L = g.L
    g.poke(L["godmode"], 1)
    g.poke(L["c_chap"], 2); g.poke(L["c_unl"], 2)
    g.call_keep(L["change_level"], regs="a=0a,x=00", tmax=150); g.frames(3)
    ctx["O"] = labels("ovl_boss2")
    ctx["b"] = g.b(L["lb_boss"]) - 1
    ctx["bxy"] = tuple(g.mem(L["bm_hdr"] + 2, 2))


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def hp(g, b):
    L = g.L
    return g.b(L["mhp"] + b) | g.b(L["mhph"] + b) << 8, g.b(L["mhm"] + b) | g.b(L["mhmh"] + b) << 8


@test("STITCH-10", "level 10: Mother Stitch has the fixed type and life (CB2_TYPE, CB2_HP); awake, the first rite plants 2 fetishes; "
      "DM_ROT x 4 frames later they are Drowned (type 1, awake, life of type 1 on the level) and she is not open")
def rot(ctx):
    g = ctx["g"]; L = g.L; O = ctx["O"]; b = ctx["b"]
    check(b >= 0, "no boss on level 10")
    check(g.b(L["mtype"] + b) == L["CB2_TYPE"] and hp(g, b) == (L["CB2_HP"], L["CB2_HP"]),
          "boss type %d life %s, expected %d %d" % (g.b(L["mtype"] + b), hp(g, b), L["CB2_TYPE"], L["CB2_HP"]))
    bx, by = ctx["bxy"]
    g.teleport(bx, by + 3); g.frames(4)
    for _ in range(80):
        if g.b(O["dm_t"]): break
        g.frames(1)
    n0 = g.b(L["lb_cnt"])
    g.frames(60)
    fets = list(range(n0, g.b(L["lb_cnt"])))
    check(len(fets) == 2 and all(g.b(L["mtype"] + i) == O["DM_TYPE"] for i in fets), "fetishes planted: %s" % fets)
    check(g.b(O["dmr_c"]) > 0, "rot counter not started (dmr_c 0)")
    g.poke(O["dmr_c"], 1); g.frames(8)
    check(all(g.b(L["mtype"] + i) == 1 and g.b(L["malive"] + i) and g.b(L["mwake"] + i) for i in fets),
          "fetishes not rotten: types %s" % [g.b(L["mtype"] + i) for i in fets])
    check(all(hp(g, i)[0] > 0 for i in fets), "rotten fetishes without life")
    check(g.b(O["dm_open"]) == 0 and g.b(O["dm_sh"]) == 0, "open (%d) or protected (%d) after the rot" % (g.b(O["dm_open"]), g.b(O["dm_sh"])))


@test("STITCH-11", "the hex: warning (DM_HW frames), the hero next to her: ovp_rate = 5/8 of s_rate for DM_HT frames, then 0; "
      "the hero far away (> DM_HR pixels): no hex")
def hex_(ctx):
    g = ctx["g"]; L = g.L; O = ctx["O"]; b = ctx["b"]
    bx, by = ctx["bxy"]
    for far in (False, True):
        g.poke(L["mhp"] + b, L["CB2_HP"] & 255); g.poke(L["mhph"] + b, L["CB2_HP"] >> 8)
        g.poke(O["dm_t"], 0); g.poke(O["dm_open"], 0); g.poke(O["dmh_t"], 0); g.poke(L["ovp_rate"], 0)
        g.teleport(bx, by + (6 if far else 1)); g.frames(2)
        g.poke(O["dmh_cd"], 1); g.poke(O["dmh_w"], 0)
        for _ in range(8):
            if g.b(O["dmh_w"]): break
            g.frames(1)
        check(g.b(O["dmh_w"]) > 0, "no hex warning")
        g.poke(L["mstun"] + b, 60)                          # the boss stays where she is during the warning
        g.frames(O["DM_HW"] + 2)
        exp = 0 if far else (g.b(L["s_rate"]) >> 1) + (g.b(L["s_rate"]) >> 3)
        check(g.b(L["ovp_rate"]) == exp, "%s: ovp_rate %d, expected %d" % ("far" if far else "near", g.b(L["ovp_rate"]), exp))
        if not far:
            check(g.b(O["dmh_t"]) > 0, "hex not running")
            g.poke(O["dmh_t"], 2); g.frames(3)
            check(g.b(L["ovp_rate"]) == 0, "ovp_rate %d after the hex" % g.b(L["ovp_rate"]))
