"""HELP compressed with ZX0 (12/11, TODO M5b, docs/help.md): the HELP file on the disk is out/work/helpz.prg, a small
decompressor (src/help/zx0sfx.asm) followed by out/work/help.zx0; at $080D it unpacks HELP to $0801 and jumps to it.
Pure Python checks (fast); the run from the disk is covered by LORE-10 (release)."""
import os, sys
from lib.runner import test, check
from lib.c64 import OUT

ROOT = os.path.dirname(OUT)
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "memory-map", "simulators")]


@test("HELP-Z-10", "out/work/help.zx0 unpacks to out/work/help.prg byte by byte; the packed file is under half the blocks")
def help_zx0(ctx):
    import zx0dec
    raw = open(os.path.join(OUT, "help.prg"), "rb").read()
    z = open(os.path.join(OUT, "help.zx0"), "rb").read()
    check(zx0dec.zx0_decompress(z) == raw[2:], "ZX0 data does not unpack to out/work/help.prg")
    pz = open(os.path.join(OUT, "helpz.prg"), "rb").read()
    check(pz[:2] == raw[:2] == b"\x01\x08", "both files must load at $0801")
    blk = lambda n: (n + 253) // 254
    check(blk(len(pz)) * 2 <= blk(len(raw)), "packed %d blocks, raw %d: not under half" % (blk(len(pz)), blk(len(raw))))


@test("HELP-Z-11", "the disk holds the packed HELP (file 'help' equals out/work/helpz.prg)")
def help_disk(ctx):
    import subprocess, tempfile
    d = os.path.join(OUT, "disk.d64")
    with tempfile.TemporaryDirectory(dir=OUT) as td:
        f = os.path.join(td, "help.prg")
        subprocess.run(["c1541", d, "-read", "help", f], capture_output=True)
        check(os.path.exists(f), "help not found on %s" % d)
        check(open(f, "rb").read() == open(os.path.join(OUT, "helpz.prg"), "rb").read(), "help on the disk differs from helpz.prg")
