"""Gold (10/11, sanity of the gold-in-tens feature, moved to regression on 11/11): inn chest gold in tens, payment with the total gold, no withdrawal, a sale
over the purse cap does nothing. Only GAME and the module MENU (its zones, out/work/menu_zK.prg; 11/11) are loaded in VICE,
without starting the game, and the real routines are called (st_gold, add_gold16, gold_need/gold_pay, shop_buy/shop_sell
with a simulated confirmation) with the state written to memory, $01 = $35 as in the menus (zone 2 is under the
KERNAL): one session, ~2 s."""
import os
from lib.c64 import Vice, labels, OUT
from c64test import test, check

GOLD_MAX = 10000
PACK_N = 8


def setup(ctx):
    v = ctx["v"] = Vice()
    v.load(os.path.join(OUT, "game.prg"))
    v.cmd("bank ram")
    for k in (1, 2, 3):
        v.load(os.path.join(OUT, "menu_z%d.prg" % k))
    v.cmd("bank cpu")
    v.poke(1, 0x35)                                             # KERNAL out, as in the menus
    L = labels("game"); L.update(labels("menu"))
    ctx["L"] = L


def teardown(ctx):
    if "v" in ctx: ctx["v"].close()


def gold(v, L): return v.w16(L["c_gold"]), v.w16(L["c_sgold"])


@test("INN-GOLD-10", "inn chest: deposit in tens (remainder kept, chest full, purse full)")
def inn_gold(ctx):
    v, L = ctx["v"], ctx["L"]
    bad = []
    for g, sg, want in [(1000, 500, (0, 600)), (1007, 500, (7, 600)), (1000, 65500, (650, 65535)), (9, 700, (9, 700)),
                        (0, 700, (0, 700)), (10000, 0, (0, 1000)), (10000, 65535, (10000, 65535))]:
        v.poke16(L["c_gold"], g); v.poke16(L["c_sgold"], sg); v.poke(L["ui_cur"], 0)
        v.call(L["st_gold"])
        if gold(v, L) != want: bad.append("%d/%d -> %s (expected %s)" % (g, sg, gold(v, L), want))
    check(not bad, "; ".join(bad))


@test("GOLD-CAP-10", "gold picked up: GOLD_MAX cap on the hero (add_gold16)")
def gold_cap(ctx):
    v, L = ctx["v"], ctx["L"]
    bad = []
    for g, add, want in [(500, 430, 930), (9990, 20, 10000), (10000, 65535, 10000), (0, 10000, 10000), (0, 10001, 10000)]:
        v.poke16(L["c_gold"], g)
        a = L["add_gold16"]                                     # sei; lda #lo; ldx #hi; jsr add_gold16; nop
        v.poke(0x0340, 0x78, 0xa9, add & 255, 0xa2, add >> 8, 0x20, a & 255, a >> 8, 0xea)
        v.brk(0x0348); v.pc(0x0340); v.go(); v.delbrk()
        if v.w16(L["c_gold"]) != want: bad.append("%d + %d -> %d (expected %d)" % (g, add, v.w16(L["c_gold"]), want))
    check(not bad, "; ".join(bad))


def model_buy(g, sg, p):
    """expected (carried, chest) after paying p, or None if there is not enough gold"""
    if g + 10 * sg < p: return None
    if g >= p: return g - p, sg
    need = p - g
    dec = -(-need // 10)
    return dec * 10 - need, sg - dec


@test("SHOP-PAY-10", "payment: carried gold first, then the chest in tens, change back on the hero (gold_need/gold_pay)")
def shop_pay(ctx):
    v, L = ctx["v"], ctx["L"]
    gn, gp = L["gold_need"], L["gold_pay"]
    # 0350: sei; jsr gold_need; php; pla; sta 03f0; bcs +3 (C=1: no payment); jsr gold_pay; nop
    v.poke(0x0350, 0x78, 0x20, gn & 255, gn >> 8, 0x08, 0x68, 0x8d, 0xf0, 0x03, 0xb0, 0x03, 0x20, gp & 255, gp >> 8, 0xea)
    bad = []
    for g, sg, price in [(100, 1000, 5000), (7, 10, 15), (5000, 10, 3000), (0, 0, 10), (100, 489, 5000), (100, 490, 5000),
                         (0, 65535, 60000), (9, 1, 19), (10000, 0, 10000), (0, 1, 10)]:
        v.poke16(L["c_gold"], g); v.poke16(L["c_sgold"], sg); v.poke16(L["shp_price"], price)
        v.brk(0x035e); v.pc(0x0350); v.go(); v.delbrk()
        c = v.b(0x03f0) & 1
        want = model_buy(g, sg, price)
        got = gold(v, L)
        if not ((want is None and c == 1 and got == (g, sg)) or (want is not None and c == 0 and got == want)):
            bad.append("%d/%d price %d -> C=%d %s (expected %s)" % (g, sg, price, c, got, want))
    check(not bad, "; ".join(bad))


def shop_ctx(ctx):
    """prices tried (lowest, median, highest among weapons, armour, shields, rings) and shop_ask patched"""
    if "picks" in ctx: return ctx["picks"]
    v, L = ctx["v"], ctx["L"]
    n = 80
    cat, pr = v.mem(L["itcat"], n), v.mem(L["itprice"], 2 * n)
    price = {i: pr[2 * i] + 256 * pr[2 * i + 1] for i in range(1, n)}
    cand = sorted((price[i], i) for i in range(1, n) if cat[i] in (1, 2, 3, 4) and 0 < price[i] <= 9000)
    v.poke(L["shop_ask"], 0x38, 0x60)                       # shop_ask: confirm (C=1) without keyboard
    ctx["picks"] = [cand[0], cand[len(cand) // 2], cand[-1]]
    return ctx["picks"]


def shop_call(ctx, routine, g, sg, pack, lc, mask, item):
    v, L = ctx["v"], ctx["L"]
    v.fill(L["c_pack"], L["c_eqm"] + 3, 0); v.fill(L["c_beltt"], L["c_beltt"] + 3, 0)
    if pack: v.poke(L["c_pack"], *pack)
    v.poke16(L["c_gold"], g); v.poke16(L["c_sgold"], sg)
    v.poke(L["ui_lc"], lc); v.poke(L["sh_mask"], mask, 0xff); v.poke(L["l8_id"], item)
    v.call(L[routine])
    h0 = L["c_gold"]
    m = v.mem(h0, L["c_sgold"] + 2 - h0)
    return m[0] + 256 * m[1], m[L["c_sgold"] - h0] + 256 * m[L["c_sgold"] - h0 + 1], m[L["c_pack"] - h0:L["c_pack"] - h0 + PACK_N]


@test("SHOP-BUY-10", "buy: 3 prices x different gold x pack full/empty (gold, chest, pack)")
def shop_buy(ctx):
    bad = []
    for p, it in shop_ctx(ctx):
        td = -(-p // 10)
        scen = [(0, 0), (p - 1, 0), (p, 0), (min(p + 1234, GOLD_MAX), 5), (0, td), (0, td - 1), (7, td), (5, (p - 5) // 10),
                (3, -(-(p - 3) // 10)), (100, 1000), (GOLD_MAX, 65535), (0, 65535), (p % 10, p // 10 + 3)]
        if p > 100: scen += [(100, -(-(p - 100) // 10)), (100, -(-(p - 100) // 10) - 1), (99, 1000)]
        for g, sg in scen:
            sg, g = max(sg, 0), min(g, GOLD_MAX)
            for full in (False, True):
                pack = [2 if it != 2 else 3] * PACK_N if full else []
                want = model_buy(g, sg, p)
                gg, ss, pk = shop_call(ctx, "shop_buy", g, sg, pack, 12, 0x7e, it)
                exp = (g, sg, 0) if want is None or full else (want[0], want[1], 1)
                if (gg, ss, pk.count(it)) != exp:
                    bad.append("price %d, %d/%d%s -> %s (expected %s)" % (p, g, sg, " pack full" if full else "", (gg, ss, pk.count(it)), exp))
    check(not bad, "; ".join(bad[:4]) + (" (+%d)" % (len(bad) - 4) if len(bad) > 4 else ""))


@test("SHOP-SELL-10", "sell: price >> SELL_SHIFT, GOLD_MAX cap (no sale), category not bought, empty entry")
def shop_sell(ctx):
    bad = []
    for p, it in shop_ctx(ctx):
        half = p >> ctx["L"]["SELL_SHIFT"]
        for g, sg, mask in [(0, 50, 0x7e), (1234, 7, 0x7e), (GOLD_MAX - half, 3, 0x7e), (GOLD_MAX - half + 1, 3, 0x7e),
                            (GOLD_MAX, 65535, 0x7e), (500, 20, 0x00)]:
            gg, ss, pk = shop_call(ctx, "shop_sell", g, sg, [it], 0, mask, 0)
            sold = mask != 0 and g + half <= GOLD_MAX
            exp = (g + half if sold else g, sg, 0 if sold else 1)
            if (gg, ss, pk.count(it)) != exp:
                bad.append("price %d, %d/%d mask %02x -> %s (expected %s)" % (p, g, sg, mask, (gg, ss, pk.count(it)), exp))
    gg, ss, pk = shop_call(ctx, "shop_sell", 777, 5, [], 3, 0x7e, 0)
    if (gg, ss) != (777, 5): bad.append("empty entry: %d/%d" % (gg, ss))
    check(not bad, "; ".join(bad))


@test("SHOP-FIX-10", "smith repair (shop_repair, confirmation simulated): sword 200, durability 10/100, 1000 gold -> 950, 99/99")
def shop_fix(ctx):
    v, L = ctx["v"], ctx["L"]
    shop_ctx(ctx)                                               # (shop_ask patched: confirmed without keyboard)
    sw = labels("game")["I_SWORD"] if "I_SWORD" in labels("game") else None
    check(sw is not None, "I_SWORD not in game.lbl")
    eq = L["c_eq"]
    v.poke(eq, sw); v.poke(L["c_eqd"], 10); v.poke(L["c_eqm"], 100)
    v.poke16(L["c_gold"], 1000); v.poke16(L["c_sgold"], 0)
    v.poke(L["ui_lc"], 8); v.poke(L["sh_mask"], 0x0e)
    v.call(L["shop_repair"], regs="x=08")
    g, d, m = v.w16(L["c_gold"]), v.b(L["c_eqd"]), v.b(L["c_eqm"])
    price = v.w16(L["itprice"] + 2 * sw)
    check(price == 200, "sword price %d (the test expects 200)" % price)
    check((g, d, m) == (950, 99, 99), "gold %d durability %d/%d (expected 950 99/99)" % (g, d, m))
