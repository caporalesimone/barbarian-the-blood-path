"""The disk (11/11: one build, one disk; POKE 1020,1 replaces the development disk); the tests enter the game through the
real START (Krill)."""
import os, re, subprocess, sys
from c64test import test, check
from lib.c64 import ROOT, OUT

D64 = (os.path.join(OUT, "disk.d64"),)


def directory(path):
    """file names and first track/sector of a d64 (directory on track 18)"""
    d = open(path, "rb").read()
    spt = [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5
    off = lambda t, s: (sum(spt[:t - 1]) + s) * 256
    out, t, s = [], 18, 1
    while t:
        b = d[off(t, s):off(t, s) + 256]
        for i in range(8):
            e = b[i * 32:(i + 1) * 32]
            if e[2] & 7:
                out.append(e[5:21].split(b"\xa0")[0].decode("latin1").lower())
        t, s = b[0], b[1]
    return out


@test("DISK-10", "the disk has every file (loader, START, game, LORE, LDAT, TITLE, HELP, JUKEBOX, saves, ...)")
def disk_files(ctx):
    rel = directory(D64[0])
    for f in ("barbarian", "start", "game", "lore", "ldat", "title", "help", "jukebox", "hl", "ksave",
              "save-01", "save-02", "save-03", "save-04", "save-05"):              # (11/11, Krill) salvataggi + plugin
        check(f in rel, "%s missing from the disks" % f)


@test("DISK-12", "entry of the tests (11/11, Krill): the real START from the monitor (Krill installed), new game in the village")
def disk_fast(ctx):
    from lib.c64 import Game
    from lib.play import new_game
    g = Game()
    try:
        g.to_menu()
        new_game(g); g.frames(3)
        L = g.L
        check(g.in_game() and g.b(L["cur_level"]) == 0, "not in the village after a new game")
        gp = open(os.path.join(OUT, "game.prg"), "rb").read()
        check(g.mem(0x0400 + 0x100, 32) == list(gp[2 + 0x100:2 + 0x120]), "GAME in RAM differs from out/work/game.prg")
    finally:
        g.close()
