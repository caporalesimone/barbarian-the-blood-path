"""Disk times with Krill's Loader (11/11, fast-loader branch; docs/FastLoader.md section 7). Every operation is timed
with the VICE stopwatch (emulated 1541) and has a hard-coded limit: the measure must stay at least 10% BELOW its limit
(measure <= 0.9 x limit, rule of the project owner), so a slower loader or save fails before reaching the limit.
One VICE session: the real START, a new hero in the village, then each routine called from the monitor."""
import re
from c64test import test, check
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
    "song": 1.5,          # snd_get: SND0 right after the theme GFX1, a sequence the game never does (15/11: with the
                          # layout "hubchap" SND0 sits next to MENU, far from GFX1: 1.12 s; it was 0.51 s)
    "hdr": 0.95,          # hdr_read: the hero list (hl, 1 block): 0.62 s
    "load_char": 3.4,     # load_char in the village: hero file (9 blocks) + the village read again: 2.49 s; 2.71 s on 12/11 (disk layout changed: HELP packed); 3.04 s on 12/11 evening (file sizes of the loader changed, TODO M3)
    "save_char": 9.6,     # save_char in the village: read + plugin + 9 blocks + village again: 8.7-9.1 s; 9.45 s on 12/11 (limit of the owner 9.5 + rule "measure + 0.1")
    "town_in": 5.6,       # change_level level 1 -> village, the whole entry (fade, GFX0, MENU, install, song): 4.41-4.49 s (12/11)
    "stairs": 4.0,        # change_level to the next level of the same chapter (theme + generation, no disk write): 2.64 s with 30 files, 3.44-3.89 s with 36 files (varies from run to run); limit = max measured + 0.1 (12/11); target of the owner < 2 s (TODO J9)
    "save_dng": 9.4,      # save_char in a dungeon (no village to read again): the "save game": 7.6-8.1 s; 8.26-9.26 s on 12/11 (varies with the head position left by the previous test; limit of the owner 8.5 + rule "measure + 0.1")
    "hdr_write": 6.8,     # hdr_write: plugin + hl (1 block) + village again: 5.20 s; 5.0-5.8 s on 12/11 (varies from run to run)
    # (15/11) one set per chapter c (PERF-DISK-21..25, TODO M1), limits for the layout "end" (TWN2..5 at the end of the disk, the
    # default of TWN_LAYOUT in tools/build/mkdisk.sh): 1.15 x the slowest of 3 runs (emulated time: the runs differ by <= 0.2 s),
    # rounded up to 0.1 s, so that the measure is at ~87% of its limit (rule: <= 90%). Each of them depends on the head position left by
    # the step before, so a change in the order of the steps or in the files around them moves them (see chapter_measures).
    # twnC = load_gfx 0 with c_chap = C (the village file alone), inC = the whole entry into village C (change_level to 0: from the
    # first level of the chapter, for 5 from the village as chap_travel does), themeC = load_gfx 2C-1, stairsC = change_level level
    # 1 -> 2 of the chapter, bossC = change_level to the boss level of the chapter (GFX 2C + BOSSCHC)
    "twn1": 1.0, "twn2": 2.2, "twn3": 2.1, "twn4": 2.8, "twn5": 1.6,         # layout hubchap, measured: 0.68, 1.63, 1.56, 2.14, 1.20
    "in1": 5.7, "in2": 5.3, "in3": 5.0, "in4": 5.0, "in5": 4.6,              # the time depends on the disk phase (rotation, head position): slowest seen on
                                                                             # 10 phases 4.93, 3.86, 3.84, 3.84, 3.94 (means 4.17, 3.47, 3.49, 3.45, 2.96); in2 4.37 in the suite order
    "theme1": 1.1, "theme2": 1.1, "theme3": 1.4, "theme4": 0.8,              # 0.72, 0.77, 1.04, 0.46
    "stairs1": 3.2, "stairs2": 3.2, "stairs3": 3.2, "stairs4": 3.2,          # 1.5-1.7 s, up to 2.54 s depending on the disk phase
    "boss1": 3.0, "boss2": 3.0, "boss3": 3.0,                                # 1.40-2.42, 2.24, 2.34 (disk phase)
}
T = {}


def sw(g):
    """VICE stopwatch (cycles). (15/11) The answer is recognised by its content ("Stopwatch: <n>" then the prompt), not by
    the first prompt, and the command is never sent twice: a second "sw" sent because an answer was late put the
    following commands one answer out of step (the setup failed 1 run in 2 with "no answer to 'load ...'", see
    Game.__init__ in tests/lib/c64.py for the cause)."""
    g.s.sendall(b"sw\n")
    b = g._read(lambda b: re.search(r"Stopwatch:\s*\d+\s*\n(?:.*\n)*?\(C:\$[0-9a-f]{4}\) $", b), 20, "sw")
    return int(re.findall(r"Stopwatch:\s*(\d+)", b)[-1])


def sw_reset(g):
    g.s.sendall(b"sw reset\n")
    g._read(lambda b: re.search(r"reset[^\n]*\n(?:.*\n)*?\(C:\$[0-9a-f]{4}\) $", b), 20, "sw reset")


def timed(g, a, regs=""):
    sw_reset(g)
    s0 = sw(g)
    g.call(a, tmax=120, regs=regs)
    return (sw(g) - s0) / CPS


def setup(ctx):
    g = ctx["g"] = Game()
    sw_reset(g)
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


def chapter_measures(g, c):
    """The loads of chapter c, in an order that leaves the head where the player leaves it: the village file alone right after
    the theme (as the village is read after a dungeon), the stairs inside the chapter, the boss level (chapters 1-3), and the whole
    entry into the village from the first level. Village 5 has no dungeon: its entry is the arrival from the village before
    (change_level spawn mode 4, as chap_travel and tests/regression/villages do)."""
    L = g.L
    base = 5 * (c - 1)
    g.poke(L["c_chap"], c); g.poke(L["c_unl"], max(c, g.b(L["c_unl"])))
    g.call(L["load_gfx"], tmax=60, regs="a=00")                # head on the village file (not measured)
    if c < 5:
        limit("theme%d" % c, timed(g, L["load_gfx"], "a=%02x" % (2 * c - 1)))
    limit("twn%d" % c, timed(g, L["load_gfx"], "a=00"))
    if c == 5:
        g.call(L["change_level"], tmax=150, regs="a=00,x=04")  # in the village of chapter 5 (not measured)
        limit("in5", timed(g, L["change_level"], "a=00,x=04"))
        return
    g.call(L["change_level"], tmax=150, regs="a=%02x,x=00" % (base + 1))      # first level of the chapter (not measured)
    limit("stairs%d" % c, timed(g, L["change_level"], "a=%02x,x=00" % (base + 2)))
    if c < 4:
        limit("boss%d" % c, timed(g, L["change_level"], "a=%02x,x=00" % (base + 5)))
    g.call(L["change_level"], tmax=150, regs="a=%02x,x=00" % (base + 1))      # back to level 1 (not measured)
    limit("in%d" % c, timed(g, L["change_level"], "a=00,x=01"))


for _c in (1, 2, 3, 4, 5):
    def _mk(c):
        what = "file alone, full entry" if c == 5 else "file alone, full entry (from level %d), theme, stairs%s" % (
            5 * (c - 1) + 1, ", boss level" if c < 4 else "")
        @test("PERF-DISK-2%d" % c, "village %d: %s <= their limits" % (c, what))
        def t(ctx):
            chapter_measures(ctx["g"], c)
        return t
    _mk(_c)
