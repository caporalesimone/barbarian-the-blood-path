#!/usr/bin/env python3
"""Monster chase with a short path (17/11, mon_path / mon_follow): seed ANOANO, cases found by the movement simulator where the
old chase (sliding along the wall) stayed in a corner or shook on the edge of a wall (1 px corner slide forth and back). For
every case: hero on a tile, one monster moved to a tile, awake; within 12 x 30 frames it must be next to the hero. Cases
picked with the simulator: the old chase fails, the new one reaches the hero (out/tmp: not kept; docs/wiki/mostri.md)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves"))
import test_saves as T  # noqa: E402

CASES = [  # (level, monster tile, hero tile): the old code stayed at the monster tile, shook there or went into a pocket
    (1, (18, 10), (13, 15)),
    (1, (13, 16), (6, 18)),
    (3, (38, 32), (41, 27)),
    # (18/11) the cases on levels 6 and 7 are gone: since then they are swamp levels (islands and boardwalks), their maps are not
    # those of the simulator any more
]
err = []
T.fresh()
v = T.Vice()
L = T.lbl
try:
    v.menu(); v.cmd("> %04x 0a 17 18 0a 17 18" % L["seedbuf"]); v.play(1)
    w = lambda a: "%02x %02x" % (a & 255, a >> 8)
    for lv, (mx, my), (hx, hy) in CASES:
        if not v.level(lv):
            sys.exit("level %d not reached" % lv)
        v.cmd("> %04x e8 03" % L["hpmax"])
        n = v.mem(L["lb_cnt"], 1)[0]
        for i in range(n):                                   # the others asleep and far away: only monster 0 moves
            v.cmd("> %04x 00" % (L["malive"] + i))
        X, Y = hx * 16 + 8, hy * 16 + 8
        v.cmd("> %04x %s" % (L["px"], w(X))); v.cmd("> %04x %s" % (L["py"], w(Y))); v.cmd("> %04x 01" % L["force_redraw"])
        A, B = mx * 16 + 8, my * 16 + 8
        for k, val in (("malive", 1), ("mwake", 1), ("mfar", 0), ("mslide", 0), ("mslc", 0)):
            v.cmd("> %04x %02x" % (L[k], val))
        v.cmd("> %04x %02x" % (L["mxl"], A & 255)); v.cmd("> %04x %02x" % (L["mxh"], A >> 8))
        v.cmd("> %04x %02x" % (L["myl"], B & 255)); v.cmd("> %04x %02x" % (L["myh"], B >> 8))
        best = 99
        for k in range(12):
            v.cmd("> %04x e8 03" % L["c_hp"])
            v.cmd("break %04x" % L["main_loop"])
            for _ in range(30): v.go(10)
            v.cmd("del")
            x = (v.mem(L["mxl"], 1)[0] + 256 * v.mem(L["mxh"], 1)[0]) / 16
            y = (v.mem(L["myl"], 1)[0] + 256 * v.mem(L["myh"], 1)[0]) / 16
            best = min(best, max(abs(x - hx - .5), abs(y - hy - .5)))
            if best <= 1.6: break
        print("level %d: monster from %s to the hero at %s: %.1f tiles away at the end (%d x 30 frames)" % (lv, (mx, my), (hx, hy), best, k + 1))
        if best > 1.6:
            err.append("level %d: monster from %s does not reach the hero at %s (%.1f tiles)" % (lv, (mx, my), (hx, hy), best))
finally:
    v.close()
if err:
    print("\n".join(err)); sys.exit(1)
print("paths ok")
