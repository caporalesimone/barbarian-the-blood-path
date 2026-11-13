#!/usr/bin/env python3
"""Start of the game in VICE (warp, emulated 1541), on tests/lib/c64.py (11/11, G2: no fixed delays, English).
Release: START (out/start.prg, run from the monitor): Krill installed, GAME and LOBBY loaded without errors (okf = 3),
hero list (file hl) read.
"dev" (11/11: one disk, POKE 1020,1 as for development): the whole chain from the RUN of BARBARIAN (without menu) loading START
from disk, up to the game menu ($C000), with the menu and the village already in memory.
Also checks the hero list read by START (file hl, 11/11 Krill): CHRTMP = 1 (read) and version = SAVE_VER, and that
GAME unpacked by the 6502 ZX0 decoder equals out/game.prg byte for byte.
Usage: tests/regression/boot/test_start.py [dev] [--shot file.png ...]   (needs an up-to-date out/disk.d64)."""
import os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from lib import c64 as C64  # noqa: E402

DEV = len(sys.argv) > 1 and sys.argv[1] == "dev"
SHOTS = sys.argv[sys.argv.index("--shot") + 1:] if "--shot" in sys.argv else []
GLBL = C64.labels("game")
lst = open(os.path.join(ROOT, "out", "start.lst")).read()                      # (11/11) un solo START
sg = int(re.search(r"^\.\w+\s+(\w+)\s+start_game\s*$", lst, re.M).group(1), 16)        # address of start_game
chrtmp = int(re.search(r"^=\$([0-9a-f]+)\s+CHRTMP\s*=", lst, re.M).group(1), 16)
okf = int(re.search(r"^>\w+\s+(\w+)\s+00\s+okf\s", lst, re.M).group(1), 16)
unp = int(re.search(r"^\.\w+\s+(\w+)\s+20 \w\w \w\w\s+jsr \$\w+\s+jsr zx0_unpack", lst, re.M).group(1), 16)


def fail(msg):
    print("FAIL " + msg); sys.exit(1)


v = C64.Vice(os.path.join(ROOT, "out", "disk.d64"))
try:
    v.load(os.path.join(ROOT, "out", "barbarian.prg" if DEV else "start.prg"))
    if DEV: v.poke(0x03fc, 1)                       # POKE 1020,1: BARBARIAN without its menu, straight to START
    v.cmd("sw reset")
    # GAME packed with ZX0 (tools/build/pack.py): stop right after the in-place unpacking, compare with out/game.prg
    v.brk(unp + 3); v.pc(0x080d)
    try:
        v.go(200)
    except C64.MonitorError:
        fail("GAME not unpacked (START stuck or not loaded)")
    v.delbrk()
    gp = open(os.path.join(ROOT, "out", "game.prg"), "rb").read()
    g0 = gp[0] | gp[1] << 8
    dump = os.path.join(ROOT, "out", "test_zx0_dump.prg")
    if os.path.exists(dump): os.remove(dump)
    v.cmd('s "%s" 0 %04x %04x' % (dump, g0, g0 + len(gp) - 3))
    for _ in range(40):
        if os.path.exists(dump) and os.path.getsize(dump) == len(gp): break
        time.sleep(0.05)
    zx_ok = os.path.exists(dump) and open(dump, "rb").read() == gp
    print("ZX0 unpacking of GAME in VICE:", "identical to out/game.prg" if zx_ok else "DIFFERENT")
    if not zx_ok: fail("ZX0: GAME differs from out/game.prg")
    # end of the loading (start_game): hero list read (CHRTMP: $B000 debug, $B800 release with the bar)
    v.brk(sg)
    try:
        v.go(200)
    except C64.MonitorError:
        fail("START stuck (start_game not reached)")
    v.delbrk()
    sw = int(re.findall(r"Stopwatch:\s*(\d+)", v.cmd("sw"))[0])
    v.cmd("bank ram")
    ch = v.mem(chrtmp, 2)
    files_ok = v.b(okf)
    v.cmd("bank cpu")
    hdr_ok = ch[0] == 1 and ch[1] == GLBL["SAVE_VER"]
    print("hero list (file hl at $%04x): read = %d, version = $%02x (SAVE_VER $%02x); files ok = %d/3"
          % (chrtmp, ch[0], ch[1], GLBL["SAVE_VER"], files_ok))
    for f in SHOTS:
        v.screenshot(os.path.abspath(f))
    # then the game menu, with the LOBBY already in memory (flag LDFLAGS at $8E used; 11/11, Krill: no village cache)
    v.brk(0xc000)
    try:
        v.go(200)
    except C64.MonitorError:
        fail("game menu not reached")
    f = v.mem(0x8e, 1)
    print("%.1f s to the end of the loading, menu flag = %02x" % (sw / 985248, f[0]))
    ok = f == [0] and hdr_ok and files_ok == 3
    if not ok: print("FAIL start: menu flag %s, hero list %s, files %d/3" % (f, hdr_ok, files_ok))
    sys.exit(0 if ok else 1)
finally:
    v.close()
