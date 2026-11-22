"""Affixes, phase 5 (21/11 evening, owner's decisions O7, O8, ex B4): quality colour of the name (magic light blue, cursed grey
UC_CURSED), full name in the title of the item box (up to 34 columns), long names scrolling on the cursor row of the lists
(sl_nav: one character every 8 frames, pauses at both ends). One VICE session, the village, the real inventory."""
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


def sgn(b):
    return b - 256 if b > 127 else b


def row(g, y):
    return "".join(chr(b + 96) if 1 <= b <= 26 else chr(b) if 32 <= b < 64 else "." for b in g.mem(0xB400 + 40 * y, 40))


def find_row(g, text):
    for y in range(25):
        if text in row(g, y): return y
    return None


def rows(g, n):
    L = g.L
    p, v = g.mem(L["af_pw"], n), g.mem(L["af_val"], n)
    return p, v


@test("AFU-10", "inventory: an item with a cursed prefix has its name in grey (UC_CURSED), a magic one in light blue (UC_MAGIC)")
def afu_colour(ctx):
    g = ctx["g"]; L = g.L
    n = L["AF_NP"] + L["AF_NS"] + 1
    p, v = rows(g, n)
    cur = next(k for k in range(1, L["AF_NP"] + 1) if sgn(v[k]) < 0 and p[k] in (L["PW_DMG"], L["PW_ATT_DMG"]))
    g.poke(L["c_pack"], L["I_SWORD"], L["I_MACE"], 0, 0, 0, 0, 0, 0)
    g.poke(L["c_packb"], cur, L["MAG_W1"], 0, 0, 0, 0, 0, 0); g.poke(L["c_packs"], 0, 0, 0, 0, 0, 0, 0, 0)
    key(g, K_I, 3)
    check(not g.in_game(), "the inventory does not open")
    g.frames(1, joy=D); g.frames(1); g.frames(1, joy=U); g.frames(2)
    y = find_row(g, "sword"); y2 = find_row(g, " mace")
    check(y is not None and y2 is not None, "names not on the screen")
    x = row(g, y).index("sword"); x2 = row(g, y2).index("mace")
    c, c2 = g.b(0xD800 + 40 * y + x) & 15, g.b(0xD800 + 40 * y2 + x2) & 15
    check(c == L["UC_CURSED"] and c2 == L["UC_MAGIC"], "colours %d / %d (expected %d cursed, %d magic)" % (c, c2, L["UC_CURSED"], L["UC_MAGIC"]))
    g.run_stop(); g.frames(2)


@test("AFU-11", "inventory: the item box title shows the full name beyond 16 columns ('... studded armor of ...')")
def afu_title(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_pack"], L["I_STUDDED_ARMOR"], 0, 0, 0, 0, 0, 0, 0)
    g.poke(L["c_packb"], L["MAG_A2"], 0, 0, 0, 0, 0, 0, 0); g.poke(L["c_packs"], L["RSX_11"], 0, 0, 0, 0, 0, 0, 0)
    key(g, K_I, 3)
    g.frames(1, joy=D); g.frames(1); g.frames(1, joy=U); g.frames(2)
    t = row(g, L["IV_SY"])
    check("studded armor of" in t, "box title %r" % t.strip())
    g.run_stop(); g.frames(2)


@test("AFU-12", "inventory: a 32-character name is whole on its row (33 columns, 22/11); a 35-character one scrolls on the cursor row")
def afu_scroll(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_pack"], L["I_STUDDED_ARMOR"], L["I_VIKING_SWORD"], 0, 0, 0, 0, 0, 0)
    g.poke(L["c_packb"], L["MAG_A2"], L["MAG_W3"], 0, 0, 0, 0, 0, 0); g.poke(L["c_packs"], L["RSX_11"], L["RSX_21"], 0, 0, 0, 0, 0, 0)
    key(g, K_I, 3)
    g.frames(1, joy=D); g.frames(1); g.frames(1, joy=U); g.frames(2)
    y = next((y for y in range(25) if row(g, y).startswith(".>")), None)
    check(y is not None, "no cursor row")
    rs = [row(g, k) for k in range(25)]
    check(any("strong studded armor of strength" in r for r in rs), "the 32-character name is not whole in the list")
    sw = next((k for k in range(25) if "viking sword" in rs[k]), None)
    check(sw is not None, "no viking sword row")
    while y != sw:                      # cursor on the sword
        g.frames(1, joy=D if sw > y else U); g.frames(2)
        y = next(k for k in range(25) if row(g, k).startswith(".>"))
    r0 = row(g, y)
    for _ in range(80): g.frames(1)       # 8 frames per step: 6 steps of pause, then 2 characters (skip 2 from step 8)
    r1 = row(g, y)
    print("      %r -> %r" % (r0[4:39], r1[4:39]))
    check("of dexterity" not in r0 and "of dexterity" in r1, "the 35-character name does not scroll: %r -> %r" % (r0, r1))
    g.run_stop(); g.frames(2)


@test("AFU-13", "inventory: the item box lists the powers not in the numbers: armor 'of the wolf' -> 'hp+12', shield 'of health' -> 'hit-1'")
def afu_powers(ctx):
    g = ctx["g"]; L = g.L
    n = L["AF_NP"] + L["AF_NS"] + 1
    p, v = rows(g, n)
    def sfx(pw, val):
        return next(k - L["AF_SX0"] for k in range(L["AF_SX0"] + 1, n) if p[k] == L["PW_" + pw] and sgn(v[k]) == val)
    for item, s, want in ((L["I_LEATHER_ARMOR"], sfx("LIFE", 12), "hp+12"), (L["I_SMALL_SHIELD"], sfx("GETHIT", 1), "hit-1")):
        g.poke(L["c_pack"], item, 0, 0, 0, 0, 0, 0, 0)
        g.poke(L["c_packb"], 0, 0, 0, 0, 0, 0, 0, 0); g.poke(L["c_packs"], s, 0, 0, 0, 0, 0, 0, 0)
        key(g, K_I, 3)
        g.frames(1, joy=D); g.frames(1); g.frames(1, joy=U); g.frames(2)
        r = row(g, L["IV_SY"] + 1)
        check(want in r, "box row %r without %r" % (r.strip(), want))
        g.run_stop(); g.frames(2)
