"""Load checks for Krill's Loader (15/11, ex TODO A2, docs/wiki/FastLoader.md 4.1): directory and files of the mounted d64, a direct
krill_loadraw call, and LoadCheck, which runs game routines while every load they do is compared with its file on the disk
(bytes in RAM and end address returned by the loader). Used by tests/regression/krill_cache and krill_walk.

Why: in r194 a file of one block loaded right after its predecessor in the directory came from the drive's next-file cache
with a wrong length (shorter or longer, no error). A load that does not equal its file must never pass unnoticed."""
import re

LOADRAW = 0x0200                     # krill_loadraw (resident, out/work/krill.inc)
ENDADDR = 0x43                       # krill_endaddrlo/hi
LOADADDR = 0x41                      # krill_loadaddrlo/hi
SPT = [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5
SAVES = ("hl", "save-01", "save-02", "save-03", "save-04", "save-05")   # rewritten by the save plugin during a session


def directory(path):
    """[(name, blocks, data)] in directory order; data = the file with its 2-byte load address"""
    d = open(path, "rb").read()
    off = lambda t, s: (sum(SPT[:t - 1]) + s) * 256
    blk = lambda t, s: d[off(t, s):off(t, s) + 256]
    out, t, s = [], 18, 1
    while t:
        b = blk(t, s)
        for i in range(8):
            e = b[i * 32:(i + 1) * 32]
            if e[2] & 7 == 0:
                continue
            data, ft, fs = b"", e[3], e[4]
            while ft:
                x = blk(ft, fs)
                data += x[2:] if x[0] else x[2:x[1] + 1]
                ft, fs = x[0], x[1]
            out.append((e[5:21].split(b"\xa0")[0].decode("latin1").lower(), e[30] | e[31] << 8, data))
        t, s = b[0], b[1]
    return out


def ram(g, a, n):
    """n bytes of RAM (also under the ROMs)"""
    g.cmd("bank ram")
    try:
        return bytes(g.mem(a, n)) if n else b""
    finally:
        g.cmd("bank cpu")


def load_to(g, name, dest, name_at=0x0380, stub=0x0340):
    """krill_loadraw of 'name' to dest (LOAD_TO, interrupts off) from the current stop: returns (carry, end address)"""
    g.poke(name_at, *name.upper().encode("latin1"), 0)
    g.poke(LOADADDR, dest & 255, dest >> 8)
    g.poke(stub, 0x78, 0x38, 0xa2, name_at & 255, 0xa0, name_at >> 8, 0x20, LOADRAW & 255, LOADRAW >> 8, 0xea)
    g.brk(stub + 9); g.pc(stub); g.go(60); g.delbrk()
    return g.regs()["c"], g.w16(ENDADDR)


class LoadCheck:
    """call game routines (like Game.call_keep) while every krill_loadraw they do is checked against its file"""

    def __init__(self, g, disk=None):
        self.g = g
        self.files = {n: d for n, _, d in directory(disk or g.disk)}
        self.loads = []                  # (name, ok, detail)

    def _check(self, name, carry, dest):
        g = self.g
        f = self.files.get(name)
        if f is None:
            return False, "not on the disk"
        la = dest if dest is not None else f[0] | f[1] << 8
        data, end = f[2:], g.w16(ENDADDR)
        if carry:
            return False, "loader error (C = 1, A = %02x)" % g.regs()["a"]
        if end != la + len(data):
            return False, "end address $%04x, expected $%04x (%+d bytes)" % (end, la + len(data), end - la - len(data))
        if name not in SAVES:
            got = ram(g, la, len(data))
            if got != data:
                return False, "bytes differ from offset %d" % next(i for i in range(len(data)) if got[i] != data[i])
        return True, "%d B at $%04x" % (len(data), la)

    def call(self, a, regs="", tmax=150, stub=0x0340):
        g = self.g
        r0 = g.regs()
        g.delbrk()
        g.poke(stub, 0x20, a & 255, a >> 8, 0xea)
        g.brk(stub + 3); g.brk(LOADRAW); g.pc(stub)
        if regs: g.cmd("r " + regs)
        pend = None
        while True:
            g.go(tmax)
            r = g.regs()
            if r["pc"] == stub + 3:
                break
            if r["pc"] == LOADRAW:
                p = r["x"] | r["y"] << 8
                nm = bytes(g.mem(p, 17)).split(b"\0")[0].decode("latin1").lower()
                lo, hi = g.mem(0x0100 + r["sp"] + 1, 2)
                ret = (lo | hi << 8) + 1
                pend = (nm, g.w16(LOADADDR) if r["c"] else None, ret)
                g.brk(ret)
            elif pend and r["pc"] == pend[2]:
                ok, why = self._check(pend[0], r["c"], pend[1])
                self.loads.append((pend[0], ok, why))
                pend = None
                g.delbrk(); g.brk(stub + 3); g.brk(LOADRAW)
        out = g.regs()
        g.delbrk()
        if g.at_input: g.brk(g.RI)
        g.cmd("r pc=%04x" % r0["pc"]); g.cmd("r a=%02x" % r0["a"]); g.cmd("r x=%02x" % r0["x"]); g.cmd("r y=%02x" % r0["y"])
        return out

    def bad(self):
        return [(n, why) for n, ok, why in self.loads if not ok]

    def pairs(self):
        """consecutive loads (previous, next) as names"""
        n = [x[0] for x in self.loads]
        return list(zip(n, n[1:]))
