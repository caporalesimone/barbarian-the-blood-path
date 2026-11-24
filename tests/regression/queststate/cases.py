"""Quest state in the save (22/11, save format $CE, owner's decision D1): the inn chest leaves the hero block (it lives at
INN_AT, in the RAM under the KERNAL, and follows CHRBLK in the file save-0N); the hero block gets the 32 bytes of the quest
state (q_step .. q_item; q_free removed on 24/11 for the 8-slot belt). One VICE session, the village."""
import os
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game

CHAIN = True
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "out", "work")
QF = ("q_step", 1), ("q_flag", 1), ("q_cnt", 1), ("q_sdone", 2), ("q_side", 8), ("q_rep", 10), ("q_item", 6)


def poke_n(g, a, v):
    """the monitor command line is short: 120 values in one '>' are dropped (seen on 22/11)"""
    for i in range(0, len(v), 32): g.poke(a + i, *v[i:i + 32])


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


@test("QSAVE-10", "layout: 32 B of quest state contiguous in CHRBLK, inn chest at INN_AT (120 B under the KERNAL), file = CHRBLK + chest + 5 floors (4 blocks)")
def qsave_layout(ctx):
    L = ctx["g"].L
    a = L["q_step"]
    for name, n in QF:
        check(L[name] == a, "%s at $%04x (expected $%04x)" % (name, L[name], a))
        a += n
    check(a - L["q_step"] == 32 and a <= L["CHREND"], "quest state %d B, ends at $%04x (CHREND $%04x)" % (a - L["q_step"], a, L["CHREND"]))
    check(L["INN_AT"] == 0xff80 and L["INN_LEN"] == 5 * L["STASH_N"] and L["st_id"] == L["INN_AT"], "INN_AT $%04x INN_LEN %d" % (L["INN_AT"], L["INN_LEN"]))
    check(L["HERO_LEN"] == L["CHREND"] - L["CHRBLK"] <= 255, "HERO_LEN %d" % L["HERO_LEN"])
    check(L["SV_LEN"] == L["HERO_LEN"] + L["INN_LEN"] + 5 * L["LV_SLOT"], "SV_LEN %d" % L["SV_LEN"])
    check(-(-(L["SV_LEN"] + 2) // 254) == 4, "save file of %d blocks (expected 4)" % (-(-(L["SV_LEN"] + 2) // 254)))


@test("QSAVE-11", "save_char then load_char gives back the whole inn chest (120 B) and the 32 B of quest state; new_character empties both")
def qsave_roundtrip(ctx):
    g = ctx["g"]; L = g.L
    chest = [(i * 37 + 11) & 255 for i in range(L["INN_LEN"])]
    qs = [(i * 13 + 200) & 255 for i in range(32)]
    poke_n(g, L["INN_AT"], chest); poke_n(g, L["q_step"], qs)
    check(g.mem(L["INN_AT"], L["INN_LEN"]) == chest, "monitor: the chest was not written")
    h0 = g.mem(L["CHRBLK"], L["HERO_LEN"])
    g.call_keep(L["save_char"], tmax=90)
    g.fill(L["CHRBLK"], L["CHRBLK"] + L["HERO_LEN"] - 1, 0)
    g.fill(L["INN_AT"], L["INN_AT"] + L["INN_LEN"] - 1, 0)
    g.call_keep(L["load_char"], tmax=90)
    c1, h1 = g.mem(L["INN_AT"], L["INN_LEN"]), g.mem(L["CHRBLK"], L["HERO_LEN"])
    check(c1 == chest, "chest from disk differs at %s" % [i for i, (a, b) in enumerate(zip(chest, c1)) if a != b][:8])
    check(h1 == h0, "hero from disk differs at %s" % [i for i, (a, b) in enumerate(zip(h0, h1)) if a != b][:8])
    check(g.mem(L["q_step"], 32) == qs, "quest state %s" % g.mem(L["q_step"], 32))
    g.call_keep(L["new_character"], tmax=10)
    check(not any(g.mem(L["INN_AT"], L["INN_LEN"])) and not any(g.mem(L["q_step"], 32)), "new_character: chest %s, quest state %s" % (
        g.mem(L["INN_AT"], 8), g.mem(L["q_step"], 8)))
