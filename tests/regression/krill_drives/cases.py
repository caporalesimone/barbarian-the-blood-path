"""Krill's Loader on other drive types emulated by VICE (12/11, TODO M7 KRILL-17): the same disk with -drive8type.
The ROMs of the drives come from roms/ (dos1541ii, dos1570, dos1571: tests/lib/c64.py passes them to x64sc, nothing is read
from VICE's data folder or from /usr/share/vice)."""
import os
from lib.runner import test, check, Skip
from lib.c64 import Game, ROMS
from lib.play import new_game

DRIVES = ROMS                                   # the drive ROMs live in roms/ (project rule: no system paths)


def boot(dtype):
    g = Game(extra=["-drive8type", str(dtype)])
    try:
        g.to_menu()
        new_game(g); g.frames(3)
        L = g.L
        ok = g.b(L["cur_level"]) == 0 and g.b(L["c_chap"]) == 1 and bytes(g.mem(L["cmdbuf"] + 3, 4)) in (b"SND0", b"TWN1")
        name = bytes(g.mem(L["cmdbuf"] + 3, 8))
    finally:
        g.close()
    return ok, name


@test("KRILL-17", "1541-II (VICE 1542): START with Krill, menu, new hero (save plugin), village read")
def krill_1541ii(ctx):
    ok, name = boot(1542)
    check(ok, "1541-II: the village was not reached (last file %r)" % name)


@test("KRILL-18", "1570 / 1571 in 1541 mode: as KRILL-17 (ROMs dos1570 / dos1571 from roms/)")
def krill_157x(ctx):
    roms = [f for f in os.listdir(DRIVES) if f.startswith(("dos1570", "dos1571"))] if os.path.isdir(DRIVES) else []
    if not roms:
        raise Skip("no 1570/1571 ROM in roms/ (%s)" % DRIVES)
    for d in (1570, 1571):
        ok, name = boot(d)
        check(ok, "%d: the village was not reached (last file %r)" % (d, name))


@test("KRILL-14", "Krill install fails (simulated: from the install straight to kr_fail): message, a key, BARBARIAN loaded again")
def krill_fail(ctx):
    """The real failure (unsupported drive) cannot be produced here: VICE without the true drive does not load START
    with the KERNAL either (red border of the trampoline). So the install is skipped and kr_fail runs as after an error."""
    from lib.c64 import OUT, Vice, labels
    S = labels("start")
    g = Vice(os.path.join(OUT, "disk.d64"))
    try:
        g.load(os.path.join(OUT, "start.prg"))
        g.brk(S["krill_install"]); g.pc(0x080d); g.go(30); g.delbrk()
        g.pc(S["kr_fail"])
        g.brk(0xffe4); g.go(30); g.delbrk()                   # the message is on the screen when the key loop starts
        scr = bytes(g.mem(0x0400 + 40 * 10, 40))
        check(b"\x14\x08\x09\x13" in scr, "no message on the screen: %r" % scr[:20])      # "this" in screen codes
        g.poke(0x0277, 0x20); g.poke(0xc6, 1)                  # SPACE in the KERNAL keyboard buffer
        barb = open(os.path.join(OUT, "barbarian.prg"), "rb").read()
        g.brk(0x080d)
        g.go(60)
        got = bytes(g.mem(0x0801, 32))
        check(got == barb[2:34], "BARBARIAN not loaded again at $0801")
    finally:
        g.close()
