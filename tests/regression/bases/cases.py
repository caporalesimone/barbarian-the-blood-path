"""Full item bases (21/11 evening, owner's decisions O1, O6; data/items/items.tsv from data/items/next/bases.tsv): 11 armors and
4 shields in the game, the DEX requirement (column min_dex -> itreq bit 7, req_chk). One VICE session, the village."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, K_I, D, U, inv_pack

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def screen(g):
    return "".join(chr(b + 96) if 1 <= b <= 26 else chr(b) if 32 <= b < 64 else " " for b in g.mem(0xB400, 1000))


@test("BASES-10", "item tables: 11 armors with CA 1..10, 4 shields with CA 1..4")
def bases_tables(ctx):
    g = ctx["g"]; L = g.L
    n = L["N_ITEMS"]
    cat, val = g.mem(L["itcat"], n), g.mem(L["itval"], n)
    ar = [val[i] for i in range(n) if cat[i] == L["CAT_ARMOR"]]
    sh = [val[i] for i in range(n) if cat[i] == L["CAT_SHIELD"]]
    check(len(ar) == 11 and ar[0] == 1 and ar[-1] == 10 and ar == sorted(ar), "armors CA %s (expected 11, 1..10 growing)" % ar)
    check(sh == [1, 2, 3, 4], "shields CA %s (expected 1, 2, 3, 4)" % sh)


@test("BASES-11", "inventory: the studded armor (DEX 14) stays in the pack with s_dex 13 ('dex 14' in its box); with DEX 14 it is equipped")
def bases_dex(ctx):
    g = ctx["g"]; L = g.L
    sa = L["I_STUDDED_ARMOR"]
    req = g.b(L["itreq"] + sa)
    check(req == 0x80 | 14, "itreq of the studded armor $%02x (expected $8e: DEX 14)" % req)
    a0 = g.b(L["c_eq"] + 1)
    g.poke(L["c_pack"], sa, 0, 0, 0, 0, 0, 0, 0); g.poke(L["c_packd"], 30); g.poke(L["c_packm"], 40); g.poke(L["c_packb"], 0)
    inv_pack(g)
    check(not g.in_game(), "the inventory does not open")
    g.poke(L["s_dex"], 13); g.poke(L["s_str"], 18)
    g.frames(1, joy=D); g.frames(1); g.frames(1, joy=U); g.frames(2)  # away and back: the box is redrawn
    check("dex 14" in screen(g), "no 'dex 14' on the screen")
    g.press_fire(); g.frames(2)
    check(g.b(L["c_eq"] + 1) == a0 and g.b(L["c_pack"]) == sa, "equipped with DEX 13 < 14")
    g.poke(L["s_dex"], 14)
    g.press_fire(); g.frames(2)
    check(g.b(L["c_eq"] + 1) == sa, "not equipped with DEX = requirement (armor %d)" % g.b(L["c_eq"] + 1))
    g.run_stop(); g.frames(2)
