#!/usr/bin/env python3
"""Choice of the potion slot in the shop (alchemist, shop_buy): W/S (up/down) go through the free slots only, with
wrap, fire pays and puts the potion, RUN/STOP cancels without paying (09/11). Real code in VICE (development disk):
after entering the village the alchemist opens (MENU_SHOP of the module MENU, 11/11), then shop_buy with the belt [-,P,-,P] and keys
simulated by writing joynew / keynew at the exit of ui_input (like test_saves.py, case 7)."""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves"))
import test_saves as T

L, err = dict(T.lbl), T.err
_ml = open(os.path.join(T.ROOT, "out", "work", "menu.lbl")).read()                  # (11/11) i negozi sono nel modulo MENU
L.update({m.group(1): int(m.group(2), 16) for m in re.finditer(r"^(\w+)\s*=\s*\$([0-9a-f]+)", _ml, re.M)})
L.update({m.group(1): int(m.group(2)) for m in re.finditer(r"^(\w+)\s*=\s*(\d+)\s*$", _ml, re.M)})
gl = open(os.path.join(T.ROOT, "out", "work", "menu.lst")).read()
# instruction after "jsr ui_input" in the loop of shop_buy (_l): after it keynew+7 and joynew are read
sb, ss = L["shop_buy"], L["shop_sell"]
POT = L["I_POTR"]                                   # (21/11: was 13, the ids moved with the new weapons)
cand = [int(m.group(1), 16) for m in re.finditer(r"^\.(\w+)\s+ad \w\w \w\w\s+lda \$\w+\s+lda keynew\+7", gl, re.M)]
cand = [c for c in cand if sb < c < ss]
if len(cand) != 1:
    print("shop_buy: key reading point not found", cand); sys.exit(1)
RET = cand[0]
KN, JN = L["keynew"], L["joynew"]


def run():
    T.fresh()
    v = T.Vice()
    try:
        if not v.menu(): err.append("slot: menu not reached"); return
        if not v.play(1): err.append("slot: game not started"); return
        es = L["MENU_SHOP"]                                                             # (11/11) KERNAL out, then enter_shop
        v.cmd("> 0340 a9 01 20 %02x %02x 4c 45 03" % (es & 255, es >> 8))              # alchemist (shop_id 1; 09/11: no armorer)
        v.cmd("break %04x" % (L["sl_nav"] + 3)); v.cmd("r pc=0340")   # (21/11) shops on the scrolling lists
        if not v.go(40): err.append("slot: alchemist not opened"); return
        v.cmd("del")
        sbuy = L["shop_buy"]
        v.cmd("> 0350 20 %02x %02x 4c 53 03" % (sbuy & 255, sbuy >> 8))                 # shop_buy then stop
        v.cmd("> %04x %02x" % (L["l8_id"], POT)); v.cmd("> %04x %02x" % (L["ui_lc"], L["LC_W"]))   # ware 0 = potion, entry LC_W
        v.cmd("> %04x 88 13" % L["c_gold"])                                             # 5000 gold
        v.cmd("> %04x 00 %02x 00 %02x" % (L["c_beltt"], POT, POT))                      # belt: -, P, -, P
        price = None

        def press(joy=0, row=-1, mask=0):
            v.cmd("> %04x %02x" % (JN, joy))
            for r in range(8): v.cmd("> %04x 00" % (KN + r))
            if row >= 0: v.cmd("> %04x %02x" % (KN + row, mask))

        def slot(): return v.mem(L["sh_slot"], 1)[0]

        g0 = v.mem(L["c_gold"], 2)
        v.cmd("break %04x" % RET); v.cmd("r pc=0350")
        if not v.go(20): err.append("slot: shop_buy does not reach the choice"); return
        s = slot(); print("first slot:", s)
        if s != 0: err.append("first free slot: expected 0, %d" % s)
        seq = [("down", 0x02, 2), ("up", 0x01, 0), ("up (wrap)", 0x01, 2), ("down (wrap)", 0x02, 0), ("down", 0x02, 2)]
        for name, joy, want in seq:
            press(joy)
            if not v.go(10): err.append("slot: %s: no stop" % name); return
            s = slot(); print("%-12s -> slot %d" % (name, s))
            if s != want: err.append("%s: expected slot %d, found %d" % (name, want, s))
        v.cmd("break 0353")                                                              # end of shop_buy (jmp *)
        press(0, 7, 0x80)                                                                # RUN/STOP: cancel
        if not v.go(10): err.append("slot: RUN/STOP: no stop"); return
        s = slot(); belt = v.mem(L["c_beltt"], 4); g1 = v.mem(L["c_gold"], 2)
        print("after RUN/STOP: sh_slot %02x, belt %s, gold %s" % (s, belt, g1))
        if s != 0xff: err.append("RUN/STOP: sh_slot not cleared (%02x)" % s)
        if belt != [0, POT, 0, POT] or g1 != g0: err.append("RUN/STOP: it bought (belt %s, gold %s)" % (belt, g1))
        # second try: down (slot 2), fire: buys into the chosen slot
        v.cmd("> %04x 00 %02x 00 %02x" % (L["c_beltt"], POT, POT))
        press(0)
        v.cmd("r pc=0350")
        if not v.go(20): err.append("slot: second choice not reached"); return
        press(0x02)
        if not v.go(10): err.append("slot: down (2)"); return
        press(0x10)                                                                      # fire
        if not v.go(10): err.append("slot: fire: shop_buy does not end"); return
        belt = v.mem(L["c_beltt"], 4); g2 = v.mem(L["c_gold"], 2); s = slot()
        print("after fire: belt %s, gold %s -> %s, sh_slot %02x" % (belt, g1, g2, s))
        if belt != [0, POT, POT, POT]: err.append("fire: potion in the wrong slot %s (expected [0,P,P,P])" % belt)
        if (g2[1] * 256 + g2[0]) >= (g1[1] * 256 + g1[0]): err.append("fire: gold not taken")
        if s != 0xff: err.append("fire: sh_slot not cleared (%02x)" % s)
    finally:
        v.close()


run()
if err:
    print("\n".join(err)); sys.exit(1)
print("potion slot choice ok")
