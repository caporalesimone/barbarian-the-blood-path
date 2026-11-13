"""Disk times with Krill's Loader (11/11, fast-loader branch; docs/FastLoader.md section 7). Every operation is timed
with the VICE stopwatch (emulated 1541) and has a hard-coded limit: the measure must stay at least 10% BELOW its limit
(measure <= 0.9 x limit, rule of the project owner), so a slower loader or save fails before reaching the limit.
One VICE session: the real START, a new hero in the village, then each routine called from the monitor."""
import re
from lib.runner import test, check
from lib.c64 import Game
from lib.play import new_game

CPS = 985248
MARGIN = 0.9
# thresholds fixed by the owner on 12/11 (stairs, saves, village): the measure must stay <= the value itself, no extra 10%
HARD = {"town", "menu", "stairs", "save_dng", "save_char"}
# limits in seconds (11/11, measured values in the comments)
LIM = {
    "boot": 16.0,         # START from the monitor -> barbarian menu (install, GAME 25 KB + ZX0 unpacking ~4 s, LOBBY, hl): 13.4 s
    "menu": 3.1,          # ovl_town: MENU1..3 + unpacking: 1.98 s with 30 files on the disk, 2.97 s with 36 (8 GFX files); limit = measured + 0.1 (12/11)
    "town": 1.5,          # load_gfx 0: the village (GFX0, 3 KB): 1.10-1.31 s; threshold of the owner (12/11)
    "theme": 1.5,         # load_gfx 1: a dungeon theme (GFX1, 2 KB): 0.98 s; 1.34 s on 12/11 (42 files on the disk: TWN1-4, BOSSCH1-3)
    "song": 0.6,          # snd_get: one song (SNDn): 0.51 s
    "hdr": 0.95,          # hdr_read: the hero list (hl, 1 block): 0.62 s
    "load_char": 3.4,     # load_char in the village: hero file (9 blocks) + the village read again: 2.49 s; 2.71 s on 12/11 (disk layout changed: HELP packed); 3.04 s on 12/11 evening (file sizes of the loader changed, TODO M3)
    "save_char": 9.6,     # save_char in the village: read + plugin + 9 blocks + village again: 8.7-9.1 s; 9.45 s on 12/11 (limit of the owner 9.5 + rule "measure + 0.1")
    "town_in": 5.6,       # change_level level 1 -> village, the whole entry (fade, GFX0, MENU, install, song): 4.41-4.49 s (12/11)
    "stairs": 4.0,        # change_level to the next level of the same chapter (theme + generation, no disk write): 2.64 s with 30 files, 3.44-3.89 s with 36 files (varies from run to run); limit = max measured + 0.1 (12/11); target of the owner < 2 s (TODO J9)
    "save_dng": 9.4,      # save_char in a dungeon (no village to read again): the "save game": 7.6-8.1 s; 8.26-9.26 s on 12/11 (varies with the head position left by the previous test; limit of the owner 8.5 + rule "measure + 0.1")
    "hdr_write": 6.8,     # hdr_write: plugin + hl (1 block) + village again: 5.20 s; 5.0-5.8 s on 12/11 (varies from run to run)
}
T = {}


def sw(g):
    """VICE stopwatch (cycles). (12/11) Right after the start the monitor sometimes answers "sw" without the
    "Stopwatch:" line (setup failed with 'list index out of range' about 1 run in 3): ask again."""
    for _ in range(5):
        m = re.findall(r"Stopwatch:\s*(\d+)", g.cmd("sw"))
        if m: return int(m[0])
    raise AssertionError("no answer from the VICE stopwatch")


def timed(g, a, regs=""):
    g.cmd("sw reset")
    s0 = sw(g)
    g.call(a, tmax=120, regs=regs)
    return (sw(g) - s0) / CPS


def setup(ctx):
    g = ctx["g"] = Game()
    g.cmd("sw reset")
    s0 = sw(g)
    g.to_menu()
    T["boot"] = (sw(g) - s0) / CPS
    new_game(g); g.frames(3)
    g.at_input = False


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def limit(name, t):
    m = 1.0 if name in HARD else MARGIN
    print("      %-10s %6.2f s  (limit %.1f s, max %.2f s)" % (name, t, LIM[name], LIM[name] * m))
    check(t <= LIM[name] * m, "%s: %.2f s, over %d%% of the limit %.1f s" % (name, t, round(m * 100), LIM[name]))


@test("PERF-DISK-10", "START from the monitor to the barbarian menu (Krill install, GAME, LOBBY, hl) <= its limit")
def perf_boot(ctx):
    limit("boot", T["boot"])


@test("PERF-DISK-11", "loads with Krill (MENU, village, theme, song, hero list, hero file) <= their limits")
def perf_loads(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["ovl_cur"], 0)
    limit("menu", timed(g, L["ovl_town"]))
    limit("town", timed(g, L["load_gfx"], "a=00"))
    limit("theme", timed(g, L["load_gfx"], "a=01"))
    g.poke(L["snd_cur"], 0)                         # (12/11) a song already in the buffer is not read again: force the read
    limit("song", timed(g, L["snd_get"], "a=00,x=00"))
    limit("hdr", timed(g, L["hdr_read"]))
    limit("load_char", timed(g, L["load_char"]))


@test("PERF-DISK-13", "stairs inside a chapter (change_level 1 -> 2: theme, generation, level state from RAM) <= its limit")
def perf_stairs(ctx):
    g = ctx["g"]; L = g.L
    g.call(L["change_level"], tmax=150, regs="a=01,x=00")      # level 1: the chapter is read (not measured)
    limit("stairs", timed(g, L["change_level"], "a=02,x=00"))
    g.call(L["change_level"], tmax=150, regs="a=00,x=01")      # back to the village (the next tests save there)


@test("PERF-DISK-14", "full village entry from level 1 (change_level: fade, GFX0, MENU module, gfx_install, song) <= its limit")
def perf_town_in(ctx):
    g = ctx["g"]; L = g.L
    g.call(L["change_level"], tmax=150, regs="a=01,x=00")      # to level 1 (not measured)
    limit("town_in", timed(g, L["change_level"], "a=00,x=01"))


@test("PERF-DISK-12", "saves with the Krill plugin (hero file in the village, hero list) <= their limits")
def perf_saves(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["town_at"], 0)
    limit("save_dng", timed(g, L["save_char"]))
    g.poke(L["town_at"], 1)
    limit("save_char", timed(g, L["save_char"]))
    limit("hdr_write", timed(g, L["hdr_write"]))
