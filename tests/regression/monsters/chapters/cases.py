"""Monsters of the chapters (15/11, TODO M9, docs/wiki/bestiario.md): every chapter has its own 4 families + 4 strong variants
(same monster types 1..8: the statistics do not change, data/balance.yaml by depth). The theme file GFXn of the chapter
carries their sprites and, in an "info" block at its end, their sprite colours and names (tools/build/gen_gfx.py);
gfx_install copies the sprites to the sprite slots and the info block to NM_AT. The expected values come from the drawings
(tools/build/monsters.py, tools/build/monsters_chap.py) through the same functions as the build. One VICE session (CHAIN).
Screenshots: out/work/villages/monsters<c>.png (a monster of the chapter targeted, its name in the target row)."""
import os
from c64test import test, check
from lib.c64 import Game, ROOT
from lib.play import new_game, alive, mpos, floor_next, FLOOR_D
import gen_gfx as GG, monsters as MO, monsters_chap as MC

CHAIN = True
SHOTS = os.path.join(ROOT, "out", "work", "villages")


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    g.poke(g.L["godmode"], 1)
    os.makedirs(SHOTS, exist_ok=True)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def names(c, boss=False):
    """the 8 names of chapter c straight from the drawings (base 1..4, strong 5..8); boss file: the boss's summon
    (19/11, MO.SUMMONS: the fetish of Mother Stitch) in the place of its type"""
    if c == 1:
        out = [m[0] for m in MO.BASE + MO.STRONG]
    else:
        fam = MC.CHAPTER_MONSTERS[c]
        out = [f[0] for f in fam] + [f[4] for f in fam]
    if boss and c in MO.SUMMONS:
        out[MO.SUMMONS[c][0] - 1] = MO.SUMMONS[c][1][0]
    return out


def colors(c, boss=False):
    if c == 1:
        out = [m[2] for m in MO.BASE + MO.STRONG]
    else:
        fam = MC.CHAPTER_MONSTERS[c]
        out = [f[3] for f in fam] + [f[6] for f in fam]
    if boss and c in MO.SUMMONS:
        out[MO.SUMMONS[c][0] - 1] = MO.SUMMONS[c][1][2]
    return out


def enter(g, c, lvl):
    L = g.L
    g.poke(L["c_chap"], c); g.poke(L["c_unl"], c)
    g.call_keep(L["change_level"], regs="a=%02x,x=00" % lvl, tmax=150); g.frames(3)
    check(g.b(L["cur_level"]) == lvl, "level %d, expected %d" % (g.b(L["cur_level"]), lvl))


def check_set(g, c, boss):
    """sprites in the slots, colours and names at NM_AT = the set of chapter c (boss file: its boss slot)"""
    L = g.L
    mset = MO.chapter_set(c, boss)
    mons, strong = GG.mon_bytes(mset)
    raw = GG.info_raw(mset)
    info = GG.info_bytes(raw, L["GFX_INFO"])
    check(bytes(g.mem(L["SPR_DATA"] + 12 * 64, len(mons))) == mons, "chapter %d: base sprites (slots 12..19) differ" % c)
    check(bytes(g.mem(0x8c00, len(strong))) == strong, "chapter %d: strong + boss sprites ($8C00) differ" % c)
    check(bytes(g.mem(L["NM_AT"], len(info))) == info, "chapter %d: info block at NM_AT differs" % c)
    got_cols = g.mem(L["NM_AT"], 9)
    check(got_cols[:8] == colors(c, boss), "chapter %d: colours %s, drawings %s" % (c, got_cols[:8], colors(c, boss)))
    slot = (MO.CBOSS[c] if boss and c in MO.CBOSS else MO.FINAL)
    check(got_cols[8] == slot[2], "chapter %d: boss slot colour %d, expected %d (%s)" % (c, got_cols[8], slot[2], slot[0]))
    for t, n in enumerate(names(c, boss) + [slot[0]], 1):        # every name, as bar_name finds it (NM_AT+8+type: low byte)
        a = (L["NM_AT"] & 0xff00) | g.b(L["NM_AT"] + 8 + t)
        s = bytes(g.mem(a, 25)).split(b"\0")[0]
        check(s == bytes(GG.scr_text(n)), "chapter %d type %d: name %r, expected %r" % (c, t, s, n))


def hud_decode():
    """glyph code -> character of the 'hud' encoding (out/work/gfx_consts.inc, .cdef lines of the build)"""
    import re
    from lib.c64 import OUT
    G, dec = {}, {}
    for line in open(os.path.join(OUT, "gfx_consts.inc")):
        m = re.match(r"(G_\w+)\s*=\s*(\d+)", line)
        if m: G[m.group(1)] = int(m.group(2))
        m = re.match(r'\s*\.cdef "(.)", "(.)", (G_\w+)', line)
        if m:
            for k in range(ord(m.group(2)) - ord(m.group(1)) + 1):
                dec.setdefault(G[m.group(3)] + k, chr(ord(m.group(1)) + k).lower())
    return dec


def drawn(g):
    """(23/11) the text of the target row (row 20 of SCR_H, bt_row, columns 1..24), decoded with the 'hud' encoding"""
    L = g.L
    dec = hud_decode()
    return "".join(dec.get(c, "?") for c in g.mem(L["SCR_H"] + 800 + 1, 24)).rstrip()


def target(g, want):
    """teleport next to monster want and make it the target; return (name drawn in the bar, colours of the game sprites)"""
    L = g.L
    mx, my = mpos(g, want)
    p = floor_next(g, mx, my)
    check(p is not None, "no floor next to monster %d at %s" % (want, (mx, my)))
    g.poke(L["bar_t"], 0); g.poke(L["bar_m"], 0)
    g.teleport(p[0], p[1]); g.frames(2)
    g.poke(L["bar_m"], want + 1); g.poke(L["bar_t"], 250)    # the woken monster could be another one: this one
    g.frames(24)
    cols = [c & 15 for c in g.mem(L["sh_col"], 8)]          # colours of the game sprites (shadow of $D027.., the bar
    return drawn(g), cols                                   # sprites in the top border get theirs in the IRQ)


def shot(g, i, path):
    """screenshot with the hero 2 tiles from monster i (both visible, the bar still on it)"""
    mx, my = mpos(g, i)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):      # a free line of 2 floor tiles (same room: the monster stays drawn)
        if all(g.tile(mx + k * dx, my + k * dy) in FLOOR_D for k in (1, 2)):
            g.teleport(mx + 2 * dx, my + 2 * dy); g.frames(4)
            break
    g.screenshot(path)


def chapter_test(c):
    @test("MON-CHAP-%d" % (10 + c), "chapter %d: a dungeon level and the boss level give the sprites, colours and names of the chapter; "
          "a monster of the chapter has its name drawn in the target row" % c)
    def t(ctx):
        g = ctx["g"]; L = g.L
        lvl = 5 * (c - 1) + 2
        enter(g, c, lvl)
        check_set(g, c, False)
        ms = [i for i in alive(g) if i + 1 != g.b(L["lb_boss"])]
        check(ms, "chapter %d level %d: no monster" % (c, lvl))
        i = ms[0]
        ty = g.b(L["mtype"] + i)
        name, cols = target(g, i)
        exp = names(c)[ty - 1]
        check(name == exp, "chapter %d: bar shows %r, expected %r (type %d)" % (c, name, exp, ty))
        check(colors(c)[ty - 1] in cols, "chapter %d: colour %d of %s not among the sprite colours %s" % (c, colors(c)[ty - 1], exp, cols))
        shot(g, i, os.path.join(SHOTS, "monsters%d.png" % c))
        enter(g, c, 5 * c)                                  # boss level of the chapter
        check_set(g, c, True)
        b = g.b(L["lb_boss"]) - 1
        check(b >= 0, "chapter %d: no boss on level %d" % (c, 5 * c))
        name, cols = target(g, b)
        slot = MO.CBOSS[c] if c in MO.CBOSS else MO.FINAL
        check(name == slot[0], "chapter %d boss: bar shows %r, expected %r" % (c, name, slot[0]))
        check(slot[2] in cols, "chapter %d boss: colour %d not among %s" % (c, slot[2], cols))
        shot(g, b, os.path.join(SHOTS, "monsters%d_boss.png" % c))
    return t


for _c in range(1, MO.CHAPTERS + 1):
    chapter_test(_c)


@test("MON-CHAP-20", "back to chapter 1 after chapter 4: the chapter 1 set (fallen ... balrog, lord of ruin) is restored")
def back(ctx):
    g = ctx["g"]
    enter(g, 1, 3)
    check_set(g, 1, False)
