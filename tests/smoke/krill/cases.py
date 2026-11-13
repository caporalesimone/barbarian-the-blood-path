"""Krill's Loader, happy path (11/11): after the real START the game loads its files with Krill; a dungeon theme and
a song arrive in RAM equal to the files of out/ (the theme under the KERNAL, read with 'bank ram')."""
import os
from lib.runner import test, check
from lib.c64 import OUT, Game


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


@test("KRILL-01", "load_gfx 1 (Krill, LOAD_TO): the theme at GFX_DUN_AT ($ED00, under the KERNAL) equals out/gfx/gfx1.prg")
def krill_theme(ctx):
    g = ctx["g"]; L = g.L
    d = open(os.path.join(OUT, "gfx", "gfx1.prg"), "rb").read()[2:]
    g.call(L["load_gfx"], tmax=60, regs="a=01")
    g.cmd("bank ram"); m = g.mem(L["GFX_DUN_AT"], len(d)); g.cmd("bank cpu")
    check(m == list(d), "theme differs at %s" % [i for i, (a, b) in enumerate(zip(m, d)) if a != b][:6])


@test("KRILL-02", "snd_get (Krill): the song in its buffer equals out/snd/snd0.prg")
def krill_song(ctx):
    g = ctx["g"]; L = g.L
    d = open(os.path.join(OUT, "snd", "snd0.prg"), "rb").read()[2:]
    g.call(L["snd_get"], tmax=60, regs="a=00,x=00")
    m = g.mem(L["SND_LBUF"], len(d))
    check(m == list(d), "song differs at %s" % [i for i, (a, b) in enumerate(zip(m, d)) if a != b][:6])
