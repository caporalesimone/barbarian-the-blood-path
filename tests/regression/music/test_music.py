#!/usr/bin/env python3
"""Music in the game (VICE, development disk; on tests/lib/c64.py, 11/11 G2): at every change of place the right song
ends up in the buffer (12/11, TODO M2: the theme of the village of the chapter, the theme of the chapter on its 5 levels -
read from the disk only when it changes -, the boss song on level MAXLEVEL), the fight tune is
one of the valid ones, the buffers hold exactly the SNDn files, the player plays (sp_on) without blocking the game,
the fight theme starts and the song of the place comes back; quitting from the game menu reaches the barbarian menu.
Prints the time of the level changes."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tests")); from lib import c64 as C64  # noqa: E402,E702  (monitor veloce, 10/11)
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "memory-map", "simulators")]
import songs  # noqa: E402
lbl = {m.group(1): int(m.group(2), 16) for m in re.finditer(r"^(\w+)\s*=\s*\$([0-9a-f]+)", open(os.path.join(ROOT, "out", "work", "game.lbl")).read(), re.M)}
num = {m.group(1): int(m.group(2)) for m in re.finditer(r"^(\w+)\s*=\s*(\d+)\s*$", open(os.path.join(ROOT, "out", "work", "game.lbl")).read(), re.M)}
mlst = open(os.path.join(ROOT, "out", "work", "lobby.lst")).read()
ui_menu = re.search(r"^\.(\w+)\s+ui_menu:", mlst, re.M).group(1)
rts = re.search(r"^\.(\w+)\s+60\s", mlst, re.M).group(1)
P = songs.PLAYLIST
GAME = songs.game_files(P)                                # (12/11) one file per song, no repetitions
LVL = [GAME.index(n) for n in P["level"]]                  # theme of chapter 1..4
TOWN = [GAME.index(n) for n in P["town"]]
BOSS = GAME.index(P["boss"][0])
FIG = [GAME.index(n) for n in P["fight"]]
FILES = [open(os.path.join(ROOT, "out", "work", "snd", n + ".bin"), "rb").read() for n in GAME]
err = []
vv = C64.Vice(os.path.join(ROOT, "out", "work", "disk.d64"))      # (11/11, G2: tests/lib/c64.py, a copy of the disk)
try:
    def cmd(c, w=None): return vv.cmd(c)
    def go(lim):
        try:
            vv.go(lim); return True
        except C64.MonitorError:
            return False
    def mem(a, n): return vv.mem(a, n)
    def level(lv, mode=0):
        cl, ml = lbl["change_level"], lbl["main_loop"]
        cmd("> 0340 a9 %02x a2 %02x 20 %02x %02x 4c %02x %02x" % (lv, mode, cl & 255, cl >> 8, ml & 255, ml >> 8), 0.3)
        cmd("break %04x" % ml, 0.2); cmd("r pc=0340", 0.2); cmd("sw reset", 0.2)
        ok = go(150)
        cyc = int(re.findall(r"Stopwatch:\s*(\d+)", cmd("sw", 0.4))[-1])
        cmd("del", 0.2)
        if not ok:
            sys.exit("level %d not reached" % lv)
        return cyc
    def frames(n):
        """n passages through main_loop (the game runs, the music goes on)"""
        r = cmd("break %04x" % lbl["main_loop"], 0.2)
        bp = re.findall(r"BREAK:\s*(\d+)", r)
        if bp:
            cmd("ignore %s %d" % (bp[0], n - 1), 0.2)
        ok = go(60); cmd("del", 0.2)
        return ok
    def state():
        cur = mem(lbl["snd_cur"], 2)
        return dict(lvl=cur[0] - 1, fig=cur[1] - 1, trk=mem(lbl["mus_trk"], 1)[0], want=mem(lbl["mus_want"], 1)[0],
                    on=mem(lbl["sp_on"], 1)[0], sv=mem(lbl["mus_sv"], 1)[0])
    def check_buf(i, at):
        got = bytes(mem(at, len(FILES[i])))
        if got != FILES[i]:
            err.append("buffer %04x differs from file SND%d (%s)" % (at, i, GAME[i]))
    vv.load(os.path.join(ROOT, "out", "work", "start.prg"))
    cmd("break " + ui_menu, 0.2); cmd("r pc=080d", 0.3)
    if not go(200): sys.exit("menu not reached")
    cmd("del", 0.2); cmd("r pc=" + rts, 0.2); cmd("r a=01", 0.2)     # new game (slot 0)
    cmd("break %04x" % lbl["main_loop"], 0.2); go(60); cmd("del", 0.2)
    # new game: starting weapon with a rolled durability (not DUR_MIN because rnd was 0), full
    eqd, eqm, rn = mem(lbl["c_eqd"], 1)[0], mem(lbl["c_eqm"], 1)[0], mem(lbl["rnd"], 2)
    print("starting weapon: durability %d/%d, rnd %s" % (eqd, eqm, rn))
    if eqm < 10 or eqd != eqm or rn == [0, 0]:
        err.append("starting weapon: durability %d/%d, rnd %s" % (eqd, eqm, rn))
    seen, prev, times = [], None, []
    for lv in (1, 2, 3, 4, 5, 6):
        c = level(lv)
        frames(60)
        st = state()
        times.append((lv, c, GAME[st["lvl"]] if 0 <= st["lvl"] < len(GAME) else "?"))
        want = LVL[(lv - 1) // 5]
        if st["lvl"] != want: err.append("level %d: song %d, the theme of its chapter is %d" % (lv, st["lvl"], want))
        if st["fig"] not in FIG: err.append("level %d: fight tune %d not valid" % (lv, st["fig"]))
        if st["trk"] != 1 or not st["on"]: err.append("level %d: music stopped %s" % (lv, st))
        check_buf(st["lvl"], lbl["SND_LBUF"]); check_buf(st["fig"], lbl["SND_FBUF"])
        prev = st["lvl"]; seen.append(st["lvl"])
    # fight: the tune starts, then the song of the place comes back
    cmd("> %04x 14" % lbl["mus_cmb"], 0.2)                # 20 units of 4 frames
    frames(40)
    st = state()
    if st["trk"] != 2 or not st["on"]: err.append("fight: tune not started %s" % st)
    frames(160)
    st = state()
    if st["trk"] != 1 or not st["sv"]: err.append("after the fight: the song of the place did not come back %s" % st)
    # final boss and village
    level(lbl["MAXLEVEL"] if "MAXLEVEL" in lbl else num["MAXLEVEL"]); frames(30)
    st = state()
    if st["lvl"] != BOSS: err.append("final level: song %d is not the boss song" % st["lvl"])
    times.append(("boss", None, GAME[st["lvl"]]))
    level(0, 2); frames(30)
    st = state()
    if st["lvl"] != TOWN[0]: err.append("village: song %d" % st["lvl"])
    check_buf(st["lvl"], lbl["SND_LBUF"])
    # quit to the main menu (ui_gamemenu, entry 2: resume, save, quit): the choice must reach the question (_qask) and the
    # confirmation (_quit: game_start without saving, 11/11 evening) the barbarian menu. 06/11: "bne +" jumped to the help and back to the game menu
    gl = open(os.path.join(ROOT, "out", "work", "game.lst")).read()
    a_sel = int(re.search(r"^\.(\w+)\s+(?:ad \w\w \w\w|a5 \w\w)\s+lda \$\w+\s+lda ui_cur\n\.\w+\s+f0 \w\w\s+beq \$\w+\s+beq _back", gl, re.M).group(1), 16)
    a_ask = int(re.search(r"^\.(\w+)\s+_qask", gl, re.M).group(1), 16)
    a_quit = int(re.search(r"^\.(\w+)\s+[0-9a-f ]+\s+\w+(?: \S+)?\s+_quit\s", gl, re.M).group(1), 16)
    cmd("> %04x 02" % lbl["ui_cur"], 0.2)
    cmd("break %04x" % a_ask, 0.2); cmd("r pc=%04x" % a_sel, 0.2)
    if not go(20): err.append("quit: entry 3 of the game menu does not reach the question (_qask)")
    cmd("del", 0.2)
    cmd("break " + ui_menu, 0.2); cmd("r pc=%04x" % a_quit, 0.2)
    if not go(120): err.append("quit: after the confirmation the main menu does not come")
    cmd("del", 0.2)
    for t in times:
        print("level %s: %s, song %s" % (t[0], ("%.2f s to change level" % (t[1] / 985248.0)) if t[1] else "-", t[2]))
finally:
    vv.close()
if err:
    print("\n".join(err)); sys.exit(1)
print("music ok")
