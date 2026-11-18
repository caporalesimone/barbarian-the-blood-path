#!/usr/bin/env python3
"""Level generator (VICE, development disk). With a fixed seed the map (MAP) of some levels must stay the reference
one (tests/regression/gen/gen_ref.json): the generator runs under the I/O (src/game/gen_io.asm) and the throne room
comes from the file FMAP (tools/build/gen_final.py); every change of the generation breaks the saved levels, so it must be
wanted (then: python3 tests/regression/gen/test_gen.py --update and the generator version c_gver).
Level 20: always read from the disk (no cache since 11/11, branch fast-loader); boss alive, boss dead, lever pulled.
Usage: python3 tests/regression/gen/test_gen.py [--update]"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves"))
import test_saves as T  # noqa: E402
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_ref.json")
SEED = [10, 23, 24, 10, 23, 24]          # "ANOANO" (digits 0-35)
CASES = [(1, 0, 0), (2, 0, 0), (5, 0, 0), (9, 0, 0), (11, 0, 0), (13, 0, 0), (19, 0, 0), (20, 0, 0), (20, 1, 0), (20, 1, 1)]   # (18/11) 11, 13: grotte


def main():
    T.fresh()
    v = T.Vice()
    got, err = {}, []
    try:
        if not v.menu() or not v.play(1):
            sys.exit("menu / new game not reached")
        v.cmd("> %04x %s" % (T.lbl["c_seedt"], " ".join("%02x" % d for d in SEED)))
        v.level(0, 2)                    # village before level 20: its map (cache $E5A0) must not change
        town0 = hashlib.sha1(bytes(v.mem(0xC000, 48 * 48))).hexdigest()
        for lv, won, lev in CASES:
            v.cmd("> %04x %02x %02x" % (T.lbl["c_won"], won, lev))
            if not v.level(lv):
                sys.exit("level %d not reached" % lv)
            m = bytes(v.mem(0xC000, 48 * 48))
            got["%d/%d/%d" % (lv, won, lev)] = hashlib.sha1(m).hexdigest()
        # level 20 again (read again): same map
        v.cmd("> %04x 00 00" % T.lbl["c_won"])
        v.level(20)
        if hashlib.sha1(bytes(v.mem(0xC000, 48 * 48))).hexdigest() != got["20/0/0"]:
            err.append("level 20 read twice differs from the first reading")
        v.level(0, 2)                    # FMAP is at the end of the village cache: the village map is intact
        if hashlib.sha1(bytes(v.mem(0xC000, 48 * 48))).hexdigest() != town0:
            err.append("village after level 20: map changed (did FMAP spoil the cache?)")
    finally:
        v.close()
    if "--update" in sys.argv:
        json.dump(got, open(REF, "w"), indent=1)
        print("reference updated:", REF)
    else:
        ref = json.load(open(REF))
        for k, h in got.items():
            if ref.get(k) != h:
                err.append("level %s: map differs from the reference" % k)
    if err:
        print("\n".join(err)); sys.exit(1)
    print("generator ok (%d levels)" % len(got))


if __name__ == "__main__":
    main()
