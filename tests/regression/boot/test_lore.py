#!/usr/bin/env python3
"""Release disk in VICE (warp, emulated 1541): BARBARIAN (menu) -> HELP -> LORE -> BARBARIAN -> START.
On tests/lib/c64.py (11/11, G2: English, no fixed delays: the waits stop on GETIN, on the LORE IRQ or on addresses).
1. The loader BARBARIAN (out/barbarian.prg, release build) shows its three entries; key "2": the manual HELP from disk,
   the 5 pages (space = next), RUN/STOP and fire from the last page go back to the menu.
2. Key "1" (KERNAL keyboard buffer): the trampoline loads LORE from disk; LORE installs Krill's Loader (11/11), loads
   TITLE + LDAT and unpacks LDAT in place: byte by byte against out/ldat_raw.bin (tools/build/gen_lore.py).
3. At PRESS SPACE jump to lore_start: after the pause the story scrolls (state 2, the stream advances, no hang);
   screenshots of the logo and of the scroll with --shot (real speed: only there the waits are timed).
4. RUN/STOP (variable lstop): back to BARBARIAN (Krill uninstalled, BARBARIAN reloaded by the KERNAL); RUN/STOP
   while LORE loads (ld_stop): same.
5. Key "3": the trampoline loads START and the game start runs ($A000).
Usage: tests/regression/boot/test_lore.py [--shot prefix]   (needs an up-to-date out/disk.d64)."""
import os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from lib import c64 as C64  # noqa: E402

SHOT = sys.argv[sys.argv.index("--shot") + 1] if "--shot" in sys.argv else None
LBL = C64.labels("lore")
lst = open(os.path.join(ROOT, "out", "lore.lst")).read()
WAIT = int(re.search(r"^\.\w+\s+(\w+)\s.*_wait\s+lda", lst, re.M).group(1), 16)
UNP = int(re.search(r"^\.\w+\s+(\w+)\s+20 \w\w \w\w\s+jsr \$\w+\s+jsr zx0_unpack", lst, re.M).group(1), 16) + 3
AFTER_LDSTOP = int(re.search(r"^\.\w+\s+(\w+)\s+8d \w\w \w\w\s+sta \$\w+\s+sta ld_stop\s+; RUN/STOP non", lst, re.M).group(1), 16) + 3
RAW = open(os.path.join(ROOT, "out", "ldat_raw.bin"), "rb").read()
GETIN = 0xffe4
fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)


v = C64.Vice(os.path.join(ROOT, "out", "disk.d64"))


def scr_text():
    v.cmd("bank ram")
    b = v.mem(0x0400, 1000)
    v.cmd("bank cpu")
    return "".join(chr(c + 96) if 1 <= c <= 26 else (chr(c) if 32 <= c < 64 else ".") for c in b)


def key(ch):
    v.poke(0x0277, ord(ch)); v.poke(0x00c6, 1)


def stops(addr, n, tmax=60):
    """continue through n passages on addr (e.g. n frames of an IRQ); False if the program never gets there"""
    v.brk(addr)
    try:
        for _ in range(n): v.go(tmax)
        return True
    except C64.MonitorError:
        return False
    finally:
        v.delbrk()


def until(addr, tmax=200):
    v.brk(addr)
    try:
        v.go(tmax); return True
    except C64.MonitorError:
        return False
    finally:
        v.delbrk()


def wait_text(txt, polls=400, every=40):
    """the program calls GETIN while it waits for a key: check the screen every 'every' calls"""
    for _ in range(polls):
        if not stops(GETIN, every): return False
        if txt in scr_text(): return True
    return False


def shot(name, sec):
    """only with --shot: real speed for 'sec' seconds, then a screenshot"""
    if not SHOT: return
    v.cmd("warp off")
    v.s.sendall(b"x\n"); time.sleep(sec); v.quiet()
    v.screenshot("%s_%s.png" % (os.path.abspath(SHOT), name))
    v.cmd("warp on")


try:
    # 1. menu
    v.load(os.path.join(ROOT, "out", "barbarian.prg"))
    v.pc(0x080d)
    check(wait_text("hear the legend") and all(t in scr_text() for t in ("game manual", "walk the blood path")),
          "BARBARIAN: menu with its three entries")
    shot("front", 1.0)
    key("2")                                                    # the manual (HELP from disk): 5 pages
    check(wait_text("moving and fighting"), "BARBARIAN -> HELP: page 1 (moving and fighting)")
    shot("help1", 1.0)
    for n, t in enumerate(["fire on places", "inventory, chests and shops", "menus and saving", "the hud"]):
        key(" ")
        check(wait_text(t, 40), "HELP: page %d (%s)" % (n + 2, t))
        shot("help%d" % (n + 2), 1.0)
    key(chr(3))                                                 # RUN/STOP (GETIN = 3)
    check(wait_text("hear the legend"), "HELP -> BARBARIAN (RUN/STOP): the menu again")
    key("2")
    wait_text("moving and fighting")
    for _ in range(5):
        key(" "); stops(GETIN, 40)
    check(wait_text("hear the legend"), "HELP: fire on the last page goes back to the menu")
    # 2. key 1 -> LORE: loading, LDAT unpacked
    v.cmd("sw reset")
    key("1")
    ok = until(UNP)
    check(ok, "BARBARIAN -> LORE: LORE loaded, LDAT read and unpacked")
    if ok:
        dump = os.path.join(ROOT, "out", "test_ldat_dump.prg")
        if os.path.exists(dump): os.remove(dump)
        v.cmd("bank ram")
        v.cmd('s "%s" 0 %04x %04x' % (dump, LBL["LD_DST"], LBL["LD_DST"] + len(RAW) - 1))
        v.cmd("bank cpu")
        for _ in range(100):
            if os.path.exists(dump) and os.path.getsize(dump) == len(RAW) + 2: break
            time.sleep(0.05)
        got = open(dump, "rb").read()[2:] if os.path.exists(dump) else b""
        check(got == RAW, "LDAT unpacked in VICE = out/ldat_raw.bin (%d B)" % len(RAW))
        if os.path.exists(dump): os.remove(dump)
    ok = until(WAIT)
    sw = re.findall(r"Stopwatch:\s*(\d+)", v.cmd("sw"))
    check(ok, "LORE: title complete, PRESS SPACE (%.0f s from key 1, emulated 1541)" % (int(sw[0]) / 985248 if sw else -1))
    # 3. the story
    v.pc(LBL["lore_start"])
    shot("logo", 2.5)
    stops(LBL["lirq"], 20)
    st0 = v.b(LBL["lstate"]); p0 = v.mem(0x60, 2)
    if SHOT:                            # real speed, a screenshot every 8 s up to the end (stop on the bottom IRQ:
        v.cmd("warp off")               # a whole frame; stopped mid-frame VICE shows half old half new: "double" rows)
        for i in range(9):
            v.s.sendall(b"x\n"); time.sleep(8); v.quiet()
            stops(LBL["lirq"], 1, 5)
            v.screenshot("%s_run%d.png" % (os.path.abspath(SHOT), i))
        v.cmd("warp on")
    else:
        stops(LBL["lirq"], 600)                                 # past the pause on the logo (250 frames)
    st1 = v.b(LBL["lstate"]); p1 = v.mem(0x60, 2)
    check(st0 in (1, 2) and st1 in (2, 3), "LORE: pause on the logo, then scrolling (state %d -> %d)" % (st0, st1))
    check(p1 != p0, "LORE: the line stream advances ($%02x%02x -> $%02x%02x)" % (p0[1], p0[0], p1[1], p1[0]))
    for _ in range(200):                                        # to the end of the story (state 3)
        if v.b(LBL["lstate"]) == 3: break
        stops(LBL["lirq"], 100)
    check(v.b(LBL["lstate"]) == 3, "LORE: the story reaches its end and stops (state 3)")
    shot("end", 1.0)
    # 4. RUN/STOP -> BARBARIAN
    until(LBL["lmain"])                                         # (the IRQ rewrites lstop from the keyboard: poke it
    v.poke(LBL["lstop"], 1)                                     # in the main loop, which reads it right away)
    t_ok = wait_text("hear the legend")
    check(t_ok and "walk the blood path" in scr_text(), "LORE -> BARBARIAN (RUN/STOP): the menu again")
    # 4b. RUN/STOP while LORE loads (ld_stop, set by the music IRQ): files closed, the menu again
    key("1")
    ok = until(AFTER_LDSTOP, 60)
    v.poke(LBL["ld_stop"], 1)
    check(ok and wait_text("hear the legend"), "LORE -> BARBARIAN (RUN/STOP during the loading)")
    # 5. key 3 -> START
    key("3")
    check(until(0xa000, 60), "BARBARIAN -> START: the game start runs ($A000)")
finally:
    v.close()
print("LORE test: %s" % ("all ok" if not fails else "%d failures" % len(fails)))
sys.exit(1 if fails else 0)
