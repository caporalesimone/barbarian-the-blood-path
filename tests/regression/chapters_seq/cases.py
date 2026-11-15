"""(moved from sanity to regression on 12/11) Chapter sequence (12/11, TODO M1, docs/capitoli.md): every chapter c has its village (file TWNc) and CH_LV levels; the
last one of chapters 1-3 is the boss level (fixed map BOSSCHc, placeholder; boss drawn with the final boss graphics);
killing that boss unlocks chapter c+1 (c_unl) and the exit of the village (tiles '=' of data/town_map.txt) takes the
hero to the next village (save of hero + levels, then TWNc+1). One VICE session, tests in order (CHAIN)."""
from c64test import test, check
from lib.c64 import Game
from lib.play import new_game, find, fire_to, U

CHAIN = True
import os
import gen_maps as GM, villages as V
from lib.c64 import ROOT
EXIT = (26, 0)                       # data/town_map.txt: '=' on the north edge (columns 26-27)
TOWN_N = tuple(GM.build(2, V.VILLAGES[2])[1][4:6])     # entry of village 2 (letter E of data/town_map2.txt; 15/11: every village has its own)


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def label(g):
    """id of the place label under the hero (loc_id; 19 = travel to next chapter)"""
    g.frames(2)
    a = g.call_keep(g.L["loc_id"])["a"]
    g.frames(1)                      # (after call_keep the first go stops again at the same input read)
    return a


def level(g, n):
    """change_level to level n (spawn mode 0) from the current input read"""
    g.call_keep(g.L["change_level"], regs="a=%02x,x=00" % n, tmax=150)
    g.frames(3)


@test("CHAP-SEQ-10", "new hero in chapter 1 (c_chap = c_unl = 1); the village exit is closed: no label, the edge stops the hero")
def seq_new(ctx):
    g = ctx["g"]; L = g.L
    check((g.b(L["c_chap"]), g.b(L["c_unl"])) == (1, 1), "c_chap/c_unl %d/%d" % (g.b(L["c_chap"]), g.b(L["c_unl"])))
    g.teleport(*EXIT)
    check(label(g) != 19, "travel label shown with the chapter locked")
    g.frames(20, joy=U)
    check(g.ptile()[1] == 0 and g.w16(L["py"]) < 16, "the hero left the map at the top: py = %d" % g.w16(L["py"]))


@test("CHAP-SEQ-11", "level 5 = boss level of chapter 1: map BOSSCH1 (stairs up, no stairs down), boss drawn as the final boss")
def seq_boss_level(ctx):
    g = ctx["g"]; L = g.L
    level(g, 5)
    check(g.b(L["cur_level"]) == 5 and g.b(L["lv_cboss"]) == 1, "lv_cboss %d" % g.b(L["lv_cboss"]))
    sx, sy, bx, by = g.mem(L["bm_hdr"], 4)
    check(g.tile(sx, sy) == L["T_STAIRSU"], "no stairs up at (%d,%d)" % (sx, sy))
    check(not find(g, L["T_STAIRSD"]), "stairs down on the boss level")
    nb = g.b(L["lb_boss"])
    check(nb > 0, "no boss on the level")
    g.teleport(bx, by + 3); g.frames(3)
    fin = g.b(L["mon_ptr"] + L["T_FINAL"])
    ptrs = g.mem(0xb400 + 0x3fb, 5) + g.mem(0xbc00 + 0x3fb, 5)
    check(fin in ptrs or fin + 1 in ptrs, "boss sprite is not the final boss (%02x not in %s)" % (fin, ptrs))


@test("CHAP-SEQ-12", "killing the boss of chapter 1 unlocks chapter 2 (c_unl = 2)")
def seq_kill(ctx):
    g = ctx["g"]; L = g.L
    g.call_keep(L["kill_monster"], regs="x=%02x" % (g.b(L["lb_boss"]) - 1))
    check(g.b(L["c_unl"]) == 2, "c_unl %d" % g.b(L["c_unl"]))


@test("CHAP-SEQ-13", "village exit open: label 'travel to next chapter'; fire: chapter 2, village TWN2 at the south entry, hero saved")
def seq_travel(ctx):
    g = ctx["g"]; L = g.L
    level(g, 0)
    g.teleport(*EXIT)
    check(label(g) == 19, "no travel label on the open exit")
    g.press_fire(1); g.wait_main(); g.frames(3)
    check(g.b(L["c_chap"]) == 2 and g.b(L["cur_level"]) == 0, "c_chap %d, level %d" % (g.b(L["c_chap"]), g.b(L["cur_level"])))
    check(g.ptile() == TOWN_N, "hero at %s, not at the entry of village 2 %s" % (g.ptile(), TOWN_N))
    g.call_keep(L["load_gfx"], tmax=60, regs="a=00")
    check(bytes(g.mem(L["cmdbuf"] + 3, 4)) == b"TWN2", "village file %r" % bytes(g.mem(L["cmdbuf"] + 3, 4)))
    g.poke(L["c_chap"], 9); g.poke(L["c_unl"], 9)
    g.call_keep(L["load_char"], tmax=60)
    check((g.b(L["c_chap"]), g.b(L["c_unl"])) == (2, 2), "hero on the disk: c_chap/c_unl %d/%d" % (g.b(L["c_chap"]), g.b(L["c_unl"])))


@test("CHAP-SEQ-14", "chapter 2: the crypt leads to level 6 (first of the chapter); its stairs up lead back to the village")
def seq_ch2(ctx):
    g = ctx["g"]; L = g.L
    level(g, 0)
    fire_to(g, *find(g, L["T_TSTAIRS"])[0]); g.wait_main(); g.frames(2)
    check(g.b(L["cur_level"]) == 6, "crypt -> level %d" % g.b(L["cur_level"]))
    fire_to(g, *find(g, L["T_STAIRSU"])[0]); g.wait_main(); g.frames(2)
    check(g.b(L["cur_level"]) == 0 and g.b(L["c_chap"]) == 2, "stairs up of level 6 -> level %d" % g.b(L["cur_level"]))
