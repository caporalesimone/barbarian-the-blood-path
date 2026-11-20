#!/usr/bin/env python3
"""Floor census (20/11): the real game (VICE) generates floors 1..20 for several world seeds; for each floor it reads the
monster types (mtype), the floor boss (lb_boss) and the chest types (ch_t). The gold simulator
(tools/simulators/sim_gold.py) uses this census instead of averages, so chest and monster counts are the game's own.

Usage (from the project root, in the lab64-tools container):
  lab64 run python3 tools/vice/floor_census.py [N_SEEDS] [OUT.json]   (default 24 seeds, ~25 minutes)
Output: tools/simulators/data/floor_census.json (versioned reference, like the generator reference maps): redo it when the
generator changes (GVER) or spawn/chest rules change; sim_gold.py warns if the generator version differs.
Needs the build (out/work/disk.d64, game.lbl). Drives the game through the save-test harness (tests/regression/saves)."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tests", "regression", "saves"))
import test_saves as T  # noqa: E402

OUT = os.path.join(ROOT, "tools", "simulators", "data", "floor_census.json")


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    dest = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else OUT
    L = T.lbl
    lbl = open(os.path.join(ROOT, "out", "work", "game.lbl")).read()
    m = re.search(r"^GVER\s*=\s*(\$?)([0-9a-fA-F]+)", lbl, re.M)
    gver = int(m.group(2), 16 if m.group(1) else 10)
    ver = re.search(r'^version:\s*"?([0-9.]+)', open(os.path.join(ROOT, "version.yaml")).read(), re.M).group(1)
    out = {"gver": gver, "version": ver, "floors": list(range(1, 21)), "seeds": {}}
    T.fresh()
    v = T.Vice()
    try:
        if not v.menu() or not v.play(1):
            sys.exit("floor_census: menu / new game not reached")
        for s in range(n_seeds):
            seed = [(7 * s + 3 * k + 1) % 36 for k in range(6)]
            v.cmd("> %04x %s" % (L["c_seedt"], " ".join("%02x" % d for d in seed)))
            v.cmd("> %04x 00 00" % L["c_won"])
            res = {}
            for lv in out["floors"]:
                if not v.level(lv):
                    sys.exit("floor_census: seed %d floor %d not reached" % (s, lv))
                n = v.mem(L["lb_cnt"], 1)[0]
                res[lv] = {"m": list(v.mem(L["mtype"], max(n, 1)))[:n], "boss": v.mem(L["lb_boss"], 1)[0],
                           "ch": [c for c in v.mem(L["ch_t"], 15) if c]}
            out["seeds"][s] = res
            print("seed %d/%d done" % (s + 1, n_seeds), flush=True)
    finally:
        v.close()
    json.dump(out, open(dest, "w"), separators=(",", ":"))
    print("written", os.path.relpath(dest, ROOT))


if __name__ == "__main__":
    main()
