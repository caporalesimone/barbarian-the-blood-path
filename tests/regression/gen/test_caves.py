#!/usr/bin/env python3
"""(18/11, TODO M11) Caves of chapter 3 (src/game/gen_io.asm: carve_blob, carve_worm, cave_smooth), in VICE: for SEEDS seeds
and the generated levels 11-14, the map must be connected (every floor tile reachable from the stairs up, the stairs down
among them), the border of the map is wall, there are at least MIN_FLOOR floor tiles and the generation time stays under
MAX_GEN seconds (emulated). Palette of the level: 9 on level 11 (snowy rock), 10 on 12-14 (data/chapters.yaml map.palettes).
Usage: python3 tests/regression/gen/test_caves.py"""
import collections, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "perf_disk"))
from lib.c64 import Game  # noqa: E402
from lib.play import new_game  # noqa: E402
import cases as PD  # noqa: E402   (stopwatch of VICE: sw_reset, sw, CPS)

SEEDS = 6
MIN_FLOOR = 300
MAX_GEN = 1.2            # s; measured 18/11: 0.76-0.95 s (rooms: ~0.3 s)
W = 48


def main():
    rng = random.Random(1811)
    g = Game()
    err = []
    try:
        PD.sw_reset(g)
        g.to_menu(); new_game(g); g.frames(3); g.at_input = False
        L = g.L
        g.poke(L["c_chap"], 3); g.poke(L["c_unl"], 3)
        worst = 0
        for s in range(SEEDS):
            g.poke(L["c_seedt"], *[rng.randrange(36) for _ in range(6)])
            g.poke(L["c_vis"], 0, 0, 0)
            for lv in (11, 12, 13, 14):
                g.call(L["change_level"], tmax=150, regs="a=%02x,x=00" % lv)
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
                    for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if n in fl and n not in seen:
                            seen.add(n); q.append(n)
                tag = "seed %d level %d" % (s, lv)
                if up not in fl or dn not in seen:
                    err.append("%s: stairs down not reachable from the stairs up" % tag)
                if seen != fl:
                    err.append("%s: %d floor tiles not reachable" % (tag, len(fl - seen)))
                if any(m[i] >= 2 for i in range(W)) or any(m[(W - 1) * W + i] >= 2 for i in range(W)) or \
                        any(m[y * W] >= 2 or m[y * W + W - 1] >= 2 for y in range(W)):
                    err.append("%s: floor on the border of the map" % tag)
                if len(fl) < MIN_FLOOR:
                    err.append("%s: only %d floor tiles" % (tag, len(fl)))
                if t > MAX_GEN:
                    err.append("%s: generation %.2f s (max %.1f s)" % (tag, t, MAX_GEN))
                look = g.b(L["lv_look"] + lv)
                want = 9 if lv == 11 else 10
                if look & 15 != want or not look & 0x10:
                    err.append("%s: lv_look %02x (palette %d and caves wanted)" % (tag, look, want))
        print("caves: %d seeds x levels 11-14, slowest generation %.2f s" % (SEEDS, worst))
    finally:
        g.close()
    if err:
        print("\n".join(err)); sys.exit(1)
    print("caves ok")


if __name__ == "__main__":
    main()
