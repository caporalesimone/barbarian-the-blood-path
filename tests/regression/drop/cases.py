"""(23/11, owner's request) Death of a monster in the dungeon: its name and life bar leave the target row of the HUD at once
(before: BTH_FR = 50 frames, ~1 s, with the life of the last redraw), and its chest appears DROP_T frames after the death
(~0.25 s) also while another monster is still in contact (before: 100 frames after the last contact with any monster,
cmb_t). Chests still do not open with a monster within 2 tiles (chest_fire, 'monster too close!'). Level 1 of chapter 1, one
VICE session (CHAIN)."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game, go_level

CHAIN = True
NEAR = ((1, 0), (-1, 0), (0, 1), (0, -1))


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    go_level(g, 1); g.frames(5)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def place(g, m, x, y):
    L = g.L
    g.poke(L["mxl"] + m, (x * 16) & 255); g.poke(L["mxh"] + m, (x * 16) >> 8)
    g.poke(L["myl"] + m, (y * 16) & 255); g.poke(L["myh"] + m, (y * 16) >> 8)
    g.poke(L["mwake"] + m, 1)


def floor_cells(g, n):
    """n free floor tiles next to the hero (no chest, no monster): needed walkable and empty"""
    L = g.L
    px, py = g.b(L["ptx"]), g.b(L["pty"])
    out = []
    for dx, dy in NEAR + ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        x, y = px + dx, py + dy
        if g.tile(x, y) != 0xff and not (g.b(L["solidtab"] + g.tile(x, y)) & 1):
            out.append((x, y))
    check(len(out) >= n, "fewer than %d free tiles around the hero: %s" % (n, out))
    return out[:n]


def living(g, n):
    L = g.L
    a = g.mem(L["malive"], g.b(L["lb_cnt"]))
    b = g.b(L["lb_boss"]) - 1
    ms = [i for i, v in enumerate(a) if v and i != b]
    check(len(ms) >= n, "fewer than %d common monsters alive" % n)
    return ms[:n]


def row(g):
    return g.mem(g.L["BTR_SCR"], 40)


@test("DROP-10", "a monster hit shows its name and life in the target row; when it dies the row is empty within 2 frames (not after BTH_FR = 50)")
def bar_gone(ctx):
    g = ctx["g"]; L = g.L
    (m,) = living(g, 1)
    (c,) = floor_cells(g, 1)
    place(g, m, *c)
    g.call_keep(L["bar_target"], regs="x=%02x" % m)
    g.frames(8)
    check(any(v != L["G_BLANK"] for v in row(g)), "no name in the target row after bar_target: %s" % row(g))
    g.call_keep(L["kill_monster"], regs="x=%02x" % m)
    g.frames(2)
    r = row(g)
    check(all(v == L["G_BLANK"] for v in r), "the target row still shows something 2 frames after the death: %s" % r)


@test("DROP-11", "a chest left by a dead monster (defer_drop) appears DROP_T frames later (+-2), with another monster still in contact with the hero (combat going on)")
def chest_soon(ctx):
    g = ctx["g"]; L = g.L
    (m2,) = living(g, 1)
    c1, c2 = floor_cells(g, 2)
    place(g, m2, *c2)                                   # in contact: before 23/11 the chest waited for the end of the combat
    g.poke(L["c_hp"], 255)
    n0 = sum(1 for v in g.mem(L["ch_t"], L["CH_MAX"]) if v)
    g.poke(L["loot_x"], c1[0]); g.poke(L["loot_y"], c1[1]); g.poke(L["dc_b"], 0); g.poke(L["gi_ll"], 1)
    g.call_keep(L["defer_drop"], regs="a=01,x=01")
    n = None
    for f in range(1, 40):
        g.frames(1)
        g.poke(L["c_hp"], 255)
        if sum(1 for v in g.mem(L["ch_t"], L["CH_MAX"]) if v) > n0:
            n = f
            break
    check(n is not None and abs(n - L["DROP_T"]) <= 2, "chest after %s frames (DROP_T %d)" % (n, L["DROP_T"]))
    i = next(i for i, v in enumerate(g.mem(L["ch_t"], L["CH_MAX"])) if v & 8)
    check((g.b(L["cx_x"] + i), g.b(L["cx_y"] + i)) == c1, "chest at %s, expected the body tile %s" % ((g.b(L["cx_x"] + i), g.b(L["cx_y"] + i)), c1))
