"""(15/11, TODO T1) One VICE session that ENDS in each program of the disk, so that the run-time memory probe
(C64_MEMPROBE=1: ./build.sh --probe or --release, Lab64 memmap/probe.py) has dumps for every memory map, not only for GAME.
A dump goes to the program whose main file is in RAM when the session closes (docs/wiki/build.md section 4a): before these
tests LORE, HELP, START and JUKEBOX had none and BARBARIAN two. Each test drives its program through its normal use, checks
that it got there (they are useful tests without the probe too) and closes the session while the program is still in RAM.
GAME has plenty of sessions already (smoke, sanity and most of regression)."""
import os, re
from c64test import test, check
from lib.c64 import Vice, OUT, MonitorError, labels

GETIN = 0xffe4


def scr_text(v):
    v.cmd("bank ram")
    b = v.mem(0x0400, 1000)
    v.cmd("bank cpu")
    return "".join(chr(c + 96) if 1 <= c <= 26 else (chr(c) if 32 <= c < 64 else ".") for c in b)


def key(v, ch):
    v.poke(0x0277, ord(ch)); v.poke(0x00c6, 1)


def stops(v, addr, n, tmax=60):
    """continue through n passages on addr; False if the program never gets there"""
    v.brk(addr)
    try:
        for _ in range(n): v.go(tmax)
        return True
    except MonitorError:
        return False
    finally:
        v.delbrk()


def wait_text(v, txt, polls=400, every=40):
    """the program calls GETIN while it waits for a key: look at the screen every 'every' calls"""
    for _ in range(polls):
        if not stops(v, GETIN, every): return False
        if txt in scr_text(v): return True
    return False


def barbarian_menu(v):
    v.load(os.path.join(OUT, "barbarian.prg")); v.pc(0x080d)
    return wait_text(v, "hear the legend")


@test("PROBE-10", "BARBARIAN: the loader menu with its three entries; the session ends in BARBARIAN (memory probe)")
def probe_barbarian(ctx):
    v = Vice(os.path.join(OUT, "disk.d64"))
    try:
        check(barbarian_menu(v), "no BARBARIAN menu")
        t = scr_text(v)
        check(all(x in t for x in ("game manual", "walk the blood path")), "BARBARIAN menu without its entries")
        stops(v, GETIN, 200)                                     # some idle frames in the menu
    finally:
        v.close()


@test("PROBE-11", "LORE from the BARBARIAN menu: title, PRESS SPACE, the story scrolls; the session ends in LORE (memory probe)")
def probe_lore(ctx):
    L = labels("lore")
    v = Vice(os.path.join(OUT, "disk.d64"))
    try:
        check(barbarian_menu(v), "no BARBARIAN menu")
        key(v, "1")                                              # the trampoline loads LORE with the KERNAL
        lst = open(os.path.join(OUT, "lore.lst")).read()
        wait = int(re.search(r"^\.\w+\s+(\w+)\s.*_wait\s+lda", lst, re.M).group(1), 16)   # PRESS SPACE loop (as LORE-10)
        check(stops(v, wait, 1, 200), "LORE never reached PRESS SPACE")
        v.pc(L["lore_start"])                                    # SPACE pressed: the story
        check(stops(v, L["lirq"], 700), "LORE: no IRQ after lore_start")
        check(v.b(L["lstate"]) in (2, 3), "LORE: the story does not scroll (state %d)" % v.b(L["lstate"]))
    finally:
        v.close()


@test("PROBE-12", "HELP from the BARBARIAN menu: all the pages (data/help.txt); the session ends in HELP on the last page (memory probe)")
def probe_help(ctx):
    HP = [ln[4:].strip() for ln in open(os.path.join(OUT, "..", "..", "data", "help.txt")) if ln.startswith("=== ")]
    v = Vice(os.path.join(OUT, "disk.d64"))
    try:
        check(barbarian_menu(v), "no BARBARIAN menu")
        key(v, "2")
        check(wait_text(v, HP[0]), "BARBARIAN -> HELP: no page 1")
        for n, t in enumerate(HP[1:]):
            key(v, " ")
            check(wait_text(v, t, 40), "HELP: no page %d (%s)" % (n + 2, t))
    finally:
        v.close()


@test("PROBE-13", "START: Krill installed, GAME loaded; the session ends in START just before GAME is unpacked (memory probe)")
def probe_start(ctx):
    """Stopped at zx0_unpack: later GAME is unpacked over $0400 and the dump would hold both main files (a tie)."""
    L = labels("start")
    v = Vice(os.path.join(OUT, "disk.d64"))
    try:
        v.load(os.path.join(OUT, "start.prg"))
        v.brk(L["zx0_unpack"]); v.pc(0x080d)
        try:
            v.go(120)
        except MonitorError:
            check(False, "START never reached zx0_unpack (GAME not loaded)")
        v.delbrk()
        check(v.regs()["pc"] == L["zx0_unpack"], "START: not at zx0_unpack")
    finally:
        v.close()


@test("PROBE-14", "JUKEBOX: two tunes played and stopped; the session ends in JUKEBOX (memory probe)")
def probe_jukebox(ctx):
    L = labels("jukebox")
    v = Vice(os.path.join(OUT, "disk.d64"))
    try:
        v.load(os.path.join(OUT, "jukebox.prg")); v.pc(0x080d)
        check(stops(v, GETIN, 50), "JUKEBOX: no GETIN (not running)")
        key(v, chr(13))                                          # RETURN: play the selected tune
        stops(v, GETIN, 1000)                                    # the tune plays in the IRQ meanwhile
        check(v.b(L["playing"]) != 0xff, "JUKEBOX: RETURN does not play")
        key(v, "S"); stops(v, GETIN, 20)                         # next entry
        key(v, chr(13)); stops(v, GETIN, 1000)
        key(v, "X"); stops(v, GETIN, 50)                         # stop
        check(v.b(L["playing"]) == 0xff, "JUKEBOX: X does not stop")
    finally:
        v.close()
