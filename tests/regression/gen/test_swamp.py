#!/usr/bin/env python3
"""(18/11, TODO M11) Swamp of chapter 2 (src/game/gen_io.asm: islands = carve_blob, boardwalks = carve_plank, swamp_gates), in
VICE: for SEEDS seeds and the levels 6-9, every walkable tile is reachable from the entry gate (stairs up), the exit gate
(stairs down) among them; both gates are on the border (x or y = 1 or 46), on two different sides; the exit gate of level L
and the entry gate of level L+1 are on opposite sides at the same point (the levels side by side make one swamp, in a random
path: not always west to east); over all the seeds the exits use at least 3 of the 4 sides; generation under MAX_GEN s,
palette 12 on every level; (19/11) the two gates of a level at least MIN_GATE_D tiles apart.
Usage: python3 tests/regression/gen/test_swamp.py"""
import collections, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "perf_disk"))
from lib.c64 import Game  # noqa: E402
from lib.play import new_game  # noqa: E402
import cases as PD  # noqa: E402

SEEDS = 8
MAX_GEN = 1.2            # s; measured 18/11: 0.84-0.87 s
MIN_GATE_D = 34          # (19/11) gen_io.asm sw_adj: 40 wanted; on two sides next to each other the farthest point can give 34
WALK = {2, 3, 4, 5, 6, 14, 24}      # floors, gates (stairs), boardwalk (PATH), chest
W = 48


def main():
    rng = random.Random(1806)
    g = Game()
    err = []
    try:
        PD.sw_reset(g)
        g.to_menu(); new_game(g); g.frames(3); g.at_input = False
        L = g.L
        g.poke(L["c_chap"], 2); g.poke(L["c_unl"], 2)
        worst = 0
        sides = [0, 0, 0, 0]
        dmin = 999
        for s in range(SEEDS):
            g.poke(L["c_seedt"], *[rng.randrange(36) for _ in range(6)])
            g.poke(L["c_vis"], 0, 0, 0)
            prev = None
            for lv in (6, 7, 8, 9):
                g.call(L["change_level"], tmax=150, regs="a=%02x,x=00" % lv)
                PD.sw_reset(g); t0 = PD.sw(g)
                g.call(L["gen_dungeon"], tmax=60)
                t = (PD.sw(g) - t0) / PD.CPS
                worst = max(worst, t)
                m = g.mem(0xC000, W * W)
                up = (g.b(L["st_up_x"]), g.b(L["st_up_y"]))
                dn = (g.b(L["st_dn_x"]), g.b(L["st_dn_y"]))
                fl = {(i % W, i // W) for i, v in enumerate(m) if v in WALK}
                seen = {up}
                q = collections.deque([up])
                while q:
                    x, y = q.popleft()
                    for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if n in fl and n not in seen:
                            seen.add(n); q.append(n)
                tag = "seed %d level %d" % (s, lv)
                side = lambda p: 3 if p[0] == 1 else 1 if p[0] == W - 2 else 0 if p[1] == 1 else 2 if p[1] == W - 2 else None
                si, so = side(up), side(dn)
                if si is None or so is None or si == so:
                    err.append("%s: gates at %s and %s (on two different sides of the border wanted)" % (tag, up, dn))
                if so is not None:
                    sides[so] += 1
                d = abs(up[0] - dn[0]) + abs(up[1] - dn[1])
                dmin = min(dmin, d)
                if d < MIN_GATE_D:
                    err.append("%s: gates %s and %s only %d tiles apart (min %d)" % (tag, up, dn, d, MIN_GATE_D))
                if dn not in seen or seen != fl:
                    err.append("%s: %d walkable tiles not reachable from the entry gate (exit gate reachable: %s)" % (tag, len(fl - seen), dn in seen))
                if prev is not None:
                    want = {1: (1, prev[1]), 3: (W - 2, prev[1]), 0: (prev[0], W - 2), 2: (prev[0], 1)}.get(side(prev))
                    if up != want:
                        err.append("%s: entry gate at %s, the exit gate of the level before at %s wants %s" % (tag, up, prev, want))
                prev = dn
                if t > MAX_GEN:
                    err.append("%s: generation %.2f s (max %.1f s)" % (tag, t, MAX_GEN))
                look = g.b(L["lv_look"] + lv)
                if look != 0x2C:
                    err.append("%s: lv_look %02x (palette 12 and swamp wanted)" % (tag, look))
        print("swamp: %d seeds x levels 6-9, slowest generation %.2f s, exits N E S W %s, closest gates %d tiles" % (SEEDS, worst, sides, dmin))
        if sum(1 for n in sides if n) < 3:
            err.append("exits on %s sides only (N E S W: %s)" % (sum(1 for n in sides if n), sides))
    finally:
        g.close()
    if err:
        print("\n".join(err)); sys.exit(1)
    print("swamp ok")


if __name__ == "__main__":
    main()
