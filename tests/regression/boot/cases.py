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
rel_script("LORE-10", "release: BARBARIAN menu, HELP (5 pages), LORE (identical LDAT), joystick fire held = double scroll speed (released: normal; held at the end: no exit), return, START", [PY, os.path.join(H, "test_lore.py")])
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


script("TITLEMUSIC-10", "HELP: Demon's Eye with its own IRQ clock (CIA1 timer A, 19656 cycles), IRQ/SID/CIA restored before the KERNAL LOAD",
       [PY, os.path.join(H, "test_title_music.py"), "help"])
script("TITLEMUSIC-11", "BARBARIAN: Demon's Eye with its own IRQ clock (CIA1 timer A, 19656 cycles), IRQ/SID/CIA restored before the KERNAL LOAD",
       [PY, os.path.join(H, "test_title_music.py"), "barbarian"])
