"""Quests of chapter 2 (24/11, docs/wiki/quests.md D13): the gate D4 and the unlock at QGIV extended to chapter 2 (QGATE_CH = 2);
the monster types of the quests of chapter 2 are the monsters of chapter 2 (tools/build/gen_qdata.py: type = place in the
chapter's bestiary, the same order as its theme file). One VICE session, a new barbarian moved to the village of chapter 2
with steps 1-3 handed in; the steps follow each other."""
from c64test import test, check
from lib.c64 import Game
from lib.play import new_game, alive
from lib.qgiv import talk, close

CHAIN = True
SABINE = 0          # fixed NPC 0 of village 2 (tools/build/villages.py FIXED)


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(4)
    L = g.L
    g.poke(L["c_lvl"], 8)
    g.poke(L["c_chap"], 2); g.poke(L["c_unl"], 2)
    g.call_keep(L["change_level"], regs="a=00,x=00", tmax=150); g.frames(3)
    g.poke(L["q_step"], 3, 0x10, 0)                     # steps 1-3 handed in, purse step 1


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def name_at(g, t):
    """name of monster type t in the set of the current theme (NM_AT, as bar_name)"""
    L = g.L
    a = (L["NM_AT"] & 0xff00) | g.b(L["NM_AT"] + 8 + t)
    return "".join(chr(b + 96) if 1 <= b <= 26 else chr(b) for b in bytes(g.mem(a, 25)).split(b"\0")[0])


@test("QCH2-10", "village 2: mama sabine gives step 4 ('the silent village', slay the drowned: 0/12); in level 7 the quest monster "
      "type is the drowned (its name in the theme), a drowned killed counts, a bog crawler does not")
def step4(ctx):
    g = ctx["g"]; L = g.L
    t = talk(g, SABINE); close(g)
    check(g.b(L["q_flag"]) & 1 and g.b(L["q_step"]) == 3, "step 4 not taken: q_step %d q_flag %d" % (g.b(L["q_step"]), g.b(L["q_flag"])))
    check("drowned" in t and "silent village" in t, "text of step 4: %r" % t[:400])
    g.poke(L["c_unl"], 2)
    g.call_keep(L["change_level"], regs="a=07,x=00", tmax=150); g.frames(3)
    mt = g.b(L["qt_p1"] + 3)                                # monster type of quest 4 (chain index 3, qtab.inc)
    check(name_at(g, mt) == "drowned", "quest type %d is %r in chapter 2" % (mt, name_at(g, mt)))
    check(any(g.b(L["mtype"] + i) == mt for i in alive(g)), "no drowned on level 7 (D11)")
    for ty, n in ((mt, 1), (mt + 1, 1)):
        g.poke(L["mtype"], ty); g.poke(L["km_i"], 0); g.poke(L["lb_boss"], 0)
        g.call_keep(L["q_kill"], regs="x=00")
        check(g.b(L["q_cnt"]) == n, "after killing type %d (%s): q_cnt %d, expected %d" % (ty, name_at(g, ty), g.b(L["q_cnt"]), n))


@test("QCH2-11", "step 6 (the silver needle) handed in to mama sabine: q_step 6, chapter 3 unlocked (c_unl 3), purse step 2; the boss "
      "of chapter 2 dying does not unlock chapter 3")
def step6(ctx):
    g = ctx["g"]; L = g.L
    lv = g.b(L["cur_level"])
    g.poke(L["q_step"], 5, 0x10, 0)
    g.poke(L["cur_level"], 10); g.call_keep(L["chap_won"]); g.poke(L["cur_level"], lv)
    check(g.b(L["c_unl"]) == 2, "c_unl %d after the boss of chapter 2, expected 2" % g.b(L["c_unl"]))
    g.call_keep(L["change_level"], regs="a=00,x=00", tmax=150); g.frames(3)
    g.poke(L["q_flag"], 0x13); g.poke(L["c_beltt"], 0, 0, 0, 0)        # taken + reached; room for the 3 yellow potions
    talk(g, SABINE); close(g)
    check(g.b(L["q_step"]) == 6, "q_step %d, expected 6" % g.b(L["q_step"]))
    check(g.b(L["c_unl"]) == 3, "c_unl %d after step 6, expected 3" % g.b(L["c_unl"]))
    check(g.b(L["q_flag"]) >> 4 == 2, "purse step %d, expected 2" % (g.b(L["q_flag"]) >> 4))
