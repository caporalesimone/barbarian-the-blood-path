import os, sys
from lib.runner import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Boot from the real disk (emulated 1541, one disk since 11/11): BARBARIAN with POKE 1020,1 -> START -> menu;
START with the progress bar, LORE and HELP, HUD crop in the help."""
from lib.runner import test, Skip, check  # noqa: E402
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
rel_script("LORE-10", "release: BARBARIAN menu, HELP (5 pages), LORE (identical LDAT), return, START", [PY, os.path.join(H, "test_lore.py")])
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
