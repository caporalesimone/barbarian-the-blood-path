#!/usr/bin/env python3
"""XP row of the HUD (07/11): up to 9999 the whole number, from 10000 in thousands without decimals ("10K", "30K" ...
"65K"; hput_k in src/game/hud.asm). Test build (TESTUI=28, level 19) in VICE: c_xp and the level-19 threshold are
written in RAM, the HUD is redrawn and row 22 is read from the HUD screen. On tests/lib/c64.py (11/11, G2).
Usage: tests/regression/hud/test_hudxp.py"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from lib import c64 as C64  # noqa: E402

os.chdir(ROOT)
env = dict(os.environ, NOKEYS="1", TESTUI="28", TESTCL="19", TESTLVL="2", TESTSP="1")
subprocess.run(["tools/build/asm.sh", "test"], env=env, check=True, stdout=subprocess.DEVNULL)
subprocess.run(["tools/build/mkdisk.sh"], check=True, stdout=subprocess.DEVNULL)
L = C64.labels("game")
G = {m.group(1): int(m.group(2)) for m in re.finditer(r"^(G_\w+)\s*=\s*(\d+)\s*$", open("out/work/game.lbl").read(), re.M)}
fails = []


def text(codes):
    inv = {G["G_%d" % d]: str(d) for d in range(10)}
    inv.update({G["G_K"]: "K", G["G_SLASH"]: "/", G["G_BLANK"]: " ", G["G_X"]: "X", G["G_P"]: "P"})
    return "".join(inv.get(c, "?") for c in codes)


v = C64.Vice(os.path.join(ROOT, "out", "work", "disk.d64"))
try:
    v.load(os.path.join(ROOT, "out", "work", "start.prg"))           # (11/11) START: installs Krill, GAME from the disk
    v.brk(L["main_loop"]); v.pc(0x080d); v.go(60)

    def frames(n):
        for _ in range(n): v.go(10)

    frames(30)
    lvl = v.b(L["c_lvl"])
    if lvl != 19: fails.append("level %d (expected 19)" % lvl)
    thr = L["xp_n0"] + 18, L["xp_n1"] + 18          # threshold level 19 -> 20 (27146 by default)

    def row(xp, need):
        v.poke16(L["c_xp"], xp)
        v.poke(thr[0], need & 255); v.poke(thr[1], need >> 8)
        v.poke(L["hud_dirty"], 1)
        frames(8)
        return text(v.mem(L["SCR_H"] + 800 + 80 + 4, 12)).rstrip()

    cases = [(9999, 27146, "9999/27K"), (10000, 27146, "10K/27K"), (12345, 9999, "12K/9999"),
             (29999, 27146, "29K/27K"), (30000, 27146, "30K/27K"), (30512, 65535, "30K/65K"),
             (65535, 30000, "65K/30K"), (500, 9999, "500/9999"), (0, 27146, "0/27K")]
    for xp, need, want in cases:
        got = row(xp, need)
        ok = got == want
        print(("ok   " if ok else "FAIL ") + "xp %5d threshold %5d -> '%s'%s" % (xp, need, got, "" if ok else " (expected '%s')" % want))
        if not ok: fails.append(want)
finally:
    v.close()
subprocess.run(["tools/build/asm.sh"], stdout=subprocess.DEVNULL)            # the normal build again
subprocess.run(["tools/build/mkdisk.sh"], stdout=subprocess.DEVNULL)
print("HUD XP test: %s" % ("all ok" if not fails else "%d failures" % len(fails)))
sys.exit(1 if fails else 0)
