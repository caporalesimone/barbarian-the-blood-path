import os, sys
from lib.runner import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""In-game music."""
script("MUSIC-10", "songs per level, buffer = SNDn files, combat and resume, copy under I/O", [PY, os.path.join(H, "test_music.py")])


# (14/11) the .sid files of the songs (tools/build/gen_sid.py): every one is a valid PSID and its player really plays
from lib.runner import test, check  # noqa: E402
from lib.c64 import Vice, OUT  # noqa: E402


@test("MUSIC-11", ".sid files: one per song, PSID header, init + 50 frames of play write gate and frequency of the SID voices")
def sid_files(ctx):
    import glob, struct
    sids = sorted(glob.glob(os.path.join(OUT, "sid", "*.sid")))
    check(sids, "no .sid in out/work/sid (tools/build/gen_sid.py)")
    v = Vice()
    try:
        for f in sids:
            d = open(f, "rb").read()
            magic, ver, off, load, init, play = struct.unpack(">4sHHHHH", d[:14])
            check(magic == b"PSID" and ver == 2 and off == 0x7C and load == 0, "%s: header" % os.path.basename(f))
            prg = os.path.join(OUT, "tmp_sid.prg")
            open(prg, "wb").write(d[off:])
            v.load(prg)
            v.fill(0xD400, 0xD418, 0)
            v.call(init)
            seen = set()
            for _ in range(50):
                v.call(play)
                sid = v.mem(0xD400, 0x19)
                seen |= {i for i in (0, 7, 14) if sid[i + 4] & 1 and (sid[i] | sid[i + 1])}
            check(seen, "%s: no voice with gate and frequency after 50 frames" % os.path.basename(f))
    finally:
        v.close()
