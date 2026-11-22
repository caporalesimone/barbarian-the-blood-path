"""Affixes, phase 3 (21/11 evening): generation with every row of data/items/next/ (af_gen / af_pick: magic chance mag_t[T],
prefix / suffix / both, level window, cursed rows, rings by metal), prices with the affixes (it_cost) and the shops with 3..8
random wares (repetitions allowed, shop_rules.wares) whose magic share grows with the hero level (shm_t). One VICE session."""
from collections import Counter
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, find, fire_to

CHAIN = True
N = 250


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def sgn16(lo, hi):
    v = lo | hi << 8
    return v - 65536 if v > 32767 else v


@test("AFG-10", "gen_item at chestLevel 80 (T 10): magic share of weapons/armors/shields near mag_t[10]; every affix fits the item type; rings always have affixes, silver and gold both")
def afg_loot(ctx):
    g = ctx["g"]; L = g.L
    n = L["AF_NP"] + L["AF_NS"] + 1
    g.cmd("bank ram"); ty, mn = g.mem(L["af_ty"], n), g.mem(L["af_min"], n); g.cmd("bank cpu")   # (under the I/O, with the generator)
    cat = g.mem(L["itcat"], L["N_ITEMS"]); val = g.mem(L["itval"], L["N_ITEMS"])
    eq = mag = uq = 0; bad = []; rings = Counter()
    for _ in range(N):
        g.poke(L["gi_ll"], 80); g.poke(L["gi_force"], 0)
        r = g.call_keep(L["gen_item"])
        i, p, s = r["a"], g.b(L["ap_b"]), g.b(L["ap_s"])
        g.poke(L["ap_b"], 0); g.poke(L["ap_s"], 0)
        c = cat[i]
        if c > L["CAT_RING"]:
            check(p == 0 and s == 0, "potion or scroll %d with affixes %d/%d" % (i, p, s)); continue
        if s >= 0x80:                   # (22/11, phase 6) a unique: no affixes, its base (UNQ-13); counted apart
            check(p == 0 and g.b(L["un_base"] + (s & 0x7f)) == i, "unique %02x on item %d with prefix %d" % (s, i, p))
            uq += 1; continue
        bit = 1 << (c - 1)
        for k in ([p] if p else []) + ([s + L["AF_SX0"]] if s else []):
            if not ty[k] & bit or (mn[k] & 0x7f) > 20: bad.append((i, k))
        if c == L["CAT_RING"]:
            rings[(val[i], bool(p) + bool(s))] += 1
        else:
            eq += 1; mag += 1 if p or s else 0
    check(not bad, "affixes that do not fit: %s" % bad[:6])
    g.cmd("bank ram"); want = g.b(L["mag_t"] + 10) / 256; g.cmd("bank cpu")
    share = mag / max(1, eq)
    print("      magic %d / %d = %.2f (mag_t %.2f), rings %s, uniques %d" % (mag, eq, share, want, dict(rings), uq))
    # (below mag_t: an item of level 0 has no row with min_level <= 0, as in tools/simulators/items_model.py)
    check(eq >= 60 and 0.1 <= share <= want + 0.1, "magic share %.2f, expected up to about %.2f" % (share, want))
    check(all(k[1] >= 1 for k in rings) and all(k[1] == 2 for k in rings if k[0] >= 2), "rings: %s" % dict(rings))


@test("AFG-11", "it_cost: price = itprice + price_add of prefix and suffix (signed: a cursed row costs less), at least 1; scrolls ignore the quantity")
def afg_cost(ctx):
    g = ctx["g"]; L = g.L
    n = L["AF_NP"] + L["AF_NS"] + 1
    pl, ph = g.mem(L["af_pl"], n), g.mem(L["af_ph"], n)
    g.cmd("bank ram"); mn = g.mem(L["af_min"], n); g.cmd("bank cpu")
    sw = L["I_SWORD"]
    base = g.b(L["itprice"] + 2 * sw) | g.b(L["itprice"] + 2 * sw + 1) << 8
    p, cur = L["MAG_W2"], next(k for k in range(1, L["AF_NP"] + 1) if mn[k] & 0x80)
    s = L["RSX_11"]
    def cost(i, x, y):
        g.call_keep(L["it_cost"], regs="a=%02x,x=%02x,y=%02x" % (i, x, y))
        return g.b(L["tmp0"]) | g.b(L["tmp1"]) << 8
    got = cost(sw, p, s)
    want = base + sgn16(pl[p], ph[p]) + sgn16(pl[s + L["AF_SX0"]], ph[s + L["AF_SX0"]])
    check(got == want, "sword with prefix %d and suffix %d: %d (expected %d)" % (p, s, got, want))
    got = cost(sw, cur, 0)
    check(got == max(1, base + sgn16(pl[cur], ph[cur])) and got < base, "sword with a cursed prefix: %d (base %d)" % (got, base))
    sc = L["I_SCROLL"]
    check(cost(sc, 7, 0) == (g.b(L["itprice"] + 2 * sc) | g.b(L["itprice"] + 2 * sc + 1) << 8), "scroll price with quantity 7")


@test("AFG-12", "blacksmith: 3..8 wares from the filtered pool (repetitions allowed), empty entries after them")
def afg_shop(ctx):
    g = ctx["g"]; L = g.L
    door = find(g, L["T_DSMITH"])
    check(door, "no blacksmith door on the map")
    fire_to(g, door[0][0], door[0][1] + 1)
    check(g.b(L["sh_mask"]) != 0, "the blacksmith does not open")
    ids = g.mem(L["l8_id"], 8)
    k = sum(1 for i in ids if i)
    check(L["SHOP_KMIN"] <= k <= L["SHOP_KMIN"] + L["SHOP_KN"] - 1 and all(ids[:k]) and not any(ids[k:]), "wares %s" % ids)
    cat = g.mem(L["itcat"], L["N_ITEMS"])
    check(all(cat[i] <= L["CAT_SHIELD"] for i in ids[:k]), "the blacksmith sells %s" % ids)
    g.run_stop(); g.frames(2)
