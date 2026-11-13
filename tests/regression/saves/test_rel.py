#!/usr/bin/env python3
"""REL saves in VICE (development disk; on tests/lib/c64.py, 11/11 G2): new game, level 1, changes (a monster
dead, a level chest opened, map explored), level 2 and back to level 1. The state of level 1 must come back the same
(the opened chest disappears, the fog comes back in 2x2 sectors) and the hero list must hold the new hero. Opens the
boss chest (gold and items generated at the opening). Repopulation of the level with another game number. Also checks
that the monsters of the level have stats and hp (floor_types, mon_hp_init), and the inn chest on disk."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tests")); from lib import c64 as C64  # noqa: E402,E702  (monitor veloce, 10/11)
lbl = {m.group(1): int(m.group(2), 16) for m in re.finditer(r"^(\w+)\s*=\s*\$([0-9a-f]+)", open(os.path.join(ROOT, "out", "game.lbl")).read(), re.M)}
mlst = open(os.path.join(ROOT, "out", "lobby.lst")).read()
ui_menu = re.search(r"^\.(\w+)\s+ui_menu:", mlst, re.M).group(1)
rts = re.search(r"^\.(\w+)\s+60\s", mlst, re.M).group(1)                 # any rts of the LOBBY module
_mt = open(os.path.join(ROOT, "out", "menu.lbl")).read()                 # (11/11) locanda nel modulo MENU
olbl = {m.group(1): int(m.group(2), 16) for m in re.finditer(r"^(\w+)\s*=\s*\$([0-9a-f]+)", _mt, re.M)}
olbl.update({m.group(1): int(m.group(2)) for m in re.finditer(r"^(\w+)\s*=\s*(\d+)\s*$", _mt, re.M)})
vv = C64.Vice(os.path.join(ROOT, "out", "disk.d64"))      # (11/11, G2: tests/lib/c64.py, a copy of the disk)
try:
    def cmd(c, w=None): return vv.cmd(c)
    def go(lim):
        try:
            vv.go(lim); return True
        except C64.MonitorError:
            return False
    def mem(a, n): return vv.mem(a, n)
    def level(lv, mode):
        cl = lbl["change_level"]
        ml = lbl["main_loop"]
        cmd("> 0340 a9 %02x a2 %02x 20 %02x %02x 4c %02x %02x" % (lv, mode, cl & 255, cl >> 8, ml & 255, ml >> 8), 0.3)
        cmd("break %04x" % lbl["main_loop"], 0.2); cmd("r pc=0340", 0.2)
        ok = go(150); cmd("del", 0.2); return ok
    vv.load(os.path.join(ROOT, "out", "start.prg"))
    cmd("break " + ui_menu, 0.2); cmd("r pc=080d", 0.3)     # debug START from its BASIC stub (the loader BARBARIAN is tested by test_start.py)
    if not go(200): sys.exit("menu not reached")
    cmd("del", 0.2); cmd("r pc=" + rts, 0.2); cmd("r a=01", 0.2)     # new game (slot 0)
    cmd("break %04x" % lbl["main_loop"], 0.2); go(60); cmd("del", 0.2)
    if not level(1, 0): sys.exit("level 1 not reached")
    # stats of the monsters of the level (floor_types) and starting hp of every monster (mon_hp_init)
    n = nmon = mem(lbl["lb_cnt"], 1)[0]
    hp = [a + 256 * b for a, b in zip(mem(lbl["mhm"], n), mem(lbl["mhmh"], n))]
    ft = mem(lbl["ft_hpl"], 4)
    print("level 1: %d monsters, hp %s, ft_hpl %s" % (n, hp, ft))
    if n < 2 or min(hp) < 1 or not any(ft[1:]): sys.exit("monsters of the level without stats")
    cmd("> %04x 00" % (lbl["malive"] + 1), 0.2)                       # monster 1 dead
    ct = mem(lbl["ch_t"], 15)
    first = next(i for i, t in enumerate(ct) if t)
    cmd("> %04x %02x" % (lbl["ch_t"] + first, ct[first] | 0x20), 0.2)  # chest opened
    cmd("f %04x %04x aa" % (lbl["EXPL"], lbl["EXPL"] + 20), 0.2)
    # boss chest left on the floor (drop_now with dc_b = 1): must come back the same after the save
    def w(a): return "%02x %02x" % (a & 255, a >> 8)
    code = ("ad %s 8d %s ad %s 8d %s a9 18 8d %s a9 01 8d %s a2 02 a9 01 20 %s 4c 80 03" %     # chestLevel 24
            (w(lbl["st_up_x"]), w(lbl["loot_x"]), w(lbl["st_up_y"]), w(lbl["loot_y"]), w(lbl["gi_ll"]), w(lbl["dc_b"]), w(lbl["drop_now"])))
    cmd("> 0360 " + code, 0.3); cmd("break 0380", 0.2); cmd("r pc=0360", 0.2); go(60); cmd("del", 0.2)
    bch = mem(lbl["lb_bch"], 1)[0]
    if not bch: sys.exit("boss chest not created")
    BC = lambda b: (mem(lbl["cx_x"] + b - 1, 1) + mem(lbl["cx_y"] + b - 1, 1) + mem(lbl["ch_t"] + b - 1, 1)
                    + mem(lbl["ch_i"] + 4 * (b - 1), 4) + mem(lbl["ch_b"] + 4 * (b - 1), 4))
    bc_a = BC(bch)
    A = {k: mem(lbl[k], n) for k, n in (("malive", 32), ("mtype", 32), ("ch_t", 15), ("cx_x", 15), ("EXPL", 288))}
    ox, oy = mem(lbl["cx_x"] + first, 1)[0], mem(lbl["cx_y"] + first, 1)[0]     # opened chest: where it is
    level(2, 0); level(1, 1)
    # 07/11 (seed ANOANO): the opened chest must not stay as a tile on the map (Fire did not open it any more)
    gc = open(os.path.join(ROOT, "out", "gfx_consts.inc")).read()
    tc = [int(re.search(r"^%s\s*=\s*(\d+)" % k, gc, re.M).group(1)) for k in ("T_CHEST", "T_CHEST")]    # 10/11: one tile for all chests
    cmd("bank ram", 0.1); tile = mem(lbl["MAP"] + oy * 48 + ox, 1)[0]; cmd("bank cpu", 0.1)
    print("tile of the opened chest (%d,%d) after the return: %d" % (ox, oy, tile))
    if tc[0] <= tile <= tc[1]: sys.exit("the opened chest stayed on the map")
    B = {k: mem(lbl[k], n) for k, n in (("malive", 32), ("mtype", 32), ("ch_t", 15), ("cx_x", 15), ("EXPL", 288))}
    bch2 = mem(lbl["lb_bch"], 1)[0]
    bc_b = BC(bch2) if bch2 else None
    print("boss chest:", bc_a, "->", bc_b)
    # chests (but the boss one, which can move): the opened one disappears, the others stay
    def chests(D, b):
        return sorted((x, t) for i, (x, t) in enumerate(zip(D["cx_x"], D["ch_t"])) if t and i != b - 1)
    ca = [c for c in chests(A, bch) if c != (A["cx_x"][first], A["ch_t"][first])]
    cb = chests(B, bch2)
    def fog(e):
        """fog saved in 2x2 sectors and read back: every sector with at least one explored tile -> 2x2 tiles"""
        out = list(e)
        for r in range(0, 48, 2):
            for c in range(6):
                v = e[r * 6 + c] | e[(r + 1) * 6 + c]
                w = 0
                for k in range(4):
                    if v & (3 << (2 * k)): w |= 3 << (2 * k)
                out[r * 6 + c] = out[(r + 1) * 6 + c] = w
        return out
    exp = {"EXPL": fog(A["EXPL"])}
    bad = [k for k in ("malive", "mtype", "EXPL") if B[k] != exp.get(k, A[k])]
    if ca != cb: bad.append("chests %s -> %s" % (ca, cb))
    if bad: print("A", {k: A[k] for k in bad}, "\nB", {k: B[k] for k in bad})
    cmd("> 0370 20 %02x %02x 4c 73 03" % (lbl["hdr_read"] & 255, lbl["hdr_read"] >> 8), 0.2)   # ($0300: Krill)
    cmd("break 0373", 0.2); cmd("r pc=0370", 0.2); go(60); cmd("del", 0.2)
    hdr = mem(lbl["hdrbuf"], 6)
    print("state of the level after the return:", "ok" if not bad else "DIFFERENT " + str(bad), "| hero list:", hdr)
    if bc_b != bc_a: bad.append("boss chest")
    # opening the boss chest (a monster treasure): gold and items generated now from the saved loot level
    if bch2:
        g0 = mem(lbl["c_gold"], 2); x, y = bc_b[0], bc_b[1]
        cmd("> %04x %02x" % (lbl["ptx"], x), 0.2); cmd("> %04x %02x" % (lbl["pty"], y), 0.2)
        cmd("> 0370 20 %02x %02x 4c 73 03" % (lbl["chest_open"] & 255, lbl["chest_open"] >> 8), 0.2)
        cmd("break %04x" % lbl["ui_chest"], 0.2); cmd("r pc=0370", 0.2); go(60); cmd("del", 0.2)
        c = BC(bch2); g1 = mem(lbl["c_gold"], 2)
        n = sum(1 for i in c[3:7] if i)
        print("boss chest opened:", c, "gold", g0, "->", g1)
        if not (c[2] & 0x80) or (c[2] & 0x08) or n != bc_a[3] or g1 == g0:
            bad.append("opening of the boss chest")
    # repopulation per game: with another game number (c_game) level 1 comes back with all the monsters alive and
    # its chests closed; with the same number it stays as saved (monster 1 dead)
    level(2, 0)                                                        # level 1 is saved with the current game
    g = mem(lbl["c_game"], 1)[0]
    cmd("> %04x %02x" % (lbl["c_game"], (g + 1) & 255), 0.2)            # ... then another game, and back in
    level(1, 1)
    C = {k: mem(lbl[k], n) for k, n in (("malive", 32), ("ch_t", 15))}
    nalive = sum(1 for i, m in enumerate(C["malive"]) if i < nmon and m)
    print("another game: monsters alive %d/%d (saved %d), chests %d" % (nalive, nmon, sum(A["malive"][:nmon]), sum(1 for t in C["ch_t"] if t & 0x10)))
    if nalive != nmon: bad.append("repopulation: not all the monsters alive")
    if sum(1 for t in C["ch_t"] if t & 0x10) <= sum(1 for t in B["ch_t"] if t & 0x10): bad.append("repopulation: chests of the level not restored")
    # inn chest (08/11): in the hero record. pack -> chest (st_move in the module MENU), save_char, chest cleared in RAM,
    # load_char: slot 0 comes back from disk. Time of save_char measured (cycle counter)
    level(0, 0)
    def w2(a): return "%02x %02x" % (a & 255, a >> 8)
    dec = {m.group(1): int(m.group(2)) for m in re.finditer(r"^(\w+)\s*=\s*(\d+)\s*$", open(os.path.join(ROOT, "out", "game.lbl")).read(), re.M)}
    SW = dec["I_SWORD"]
    cmd("> %04x %02x" % (lbl["c_pack"], SW), 0.2); cmd("> %04x 02" % lbl["c_packb"], 0.2)
    cmd("> %04x 4d" % lbl["c_packd"], 0.2); cmd("> %04x 96" % lbl["c_packm"], 0.2)
    code = ("20 %s 78 a9 35 85 01 a9 00 8d %s a2 00 20 %s a9 36 85 01 58 4c 80 03" %
            (w2(lbl["ovl_town"]), w2(lbl["st_col"]), w2(olbl["st_move"])))
    cmd("> 0360 " + code, 0.3); cmd("break 0380", 0.2); cmd("r pc=0360", 0.2); ok1 = go(90); cmd("del", 0.2)
    pk = mem(lbl["c_pack"], 1)[0]
    # save_char alone, with the cycle counter of the monitor (stopwatch)
    cmd("> 0360 20 %s 4c 80 03" % w2(lbl["save_char"]), 0.3); cmd("break 0363", 0.2)
    cmd("r pc=0360", 0.2); cmd("sw reset", 0.3); ok3 = go(60)
    cyc = [int(x) for x in re.findall(r"\b(\d{5,})\b", cmd("sw", 0.5))]
    cmd("del", 0.2)
    E = lbl["st_id"]; N = dec["STASH_N"]
    cmd("f %04x %04x 00" % (E, E + 4 * N - 1), 0.2)
    cmd("> 0360 20 %s 4c 80 03" % w2(lbl["load_char"]), 0.3); cmd("break 0380", 0.2); cmd("r pc=0360", 0.2); ok2 = go(60); cmd("del", 0.2)
    st = [mem(E + k * N, 1)[0] for k in range(4)]
    print("inn chest (in the hero record): pack %d, slot 0 read back from disk %s; save_char %s cycles (%.2f s at 985 kHz)" %
          (pk, st, cyc[-1] if cyc else "?", (cyc[-1] / 985248) if cyc else 0))
    if not (ok1 and ok2 and ok3) or pk == SW or st != [SW, 2, 0x4d, 0x96]: bad.append("inn chest on disk")
    if bad: print("FAIL", bad)
    sys.exit(0 if not bad and hdr[:2] == [lbl["SAVE_VER"], 1] and hdr[2:6] == [0, 0, 0, 0] else 1)
finally:
    vv.close()
