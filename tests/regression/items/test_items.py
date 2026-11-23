#!/usr/bin/env python3
"""Real code (arena build, after a fight):
- 255 items generated in a row (gen_item, chestLevel 96): the program must come back (06/11: the scroll category
  jumped into the middle of an instruction and ended in BRK);
- weapon breaking (wear with durability 1): the weapon stays with durability 0 and damage 0 (07/11: no fists), "broken";
- HUD warnings (low hp, weapon about to break);
- time played from the TOD clock of CIA2: tod_start at 50 Hz, tod_tick adds minutes and hours to c_game."""
import os, re, sys, time
sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "tools", d) for d in ("build", "vice", "atlas", "simulators")]
import arena as AR

G = AR.G
err = []
with AR.Arena() as a:
    a.run(lvl=2, plvl=3, monsters=["fallen"], fights=1)
    a.cmd("del", 0.2)

    def call(code, lim=30):
        n = len(code.split())
        end = 0x340 + n
        a.cmd("> 0340 %s 4c %02x %02x" % (code, end & 255, end >> 8), 0.3)
        a.cmd("break %04x" % end, 0.2)
        a.cmd("r pc=0340", 0.2)
        a.go(lim)                                        # (11/11: the shared VICE client)
        a.cmd("del", 0.2)

    def jsr(lbl):
        return "20 %02x %02x" % (G[lbl] & 255, G[lbl] >> 8)

    def rd(lbl, n=1, off=0):
        return a.mem(G[lbl] + off, n)

    def wr(lbl, *v, off=0):
        a.cmd("> %04x %s" % (G[lbl] + off, " ".join("%02x" % x for x in v)), 0.2)

    SW = G["I_SWORD"]
    # ---- 255 items generated (every category, scroll too): no crash
    def w(l): return "%02x %02x" % (G[l] & 255, G[l] >> 8)
    wr("gi_force", 0)
    call("a0 ff a9 60 8d %s 98 48 %s 68 a8 88 d0 f1" % (w("gi_ll"), jsr("gen_item")), lim=40)
    pc = re.findall(r"\.;([0-9a-f]{4})", a.cmd("r", 0.5))
    if not pc or int(pc[-1], 16) != 0x340 + 17:
        err.append("gen_item x 255: the program did not come back (pc %s)" % pc)
    # ---- weapon breaking
    wr("c_eq", SW); wr("c_eqb", 0); wr("c_eqd", 1); wr("c_eqm", 50)
    call(jsr("recalc_stats") + " a9 01 a2 00 " + jsr("wear"))
    st = rd("s_dn", 3)
    # 07/11: the broken weapon stays in hand (durability 0) and does no damage: no fists
    if rd("c_eq") != [SW] or rd("c_eqd") != [0] or rd("c_eqm") != [50] or rd("hud_nm") != [4] or st != [0, 8, 0]:
        err.append("breaking: c_eq %s c_eqd %s c_eqm %s hud_nm %s dice %s (expected sword 0 50 4 [0, 8, 0])"
                   % (rd("c_eq"), rd("c_eqd"), rd("c_eqm"), rd("hud_nm"), st))
    call("a9 01 a2 00 " + jsr("wear"))          # more wear on the broken weapon: stays at 0 (no wrap to 255)
    if rd("c_eqd") != [0]:
        err.append("broken weapon worn again: durability %s (expected 0)" % rd("c_eqd"))
    # armor (07/11): at 0 it stays worn but gives no AC
    AR = G["I_CHAIN_MAIL"]
    wr("c_eq", AR, off=1); wr("c_eqb", 0, off=1); wr("c_eqd", 9, off=1); wr("c_eqm", 50, off=1)
    call(jsr("recalc_stats")); ac_ok = rd("s_ac")[0]
    wr("c_eqd", 1, off=1)
    call("a9 01 a2 01 " + jsr("wear"))
    ac_br = rd("s_ac")[0]
    if rd("c_eq", 2)[1] != AR or rd("c_eqd", 2)[1] != 0 or ac_br >= ac_ok:
        err.append("broken armor: c_eq %s c_eqd %s AC %d -> %d (expected the same armor at 0 and a lower AC)"
                   % (rd("c_eq", 2), rd("c_eqd", 2), ac_ok, ac_br))
    wr("c_eq", 0, off=1); wr("c_eqm", 0, off=1)
    # (11/11) the smith repair is in the module MENU, not in the arena build: SHOP-FIX-10 (tests/regression/gold)
    # ---- HUD warnings: low hp (HP cells colour alternating) and icon of the weapon about to break
    wr("hpmax", 100, 0); wr("c_hp", 10, 0); wr("hw_low", 0)
    wr("c_eq", SW); wr("c_eqd", 5, 0, 0); wr("c_eqm", 100, 0, 0)
    wr("frame", 0)
    call(jsr("hud_p0"))                               # (23/11) the HP bar (row 22): the low-HP blink colours its full cells
    call(jsr("hud_warn"))
    c0, low = a.mem(0xdb71, 1)[0] & 15, rd("hw_low")[0]
    ico = a.mem(G["SCR_H"] + 899, 3)
    wr("frame", 16)
    call(jsr("hud_warn"))
    c1 = a.mem(0xdb71, 1)[0] & 15
    if (c0, c1, low) != (2, 7, 1) or ico != [G["G_WSWORD"], G["G_BLANK"], G["G_BLANK"]]:
        err.append("HUD warnings: HP bar colours %d/%d (expected 2/7), hw_low %d, icons %s" % (c0, c1, low, ico))
    wr("c_hp", 90, 0); wr("c_eqd", 60)
    call(jsr("hud_warn"))
    if rd("hw_low")[0] != 0 or a.mem(G["SCR_H"] + 899, 1)[0] != G["G_BLANK"]:
        err.append("HUD warnings: they do not switch off (hw_low %d)" % rd("hw_low")[0])
    # threshold in percent (rules.yaml durability.warn_percent): new dagger 15/15 no icon, 3/15 (20%) icon,
    # 4/15 no; 60/255 (x5 above 255) no
    for d, m, want in ((15, 15, 0), (3, 15, 1), (4, 15, 0), (60, 255, 0), (51, 255, 1)):
        wr("c_eqd", d); wr("c_eqm", m)
        call(jsr("hud_warn"))
        on = a.mem(G["SCR_H"] + 899, 1)[0] == G["G_WSWORD"]
        if on != bool(want):
            err.append("durability warning %d/%d: icon %s (expected %s)" % (d, m, on, bool(want)))
    # ---- TOD clock
    wr("c_game", 1, 0, 0)
    # tod_start, then ~11 s of waiting (32 x 65536 x 5 cycles + IRQ); the VICE stopwatch measures the cycles:
    # TOD seconds = cycles / 985248 (PAL) at 50 Hz, x 1.2 if it were 60 Hz
    a.cmd("sw reset", 0.3)
    call(jsr("tod_start") + " a9 20 85 fb a0 00 a2 00 ca d0 fd 88 d0 f8 c6 fb d0 f4", lim=60)
    cyc = int(re.findall(r"Stopwatch:\s+(\d+)", a.cmd("sw", 0.5))[-1])
    t = a.mem(0xdd09, 2)                             # seconds, minutes (BCD)
    sec = (t[0] >> 4) * 10 + (t[0] & 15) + 60 * ((t[1] >> 4) * 10 + (t[1] & 15))
    want = cyc / 985248
    if abs(sec - want) > 1:
        err.append("TOD: %d s after %.1f s of cycles (50 Hz?)" % (sec, want))
    a.cmd("> dd0a 02", 0.2)                          # 2 minutes
    call(jsr("tod_tick"))
    if rd("c_game", 3) != [1, 4, 0] or a.mem(0xdd0a, 1)[0] != 0:
        err.append("TOD 2 minutes: c_game %s TOD minutes $%02x" % (rd("c_game", 3), a.mem(0xdd0a, 1)[0]))
    a.cmd("> dd0b 01", 0.2)                          # 1 hour 59 minutes: + 119 -> 121 minutes (bits 9..23)
    a.cmd("> dd0a 59", 0.2)
    a.cmd("> dd08 00", 0.2)
    call(jsr("tod_tick"))
    m = (rd("c_game", 3)[1] | rd("c_game", 3)[2] << 8) >> 1
    if m != 121 or rd("c_game") != [1]:
        err.append("TOD 1:59: minutes %d (expected 121), game %s" % (m, rd("c_game")))
print("weapon, repair, HUD warnings, TOD clock:", "ok" if not err else "FAIL " + "; ".join(err))
sys.exit(1 if err else 0)
