#!/usr/bin/env python3
"""(18/11, TODO M11) Swamp of chapter 2 (src/game/gen_io.asm: islands = carve_blob, boardwalks = carve_plank, swamp_gates), in
VICE: for SEEDS seeds and the levels 6-9, every walkable tile is reachable from the west gate (stairs up), the east gate
(stairs down) among them, the gates are on the borders (x = 1 and x = 46) and the east gate of level L is on the same row as
the west gate of level L+1 (the levels side by side make one swamp), generation under MAX_GEN s, palette 12 on every level.
Usage: python3 tests/regression/gen/test_swamp.py"""
import collections, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "perf_disk"))
from lib.c64 import Game  # noqa: E402
from lib.play import new_game  # noqa: E402
import cases as PD  # noqa: E402

SEEDS = 5
MAX_GEN = 1.2            # s; measured 18/11: 0.84-0.87 s
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
                if up[0] != 1 or dn[0] != W - 2:
                    err.append("%s: gates at x %d and %d (1 and 46 wanted)" % (tag, up[0], dn[0]))
                if dn not in seen or seen != fl:
                    err.append("%s: %d walkable tiles not reachable from the west gate (east gate reachable: %s)" % (tag, len(fl - seen), dn in seen))
                if prev is not None and prev != up[1]:
                    err.append("%s: west gate on row %d, east gate of the level before on row %d" % (tag, up[1], prev))
                prev = dn[1]
                if t > MAX_GEN:
                    err.append("%s: generation %.2f s (max %.1f s)" % (tag, t, MAX_GEN))
                look = g.b(L["lv_look"] + lv)
                if look != 0x2C:
                    err.append("%s: lv_look %02x (palette 12 and swamp wanted)" % (tag, look))
        print("swamp: %d seeds x levels 6-9, slowest generation %.2f s" % (SEEDS, worst))
    finally:
        g.close()
    if err:
        print("\n".join(err)); sys.exit(1)
    print("swamp ok")


if __name__ == "__main__":
    main()
