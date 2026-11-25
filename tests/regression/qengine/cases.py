"""Resident quest engine (22/11, owner's decisions D4, D11, D13, D18, D19; src/game/qengine.asm, tables out/work/qtab.inc from
tools/build/gen_qdata.py). The quest state is poked (QGIV, the village module, comes later): chain step = q_step + 1 taken
(q_flag bit 0), reached (bit 1); side quests in q_side (id 1..15, bit 7 = reached) with their counter. One VICE session."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def state(g, step=0, flag=0, cnt=0, side=(0,) * 8):
    L = g.L
    g.poke(L["q_step"], step, flag, cnt, 0, 0, *side)
    g.poke(L["q_mt"], 0)


def kill(g, mtype, named=False):
    """q_kill on monster 0 of type mtype (the named boss if named)"""
    L = g.L
    g.poke(L["mtype"], mtype); g.poke(L["km_i"], 0); g.poke(L["lb_boss"], 1 if named else 0)
    g.call_keep(L["q_kill"], regs="x=00")


@test("QENG-10", "K (chain step 1, 8 fallen): only a fallen of chapter 1 counts; the 8th marks the step reached (q_flag bit 1) with 'quest complete'")
def qe_kill(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_chap"], 1); g.poke(L["cur_level"], 2)
    state(g, 0, 1)
    kill(g, L["M_SKELETON"])
    check(g.b(L["q_cnt"]) == 0, "a skeleton counted")
    g.poke(L["c_chap"], 2); kill(g, L["M_FALLEN"]); g.poke(L["c_chap"], 1)
    check(g.b(L["q_cnt"]) == 0, "a monster of type 1 in chapter 2 counted")
    for i in range(7):
        kill(g, L["M_FALLEN"])
    check(g.b(L["q_cnt"]) == 7 and g.b(L["q_flag"]) == 1, "after 7: cnt %d flag %d" % (g.b(L["q_cnt"]), g.b(L["q_flag"])))
    kill(g, L["M_FALLEN"])
    check(g.b(L["q_cnt"]) == 8 and g.b(L["q_flag"]) == 3, "after 8: cnt %d flag %d" % (g.b(L["q_cnt"]), g.b(L["q_flag"])))
    check(g.b(L["q_mt"]) > 0 and g.b(L["q_ml"]) == L["QL_DONE"], "message %d label %d" % (g.b(L["q_mt"]), g.b(L["q_ml"])))
    kill(g, L["M_FALLEN"])
    check(g.b(L["q_cnt"]) == 8, "a reached step still counts")
    state(g, 0, 0)
    kill(g, L["M_FALLEN"])
    check(g.b(L["q_cnt"]) == 0, "a step not taken counts (Q13)")


@test("QENG-11", "P and B (side a1.4: 10 kills on level 4; a1.3: a named boss of levels 1-4) in q_side slots 2 and 3: counted only on their level, bit 7 when reached")
def qe_side(ctx):
    g = ctx["g"]; L = g.L
    state(g, side=(0, 0, 16 - 12, 0, 15 - 12, 0, 0, 0))       # a1.4 = QID 16 (id 4), a1.3 = QID 15 (id 3)
    g.poke(L["cur_level"], 3); kill(g, L["M_ZOMBIE"])
    check(g.mem(L["q_side"], 4) == [0, 0, 4, 0], "level 3 counted: %s" % g.mem(L["q_side"], 4))
    g.poke(L["cur_level"], 4)
    for i in range(9):
        kill(g, L["M_ZOMBIE"])
    check(g.mem(L["q_side"] + 2, 2) == [4, 9] and g.mem(L["q_side"] + 4, 2) == [3, 0], "after 9: %s" % g.mem(L["q_side"], 6))
    kill(g, L["M_FALLEN"], named=True)
    check(g.mem(L["q_side"] + 2, 4) == [0x84, 10, 0x83, 1], "after the named boss: %s" % g.mem(L["q_side"], 6))


@test("QENG-12", "IC (chain step 2, Tam's amulet in the named boss chest of level 3, D19): q_chest on level 2 nothing, on level 3 'found: tam's amulet' and the step reached")
def qe_chest(ctx):
    g = ctx["g"]; L = g.L
    state(g, 1, 1)
    g.poke(L["cur_level"], 2); g.call_keep(L["q_chest"])
    check(g.b(L["q_cnt"]) == 0, "level 2 counted")
    g.poke(L["cur_level"], 3); g.call_keep(L["q_chest"])
    check(g.b(L["q_cnt"]) == 1 and g.b(L["q_flag"]) == 3, "level 3: cnt %d flag %d" % (g.b(L["q_cnt"]), g.b(L["q_flag"])))
    check(g.b(L["q_ml"]) == L["QL_FOUND"] and g.b(L["q_mi"]) == 1, "message %d item %d (expected found, 1)" % (g.b(L["q_ml"]), g.b(L["q_mi"])))


@test("QENG-13", "C and the gate (D4): the stairs to level 5 are sealed until step 3 is taken; q_cboss reaches step 3; other levels always open; "
      "chapter 2 (24/11): level 10 sealed until step 6 is taken; chapter 3 open")
def qe_gate(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_chap"], 1)

    def sealed(step, flag, lvl=5):
        state(g, step, flag)
        return bool(g.call_keep(L["q_gate"], regs="a=%02x" % lvl)["c"])
    res = [sealed(0, 0), sealed(2, 0), sealed(2, 1), sealed(3, 0), sealed(0, 0, 3)]
    g.poke(L["c_chap"], 2); ch2 = [sealed(3, 0, 10), sealed(5, 0, 10), sealed(5, 1, 10)]
    g.poke(L["c_chap"], 3); ch3 = sealed(6, 0, 15); g.poke(L["c_chap"], 1)
    check(ch2 == [True, True, False], "chapter 2 (24/11, QGATE_CH = 2): sealed with step 4 delivered, step 6 offered, taken: %s" % ch2)
    check(not ch3, "chapter 3 sealed (QGATE_CH = 2: chapters 1-2 for now)")
    check(res == [True, True, False, False, False], "sealed (step 0, step 3 offered, taken, delivered, level 3): %s" % res)
    state(g, 2, 1)
    g.call_keep(L["q_cboss"])
    check(g.b(L["q_flag"]) == 3, "q_cboss: flag %d" % g.b(L["q_flag"]))


@test("QENG-14", "D11: with step 1 taken (fallen), a level of chapter 1 without fallen gets one (the first monster that is not the boss); none on a chapter boss level")
def qe_spawn(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_chap"], 1); g.poke(L["cur_level"], 2); g.poke(L["lv_cboss"], 0)
    state(g, 0, 1)
    g.poke(L["lb_cnt"], 4); g.poke(L["lb_boss"], 1); g.poke(L["malive"], 1, 1, 1, 1)
    g.poke(L["mtype"], L["M_SKELETON"], L["M_SKELETON"], L["M_ZOMBIE"], L["M_SKELETON"])
    g.call_keep(L["q_spawn"])
    m = g.mem(L["mtype"], 4)
    check(m == [L["M_SKELETON"], L["M_FALLEN"], L["M_ZOMBIE"], L["M_SKELETON"]], "types %s" % m)
    g.poke(L["mtype"], L["M_SKELETON"], L["M_SKELETON"], L["M_FALLEN"], L["M_SKELETON"])
    g.call_keep(L["q_spawn"])
    check(g.mem(L["mtype"], 4).count(L["M_FALLEN"]) == 1, "a second fallen: %s" % g.mem(L["mtype"], 4))
    g.poke(L["mtype"], L["M_SKELETON"]); g.poke(L["lv_cboss"], 1)
    g.call_keep(L["q_spawn"])
    check(g.b(L["mtype"]) == L["M_SKELETON"], "chapter boss level changed")
    g.poke(L["lv_cboss"], 0); g.poke(L["lb_cnt"], 0); g.poke(L["cur_level"], 0); state(g)


def lvl(g, cnt, alive, boss=1, bch=0, level=2):
    """a generated level poked: cnt monsters (skeletons), alive flags, boss index + 1, boss chest place + 1"""
    L = g.L
    g.poke(L["c_chap"], 1); g.poke(L["cur_level"], level); g.poke(L["lv_cboss"], 0)
    g.poke(L["lb_cnt"], cnt); g.poke(L["lb_boss"], boss); g.poke(L["lb_bch"], bch)
    g.poke(L["mtype"], *([L["M_SKELETON"]] * cnt)); g.poke(L["malive"], *alive)


@test("QENG-15", "(25/11, 'a quest must always be completable') targeted repopulation: a cleared level comes back alive for K (chapter), "
      "P (level in range), B (named boss dead), IC (boss dead and its chest opened); not without a quest, not for a reached one, "
      "not when the level still offers something (a monster alive, the boss alive, the boss chest unopened)")
def qe_repop(ctx):
    g = ctx["g"]; L = g.L
    alive = lambda: g.mem(L["malive"], 4)
    lvl(g, 4, (0, 0, 0, 0)); state(g)
    g.call_keep(L["q_spawn"])
    check(alive() == [0, 0, 0, 0], "no quest taken: repopulated %s" % alive())
    state(g, 0, 1); g.call_keep(L["q_spawn"])                  # K: chain step 1 (fallen), level empty
    check(alive() == [1, 1, 1, 1], "K, empty level: %s" % alive())
    lvl(g, 4, (0, 0, 1, 0)); state(g, 0, 1); g.call_keep(L["q_spawn"])
    check(alive() == [0, 0, 1, 0], "K, one monster alive: repopulated anyway %s" % alive())
    lvl(g, 4, (0, 0, 0, 0)); state(g, 0, 3); g.call_keep(L["q_spawn"])
    check(alive() == [0, 0, 0, 0], "K reached: repopulated %s" % alive())
    lvl(g, 4, (0, 0, 0, 0), level=4); state(g, side=(16 - 12, 0, 0, 0, 0, 0, 0, 0)); g.call_keep(L["q_spawn"])   # P a1.4: level 4
    check(alive() == [1, 1, 1, 1], "P on level 4: %s" % alive())
    lvl(g, 4, (0, 0, 0, 0), level=3); state(g, side=(16 - 12, 0, 0, 0, 0, 0, 0, 0)); g.call_keep(L["q_spawn"])
    check(alive() == [0, 0, 0, 0], "P out of its level (3): repopulated %s" % alive())
    lvl(g, 4, (0, 1, 1, 1), boss=1); state(g, side=(15 - 12, 0, 0, 0, 0, 0, 0, 0)); g.call_keep(L["q_spawn"])  # B a1.3
    check(alive() == [1, 1, 1, 1], "B, named boss dead: %s" % alive())
    lvl(g, 4, (1, 0, 0, 0), boss=1); state(g, side=(15 - 12, 0, 0, 0, 0, 0, 0, 0)); g.call_keep(L["q_spawn"])
    check(alive() == [1, 0, 0, 0], "B, named boss alive: repopulated %s" % alive())
    lvl(g, 4, (0, 0, 0, 0), boss=1, bch=1, level=3); state(g, 1, 1); g.call_keep(L["q_spawn"])               # IC: step 2, level 3
    check(alive() == [0, 0, 0, 0], "IC, boss chest unopened: repopulated %s" % alive())
    lvl(g, 4, (0, 0, 0, 0), boss=1, bch=0, level=3); state(g, 1, 1); g.call_keep(L["q_spawn"])
    check(alive() == [1, 1, 1, 1], "IC, boss dead and chest opened: %s" % alive())
    g.poke(L["lb_cnt"], 0); g.poke(L["cur_level"], 0); state(g)


@test("QENG-16", "D11 after the saved state (25/11): a dead fallen does not count, the converted monster is a living one (not the boss)")
def qe_spawn_alive(ctx):
    g = ctx["g"]; L = g.L
    lvl(g, 4, (1, 0, 1, 1), boss=1)
    g.poke(L["mtype"] + 1, L["M_FALLEN"])                     # the only fallen is dead
    state(g, 0, 1); g.call_keep(L["q_spawn"])
    m = g.mem(L["mtype"], 4)
    check(m == [L["M_SKELETON"], L["M_FALLEN"], L["M_FALLEN"], L["M_SKELETON"]], "types %s (expected the living monster 2 converted)" % m)
    g.poke(L["lb_cnt"], 0); g.poke(L["cur_level"], 0); state(g)


@test("QENG-17", "real game: level 2 cleared, then chain step 1 taken: back on level 2 the monsters are alive again; without the quest it stays cleared")
def qe_repop_real(ctx):
    g = ctx["g"]; L = g.L

    def go(lv):
        g.poke(L["c_chap"], 1); g.poke(L["c_unl"], 1)
        g.call_keep(L["change_level"], regs="a=%02x,x=00" % lv, tmax=150); g.frames(3)
        check(g.b(L["cur_level"]) == lv, "level %d, expected %d" % (g.b(L["cur_level"]), lv))

    def alive():
        n = g.b(L["lb_cnt"])
        return sum(1 for v in g.mem(L["malive"], n) if v)
    state(g)
    go(2)
    n = g.b(L["lb_cnt"])
    check(n > 0, "level 2 without monsters")
    g.poke(L["malive"], *([0] * n))                           # all killed
    go(3); go(2)
    check(alive() == 0, "no quest: level 2 repopulated (%d alive)" % alive())
    go(3); state(g, 0, 1); go(2)
    check(alive() == n, "chain step 1 taken: %d of %d alive" % (alive(), n))
    state(g)
