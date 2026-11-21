"""Fifth item byte, the suffix (21/11 evening, save format $CC, phase 2a of the affixes; owner's decision: 5-byte item) and the hero
file with only the floors of the current chapter (decision C1 of the plan F7). The suffix must travel with its item everywhere:
equipping (eq_get / pk_swap / eq_put), sorting (sort4 with 5 tables), the inn chest (st_move) and the hero file. One VICE session,
the village."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, K_I, D, U

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


@test("SFX-10", "inventory: equipping an armor with suffix 7 puts 7 in c_eqs[1]; the old armor goes to the pack with its suffix 5")
def sfx_equip(ctx):
    g = ctx["g"]; L = g.L
    la, ch = L["I_LEATHER_ARMOR"], L["I_QUILTED_ARMOR"]
    g.poke(L["c_eq"] + 1, ch); g.poke(L["c_eqs"] + 1, 5)
    g.poke(L["c_pack"], la, 0, 0, 0, 0, 0, 0, 0); g.poke(L["c_packs"], 7, 0, 0, 0, 0, 0, 0, 0)
    g.poke(L["c_packd"], 30); g.poke(L["c_packm"], 40); g.poke(L["c_packb"], 0)
    key(g, K_I, 3)
    check(not g.in_game(), "the inventory does not open")
    g.press_fire(); g.frames(2)
    check(g.b(L["c_eq"] + 1) == la and g.b(L["c_eqs"] + 1) == 7, "equipped %d suffix %d (expected %d, 7)" % (g.b(L["c_eq"] + 1), g.b(L["c_eqs"] + 1), la))
    check(g.b(L["c_pack"]) == ch and g.b(L["c_packs"]) == 5, "pack %d suffix %d (expected %d, 5)" % (g.b(L["c_pack"]), g.b(L["c_packs"]), ch))
    g.run_stop(); g.frames(2)


@test("SFX-11", "sort_pack: the suffix follows its item (5 parallel tables)")
def sfx_sort(ctx):
    g = ctx["g"]; L = g.L
    sw, pr = L["I_SWORD"], L["I_POTR"]
    g.poke(L["c_pack"], pr, 0, sw, 0, 0, 0, 0, 0); g.poke(L["c_packs"], 0, 0, 9, 0, 0, 0, 0, 0)
    g.call_keep(L["sort_pack"])
    p, s = g.mem(L["c_pack"], 2), g.mem(L["c_packs"], 2)
    check(p == [sw, pr] and s == [9, 0], "pack %s suffixes %s (expected [%d, %d], [9, 0])" % (p, s, sw, pr))


@test("SFX-12", "hero file: HERO_LEN 254, file of HERO_LEN + 5 x LV_SLOT; save_char then load_char gives back c_packs, c_eqs and st_sx")
def sfx_save(ctx):
    g = ctx["g"]; L = g.L
    check(L["HERO_LEN"] == 254 and L["SV_LEN"] == L["HERO_LEN"] + 5 * L["LV_SLOT"], "HERO_LEN %d SV_LEN %d" % (L["HERO_LEN"], L["SV_LEN"]))
    g.poke(L["c_packs"], 1, 2, 3, 4, 5, 6, 7, 8); g.poke(L["c_eqs"], 11, 12, 13, 14, 15); g.poke(L["st_sx"], 21, 22, 23)
    s0 = g.mem(L["CHRBLK"], L["HERO_LEN"])
    g.call_keep(L["save_char"], tmax=90)
    g.fill(L["CHRBLK"], L["CHRBLK"] + L["HERO_LEN"] - 1, 0)
    g.call_keep(L["load_char"], tmax=90)
    s1 = g.mem(L["CHRBLK"], L["HERO_LEN"])
    check(s1 == s0, "hero from disk differs at %s" % [i for i, (a, b) in enumerate(zip(s0, s1)) if a != b][:8])
