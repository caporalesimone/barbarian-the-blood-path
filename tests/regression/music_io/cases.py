"""(22/11, owner's report) The music must not go silent after a disk access made in the game with the interrupt on (the Q
page: QGIV is read, then CORE again on the way back). snd_io dims the volume for 15 frames waiting for the vertical blank: the
IRQ's music_update saw mus_mute already set, restored the volume, and snd_mute then left it at 0 with mus_mute cleared: silent
until the next change of place. SID registers read in the io bank of the VICE monitor. One VICE session (CHAIN)."""
from lib.c64 import Game
from c64test import test, check
from lib.play import new_game

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(4)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def volume(g):
    g.cmd("bank io")
    v = g.mem(0xd418, 1)[0]
    g.cmd("bank cpu")
    return v & 15


@test("MUS-IO-10", "village and level 2: Q page open and closed 3 times; back in the game the SID volume is full (15) and mus_mute is 0")
def q_page(ctx):
    g = ctx["g"]; L = g.L
    bad = []
    for lvl in (0, 2):
        if lvl:
            g.call_keep(L["change_level"], regs="a=%02x,x=00" % lvl, tmax=150); g.frames(3)
        for i in range(3):
            g.frames(1, keys={7: 0x40}); g.frames(30)          # Q: the page (QGIV from the disk)
            g.run_stop(); g.frames(40)                          # back: CORE from the disk
            v, m = volume(g), g.b(L["mus_mute"])
            if v != 15 or m:
                bad.append("level %d, time %d: volume %d, mus_mute %d" % (lvl, i + 1, v, m))
    check(g.in_game() and not bad, "; ".join(bad) or "not back in the game")
