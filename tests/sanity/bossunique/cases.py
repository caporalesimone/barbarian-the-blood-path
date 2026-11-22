"""Uniques from the boss chests (22/11, owner's decision D9): the uniques of the story only from quests; the others only from
the boss chests, from the subset of the current chapter (uniques.tsv, column boss_chapter -> un_bch), chapter boss (level
multiple of 5) UNB_C / 256, named boss of the other levels UNB_N / 256 (bu_roll, src/game/combat.asm). One VICE session."""
import csv
import os
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game

CHAIN = True
UQ = list(csv.DictReader(open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "items", "next", "uniques.tsv")),
                         delimiter="\t"))


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def rolls(g, chap, level, n, slot=1):
    """n calls of bu_roll on chest slot `slot` (first item a dagger): list of the unique numbers (None = no unique)"""
    L = g.L
    g.poke(L["c_chap"], chap); g.poke(L["cur_level"], level)
    out = []
    for _ in range(n):
        g.poke(L["ch_i"] + 4 * slot, L["I_DAGGER"]); g.poke(L["ch_b"] + 4 * slot, 3); g.poke(L["ch_s"] + 4 * slot, 0)
        g.call_keep(L["bu_roll"], regs="x=%02x" % slot)
        s = g.b(L["ch_s"] + 4 * slot)
        if s >= 0x80:
            u = s & 0x7f
            ok = g.b(L["ch_i"] + 4 * slot) == g.b(L["un_base"] + u) and g.b(L["ch_b"] + 4 * slot) == 0
            out.append(u if ok else "bad")
        else:
            ok = g.b(L["ch_i"] + 4 * slot) == L["I_DAGGER"] and g.b(L["ch_b"] + 4 * slot) == 3
            out.append(None if ok else "bad")
    return out


@test("BU-10", "data: un_bch = boss_chapter of uniques.tsv; no unique given by a quest is in a boss subset; UNB_C 128 (50%), UNB_N 32 (12.5%)")
def bu_data(ctx):
    g = ctx["g"]; L = g.L
    import yaml
    q = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "quests", "next", "quests.yaml")))
    given = {x["reward"]["unique"] for x in q["quests"] if x.get("reward", {}).get("unique")}
    bch = g.mem(L["un_bch"], len(UQ))
    check(bch == [int(u["boss_chapter"]) for u in UQ], "un_bch %s" % bch)
    both = [u["name"] for u in UQ if int(u["boss_chapter"]) and u["name"] in given]
    check(not both, "uniques both from a quest and from a boss: %s" % both)
    check(L["UNB_C"] == 128 and L["UNB_N"] == 32, "UNB_C %d UNB_N %d" % (L["UNB_C"], L["UNB_N"]))


@test("BU-11", "bu_roll: chapter 2, level 10 (chapter boss) about half the chests get a unique of the chapter 2 subset; level 7 about 1 in 8; chapter 1 (empty subset) never")
def bu_roll(ctx):
    g = ctx["g"]; L = g.L
    sub2 = {i for i, u in enumerate(UQ) if int(u["boss_chapter"]) == 2}
    r10 = rolls(g, 2, 10, 120)
    r7 = rolls(g, 2, 7, 120)
    r1 = rolls(g, 1, 5, 40)
    g.poke(L["c_chap"], 1); g.poke(L["cur_level"], 0)
    n10, n7 = sum(x is not None for x in r10), sum(x is not None for x in r7)
    print("      chapter boss %d / 120, named boss %d / 120, chapter 1 %d / 40" % (n10, n7, sum(x is not None for x in r1)))
    check("bad" not in r10 + r7 + r1, "wrong chest content after bu_roll")
    check({x for x in r10 + r7 if x is not None} <= sub2, "uniques outside the subset of chapter 2: %s" % sorted({x for x in r10 + r7 if x is not None} - sub2))
    check(35 <= n10 <= 85 and 3 <= n7 <= 30, "chapter boss %d / 120 (expected ~60), named boss %d / 120 (expected ~15)" % (n10, n7))
    check(all(x is None for x in r1), "chapter 1 gave a unique")
