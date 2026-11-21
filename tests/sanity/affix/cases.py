"""Affixes, phase 2b (21/11 evening; data/items/next/prefixes.tsv and suffixes.tsv -> af_pw / af_val in GAME, af_names in CORE):
the item byte "bonus" is the prefix id, the fifth byte the suffix id. Today's magic +N becomes a prefix (weapons ATT_DMG, armors
and shields AC: mag_px), the ring stat a suffix (of strength / dexterity / vitality and their stronger rows: ring_sx); recalc_stats
adds the affixes of what is worn; the lists show "prefix name of suffix" cut at 16 columns. One VICE session, the village."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, key, K_I

CHAIN = True
PW = ["ATT_DMG", "ATT", "DMG", "AC", "STR", "DEX", "CON", "ALL"]


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def sgn(b):
    return b - 256 if b > 127 else b


def screen(g):
    return "".join(chr(b + 96) if 1 <= b <= 26 else chr(b) if 32 <= b < 64 else " " for b in g.mem(0xB400, 1000))


@test("AFX-10", "mag_px: magic N of weapons -> an ATT_DMG +N prefix, of armors and shields -> AC +N; ring_sx: stat x metal -> STR/DEX/CON +metal suffix")
def afx_tables(ctx):
    g = ctx["g"]; L = g.L
    n = L["AF_NP"] + L["AF_NS"] + 1
    pw, val = g.mem(L["af_pw"], n), g.mem(L["af_val"], n)
    mag = g.mem(L["mag_px"], 12)
    for c, want in enumerate(("ATT_DMG", "AC", "AC")):
        check(mag[4 * c] == 0, "mag_px[%d] = %d (expected 0: no magic)" % (4 * c, mag[4 * c]))
        for k in (1, 2, 3):
            i = mag[4 * c + k]
            check(1 <= i <= L["AF_NP"] and pw[i] == L["PW_" + want] and sgn(val[i]) == k, "mag_px[%d]: row %d power %d value %d (expected %s +%d)" % (4 * c + k, i, pw[i], sgn(val[i]), want, k))
    rs = g.mem(L["ring_sx"], 9)
    for st, nm in enumerate(("STR", "DEX", "CON")):
        for m in (1, 2, 3):
            i = rs[st * 3 + m - 1] + L["AF_SX0"]
            check(pw[i] == L["PW_" + nm] and sgn(val[i]) == m, "ring_sx[%d]: power %d value %d (expected %s +%d)" % (st * 3 + m - 1, pw[i], sgn(val[i]), nm, m))


def stats(g):
    L = g.L
    g.call_keep(L["recalc_stats"])
    return dict(att=g.b(L["s_att"]), dk=g.b(L["s_dk"]), ac=g.b(L["s_ac"]), str=g.b(L["s_str"]))


@test("AFX-11", "recalc_stats: weapon prefix ATT_DMG +2 -> ATT and damage +2; armor prefix AC +2 -> AC +2; ring suffix STR +2 -> STR +4")
def afx_recalc(ctx):
    g = ctx["g"]; L = g.L
    mag, rs = g.mem(L["mag_px"], 12), g.mem(L["ring_sx"], 9)
    g.poke(L["c_eqb"], 0, 0, 0, 0, 0); g.poke(L["c_eqs"], 0, 0, 0, 0, 0)
    g.poke(L["c_eq"] + 1, L["I_LEATHER_ARMOR"]); g.poke(L["c_eqd"] + 1, 30); g.poke(L["c_eqm"] + 1, 30)
    g.poke(L["c_eq"] + 3, L["I_SILVER"])
    s0 = stats(g)
    g.poke(L["c_eqb"], mag[2]); g.poke(L["c_eqb"] + 1, mag[4 + 2])
    s1 = stats(g)
    check(s1["att"] == s0["att"] + 2 and s1["dk"] == s0["dk"] + 2, "ATT %d -> %d, damage %d -> %d (expected +2, +2)" % (s0["att"], s1["att"], s0["dk"], s1["dk"]))
    check(s1["ac"] == s0["ac"] + 2, "AC %d -> %d (expected +2)" % (s0["ac"], s1["ac"]))
    g.poke(L["c_eqs"] + 3, rs[0 * 3 + 2 - 1])                    # the ring: STR +4, so the weapon modifier +2 too
    s3 = stats(g)
    check(s3["str"] == s1["str"] + 4 and s3["att"] == s1["att"] + 2, "STR %d -> %d, ATT %d -> %d (expected +4, +2)" % (s1["str"], s3["str"], s1["att"], s3["att"]))
    g.poke(L["c_eqd"] + 1, 0)                                   # broken armor: its affix does not count
    s2 = stats(g)
    check(s2["ac"] < s1["ac"] - 2, "AC %d with the broken armor (its prefix still counts?)" % s2["ac"])
    g.poke(L["c_eqb"], 0, 0, 0, 0, 0); g.poke(L["c_eqs"], 0, 0, 0, 0, 0); g.poke(L["c_eq"] + 3, 0); g.poke(L["c_eqd"] + 1, 30)
    stats(g)


@test("AFX-12", "inventory: 'fine sword' (prefix, pack) and 'copper ring of s' (suffix, worn, cut at 16 columns) in the list")
def afx_names(ctx):
    g = ctx["g"]; L = g.L
    mag, rs = g.mem(L["mag_px"], 12), g.mem(L["ring_sx"], 9)
    g.poke(L["c_pack"], L["I_SWORD"], 0, 0, 0, 0, 0, 0, 0)
    g.poke(L["c_packb"], mag[2], 0, 0, 0, 0, 0, 0, 0); g.poke(L["c_packs"], 0, 0, 0, 0, 0, 0, 0, 0)
    g.poke(L["c_eq"] + 3, L["I_COPPER"]); g.poke(L["c_eqb"] + 3, 0); g.poke(L["c_eqs"] + 3, rs[0])   # worn: always in view
    key(g, K_I, 3)
    check(not g.in_game(), "the inventory does not open")
    s = screen(g)
    check("fine sword" in s, "no 'fine sword' on the screen")
    check("copper ring of s" in s and "copper ring of st" not in s, "ring name not cut at 16 columns: %s" % [s[i:i+40] for i in range(0, 1000, 40) if "copper" in s[i:i+40]])
    g.run_stop(); g.frames(2)
