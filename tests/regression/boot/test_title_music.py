#!/usr/bin/env python3
"""Demon's Eye in HELP and BARBARIAN (15/11, TODO E3/E4; VICE, program loaded by the monitor, no disk access).
Both run with the KERNAL IRQ and include src/common/title_music.inc: the player is clocked by CIA1 timer A (19656 cycles =
one PAL frame), NOT by the KERNAL's own rate, and the IRQ vector is the program's (tm_irq).
1. The vector $0314/5 points to tm_irq, the player runs (sp_on) and plays from the title song (sp_bl/sp_bh = sid_title);
   the SID gets written.
2. sp_play is called once per 19656 cycles (50 passes: every gap within 60 cycles of a frame, total within 0.1%).
3. Leaving for a KERNAL LOAD (the key that makes the program call tramp_run: stop there): vector back to $EA31, player
   stopped, SID all 0 (volume included), CIA1 timer A reloaded with the KERNAL latch ($4025: high byte of the counter $40).
Usage: test_title_music.py help|barbarian"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from lib import c64 as C64  # noqa: E402

prog = sys.argv[1]
KEY = {"help": 3, "barbarian": ord("2")}[prog]            # RUN/STOP from the manual, "2" (the manual) from the menu
L = C64.labels(prog)
fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)


v = C64.Vice(os.path.join(ROOT, "out", "work", "disk.d64"))
try:
    v.load(os.path.join(ROOT, "out", "work", prog + ".prg"))
    v.pc(0x080d)
    v.brk(L["sp_play"])
    v.go(60)                                               # first call of the player (IRQ)
    vec = v.mem(0x0314, 2)
    check(vec[0] + 256 * vec[1] == L["tm_irq"], "IRQ vector = tm_irq ($%04x), not the KERNAL's" % L["tm_irq"])
    check(v.mem(L["sp_bl"], 2) == [L["sid_title"] & 255, L["sid_title"] >> 8], "player on the title song (sid_title)")
    cyc = [v.go(60) for _ in range(51)]
    gaps = [b - a for a, b in zip(cyc, cyc[1:])]
    check(all(abs(g - 19656) <= 60 for g in gaps), "sp_play every 19656 cycles (gaps %d..%d)" % (min(gaps), max(gaps)))
    check(abs(sum(gaps) - 50 * 19656) <= 50 * 19656 // 1000, "50 passes = %d cycles (expected %d)" % (sum(gaps), 50 * 19656))
    check(v.b(L["sp_on"]) == 1, "player running (sp_on)")
    check(v.b(0xd418) & 0x0f != 0, "SID volume on while playing")
    v.delbrk()
    v.brk(L["tramp_run"])                                  # the program leaves for a KERNAL LOAD: stop before it starts
    v.poke(0x0277, KEY); v.poke(0x00c6, 1)                 # key in the KERNAL buffer (GETIN)
    v.go(60)
    vec = v.mem(0x0314, 2)
    check(vec[0] + 256 * vec[1] == 0xea31, "before the LOAD: IRQ vector back to $EA31")
    check(v.b(L["sp_on"]) == 0, "before the LOAD: player stopped")
    check(v.mem(0xd400, 0x19) == [0] * 0x19, "before the LOAD: SID all 0 (volume included)")
    check(0x3f <= v.b(0xdc05) <= 0x40, "before the LOAD: CIA1 timer A reloaded with the KERNAL latch (counter high $%02x)" % v.b(0xdc05))
    fl = re.search(r"([01]{8})\s", v.cmd("r").split("\n")[-3] if False else v.cmd("r"))
    check(fl is not None and fl.group(1)[5] == "1", "before the LOAD: interrupts disabled (I flag)")
finally:
    v.close()
if fails:
    print("\n".join(fails)); sys.exit(1)
print("%s: Demon's Eye ok" % prog)
