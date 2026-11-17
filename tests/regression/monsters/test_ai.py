#!/usr/bin/env python3
"""Monster chase in VICE: seed ANOANO, level 2, hero at (34,20) (report of 06/11: the skeleton of the south-east
room stayed still in the top-left corner of the room, (37,25), with the hero beyond the wall). Monster 2, awake, must
get close to the hero (17/11: with a short path, mon_path / mon_follow). Also the hero: pushed against the corner of a gap with
4 px of misalignment he gets through (corner adjustment in try_step_x/try_step_y)."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves"))
import test_saves as T  # noqa: E402

err = []
T.fresh()
v = T.Vice()
L = T.lbl
try:
    v.menu(); v.cmd("> %04x 0a 17 18 0a 17 18" % L["seedbuf"]); v.play(1)
    if not v.level(2): sys.exit("level 2 not reached")
    v.cmd("> %04x e8 03" % L["hpmax"])
    def put(tx, ty, dx=0, dy=0):
        X, Y = tx * 16 + 8 + dx, ty * 16 + 8 + dy
        v.cmd("> %04x %02x %02x" % (L["px"], X & 255, X >> 8)); v.cmd("> %04x %02x %02x" % (L["py"], Y & 255, Y >> 8))
        v.cmd("> %04x 01" % L["force_redraw"])
    def mpos(i):
        return ((v.mem(L["mxl"] + i, 1)[0] + 256 * v.mem(L["mxh"] + i, 1)[0]) / 16,
                (v.mem(L["myl"] + i, 1)[0] + 256 * v.mem(L["myh"] + i, 1)[0]) / 16)
    put(34, 20)
    p0 = mpos(2)
    v.cmd("> %04x 01" % (L["mwake"] + 2))
    best = 99
    for k in range(16):
        v.cmd("> %04x e8 03" % L["c_hp"])
        v.cmd("break %04x" % L["main_loop"])            # (11/11, G2: 30 frames of game instead of 0.6 s of real time)
        for _ in range(30): v.go(10)
        v.cmd("del")
        x, y = mpos(2)
        best = min(best, max(abs(x - 34.5), abs(y - 20.5)))
    print("monster 2: from (%.1f,%.1f) to (%.1f,%.1f), minimum distance from the hero %.1f tiles" % (p0 + (x, y) + (best,)))
    if best > 2.5:
        err.append("monster 2 does not reach the hero (stays at %.1f tiles)" % best)
    # hero against the corner: below the gap (40-41, 23-24) with the centre at x = 638 (4 px inside column 39, wall on
    # row 24): 40 steps of 2 px up with try_step_y must go through the gap (y < row 23)
    def w(a): return "%02x %02x" % (a & 255, a >> 8)
    X, Y = 638, 25 * 16 + 8
    v.cmd("> %04x %s" % (L["ent_x"], w(X))); v.cmd("> %04x %s" % (L["ent_y"], w(Y)))
    v.cmd("> 03ff 28"); v.cmd("> %04x 00" % L["st_nz"])
    v.cmd("> 0340 a9 fe 20 %s ce ff 03 d0 f6 4c 4b 03" % w(L["try_step_y"]))
    v.cmd("break 034b"); v.cmd("r pc=0340"); v.go(20); v.cmd("del")
    ex = (v.mem(L["ent_x"], 1)[0] + 256 * v.mem(L["ent_x"] + 1, 1)[0])
    ey = (v.mem(L["ent_y"], 1)[0] + 256 * v.mem(L["ent_y"] + 1, 1)[0])
    print("hero against the corner: from (%d,%d) to (%d,%d) px" % (X, Y, ex, ey))
    if ey >= 23 * 16 + 8:
        err.append("hero stuck on the corner of the gap: (%d,%d)" % (ex, ey))
finally:
    v.close()
if err:
    print("\n".join(err)); sys.exit(1)
print("chase ok")
