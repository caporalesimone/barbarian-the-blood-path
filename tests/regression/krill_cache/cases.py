"""Krill's Loader: the drive's next-file cache (15/11, ex TODO A2, docs/wiki/FastLoader.md 4.1). In r194, after a load the 1541 code
keeps the first block of the next file of the directory; if that file is asked for next, the block is served from the cache,
and when it is also the file's last block (a file of one block) its length came from a byte that the hash of the requested
name had just overwritten: the load ended early or late, with no error (village song SND0 after MENU3: 118 bytes of 241,
the song player then looped for ever in the IRQ; MENU3 after MENU2: 39 bytes past its zone, into the charset; since 18/11
MENU is one file). Fixed in the
drive code at build time (tools/build/krill_build.sh); the game also checks the end address of songs and MENU parts and
reads them again (snd_get, ovl_town). One VICE session, tests in order (CHAIN); KRILL-23 overwrites the RAM, so it is last."""
import os
from c64test import test, check
from lib.c64 import Game, OUT
from lib.play import new_game
from lib.loads import directory, ram, load_to, LOADRAW, ENDADDR

CHAIN = True


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    ctx["files"] = {n: d for n, _, d in directory(g.disk)}


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def name(g, s):
    g.poke(g.L["cmdbuf"] + 3, *s.upper().encode("latin1"), 0)


def count_loads(g, a, regs="", tmax=120):
    """call a (from the current input read, as call_keep) counting the krill_loadraw calls; returns (registers, count)"""
    L, stub, n = g.L, 0x0340, 0
    r0 = g.regs()
    g.delbrk()
    g.poke(stub, 0x20, a & 255, a >> 8, 0xea)
    g.brk(stub + 3); g.brk(LOADRAW); g.pc(stub)
    if regs: g.cmd("r " + regs)
    while True:
        g.go(tmax)
        if g.regs()["pc"] != LOADRAW: break
        n += 1
    out = g.regs()
    g.delbrk(); g.brk(g.RI)
    g.cmd("r pc=%04x" % r0["pc"]); g.cmd("r a=%02x" % r0["a"]); g.cmd("r x=%02x" % r0["x"]); g.cmd("r y=%02x" % r0["y"])
    return out, n


@test("KRILL-20", "village entry order: MENU (load_file, one file since 18/11) then SND0 (load_raw): each one read whole at the first read (end address and bytes)")
def cache_menu_snd(ctx):
    g = ctx["g"]; L = g.L; F = ctx["files"]
    end0 = g.w16(L["ml_end"])
    name(g, "menu")
    r = g.call_keep(L["load_file"], tmax=60)
    d = F["menu"]
    la = d[0] | d[1] << 8
    end = g.w16(ENDADDR)
    check(r["c"] == 0 and end == end0, "menu: C = %d, end $%04x, expected $%04x (%+d bytes)" % (r["c"], end, end0, end - end0))
    check(ram(g, la, len(d) - 2) == d[2:], "menu: bytes differ from the file")
    name(g, "snd0")
    g.poke16(L["ptr0"], L["SND_LBUF"])
    r = g.call_keep(L["load_raw"], tmax=60)
    d = F["snd0"][2:]
    end = g.w16(ENDADDR)
    check(r["c"] == 0 and end == L["SND_LBUF"] + len(d), "snd0 after menu: C = %d, end $%04x, expected $%04x (%+d bytes)" % (r["c"], end, L["SND_LBUF"] + len(d), end - L["SND_LBUF"] - len(d)))
    check(bytes(g.mem(L["SND_LBUF"], len(d))) == d, "snd0 after menu: bytes differ from the file")


@test("KRILL-21", "snd_get checks the end address: every song read once into both buffers; with a wrong expected length 3 reads, then no music in that buffer (snd_cur = 0)")
def guard_snd(ctx):
    g = ctx["g"]; L = g.L
    for sid in range(len([n for n in ctx["files"] if n.startswith("snd")])):
        for b in (0, 1):
            g.poke(L["snd_cur"] + b, 0)
            _, n = count_loads(g, L["snd_get"], "a=%02x,x=%02x" % (sid, b))
            check(n == 1 and g.b(L["snd_cur"] + b) == sid + 1, "song %d, buffer %d: %d reads, snd_cur %d" % (sid, b, n, g.b(L["snd_cur"] + b)))
    lo = g.b(L["snd_llo"])
    g.poke(L["snd_llo"], lo + 1)
    g.poke(L["snd_cur"], 0)
    try:
        _, n = count_loads(g, L["snd_get"], "a=00,x=00")
    finally:
        g.poke(L["snd_llo"], lo)
    check(n == 3 and g.b(L["snd_cur"]) == 0, "wrong length: %d reads (expected 3), snd_cur %d (expected 0)" % (n, g.b(L["snd_cur"])))


@test("KRILL-22", "ovl_town checks the end of the MENU file (= end of zone 2, ml_end): a file that does not end there is read 3 times, then C = 1")
def guard_menu(ctx):
    g = ctx["g"]; L = g.L
    g.poke(L["ovl_cur"], 0)
    r, n = count_loads(g, L["ovl_town"])
    check(n == 1 and r["c"] == 0 and g.b(L["ovl_cur"]) == 1, "right end: %d reads (expected 1: one file since 18/11), C = %d" % (n, r["c"]))
    a = L["ml_end"]
    lo = g.b(a)
    g.poke(a, lo + 1)
    g.poke(L["ovl_cur"], 0)
    try:
        r, n = count_loads(g, L["ovl_town"])
    finally:
        g.poke(a, lo)
    check(n == 3 and r["c"] == 1 and g.b(L["ovl_cur"]) == 0, "wrong end: %d reads (expected 3), C = %d" % (n, r["c"]))
    g.poke(L["ovl_cur"], 0)
    r, n = count_loads(g, L["ovl_town"])
    check(n == 1 and r["c"] == 0, "module read again: %d reads, C = %d" % (n, r["c"]))


@test("KRILL-23", "every file of the disk loaded right after its predecessor in the directory (served from the drive's next-file cache) equals its file: bytes and end address")
def cache_all(ctx):
    g = ctx["g"]
    files = directory(g.disk)
    dest, bad = 0x1000, []
    for (pn, _, _), (fn, _, d) in zip(files, files[1:]):
        load_to(g, pn, dest)
        c, end = load_to(g, fn, dest)
        d = d[2:]
        if c or end != dest + len(d) or ram(g, dest, len(d)) != d:
            bad.append("%s after %s: C = %d, %+d bytes" % (fn, pn, c, end - dest - len(d)))
    check(not bad, "; ".join(bad))
