import os, sys
from c64test import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Boot from the real disk (emulated 1541, one disk since 11/11): BARBARIAN with POKE 1020,1 -> START -> menu;
START with the progress bar, LORE and HELP, HUD crop in the help."""
from c64test import test, Skip, check  # noqa: E402
import subprocess  # noqa: E402
REL = os.environ.get("RELEASE") == "1"


@test("BOOT-10", "POKE 1020,1: BARBARIAN -> START from disk without the menu (Krill installed), GAME, LOBBY and hero list loaded")
def boot_dev(ctx):
    t = subprocess.run([PY, os.path.join(H, "test_start.py"), "dev"], cwd=ROOT, capture_output=True, text=True)
    check(t.returncode == 0, (t.stdout + t.stderr).strip().splitlines()[-1] if (t.stdout + t.stderr).strip() else "exit %d" % t.returncode)


def rel_script(tid, desc, argv, pre=True):
    @test(tid, desc)
    def f(ctx):
        if pre: subprocess.run([os.path.join(ROOT, "tools", "build", "mkdisk.sh")], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        t = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        check(t.returncode == 0, (t.stdout + t.stderr).strip().splitlines()[-1] if (t.stdout + t.stderr).strip() else "exit %d" % t.returncode)


rel_script("BOOT-11", "START from the monitor (wait screen, no bar) up to the game menu", [PY, os.path.join(H, "test_start.py")])
rel_script("LORE-10", "release: BARBARIAN menu, HELP (all the pages of data/help.txt), LORE (identical LDAT), joystick fire held = double scroll speed (released: normal; held at the end: no exit), return, START", [PY, os.path.join(H, "test_lore.py")])
rel_script("LORE-11", "LORE story stream: one blank row between the text rows of a paragraph, two between paragraphs, size limits (15/11)", [PY, os.path.join(H, "test_lore_stream.py")], pre=False)
rel_script("HELP-10", "release: the HUD crop in the help equals the game HUD", [PY, os.path.join(ROOT, "tools", "build", "gen_help.py"), "--check"], pre=False)


@test("BOOT-12", "RUN/STOP while the KERNAL loads LORE (from the BARBARIAN menu): back to the menu, no red border (12/11)")
def boot_stop_lore(ctx):
    """The trampoline loads LORE with the KERNAL (~20 s on a 1541): RUN/STOP makes LOAD return with C=1, A=0 ($F633).
    Before 12/11 the trampoline stopped on a red border; now it loads BARBARIAN again. RUN/STOP is simulated with
    STKEY ($91) = $7F at the STOP check of the LOAD loop ($F4F9), after a few blocks."""
    from lib.c64 import Vice, OUT
    v = Vice(os.path.join(OUT, "disk.d64"))
    try:
        v.load(os.path.join(OUT, "barbarian.prg")); v.pc(0x080d)
        v.brk(0xffe4); v.go(60); v.delbrk()                        # the menu waits for a key
        v.poke(0x0277, ord("1")); v.poke(0xc6, 1)                    # 1: hear the legend
        v.brk(0xf4f9)
        for _ in range(300): v.go(60)                                # some blocks of LORE
        v.delbrk()
        v.poke(0x91, 0x7f)                                           # RUN/STOP pressed
        v.brk(0x080d); v.go(120); v.delbrk()
        barb = open(os.path.join(OUT, "barbarian.prg"), "rb").read()
        check(bytes(v.mem(0x0801, 64)) == barb[2:66], "after RUN/STOP $0801 is not BARBARIAN")
        v.brk(0xffe4); v.go(60); v.delbrk()
        check(v.b(0xd020) != 2, "red border")
    finally:
        v.close()


@test("BOOT-13", "BARBARIAN menu: every choice (1 2 3) blanks the screen BEFORE loading; only its phrase (row 10, yellow) and 'please wait' (row 13), as the START wait screen (16/11)")
def menu_black(ctx):
    """Before 15/11 only "hear the legend" cleared the screen: the manual and the game wrote their phrase on row 17 over the menu
    and the screen went black only when the loaded program started. Since 16/11 the three phrases are centred on row 10 with
    "please wait" on row 13, the same as START's wait screen (txt_init), so the switch BARBARIAN -> START does not change the
    screen. Checked at tramp_run (the load starts there)."""
    from lib.c64 import Vice, OUT
    from vicemon import labels
    L = labels("barbarian")
    v = Vice(os.path.join(OUT, "disk.d64"))
    try:
        for k in "123":
            v.load(os.path.join(OUT, "barbarian.prg")); v.pc(0x080d)
            v.brk(0xffe4); v.go(60); v.delbrk()                    # the menu waits for a key
            v.poke(0x0277, ord(k)); v.poke(0xc6, 1)
            v.brk(L["tramp_run"]); v.go(60); v.delbrk()
            scr = v.mem(0x0400, 1000)
            rows = [i for i in range(25) if i not in (10, 13) and any(c != 0x20 for c in scr[i * 40:i * 40 + 40])]
            check(not rows, "choice %s: rows %s not blank when the load starts" % (k, rows))
            check(any(c != 0x20 for c in scr[400:440]), "choice %s: no phrase on row 10" % k)
            wait = [0x10, 0x0c, 0x05, 0x01, 0x13, 0x05, 0x20, 0x17, 0x01, 0x09, 0x14]       # "please wait" (screen codes)
            check(list(scr[13 * 40 + 14:13 * 40 + 25]) == wait, "choice %s: no 'please wait' on row 13" % k)
    finally:
        v.close()


@test("BOOT-14", "BARBARIAN menu: item 4 'exit game' -> BASIC (READY.), keyboard and screen as at power-on (16/11)")
def menu_exit(ctx):
    from lib.c64 import Vice, OUT
    v = Vice(os.path.join(OUT, "disk.d64"))
    try:
        v.load(os.path.join(OUT, "barbarian.prg")); v.pc(0x080d)
        v.brk(0xffe4); v.go(60); v.delbrk()
        v.poke(0x0277, ord("4")); v.poke(0xc6, 1)
        v.brk(0xa483); ok = v.go(60); v.delbrk()                   # BASIC main loop (READY.)
        check(ok, "exit game: BASIC prompt not reached")
        scr = v.mem(0x0400, 1000)
        text = "".join(chr(c + 64) if 1 <= c <= 26 else " " for c in scr[:400])
        check("READY" in text, "exit game: READY. not on screen")
        check(v.mem(0xd018, 1)[0] == 0x15, "exit game: $D018 is not the power-on value (charset/screen)")
    finally:
        v.close()


@test("BOOT-15", "START is silent (no SID player): the menu music stops when the game is chosen and restarts only in the lobby (16/11)")
def start_silent(ctx):
    from vicemon import labels
    L = labels("start")
    check("sp_play" not in L and "sid_title" not in L, "START still contains the SID player or the title song")
    Lg = labels("lore")
    check("sp_play" in Lg, "LORE lost its player (the intro has the music)")


@test("BOOT-16", "HELP and LORE exits: wait page (phrase on row 10, 'please wait' on row 13, VIC bank 0, screen on) before the reload of BARBARIAN (16/11)")
def exit_pages(ctx):
    from lib.c64 import Vice, OUT
    from vicemon import labels
    def page(v):
        scr = v.mem(0x0400, 1000)
        t = lambda r: "".join(chr(c + 96) if 1 <= c <= 26 else (chr(c) if c == 32 else "?") for c in scr[r * 40:r * 40 + 40]).strip()
        return t(10), t(13)
    for name, entry, stop, want in (("help", None, "tramp_run", "the old scroll rolls up"),
                                    ("lore", "lore_exit", "krill_uninstall", "the legend falls silent")):   # (no Krill resident here)
        L = labels(name)
        v = Vice(os.path.join(OUT, "disk.d64"))
        try:
            v.load(os.path.join(OUT, name + ".prg")); v.pc(0x080d)
            if entry is None:                                       # HELP: RUN/STOP at its key read
                v.brk(0xffe4); v.go(60); v.delbrk()
                v.poke(0x0277, 3); v.poke(0xc6, 1)
            else:                                                   # LORE: the exit routine called directly, once the stub has
                v.brk(L["lm_init"]); v.go(60); v.delbrk()           # copied the body to $A000
                v.pc(L[entry])
            v.brk(L[stop]); ok = v.go(60); v.delbrk()
            check(ok, "%s: %s not reached" % (name, stop))
            p10, p13 = page(v)
            check(p10 == want and p13 == "please wait", "%s: wait page wrong (row 10 %r, row 13 %r)" % (name, p10, p13))
            check((v.b(0xdd00) & 3) == 3 and (v.b(0xd018) & 0xfe) == 0x1e and v.b(0xd011) & 0x10, "%s: VIC not on bank 0 / $0400 / $3800 / screen on" % name)
        finally:
            v.close()


script("TITLEMUSIC-10", "HELP: Demon's Eye with its own IRQ clock (CIA1 timer A, 19656 cycles), IRQ/SID/CIA restored before the KERNAL LOAD",
       [PY, os.path.join(H, "test_title_music.py"), "help"])
script("TITLEMUSIC-11", "BARBARIAN: Demon's Eye with its own IRQ clock (CIA1 timer A, 19656 cycles), IRQ/SID/CIA restored before the KERNAL LOAD",
       [PY, os.path.join(H, "test_title_music.py"), "barbarian"])


@test("BOOT-17", "BARBARIAN menu: one loop per frame whatever the phase of the music IRQ (CIA1 timer locked to the frame; "
      "before 19/11 an IRQ over raster line 250 froze the menu for ever, TODO I6, LORE-10 hangs)")
def boot_irq_phase(ctx):
    """The menu waits for a frame with tm_wait (tm_fc, +1 in tm_irq). The IRQ is moved to a given raster line by a stub that
    reloads CIA1 timer A (force load) with the cycles to that line, then the latch of one PAL frame again; then the menu loop
    must run once per IRQ (50 IRQs). Lines 241, 246, 249: the phases that froze the old wait on line 250."""
    from lib.c64 import Vice, OUT, labels
    L = labels("barbarian")
    v = Vice(os.path.join(OUT, "disk.d64"))

    def ras():
        r = v.mem(0xd011, 2)
        return r[1] + (256 if r[0] & 0x80 else 0)
    bad = []
    try:
        v.load(os.path.join(OUT, "barbarian.prg")); v.pc(0x080d)
        v.brk(L["loop"]); v.go(60); v.delbrk()
        for line in (200, 230, 241, 246, 249, 253, 300, 10):
            n = ((line - ras()) % 312) * 63
            pc = v.regs()["pc"]
            code = [0xa9, n & 255, 0x8d, 0x04, 0xdc, 0xa9, n >> 8, 0x8d, 0x05, 0xdc, 0xa9, 0x11, 0x8d, 0x0e, 0xdc,
                    0xa9, 19655 & 255, 0x8d, 0x04, 0xdc, 0xa9, 19655 >> 8, 0x8d, 0x05, 0xdc, 0xea]
            v.poke(0xcf00, *code)                               # $CF00: free RAM for BARBARIAN (player variables at $C000)
            v.pc(0xcf00); v.brk(0xcf00 + len(code) - 1); v.go(5); v.delbrk(); v.pc(pc)
            v.brk(L["tm_irq"]); v.go(5); v.go(5)
            at = ras()
            v.brk(L["loop"])
            irq = loops = 0
            while irq < 50:
                v.go(5)
                if v.regs()["pc"] == L["tm_irq"]: irq += 1
                else: loops += 1
            v.delbrk()
            if loops < 48: bad.append("IRQ at line %d: %d menu loops in 50 frames" % (at, loops))
    finally:
        v.close()
    check(not bad, "; ".join(bad))
