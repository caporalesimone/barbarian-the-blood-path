#!/usr/bin/env python3
"""Profilo del ciclo principale per fotogramma (11/11, docs/prestazioni.md): una fermata dopo ogni `jsr` di main_loop
(indirizzi presi da out/game.lst), cicli di ogni routine a ogni giro (IRQ compresi), su un piano scelto, camminando come
i test PERF (8 direzioni, teletrasporto vicino ai mostri), con o senza corsa di Frenzy (fz_run).
Uscita: per ogni routine media / 95° percentile / massimo in cicli, giri lunghi (> 1 fotogramma), fotogrammi video per
giro (50 / questo = fotogrammi al secondo effettivi).
Uso: python3 tools/vice/frame_prof.py --level 10 [--fz 0..250] [--frames 300] [--monsters] [--json out.json]"""
import argparse, json, os, re, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from lib.c64 import Game, FRAME, listing  # noqa: E402
from lib.play import new_game, alive, mpos, floor_next, find, fire_to  # noqa: E402

U, D, LF, RT = 1, 2, 4, 8
DIRS = (RT, D, LF, U, RT | D, LF | U, RT | U, LF | D)


def loop_points():
    """(indirizzo, nome della routine che parte li') per main_loop"""
    lst = listing("game")
    i = lst.index("main_loop:")
    pts = []
    for ln in lst[i:].splitlines()[1:]:
        m = re.match(r"^\.([0-9a-f]{4})\s+(?:[0-9a-f]{2}\s){1,3}\s*(jsr|jmp)\s+\$[0-9a-f]+\s+(?:jsr|jmp)\s+(\w+)", ln)
        if m:
            pts.append((int(m.group(1), 16), m.group(3)))
            if m.group(2) == "jmp":
                break
    return pts


def go_to_level(g, lv):
    L = g.L
    if lv == 0:
        return
    g.poke(L["cur_level"], 0)
    fire_to(g, *find(g, L["T_TSTAIRS"])[0]); g.wait_main()
    if lv > 1:
        g.poke(L["cur_level"], lv - 1)
        fire_to(g, *find(g, L["T_STAIRSD"])[0]); g.wait_main()


def run(level=10, fz=0, frames=300, monsters=True):
    g = Game()
    try:
        g.to_menu(); new_game(g); g.frames(3)
        L = g.L
        g.poke(L["godmode"], 1)
        go_to_level(g, level)
        g.frames(5)
        pts = loop_points()
        names = {a: n for a, n in pts}
        order = [a for a, _ in pts]
        ri_stop = next(a for a, n in pts if n == "handle_keys")      # input already read: joystick written here
        g.delbrk()
        for a in order:
            g.brk(a)
        seg = {n: [] for _, n in pts}
        loops, work = [], []
        last = {}
        k, still, lastpos = 0, 0, None
        t_wait = None
        for f in range(frames):
            if monsters and f % 60 == 0:
                m = alive(g)
                if m:
                    p = floor_next(g, *mpos(g, m[(f // 60) % len(m)]))
                    if p: g.teleport(p[0], p[1])
            prev_a, prev_c = None, None
            for _ in range(len(order)):
                c = g.go(30)
                a = g.regs()["pc"]
                if prev_a is not None:
                    seg[names[prev_a]].append(c - prev_c)
                if a == ri_stop:
                    if fz:
                        g.poke(L["tmr"] + L["T_FZ"], 250, 0); g.poke(L["fz_run"], fz)
                    j = DIRS[k % len(DIRS)]
                    g.poke(L["joy"], j); g.poke(L["joynew"], 0)
                if a == order[1]:                                   # after wait_vblank: start of the work
                    if t_wait is not None:
                        loops.append(c - t_wait)
                    t_wait = c
                prev_a, prev_c = a, c
            pos = (g.w16(L["px"]), g.w16(L["py"]))
            still = still + 1 if pos == lastpos else 0
            lastpos = pos
            if still >= 2: k += 1; still = 0
        g.delbrk()
        return seg, loops
    finally:
        g.close()


def summary(seg, loops):
    out = {}
    for n, v in seg.items():
        if not v: continue
        v2 = sorted(v)
        out[n] = dict(avg=round(statistics.mean(v)), p95=v2[int(0.95 * (len(v2) - 1))], max=v2[-1])
    fl = [round(x / FRAME) for x in loops]
    out["_loops"] = dict(n=len(loops), long=sum(1 for x in loops if x > 1.5 * FRAME),
                         video_frames_per_loop=round(statistics.mean(fl), 3) if fl else 0,
                         fps=round(50 / statistics.mean(fl), 1) if fl else 0)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, default=10)
    ap.add_argument("--fz", type=int, default=0)
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--no-monsters", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    s = summary(*run(a.level, a.fz, a.frames, not a.no_monsters))
    lp = s.pop("_loops")
    print("level %d, fz_run %d: %d loops, %d long (> 1.5 frames), %.3f video frames per loop -> %.1f fps" % (
        a.level, a.fz, lp["n"], lp["long"], lp["video_frames_per_loop"], lp["fps"]))
    for n, v in sorted(s.items(), key=lambda x: -x[1]["avg"]):
        print("  %-16s avg %6d  p95 %6d  max %6d cycles" % (n, v["avg"], v["p95"], v["max"]))
    if a.json:
        s["_loops"] = lp
        json.dump(s, open(a.json, "w"), indent=1)
