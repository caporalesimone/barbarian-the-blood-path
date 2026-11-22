"""Affixes, phase 4 (21/11 evening): the powers beyond ATT/damage/AC/stats. recalc_stats: life (hpmax), damage taken -N (s_gh,
used by hurt_player, at least 1), penetration (s_pen), speed (s_rate: frames less, at least RATE_MIN); at birth (add_to_pack ->
af_dur): durability +50% / +100% / -50% of the rolled maximum, indestructible = no wear (maximum 0). Life leech and thorns come
after 2.0 (O5): weight 0, never generated. One VICE session, the village."""
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


def sgn(b):
    return b - 256 if b > 127 else b


def sfx(g, pw, val):
    """suffix id with power PW_<pw> and value val"""
    L = g.L
    n = L["AF_NP"] + L["AF_NS"] + 1
    p, v = g.mem(L["af_pw"], n), g.mem(L["af_val"], n)
    for k in range(L["AF_SX0"] + 1, n):
        if p[k] == L["PW_" + pw] and sgn(v[k]) == val:
            return k - L["AF_SX0"]
    raise AssertionError("no suffix %s %d" % (pw, val))


def stats(g):
    L = g.L
    g.call_keep(L["recalc_stats"])
    return dict(hp=g.w16(L["hpmax"]), gh=g.b(L["s_gh"]), pen=g.b(L["s_pen"]), rate=g.b(L["s_rate"]))


@test("AFP-10", "recalc_stats: armor 'of the wolf' -> hpmax +12; shield 'of health' -> s_gh 1; weapon 'of piercing' -> pen +1, 'of readiness' -> rate -1")
def afp_recalc(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["c_eqb"], 0, 0, 0, 0, 0); g.poke(L["c_eqs"], 0, 0, 0, 0, 0)
    g.poke(L["c_eq"] + 1, L["I_LEATHER_ARMOR"]); g.poke(L["c_eqd"] + 1, 30); g.poke(L["c_eqm"] + 1, 30)
    g.poke(L["c_eq"] + 2, L["I_SMALL_SHIELD"]); g.poke(L["c_eqd"] + 2, 30); g.poke(L["c_eqm"] + 2, 30)
    s0 = stats(g)
    g.poke(L["c_eqs"] + 1, sfx(g, "LIFE", 12)); g.poke(L["c_eqs"] + 2, sfx(g, "GETHIT", 1)); g.poke(L["c_eqs"], sfx(g, "PEN", 1))
    s1 = stats(g)
    check(s1["hp"] == s0["hp"] + 12 and s1["gh"] == 1 and s1["pen"] == s0["pen"] + 1, "before %s after %s" % (s0, s1))
    g.poke(L["c_eqs"], sfx(g, "SPEED", 1))
    s2 = stats(g)
    check(s2["rate"] == max(L["RATE_MIN"], s0["rate"] - 1), "rate %d -> %d" % (s0["rate"], s2["rate"]))


@test("AFP-11", "hurt_player with s_gh 2: 5 damage -> -3 hp, 1 damage -> -1 hp (at least 1)")
def afp_hurt(ctx):
    g = ctx["g"]; L = g.L
    for d, want in ((5, 3), (1, 1), (2, 1)):
        g.call_keep(L["recalc_stats"])
        g.poke(L["s_gh"], 2); g.poke16(L["c_hp"], 100); g.poke(L["cb_dl"], d, 0)
        g.call_keep(L["hurt_player"])
        check(g.w16(L["c_hp"]) == 100 - want, "damage %d: hp %d (expected %d)" % (d, g.w16(L["c_hp"]), 100 - want))
    g.poke(L["c_eqs"], 0, 0, 0, 0, 0); g.call_keep(L["recalc_stats"]); g.call_keep(L["hp_full"])


@test("AFP-12", "add_to_pack (same random state): durability +50 -> max + max/2, +100 -> max x 2 (at most 255), -50 -> max - max/2, indestructible -> 0")
def afp_dur(ctx):
    g = ctx["g"]; L = g.L
    sw = L["I_SWORD"]
    n = L["AF_NP"] + L["AF_NS"] + 1
    p = g.mem(L["af_pw"], n)
    ind = next(k - L["AF_SX0"] for k in range(L["AF_SX0"] + 1, n) if p[k] == L["PW_INDESTRUCTIBLE"])
    seed = g.mem(L["rnd"], 2)
    def give(s):
        g.fill(L["c_pack"], L["c_pack"] + 7, 0)
        g.poke(L["rnd"], *seed); g.poke(L["ap_b"], 0); g.poke(L["ap_s"], s); g.poke(L["ap_m"], 0)
        g.call_keep(L["add_to_pack"], regs="a=%02x" % sw)
        return g.b(L["c_packd"]), g.b(L["c_packm"]), g.b(L["c_packs"])
    d0, m0, _ = give(0)
    check(d0 == m0 and m0 > 0, "plain sword %d/%d" % (d0, m0))
    for s, want in ((sfx(g, "DUR", 50), min(255, m0 + m0 // 2)), (sfx(g, "DUR", 100), min(255, m0 + 2 * (m0 // 2))),
                    (sfx(g, "DUR", -50), max(1, m0 - m0 // 2)), (ind, 0)):
        d, m, ss = give(s)
        check((d, m, ss) == (want, want, s), "suffix %d: %d/%d (expected %d/%d)" % (s, d, m, want, want))
    g.fill(L["c_pack"], L["c_pack"] + 7, 0)


@test("AFP-13", "af_ch: life leech and thorns have weight 0 (after 2.0, decision O5), every other row a weight > 0")
def afp_weights(ctx):
    g = ctx["g"]; L = g.L
    n = L["AF_NP"] + L["AF_NS"] + 1
    p = g.mem(L["af_pw"], n)
    g.cmd("bank ram"); ch = g.mem(L["af_ch"], n); g.cmd("bank cpu")   # (under the I/O, with the generator)
    bad = [k for k in range(1, n) if (ch[k] == 0) != (p[k] in (L["PW_LEECH"], L["PW_THORNS"]))]
    check(not bad, "rows with a wrong weight: %s" % bad)


@test("AFP-14", "recalc_stats with cursed items: 3 x 'of weakness' (STR 16 -> 10) and a 'bent' weapon -> s_mod 0, s_dk 0 (not 255); 4 x -> STR 8, s_mod still 0 (not 126)")
def afp_cursed(ctx):
    g = ctx["g"]; L = g.L
    n = L["AF_NP"] + L["AF_NS"] + 1
    p, v = g.mem(L["af_pw"], n), g.mem(L["af_val"], n)
    weak = sfx(g, "STR", -1)
    bent = next(k for k in range(1, L["AF_NP"] + 1) if p[k] == L["PW_DMG"] and sgn(v[k]) == -1)
    keep = [g.mem(L[t], 5) for t in ("c_eq", "c_eqb", "c_eqs", "c_eqd", "c_eqm")]
    sadd = g.mem(L["c_sadd"], 3)
    g.poke(L["c_sadd"], 0, 0, 0)
    g.poke(L["c_eq"], L["I_SWORD"], L["I_LEATHER_ARMOR"], L["I_SMALL_SHIELD"], L["I_COPPER"], L["I_COPPER"])
    g.poke(L["c_eqd"], 30, 30, 30, 0, 0); g.poke(L["c_eqm"], 30, 30, 30, 0, 0)
    for rings, strv in ((0, 10), (1, 8)):
        g.poke(L["c_eqb"], bent, 0, 0, 0, 0)
        g.poke(L["c_eqs"], weak, weak, weak, weak if rings else 0, 0)
        g.call_keep(L["recalc_stats"])
        st, mod, dk = g.b(L["s_str"]), g.b(L["s_mod"]), g.b(L["s_dk"])
        check(st == strv and mod == 0 and dk == 0, "STR %d (expected %d), s_mod %d, s_dk %d (expected 0, 0)" % (st, strv, mod, dk))
    for t, vals in zip(("c_eq", "c_eqb", "c_eqs", "c_eqd", "c_eqm"), keep): g.poke(L[t], *vals)
    g.poke(L["c_sadd"], *sadd); g.call_keep(L["recalc_stats"]); g.call_keep(L["hp_full"])
