"""Every load of a scripted walk through all the chapters equals its file (15/11, ex TODO A2, docs/wiki/FastLoader.md 4.1): new hero,
then for each chapter: crypt, stairs down, up and back to the village, all the levels down to the boss level (chapters
1-3: BOSSCHc; chapter 4: the throne room, FMAP), the boss beaten (chap_won), back to the village (TWNc, MENU, SND0),
a save (KSAVE, the hero file), the travel to the next village (chap_travel: TWNc, save); at the end the LOBBY. Every
krill_loadraw is stopped and checked when it returns (tests/lib/loads.py, LoadCheck): bytes in RAM and end address equal to
the file on the disk (hl and save-0N: length only, the plugin rewrites them). One VICE session."""
from c64test import test, check
from lib.c64 import Game
from lib.play import new_game
from lib.loads import LoadCheck

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    ctx["lc"] = LoadCheck(g)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


@test("KRILL-24", "walk through chapters 1-4 to village 5 (levels, boss levels, villages, saves, travels, LOBBY): every load equals its file")
def walk(ctx):
    g, lc = ctx["g"], ctx["lc"]; L = g.L
    lv = lambda n, m=0: lc.call(L["change_level"], "a=%02x,x=%02x" % (n, m))
    for c in range(1, 5):
        check(g.b(L["c_chap"]) == c, "chapter %d expected, c_chap %d" % (c, g.b(L["c_chap"])))
        f = (c - 1) * 5 + 1
        lv(f); lv(f + 1); lv(f, 1); lv(0)             # crypt, stairs down, stairs up, back to the village
        for n in range(f, f + 5): lv(n)               # down to the boss level (chapter 4: the throne room)
        lc.call(L["chap_won"])
        lv(0)                                         # village of the chapter: TWNc, MENU (one file since 18/11), SND0
        lc.call(L["save_char"])                       # KSAVE, hero file read and rewritten, village read again
        lc.call(L["chap_travel"])                     # next village (save of hero and levels)
    check(g.b(L["c_chap"]) == 5, "village 5 expected, c_chap %d" % g.b(L["c_chap"]))
    lc.call(L["load_menu"])
    names = [n for n, _, _ in lc.loads]
    bad = lc.bad()
    check(not bad, "%d of %d loads differ from their file: %s" % (len(bad), len(names), "; ".join("%s (%s)" % b for b in bad[:8])))
    for need in ("menu", "snd0", "fmap", "bossch1", "bossch2", "bossch3", "twn5", "ksave", "lobby"):
        check(need in names, "the walk did not load %s (%d loads: %s)" % (need, len(names), " ".join(names)))
    check(("menu", "snd0") in lc.pairs(), "snd0 never loaded right after menu (the drive's next-file cache)")
