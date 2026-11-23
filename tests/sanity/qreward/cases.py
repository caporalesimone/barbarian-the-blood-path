"""Rewards of the chain of chapter 1 (23/11, owner's request; docs/wiki/quests.md Q15 and section 4.5):
- the skills need the level (sk_req) AND the step of the chain that gives them handed in (sk_qs, q_step >=): Whirlwind step 2,
  Battle Cry 4, Smash 8, Rage 6, Frenzy 9 (sk_ok in GAME);
- chapter 2 is unlocked when step 3 (the hollow abbot) is handed in at QGIV, not when the boss dies (chapters with the gate D4,
  1..QGATE_CH).
One VICE session, a new barbarian in the village of chapter 1; the steps follow each other."""
from c64test import test, check
from lib.c64 import Game
from lib.play import new_game
from lib.qgiv import talk, close

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(4)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def select(g, x):
    """sel_skill X (keys H J K L): the skill chosen (c_skill), starting from Slash"""
    L = g.L
    g.poke(L["c_skill"], 0)
    g.call_keep(L["sel_skill"], regs="x=%02x" % x)
    return g.b(L["c_skill"])


@test("QREW-10", "Q15: sk_qs from quests.yaml (0, 2, 4, 8, 6, 9); level 3 with step 1 handed in: no Whirlwind; level 9 with step 5: no Rage (buff_act), with step 6 Rage starts")
def qr_table(ctx):
    g = ctx["g"]; L = g.L
    check(g.mem(L["sk_qs"], 6) == [0, 2, 4, 8, 6, 9], "sk_qs %s" % g.mem(L["sk_qs"], 6))
    g.poke(L["c_lvl"], 3); g.poke(L["q_step"], 1)
    check(select(g, 1) == 0, "Whirlwind chosen with q_step 1")
    g.poke(L["c_lvl"], 9); g.poke(L["q_step"], 5)
    T = L["tmr"] + L["T_RAGE"]
    for st, on in ((5, False), (6, True)):
        g.poke(L["q_step"], st); g.poke(L["sk_cdl"] + 4, 0); g.poke(L["sk_cdh"] + 4, 0); g.poke(T, 0, 0)
        g.call_keep(L["buff_act"], regs="x=04")
        check(bool(g.w16(T)) == on, "Rage with q_step %d: timer %d" % (st, g.w16(T)))
    g.poke(T, 0, 0); g.poke(L["c_lvl"], 3); g.poke(L["q_step"], 1)


@test("QREW-11", "step 2 reached, handed in to father osric (level 3): q_step 2, 'the skill whirlwind' in the reward, then J chooses Whirlwind")
def qr_whirl(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["q_flag"], 3)
    t = talk(g, 1)
    check(g.b(L["q_step"]) == 2, "q_step %d, expected 2" % g.b(L["q_step"]))
    check("whirlwind" in t, "no whirlwind in the reward: %r" % t[19 * 40:22 * 40])
    close(g)
    check(select(g, 1) == 1, "Whirlwind not chosen with q_step 2 at level 3")


@test("QREW-12", "chapter 1: the boss dying does not unlock chapter 2 (chap_won, c_unl 1); step 3 handed in to father osric: c_unl 2, purse step 1 (550)")
def qr_unlock(ctx):
    g = ctx["g"]; L = g.L
    lv = g.b(L["cur_level"])
    g.poke(L["cur_level"], 5); g.call_keep(L["chap_won"]); g.poke(L["cur_level"], lv)
    check(g.b(L["c_unl"]) == 1, "c_unl %d after the boss of chapter 1, expected 1" % g.b(L["c_unl"]))
    talk(g, 1); close(g)                                            # step 3 offered (taken at once)
    check(g.b(L["q_step"]) == 2 and g.b(L["q_flag"]) & 1, "step 3 not taken: q_step %d q_flag %d" % (g.b(L["q_step"]), g.b(L["q_flag"])))
    g.poke(L["q_flag"], 3); g.poke(L["c_beltt"], 0, 0, 0, 0)         # room for the 3 red potions of the reward (Q12)
    talk(g, 1); close(g)
    check(g.b(L["q_step"]) == 3, "q_step %d, expected 3" % g.b(L["q_step"]))
    check(g.b(L["c_unl"]) == 2, "c_unl %d after step 3, expected 2" % g.b(L["c_unl"]))
    check(g.b(L["q_flag"]) >> 4 == 1, "purse step %d, expected 1" % (g.b(L["q_flag"]) >> 4))
