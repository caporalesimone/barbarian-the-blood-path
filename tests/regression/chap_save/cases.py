"""(moved from sanity to regression on 12/11) Level states of the chapter in RAM (11/11 evening, docs/salvataggi.md): the levels of the current chapter (groups of
CH_LV = 5 levels) keep their compact state in RAM slots (LVRAM, under the I/O); the disk is written only by "save game",
by the creation of the hero and when a level of another chapter is entered (hero + levels of the chapter). Quit, stairs,
inn and character sheet do not write the disk. One VICE session, the tests run in order (CHAIN)."""
import os, re
from c64test import test, check
from lib.c64 import OUT, Game
from lib.play import new_game, go_level, fire_to, find, K_Y, D

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def marks(g):
    """clear the traces of the disk routines: sv_nm (written by sv_read) and sv_par+2..+7 (written by sv_write)"""
    L = g.L
    g.fill(L["sv_nm"], L["sv_nm"] + 7, 0); g.fill(L["sv_par"] + 2, L["sv_par"] + 7, 0)


def traces(g):
    """(file read, file written) since marks()"""
    L = g.L
    return any(g.mem(L["sv_nm"], 8)), any(g.mem(L["sv_par"] + 2, 6))


def lvl(g, n):
    """change_level to level n (stairs down, spawn mode 0) from the current input read"""
    g.call_keep(g.L["change_level"], regs="a=%02x,x=00" % n, tmax=150)
    g.frames(2)


def up(g):
    fire_to(g, *find(g, g.L["T_STAIRSU"])[0]); g.wait_main()


@test("CHAP-SAVE-10", "stairs inside a chapter: no disk read or write; a dead monster of level 2 stays dead (RAM slot)")
def chap_stairs(ctx):
    g = ctx["g"]; L = g.L
    marks(g)
    go_level(g, 1)
    r, w = traces(g)
    check(r and not w and g.b(L["cur_chap"]) == 1, "entering level 1: read %s write %s cur_chap %d (expected read, chapter 1)"
          % (r, w, g.b(L["cur_chap"])))
    marks(g)
    go_level(g, 2)
    n = g.b(L["lb_cnt"])
    check(n >= 3, "level 2 with %d monsters" % n)
    g.poke(L["malive"], 0)
    a0 = g.mem(L["malive"], n)
    up(g); go_level(g, 2)
    a1 = g.mem(L["malive"], n)
    print("      level 2 alive before %s after %s" % (a0, a1))
    check(a1 == a0, "monsters of level 2 after the return %s (before %s)" % (a1, a0))
    check(traces(g) == (False, False), "the stairs inside chapter 1 used the disk: read/write %s" % (traces(g),))
    g.cmd("bank ram"); s = g.mem(L["LVRAM"] + L["LV_SLOT"], 1)[0]; g.cmd("bank cpu")
    check(s == 2, "slot of level 2 starts with %d (expected 2)" % s)


@test("CHAP-SAVE-11", "level 5 -> 6 (chapter 2): hero + chapter 1 written once; back to level 2 its state comes from the disk")
def chap_change(ctx):
    g = ctx["g"]; L = g.L
    lvl(g, 5)
    check(g.b(L["cur_chap"]) == 1, "level 5: cur_chap %d" % g.b(L["cur_chap"]))
    marks(g)
    lvl(g, 6)                                       # (12/11: level 5 is the boss level, no stairs down)
    r, w = traces(g)
    check(w and g.b(L["cur_chap"]) == 2, "level 6: write %s cur_chap %d (expected written, chapter 2)" % (w, g.b(L["cur_chap"])))
    check(g.mem(L["sv_par"] + 2, 2) == [L["SV_IMG"] & 255, L["SV_IMG"] >> 8], "sv_write not used (sv_par %s)" % g.mem(L["sv_par"], 8))
    check(g.b(L["c_loc"]) == 6, "c_loc %d" % g.b(L["c_loc"]))
    lvl(g, 2)                                       # chapter 2 written, chapter 1 read back from the file
    a = g.mem(L["malive"], g.b(L["lb_cnt"]))
    check(g.b(L["cur_chap"]) == 1 and a[0] == 0, "level 2 from the disk: cur_chap %d alive %s (monster 0 dead expected)"
          % (g.b(L["cur_chap"]), a))


@test("CHAP-SAVE-12", "save game, then changes, then quit (no save): continue gives the saved hero and the saved fog of level 2")
def chap_quit(ctx):
    g = ctx["g"]; L = g.L
    E = L["EXPL"]
    g.fill(E, E + 287, 0xff)                        # level 2 all explored...
    g.poke16(L["c_gold"], 1234)
    g.call_keep(L["gm_save"], tmax=150)
    g.fill(E, E + 287, 0)                           # ...then unexplored after the save: lost with the quit
    g.poke16(L["c_gold"], 999)
    marks(g)
    g.run_stop(); g.frames(2, joy=0)                # game menu: resume, save, quit
    g.frames(1, joy=D); g.frames(1); g.frames(1, joy=D); g.frames(1)
    g.press_fire(settle=2)                          # quit -> "quit game? unsaved progress will be lost"
    g.frames(1, keys={K_Y[0]: K_Y[1]}, tmax=60)     # Y: back to the barbarian menu
    check(not traces(g)[1], "quit wrote the disk")
    g.frames(3); g.press_fire(settle=3)             # first barbarian -> details
    g.press_fire(settle=1)                          # start (a new game number: the monsters come back, the fog stays)
    g.wait_main(150)
    f = sum(1 for v in g.mem(E, 288) if v == 0xff)
    print("      after continue: level %d gold %d fog bytes all explored %d/288" % (g.b(L["cur_level"]), g.w16(L["c_gold"]), f))
    check(g.b(L["cur_level"]) == 2 and g.w16(L["c_gold"]) == 1234, "level %d gold %d (expected 2, 1234)"
          % (g.b(L["cur_level"]), g.w16(L["c_gold"])))
    check(f == 288, "fog of level 2: %d/288 bytes explored (expected all: the saved state)" % f)


@test("CHAP-SAVE-13", "listing: the hero file is written only by gm_save and chap_save (sv_all) and by the new hero (save_char)")
def chap_callers(ctx):
    calls = {}
    for f in ("game", "menu", "lobby"):
        for m in re.finditer(r"^\.\w+\s+(?:20|4c) \w\w \w\w\s+(?:jsr|jmp) \$\w+\s+(?:\S+\s+)?(?:jsr|jmp) (\w+)", open(os.path.join(OUT, f + ".lst")).read(), re.M):
            calls.setdefault(m.group(1), []).append(f)
    print("      callers: sv_all %s, save_char %s, gm_save %s" % (calls.get("sv_all"), calls.get("save_char"), calls.get("gm_save")))
    check(len(calls.get("sv_all", [])) == 2, "sv_all called %s times (gm_save, chap_save)" % len(calls.get("sv_all", [])))
    check(calls.get("save_char", []) == ["game"], "save_char called from %s (only the new hero)" % calls.get("save_char"))
    check(calls.get("gm_save", []) == ["game"], "gm_save called from %s (only 'save game')" % calls.get("gm_save"))
