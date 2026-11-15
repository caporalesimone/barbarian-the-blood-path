"""Game helpers shared by the VICE tests (11/11): new game, map search, monsters, teleport + fire, minimap check,
keys. Everything works on a lib.c64.Game stopped at an input read (frames())."""
import os, sys
from lib.c64 import ROOT

sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import gen_gfx as GG  # noqa: E402

NAME = [2, 12, 1, 3, 11, 32, 20, 8, 15, 18, 14, 5]        # "black thorne" (project rule: 12 characters with a space)
SEED = [10, 11, 12, 1, 2, 3]                                # "abc123"
SOLID_V = {i for i, n in enumerate(GG.TILES) if n in GG.SOLID}
FLOOR_D = (2, 3, 4)                                         # T_FLOOR, T_FLOORB, T_FLOORC
U, D, LF, RT = 1, 2, 4, 8
INN_DOOR = (40, 43)                                         # below the inn's door (Aldric's Crossing)
SMITH_DOOR = (39, 12)                                       # below the smith's door
# keys: (row of keynew, mask) - C64 keyboard matrix
K_RUNSTOP, K_1, K_2, K_3, K_4, K_5 = (7, 0x80), (7, 0x01), (7, 0x08), (1, 0x01), (1, 0x08), (2, 0x01)
K_I, K_M, K_Y, K_N, K_RETURN, K_DEL = (4, 0x02), (4, 0x10), (3, 0x02), (4, 0x80), (0, 0x02), (0, 0x01)
K_F1, K_F3, K_F5, K_F7 = (0, 0x10), (0, 0x20), (0, 0x40), (0, 0x08)
BELT_KEYS = (K_1, K_2, K_3, K_4)                            # belt slots 1..4 (BELT_SLOTS = 4 until TODO 3.1)


def new_game(g, slot=0):
    """from the barbarian menu: a new barbarian (NAME, SEED) in the village, stopped in the main loop"""
    M = g.M
    g.poke(M["namebuf"], *NAME); g.poke(M["seedbuf"], *SEED); g.poke(M["cur_slot"], slot)
    g.menu_return(1)


def key(g, k, settle=1):
    g.frames(1, keys={k[0]: k[1]}); g.frames(settle)


def find(g, t):
    m = g.mem(g.L["MAP"], 48 * 48)
    return [(i % 48, i // 48) for i, v in enumerate(m) if v == t]


def mpos(g, i):
    L = g.L
    return (g.b(L["mxl"] + i) + 256 * g.b(L["mxh"] + i)) >> 4, (g.b(L["myl"] + i) + 256 * g.b(L["myh"] + i)) >> 4


def alive(g):
    return [i for i, a in enumerate(g.mem(g.L["malive"], g.b(g.L["lb_cnt"]))) if a]


def fire_to(g, tx, ty, frames=3):
    g.teleport(tx, ty); g.frames(frames); g.press_fire()


def floor_next(g, tx, ty):
    """a floor tile next to (tx, ty) and the joystick direction that faces (tx, ty) from it"""
    for dx, dy, j in ((0, 1, U), (0, -1, D), (1, 0, LF), (-1, 0, RT)):
        if g.tile(tx + dx, ty + dy) in FLOOR_D: return tx + dx, ty + dy, j
    return None


def clear_around(g, tx, ty, r=3):
    """kill the monsters within r-1 tiles of (tx, ty) (chest_blocked: Chebyshev distance < 3)"""
    for i in alive(g):
        mx, my = mpos(g, i)
        if max(abs(mx - tx), abs(my - ty)) < r: g.poke(g.L["malive"] + i, 0)


def go_level(g, lvl):
    """down to level lvl (1..) from the village or a level, by the stairs (fire on the stairs tile)"""
    L = g.L
    while g.b(L["cur_level"]) < lvl:
        t = L["T_TSTAIRS"] if g.b(L["cur_level"]) == 0 else L["T_STAIRSD"]
        fire_to(g, *find(g, t)[0]); g.wait_main()


def go_village(g):
    L = g.L
    while g.b(L["cur_level"]) > 0:
        fire_to(g, *find(g, L["T_STAIRSU"])[0]); g.wait_main()


def minimap(g):
    """open the minimap (M), check the hero marker (sprite 7: X = 85 + px/4, Y = 48 + py/4) and that the map cell under
    its centre is drawn (not the empty char 63); close with RUN/STOP. Returns a failure reason or ''."""
    L = g.L
    px, py = g.w16(L["px"]), g.w16(L["py"])
    key(g, K_M, 3)
    if g.in_game(): return "the minimap does not open"
    sx = g.b(0xd00e) + (256 if g.b(0xd010) & 0x80 else 0)
    sy = g.b(0xd00f)
    why = ""
    if (sx, sy) != (85 + px // 4, 48 + py // 4):
        why = "marker at %d,%d, expected %d,%d (px %d, py %d)" % (sx, sy, 85 + px // 4, 48 + py // 4, px, py)
    else:
        col, row = (sx - 24 + 3) // 8, (sy - 50 + 3) // 8         # centre of the 7x7 ring
        ch = g.b(L["SCR_A"] + row * 40 + col)
        if ch == 63: why = "the marker is on an empty cell (%d,%d)" % (col, row)
    g.run_stop(); g.frames(3)
    if not why and not g.in_game(): why = "RUN/STOP does not close the minimap"
    return why
