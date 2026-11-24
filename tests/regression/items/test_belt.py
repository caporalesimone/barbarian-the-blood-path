#!/usr/bin/env python3
"""Belt and scrolls on the real code (arena build, after a fight): 4 potions at most before chain step 6 (the fifth refused,
reason 1), 8 after it (24/11, F1: the ninth refused),
a stack of scrolls up to 10 (08/11; reason 2 beyond), drinking frees the slot and blocks every potion for the
cooldown, the scroll opens the portal and uses the stack (the last one frees the pack slot)."""
import os, sys, time
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import arena as AR

G = AR.G
err = []
with AR.Arena() as a:
    a.run(lvl=2, plvl=3, monsters=["fallen"], fights=1)
    a.cmd("del", 0.2)

    def call(code):
        n = len(code.split())
        end = 0x340 + n
        a.cmd("> 0340 %s 4c %02x %02x" % (code, end & 255, end >> 8), 0.3)
        a.cmd("break %04x" % end, 0.2)
        a.cmd("r pc=0340", 0.2)
        a.go(15)                                        # (11/11: the shared VICE client)
        a.cmd("del", 0.2)

    def give(it, b=0):
        gi = G["give_item"]
        call("a9 %02x 8d %02x %02x a9 %02x 20 %02x %02x 08 68 8d 60 03" % (b, G["ap_b"] & 255, G["ap_b"] >> 8, it, gi & 255, gi >> 8))
        return a.mem(0x360, 1)[0] & 1, a.mem(G["gv_why"], 1)[0]

    def rd(lbl, n):
        return a.mem(G[lbl], n)

    for lbl, n in (("c_beltt", 8), ("c_pack", 8), ("c_packb", 8)):     # pack: PACK_N = 8 (07/11); belt BELT_N = 8 (24/11)
        a.cmd("f %04x %04x 00" % (G[lbl], G[lbl] + n - 1), 0.2)
    a.cmd("> %04x 00" % G["c_portal"], 0.2)
    P1, P2, S = G["I_POTR"], G["I_POTY"], G["I_SCROLL"]
    a.cmd("> %04x %02x" % (G["q_step"], G["QB_BELT"] - 1), 0.2)     # (24/11) belt of 4: step 6 not handed in
    r = [give(P1), give(P2), give(P1), give(P1), give(P2)]
    if [x[0] for x in r] != [0, 0, 0, 0, 1] or r[4][1] != 1 or rd("c_beltt", 8) != [P1, P2, P1, P1, 0, 0, 0, 0]:
        err.append("potions: %s %s" % (r, rd("c_beltt", 8)))
    a.cmd("> %04x %02x" % (G["q_step"], G["QB_BELT"]), 0.2)         # belt of 8: 4 more behind, the ninth refused
    r = [give(P2), give(P2), give(P1), give(P2), give(P1)]
    if [x[0] for x in r] != [0, 0, 0, 0, 1] or r[4][1] != 1 or rd("c_beltt", 8) != [P1, P2, P1, P1, P2, P2, P1, P2]:
        err.append("potions (belt of 8): %s %s" % (r, rd("c_beltt", 8)))
    a.cmd("f %04x %04x 00" % (G["c_beltt"] + 4, G["c_beltt"] + 7), 0.2)
    r = [give(S, 4), give(S, 4), give(S, 2), give(S)]  # 4, 8, +2 = 10, the eleventh refused
    pk, pb = rd("c_pack", 1), rd("c_packb", 1)
    if [x[0] for x in r] != [0, 0, 0, 1] or r[3][1] != 2 or pk != [S] or pb != [10]:
        err.append("scrolls: %s pack %s count %s" % (r, pk, pb))
    a.cmd("> %04x 01 00" % G["c_hp"], 0.2)      # hp 1 (16 bit)
    a.cmd("f %04x %04x 00" % (G["tmr"], G["tmr"] + 5), 0.2)
    up = G["use_potion"]
    call("a2 01 20 %02x %02x" % (up & 255, up >> 8))
    hp1 = rd("c_hp", 2)
    cd = rd("tmr", 6)[4:6]
    if rd("c_beltt", 4) != [P1, 0, P1, P1] or hp1[0] + 256 * hp1[1] <= 1 or cd == [0, 0]:
        err.append("potion: belt %s hp %s cooldown %s" % (rd("c_beltt", 4), hp1, cd))
    call("a2 00 20 %02x %02x" % (up & 255, up >> 8))   # cooldown on: every potion blocked
    if rd("c_beltt", 4) != [P1, 0, P1, P1]:
        err.append("potion drunk during the cooldown: belt %s" % rd("c_beltt", 4))
    us = G["use_scroll"]
    call("20 %02x %02x" % (us & 255, us >> 8))
    if rd("c_portal", 1) != [1] or rd("c_packb", 1) != [9] or rd("c_retlvl", 1) != [2]:   # 10 - 1
        err.append("scroll: portal %s count %s" % (rd("c_portal", 1), rd("c_packb", 1)))
    a.cmd("> %04x 01" % G["c_packb"], 0.2)     # last scroll: the stack disappears
    call("20 %02x %02x" % (us & 255, us >> 8))
    if rd("c_pack", 1) != [0] or rd("c_packb", 1) != [0]:
        err.append("last scroll: pack %s %s" % (rd("c_pack", 1), rd("c_packb", 1)))
print("belt and scrolls:", "ok" if not err else "FAIL " + "; ".join(err))
sys.exit(1 if err else 0)
