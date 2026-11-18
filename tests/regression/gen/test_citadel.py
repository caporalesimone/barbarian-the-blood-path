#!/usr/bin/env python3
"""(19/11, TODO M11) Citadel of chapter 4 (src/game/gen_io.asm: cit_finish), in VICE: for SEEDS seeds and the generated levels
16-19 the map is connected (every walkable tile reachable from the stairs up, the stairs down among them), symmetric left/right
(walkable or not, mirror axis between x = 23 and 24; the stairs are the only exception), with columns (walls whose 8 neighbours
are all walkable: at least MIN_COLS) and big halls (at least MIN_FLOOR walkable tiles); generation under MAX_GEN s.
Also (19/11, bug found with the citadel): on every generated level 1-19 no monster is born inside a wall or in the water (before
19/11, in caves and swamp the rectangle of a room is not all floor: they could). The floor boss stands on the stairs down (place_boss).
Usage: python3 tests/regression/gen/test_citadel.py [--show]   (--show: prints the map of the first seed, level 16)"""
import collections, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "perf_disk"))
from lib.c64 import Game  # noqa: E402
from lib.play import new_game  # noqa: E402
import cases as PD  # noqa: E402   (stopwatch of VICE: sw_reset, sw, CPS)

SEEDS = 6
MIN_FLOOR = 700
MIN_COLS = 4
MAX_GEN = 1.0            # s; rooms ~0.3 s
FLOORS = (2, 3, 4)
W = 48


def main():
    rng = random.Random(1911)
    g = Game()
    err = []
    try:
        PD.sw_reset(g)
        g.to_menu(); new_game(g); g.frames(3); g.at_input = False
        L = g.L
        g.poke(L["c_chap"], 4); g.poke(L["c_unl"], 4)
        worst, cols_min, floor_min = 0, 999, 9999
        for s in range(SEEDS):
            g.poke(L["c_seedt"], *[rng.randrange(36) for _ in range(6)])
            g.poke(L["c_vis"], 0, 0, 0)
            for lv in range(1, 20) if s == 0 else (16, 17, 18, 19):
                g.call(L["change_level"], tmax=150, regs="a=%02x,x=00" % lv)
                n = g.b(L["lb_cnt"])
                bad = [(g.b(L["mix"] + i), g.b(L["miy"] + i), g.tile(g.b(L["mix"] + i), g.b(L["miy"] + i)), i) for i in range(n)
                       if g.tile(g.b(L["mix"] + i), g.b(L["miy"] + i)) < 2]      # wall or water (the floor boss stands on the stairs down, a chest can be under a monster)
                if bad:
                    err.append("seed %d level %d: monsters in a wall or in the water at %s" % (s, lv, bad))
                if lv < 16:
                    continue
                PD.sw_reset(g); t0 = PD.sw(g)
                g.call(L["gen_dungeon"], tmax=60)
                t = (PD.sw(g) - t0) / PD.CPS
                worst = max(worst, t)
                m = g.mem(0xC000, W * W)
                up = (g.b(L["st_up_x"]), g.b(L["st_up_y"]))
                dn = (g.b(L["st_dn_x"]), g.b(L["st_dn_y"]))
                fl = {(i % W, i // W) for i, v in enumerate(m) if v >= 2}
                seen = {up}
                q = collections.deque([up])
                while q:
                    x, y = q.popleft()
                    for nb in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if nb in fl and nb not in seen:
                            seen.add(nb); q.append(nb)
                tag = "seed %d level %d" % (s, lv)
                if up not in fl or dn not in seen:
                    err.append("%s: stairs down not reachable from the stairs up" % tag)
                if seen != fl:
                    err.append("%s: %d walkable tiles not reachable" % (tag, len(fl - seen)))
                asym = [(x, y) for y in range(W) for x in range(W // 2)
                        if ((x, y) in fl) != ((W - 1 - x, y) in fl) and {(x, y), (W - 1 - x, y)} & {up, dn} == set()]
                if asym:
                    err.append("%s: not symmetric at %s" % (tag, asym[:6]))
                cols = sum(1 for y in range(1, W - 1) for x in range(1, W - 1) if (x, y) not in fl and
                           all((x + dx, y + dy) in fl for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy))
                cols_min = min(cols_min, cols); floor_min = min(floor_min, len(fl))
                if cols < MIN_COLS:
                    err.append("%s: only %d columns" % (tag, cols))
                if len(fl) < MIN_FLOOR:
                    err.append("%s: only %d walkable tiles" % (tag, len(fl)))
                if t > MAX_GEN:
                    err.append("%s: generation %.2f s (max %.1f s)" % (tag, t, MAX_GEN))
                if not g.b(L["lv_look"] + lv) & 0x40:
                    err.append("%s: lv_look %02x (citadel wanted)" % (tag, g.b(L["lv_look"] + lv)))
                if s == 0 and lv == 16 and "--show" in sys.argv:
                    for y in range(W):
                        print("".join("U" if (x, y) == up else "D" if (x, y) == dn else "." if (x, y) in fl else "#"
                                      for x in range(W)))
        print("citadel: %d seeds x levels 16-19, slowest generation %.2f s, fewest columns %d, fewest walkable tiles %d; "
              "no monster in a wall on levels 1-19" % (SEEDS, worst, cols_min, floor_min))
    finally:
        g.close()
    if err:
        print("\n".join(err)); sys.exit(1)
    print("citadel ok")


if __name__ == "__main__":
    main()
