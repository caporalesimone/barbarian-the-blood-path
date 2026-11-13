#!/usr/bin/env python3
"""The save files in VICE (development disk, emulated 1541, Krill's Loader since 11/11: file hl + save-01..05):
  1. new disk: menu without errors, no heroes;
  2. hl missing (deleted with c1541): menu without errors, the game starts anyway;
  3. hero list (file hl) zeroed or full of random bytes: no error, no heroes;
  4. hero list of another version with one hero: the menu offers to delete it (sv_old = 1);
  5. cycles start -> new game -> level -> quit -> menu -> continue (N times): the hero stays in the list, the menu
     always comes (no stuck "reading barbarians");
  6. start menu: heroes + create + quit (no help, 07/11); quit = BASIC (READY.), no re-entry;
  7. barbarian details (07/11): right does nothing, down selects "delete barbarian", fire asks y/n, RUN/STOP cancels
     (= N), fire again and Y deletes: the list stays without the hero, also after reading the disk in a new session;
  8. new barbarian: name, seed, joystick choice, fire reopens a field, F1, DEL.
     The keys are simulated by writing joynew / keynew at the exit of ui_input.
Usage: python3 tests/regression/saves/test_saves.py [1 2 3 4 5 6 7 8]"""
import os, random, re, shutil, socket, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(ROOT)
lbl = {m.group(1): int(m.group(2), 16) for m in re.finditer(r"^(\w+)\s*=\s*\$([0-9a-f]+)", open("out/game.lbl").read(), re.M)}
num = {m.group(1): int(m.group(2)) for m in re.finditer(r"^(\w+)\s*=\s*(\d+)\s*$", open("out/game.lbl").read(), re.M)}
SAVE_VER = lbl["SAVE_VER"]
mlst = open("out/lobby.lst").read()
mlbl = {m.group(1): int(m.group(2), 16) for m in re.finditer(r"^(\w+)\s*=\s*\$([0-9a-f]+)", open("out/lobby.lbl").read(), re.M)}
after_scan = "%04x" % (int(re.search(r"^\.(\w+)\s+20 \w\w \w\w\s+jsr \$\w+\s+jsr scan_slots", mlst, re.M).group(1), 16) + 3)
rts = re.search(r"^\.(\w+)\s+60\s", mlst, re.M).group(1)
gl = open("out/game.lst").read()
a_quit = int(re.search(r"^\.(\w+)\s+[0-9a-f ]+\s+\w+(?: \S+)?\s+_quit\s", gl, re.M).group(1), 16)
DISK = os.path.join(ROOT, "out", "test_saves.d64")
err = []


def toff(t, s):
    o = 0
    for tt in range(1, t):
        o += 21 if tt <= 17 else 19 if tt <= 24 else 18 if tt <= 30 else 17
    return (o + s) * 256


def hl_data(d):
    """offset in the d64 of the data of the file HL (hero list, 11/11 Krill): first block + link (2) + load address (2)"""
    t, s = 18, 1
    ft = fs = None
    while t:
        b = d[toff(t, s):toff(t, s) + 256]
        for i in range(8):
            e = b[i * 32:i * 32 + 32]
            if e[2] & 7 and e[5:21].rstrip(b"\xa0") == b"HL":
                ft, fs = e[3], e[4]
        t, s = b[0], b[1]
    assert ft, "file HL not on the disk"
    return toff(ft, fs) + 4


def patch_hdr(data):
    d = bytearray(open(DISK, "rb").read())
    o = hl_data(d)
    data = data[:250]                       # (one block: 252 data bytes after the load address)
    d[o:o + len(data)] = data
    open(DISK, "wb").write(d)


sys.path.insert(0, os.path.join(ROOT, "tests"))
from lib import c64 as C64  # noqa: E402


class Vice(C64.Vice):
    """10/11: fast monitor of the shared library (waits for the prompt, no fixed delays); same interface as before"""
    def __init__(self):
        super().__init__(DISK, inplace=True)

    def cmd(self, c, w=None):
        if c.startswith("l "):
            self.load(c[2:].strip().rsplit(" ", 1)[0].strip('"')); return ""
        if c == "":
            return self.quiet(0.05)
        return super().cmd(c)

    def go(self, lim):
        try:
            super().go(lim); return True
        except C64.MonitorError:
            return False

    def menu(self, lim=200):
        """from the RUN of START (debug) to the menu, after the hero list is read"""
        self.cmd("", 0.3); self.cmd('l "%s" 0' % os.path.join(ROOT, "out", "start.prg"), 2)
        self.cmd("break " + after_scan); self.cmd("r pc=080d")
        ok = self.go(lim); self.cmd("del")
        return ok

    def state(self):
        return dict(sv_old=self.mem(lbl["sv_old"], 1)[0], nvalid=self.mem(lbl["nvalid"], 1)[0],
                    valid=self.mem(lbl["slot_valid"], 5), hdr=self.mem(lbl["hdrbuf"], 6))

    def play(self, a):
        """menu choice: A = 1 new game (slot 0), 0 continue slot 0 -> up to main_loop"""
        self.cmd("> %04x 00" % lbl["cur_slot"]); self.cmd("r pc=" + rts); self.cmd("r a=%02x" % a)
        self.cmd("break %04x" % lbl["main_loop"]); ok = self.go(90); self.cmd("del")
        return ok

    def level(self, lv, mode=0):
        cl, ml = lbl["change_level"], lbl["main_loop"]
        self.cmd("> 0340 a9 %02x a2 %02x 20 %02x %02x 4c %02x %02x" % (lv, mode, cl & 255, cl >> 8, ml & 255, ml >> 8))
        self.cmd("break %04x" % ml); self.cmd("r pc=0340"); ok = self.go(150); self.cmd("del")
        return ok

    def quit(self):
        self.cmd("break " + after_scan); self.cmd("r pc=%04x" % a_quit)
        ok = self.go(150); self.cmd("del")
        return ok

    def close(self):
        super().close(); subprocess.run(["pkill", "-f", "test_saves.d64"], stderr=subprocess.DEVNULL)


def fresh():
    shutil.copy(os.path.join(ROOT, "out", "disk.d64"), DISK)


def case(name, prep, check):
    fresh(); prep()
    v = Vice()
    try:
        if not v.menu():
            err.append("%s: menu not reached (stuck?)" % name); return
        st = v.state()
        print("%-36s %s" % (name, st))
        check(v, st)
    finally:
        v.close()


def c1():
    def chk(v, st):
        if st["sv_old"] or st["nvalid"]: err.append("new disk: error or heroes present %s" % st)
    case("1 new disk", lambda: None, chk)


def c2():
    def prep():
        subprocess.run(["c1541", "-attach", DISK, "-delete", "hl"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    def chk(v, st):
        if st["sv_old"] or st["nvalid"]: err.append("hl missing: error or heroes %s" % st)
        if not v.play(1): err.append("hl missing: the game does not start")
    case("2 hl missing", prep, chk)


def c3():
    def chk(v, st):
        if st["sv_old"] or st["nvalid"]: err.append("hero list damaged: error or heroes %s" % st)
    case("3a list zeroed", lambda: patch_hdr(bytes(80)), chk)
    rnd = random.Random(7)
    case("3b elenco a caso", lambda: patch_hdr(bytes(rnd.randrange(2, 256) for _ in range(80))), chk)
    case("3c list $0D (record never written)", lambda: patch_hdr(b"\x0d" * 80), chk)


def c4():
    def chk(v, st):
        if st["sv_old"] != 1: err.append("another version with a hero: no warning %s" % st)
    case("4 another version, one hero", lambda: patch_hdr(bytes([(SAVE_VER - 1) & 255, 1, 0, 0, 0, 0]) + b"OLDHERO\0\0\0\0\0" + bytes(48) + b"\xff"), chk)


def c6():
    """start menu (07/11): entries = heroes + "create new barbarian" + "quit the game" (ui_n = nvalid + 2), no help.
    "quit the game" (bb_quit) resets the C64 (READY.); no re-entry (SYS 49158 removed 11/11)"""
    fresh()
    v = Vice()
    try:
        if not v.menu(): err.append("menu: not reached"); return
        v.cmd("break %04x" % lbl["ui_input"])
        if not v.go(30): err.append("menu: does not reach the key wait"); return
        v.cmd("del")
        n, un = v.mem(lbl["nvalid"], 1)[0], v.mem(lbl["ui_n"], 1)[0]
        print("6 menu: nvalid %d, ui_n %d" % (n, un))
        if un != n + 2: err.append("menu: ui_n %d (attese %d: eroi + create + quit)" % (un, n + 2))
        v.cmd('screenshot "%s" 2' % os.path.join(ROOT, "out", "test_menu.png"), 1.5)
        v.cmd("break a483"); v.cmd("r pc=%04x" % mlbl["bb_quit"])         # BASIC: READY. loop
        if not v.go(20): err.append("quit the game: no READY."); return
        v.cmd("del")
        # (11/11) quit uninstalls Krill: the drive answers the KERNAL again. LOAD "HL",8 (SA 0) to $4000 from a stub
        stub = [0xa9, 2, 0xa2, 0x20, 0xa0, 0xc1, 0x20, 0xbd, 0xff,          # SETNAM 2, $C120
                0xa9, 1, 0xa2, 8, 0xa0, 0, 0x20, 0xba, 0xff,                # SETLFS 1, 8, 0
                0xa9, 0, 0xa2, 0x00, 0xa0, 0x40, 0x20, 0xd5, 0xff,          # LOAD -> $4000
                0x4c, 0x1b, 0xc1]                                           # $C11B: jmp * (stop here)
        v.cmd("> c100 " + " ".join("%02x" % b for b in stub))
        v.cmd("> c120 48 4c")                                                # "HL"
        v.cmd("> 4000 00")
        v.cmd("break c11b"); v.cmd("r pc=c100")
        if not v.go(60): err.append("quit the game: KERNAL LOAD after the quit does not end (drive still with Krill?)"); return
        v.cmd("del")
        hv = v.mem(0x4000, 1)[0]
        print("6 quit the game: BASIC reached (READY.), KERNAL LOAD of hl -> version $%02x" % hv)
        if hv != SAVE_VER: err.append("quit the game: KERNAL LOAD of hl gave $%02x (expected SAVE_VER $%02x)" % (hv, SAVE_VER))
    finally:
        v.close()


def c7():
    """deleting a barbarian from the details screen (menu): simulated keys, down on delete, N with RUN/STOP, then fire
    (= yes, 07/11); persistence on disk"""
    ml = open("out/lobby.lst").read()
    # return from "jsr ui_input" in ui_nav (the menu engine, first instruction) and the _hero point
    det = lbl["ui_nav"] + 3
    hero = int(re.search(r"^\.(\w+)\s+aa\s+tax\s+_hero\s+tax", ml, re.M).group(1), 16)
    dtsel = int(re.search(r"^dt_sel\s*=\s*\$([0-9a-f]+)", open("out/lobby.lbl").read(), re.M).group(1), 16)
    yn = lbl["yn_wait"] + 3                             # (09/11: ui_yesno saves row 24 first)
    kn, jn = lbl["keynew"], 0x32

    fresh()                                             # (08/11: the inn chest is in the hero record:
    v = Vice()                                          # a new barbarian starts with the block zeroed, test_rel)
    try:
        if not v.menu(): err.append("delete: menu not reached"); return
        if not v.play(1): err.append("delete: game not started"); return
        if not v.level(1): err.append("delete: change of level"); return
        if not v.quit(): err.append("delete: menu not reached after quit"); return
        st = v.state()
        if st["nvalid"] != 1: err.append("delete: expected 1 hero, %s" % st); return

        def stop(addr, what):
            v.cmd("del"); v.cmd("break %04x" % det); v.cmd("break %04x" % yn)
            ok = v.go(30)
            if not ok: err.append("delete: %s: no stop" % what)
            return ok

        def press(joy=0, row=-1, mask=0):
            v.cmd("> %04x %02x" % (jn, joy))
            for r in range(8): v.cmd("> %04x 00" % (kn + r))
            if row >= 0: v.cmd("> %04x %02x" % (kn + row, mask))

        v.cmd("del"); v.cmd("break %04x" % det); v.cmd("break %04x" % yn)
        v.cmd("r a=00"); v.cmd("r pc=%04x" % hero)
        if not v.go(30): err.append("delete: details not reached"); return
        if v.mem(dtsel, 1)[0] != 0: err.append("delete: the details screen does not start on start")
        press(0x08)                                         # right: no effect (07/11)
        if not v.go(10) or v.mem(dtsel, 1)[0] != 0: err.append("delete: right changes the choice"); return
        press(0x02)                                         # down
        if not v.go(10) or v.mem(dtsel, 1)[0] != 1: err.append("delete: down does not select delete"); return
        press(0x10)                                         # fire on delete: y/n question
        if not v.go(10) or "%04x" % yn not in v.cmd("r", 0.3).lower():
            err.append("delete: fire on delete does not ask y/n"); return
        press(0, 7, 0x80)                                   # RUN/STOP = N
        if not v.go(10) or "%04x" % det not in v.cmd("r", 0.3).lower():
            err.append("delete: RUN/STOP does not cancel the y/n question"); return
        st = v.state()
        print("7 after RUN/STOP (cancel)           %s" % st)
        if st["nvalid"] != 1 or st["valid"][0] != 1: err.append("delete: RUN/STOP deleted %s" % st)
        press(0x10)                                         # fire on delete (the choice stayed)
        if not v.go(10): err.append("delete: second question missing"); return
        v.cmd("del"); v.cmd("break %04x" % lbl["ui_input"])
        press(0x10)                                         # fire = yes
        if not v.go(30): err.append("delete: after fire the menu does not come back"); return
        st = v.state()
        names = v.mem(lbl["slot_name"], 16)
        print("7 after fire (deleted)              %s" % st)
        if st["nvalid"] != 0 or st["valid"] != [0] * 5 or st["hdr"][1] != 0:
            err.append("delete: hero still in the list %s" % st)
        if any(c != 0x20 for c in names[:12]): err.append("delete: name not cleared %s" % names)
    finally:
        v.close()
    # new session: the list read again from disk has no hero
    v = Vice()
    try:
        if not v.menu(): err.append("delete: menu not reached (second session)"); return
        st = v.state()
        print("7 new session                       %s" % st)
        if st["nvalid"] != 0 or st["hdr"][1] != 0: err.append("delete: the hero came back from disk %s" % st)
    finally:
        v.close()


def c8():
    """new barbarian (09/11): the name is typed, ENTER (not empty, not already used), the seed, ENTER (6 characters); on
    start the choice among name, seed and start only with joystick or W/S, fire reopens the field; keys simulated by
    writing keynew and joynew after ui_input"""
    ml = open("out/lobby.lst").read()
    brk = int(re.search(r"^\.(\w+)\s+20 \w\w \w\w\s+jsr \$\w+\s+_in\s+jsr ui_input", ml, re.M).group(1), 16) + 3
    mlb = {m.group(1): int(m.group(2), 16) for m in (re.match(r"(\w+)\s*=\s*\$([0-9a-f]+)", x) for x in open("out/lobby.lbl")) if m}
    kn, jn = lbl["keynew"], 0x32
    fresh()
    v = Vice()
    try:
        if not v.menu(): err.append("new barbarian: menu not reached"); return
        # slot 0 taken by "a" (to try "name already in use."), the new one goes to slot 1
        sv, sn = mlb.get("slot_valid", lbl.get("slot_valid")), mlb.get("slot_name", lbl.get("slot_name"))
        v.cmd("> %04x 01" % sv); v.cmd("> %04x 01" % lbl["cur_slot"])
        v.cmd("> %04x 01 20 20 20 20 20 20 20 20 20 20 20" % sn)
        v.cmd("del"); v.cmd("break %04x" % brk); v.cmd("r pc=%04x" % mlb["name_entry"])
        if not v.go(30): err.append("new barbarian: key wait not reached"); return
        # (row, keyboard mask, joynew): the name, ENTER, the seed, ENTER; then the choice among
        # name/seed/start only with joystick or W/S (here joynew), fire reopens a field and the logic restarts from there
        K = lambda r, m: (r, m, 0)
        J = lambda m: (0, 0, m)
        steps = [(K(0, 0x02), "nf", 0, "ENTER with an empty name"), (K(1, 0x04), "nl", 1, "letter A"),
                 (K(0, 0x02), "nf", 0, "ENTER: name already used"), (K(1, 0x04), "nl", 2, "letter A"),
                 (K(0, 0x02), "nf", 1, "ENTER: name -> seed"), (K(7, 0x01), "sl", 1, "digit 1: the seed restarts"),
                 (K(0, 0x02), "nf", 1, "ENTER with a short seed"), (J(0x02), "nf", 1, "down while typing: nothing"),
                 (K(0, 0x80), "nf", 1, "CRSR: nothing"), (K(0, 0x10), "sl", 6, "F1: random seed"),
                 (K(0, 0x02), "nf", 2, "ENTER: seed -> start"), (J(0x00), "ne", 0, "no typing on start"),
                 (J(0x02), "nf", 2, "down on start: no wrap"), (J(0x01), "nf", 1, "up: seed"),
                 (J(0x01), "nf", 0, "up: name"), (J(0x01), "nf", 0, "up from the name: no wrap"),
                 (J(0x10), "ne", 1, "fire on the name: typing again"), (K(0, 0x01), "nl", 1, "DEL: \"a\" already used"),
                 (K(0, 0x02), "nf", 0, "ENTER: name already used"), (K(1, 0x04), "nl", 2, "letter A"),
                 (K(0, 0x02), "nf", 1, "ENTER: name -> seed (the logic restarts)"), (K(0, 0x02), "nf", 2, "ENTER: seed kept"),
                 (J(0x01), "nf", 1, "up: seed"), (J(0x10), "ne", 1, "fire on the seed"), (K(7, 0x01), "sl", 1, "digit 1"),
                 (K(0, 0x02), "nf", 1, "ENTER with a short seed"), (K(0, 0x10), "sl", 6, "F1"),
                 (K(0, 0x02), "ne", 0, "ENTER: on start again")]
        for (row, mask, joy), key, want, what in steps:
            for r in range(8): v.cmd("> %04x 00" % (kn + r))
            v.cmd("> %04x %02x" % (kn + row, mask))
            v.cmd("> %04x %02x" % (jn, joy))
            if not v.go(10): err.append("new barbarian: %s: no stop" % what); return
            got = {"nf": v.mem(mlb["nfield"], 1)[0], "nl": v.mem(mlb["nlen2"], 1)[0], "sl": v.mem(mlb["slen"], 1)[0],
                   "ne": v.mem(mlb["nedit"], 1)[0]}
            if got[key] != want: err.append("new barbarian: %s: %s = %d (expected %d)" % (what, key, got[key], want)); return
        print("8 new barbarian: name, seed, joystick choice, fire reopens the field, F1, DEL ok")
    finally:
        v.close()


def c5(n=4):
    fresh()
    v = Vice()
    try:
        if not v.menu(): err.append("cycles: first menu not reached"); return
        for it in range(n):
            if not v.play(1 if it == 0 else 0): err.append("cycle %d: game not started" % it); return
            if not v.level(1 + it % 3): err.append("cycle %d: change of level" % it); return
            if not v.quit(): err.append("cycle %d: menu not reached after quit" % it); return
            st = v.state()
            print("5 cycle %d after quit               %s" % (it, st))
            if st["nvalid"] != 1 or st["sv_old"]: err.append("cycle %d: hero list %s" % (it, st))
    finally:
        v.close()


if __name__ == "__main__":
    cases = sys.argv[1:] or ["1", "2", "3", "4", "5", "6", "7", "8"]
    for c in cases:
        {"1": c1, "2": c2, "3": c3, "4": c4, "5": c5, "6": c6, "7": c7, "8": c8}[c]()
    if err:
        print("\n".join(err)); sys.exit(1)
    print("saves ok")
