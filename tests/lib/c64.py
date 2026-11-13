"""Shared test library for VICE (10/11): fast remote monitor (no fixed delays: it waits for the prompt or the stop),
program labels, simulated input and game start.

Protocol: the VICE remote monitor (port 6510) runs one command per line and answers with the prompt "(C:$xxxx) ";
several lines in one send are not all executed, so every command waits for its prompt. "x" (continue) answers only at
the next stop ("Stop on ..."): the stop line holds the C64 cycle counter, used to measure frame durations.

Input: the game reads joystick and keyboard only in read_input (menus too, via ui_input). A stop on the final rts of
read_input lets the test write joy / joynew / keynew as if the player had pressed them: the fastest way and the
closest to the real game (everything else runs as usual)."""
import glob, os, re, shutil, socket, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "out")
ROMS = os.path.join(ROOT, "toolchain", "roms", "vice-roms", "DRIVES")   # drive ROMs (toolchain/roms/roms.md)
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "memory-map", "simulators")]
from vice_rom import ROM_ARGS, XRUN  # noqa: E402  (x64sc: -default + tutte le ROM da toolchain/roms/, tools/vice/vice_rom.py)
PROMPT = re.compile(r"\(C:\$[0-9a-f]{4}\) $")
STOP = re.compile(r"Stop on[^\n]*\n[^\n]*?(\d+)\s*\n", re.S)
FRAME = 19656                                     # cycles of a PAL frame


def labels(name="game"):
    """labels and constants of out/<name>.lbl ($hex and decimal)"""
    t = open(os.path.join(OUT, name + ".lbl")).read()
    d = {m.group(1): int(m.group(2), 16) for m in re.finditer(r"^(\w+)\s*=\s*\$([0-9a-f]+)", t, re.M)}
    d.update({m.group(1): int(m.group(2)) for m in re.finditer(r"^(\w+)\s*=\s*(\d+)\s*$", t, re.M)})
    return d


def listing(name="game"):
    return open(os.path.join(OUT, name + ".lst")).read()


def addr_after(lst, label, pattern):
    """address of the first listing line after 'label:' whose instruction text matches pattern"""
    i = lst.index("\n" + label + ":") if ("\n" + label + ":") in lst else lst.index(label + ":")
    for ln in lst[i:].splitlines():
        m = re.match(r"^\.([0-9a-f]{4})\s+(?:[0-9a-f]{2}\s){1,3}\s*(.*)$", ln)
        if m and re.search(pattern, m.group(2)):
            return int(m.group(1), 16)
    raise KeyError("%s: %s not found" % (label, pattern))


class MonitorError(RuntimeError):
    pass


def drain(s, wait=0.0):
    """discard what is waiting on the socket, with a very short wait for late lines (a stop prints its register line a
    moment after "Stop on": without the wait a late prompt would be taken as the answer to the next command)"""
    if wait: s.settimeout(wait)
    else: s.setblocking(False)
    try:
        while s.recv(65536): pass
    except (socket.timeout, BlockingIOError, OSError):
        pass
    finally:
        s.settimeout(0.02)


def sync(s, c, tmax=20):
    """for scripts with their own socket: one command and its answer up to the prompt (no fixed delays).
    "" = drain without sending (an empty line would repeat the last command); "l ..." waits for "Loading"."""
    s.settimeout(0.02)
    if c == "":
        return settle(s, 0)
    drain(s, 0.02)                                  # leftovers of a previous answer (prompt after "Stop on"; the scripts read
                                                    # "Stop on" themselves and leave the rest of the stop text behind)
    s.sendall((c + "\n").encode())
    buf, t0 = "", time.time()
    load, mem = c.startswith("l "), c.startswith("m ")
    while time.time() - t0 < tmax:
        try:
            d = s.recv(65536)
            if d: buf += d.decode(errors="ignore")
        except socket.timeout:
            pass
        if PROMPT.search(buf) and (not load or "Loading" in buf) and (not mem or ">C:" in buf): return buf
    raise MonitorError("monitor: no answer to '%s'" % c)


def settle(s, boot=1.0, gap=0.1):
    """wait for the C64 boot (warp), then for the monitor to be silent"""
    time.sleep(boot)
    s.settimeout(0.02)
    buf, last = "", time.time()
    while time.time() - last < gap:
        try:
            d = s.recv(65536).decode(errors="ignore")
            if d: buf += d; last = time.time()
        except Exception:
            pass
    return buf


class Vice:
    """x64sc in warp with the remote monitor. disk: d64 mounted in drive 8 (a copy, so the original is untouched)."""

    def __init__(self, disk=None, boot_wait=1.0, extra=(), inplace=False, warp=True, show=False):
        """inplace=True: the disk is mounted as is (writes persist: needed by save tests across sessions).
        warp=False: real speed; show=True: a visible VICE window (no xvfb-run; tools/vice/arena.py --show)"""
        self.disk = None
        args = ([] if show else XRUN) + [
                "x64sc", "-silent", "-sounddev", "dummy"] + ROM_ARGS + (["-warp"] if warp else [])
        if disk and inplace:
            args += ["-8", disk]
        elif disk:
            self.disk = os.path.join(OUT, "test_%d.d64" % os.getpid())
            shutil.copy(disk, self.disk)
            args += ["-8", self.disk]
        args += list(extra) + ["-remotemonitor"]
        self.p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.s = None
        t0 = time.time()
        while time.time() - t0 < 20:
            try:
                self.s = socket.create_connection(("127.0.0.1", 6510)); break
            except OSError:
                time.sleep(0.05)
        if not self.s:
            raise MonitorError("VICE: remote monitor not reachable")
        self.s.settimeout(0.02)
        time.sleep(boot_wait)                       # the C64 reaches READY. (warp)
        self.quiet()

    # ---- protocol
    def quiet(self, gap=0.15, tmax=5):
        """read and discard until the monitor is silent for 'gap' seconds"""
        buf, last, t0 = "", time.time(), time.time()
        while time.time() - last < gap and time.time() - t0 < tmax:
            try:
                d = self.s.recv(65536).decode(errors="ignore")
                if d: buf += d; last = time.time()
            except Exception:
                pass
        return buf

    def _read(self, done, tmax, what):
        buf, t0 = "", time.time()
        while time.time() - t0 < tmax:
            try:
                d = self.s.recv(65536)
                if d: buf += d.decode(errors="ignore")
            except socket.timeout:
                pass
            except Exception as e:
                raise MonitorError("monitor: connection lost during '%s' (%s)" % (what, e))
            if done(buf): return buf
        raise MonitorError("monitor: no answer to '%s' in %d s (got: %r)" % (what, tmax, buf[-160:]))

    def cmd(self, c, tmax=20):
        self.s.sendall((c + "\n").encode())          # (no drain: "m" answers need ">C:" lines, "x" needs "Stop on")
        m = c.startswith("m ")
        return self._read(lambda b: PROMPT.search(b) and (not m or ">C:" in b), tmax, c)

    def go(self, tmax=30):
        """continue up to the next stop; returns the cycle counter at the stop"""
        self.s.sendall(b"x\n")
        b = self._read(lambda b: "Stop on" in b and PROMPT.search(b), tmax, "x")
        m = STOP.search(b)
        return int(m.group(1)) if m else None

    def load(self, prg):
        self.s.sendall(('l "%s" 0\n' % prg).encode())
        self._read(lambda b: "Loading" in b and PROMPT.search(b), 20, "load " + prg)
        self.quiet(0.05)

    # ---- memory
    def mem(self, a, n):
        got = {}
        for _ in range(3):                          # (a late stop line can cut an answer: ask again)
            for m in re.finditer(r">C:([0-9a-f]{4})\s+((?:[0-9a-f]{2}\s+)+)", self.cmd("m %04x %04x" % (a, a + n - 1))):
                for i, x in enumerate(m.group(2).split()): got[int(m.group(1), 16) + i] = int(x, 16)
            if all(a + i in got for i in range(n)): break
        return [got[a + i] for i in range(n)]

    def b(self, a): return self.mem(a, 1)[0]
    def w16(self, a): m = self.mem(a, 2); return m[0] + 256 * m[1]
    def poke(self, a, *v): self.cmd("> %04x %s" % (a, " ".join("%02x" % (x & 255) for x in v)))
    def poke16(self, a, v): self.poke(a, v & 255, v >> 8)
    def fill(self, a, e, v=0): self.cmd("f %04x %04x %02x" % (a, e, v))
    def brk(self, a): self.cmd("break %04x" % a)
    def delbrk(self): self.cmd("del")
    def pc(self, a): self.cmd("r pc=%04x" % a)

    def regs(self):
        """registers at the current stop: dict pc, a, x, y, sp"""
        m = re.search(r"\.;([0-9a-f]{4}) ([0-9a-f]{2}) ([0-9a-f]{2}) ([0-9a-f]{2}) ([0-9a-f]{2}) [0-9a-f]{2} [0-9a-f]{2} ([01]{8})", self.cmd("r"))
        r = dict(zip(("pc", "a", "x", "y", "sp"), (int(v, 16) for v in m.groups()[:5])))
        r["c"], r["z"] = int(m.group(6)[7]), int(m.group(6)[6])          # flags NV-BDIZC
        return r

    def call(self, a, tmax=30, stub=0x0340, regs=""):
        """call routine a (sei; jsr a; nop) and stop when it returns; regs = e.g. 'a=01'"""
        self.poke(stub, 0x78, 0x20, a & 255, a >> 8, 0xea)
        self.brk(stub + 4); self.pc(stub)
        if regs: self.cmd("r " + regs)
        c = self.go(tmax); self.delbrk()
        return c

    def screenshot(self, path):
        self.cmd('screenshot "%s" 2' % path)

    def close(self):
        try:
            self.s.sendall(b"quit\n")
        except Exception:
            pass
        try:
            self.p.wait(1)
        except Exception:
            self.p.kill()
        if self.disk and os.path.exists(self.disk):
            os.remove(self.disk)


class Game(Vice):
    """the real game from the development disk: menu, game, simulated input frame by frame"""

    def __init__(self, disk=os.path.join(OUT, "disk.d64"), extra=()):
        super().__init__(disk, extra=extra)          # extra: more x64sc options (12/11: drive type, KRILL-17)
        self.L = labels("game")
        self.M = labels("lobby")
        self.MN = labels("menu")                        # (11/11) modulo MENU: locanda e negozi (src/menu.asm)
        gl, ml = listing("game"), listing("lobby")
        self.RI = addr_after(gl, "read_input", r"^rts\b")          # rts of read_input: input is written here
        self.AFTER_SCAN = addr_after(ml, "menu_main", r"jsr scan_slots") + 3
        self.RET_GAME = addr_after(gl, "main_loop", r"jsr \$%04x" % self.L["read_input"]) + 3   # return address in the main loop
        self.joy = 0
        self.at_input = False
        self.hits, self.until, self.stopped = {}, set(), None

    # ---- menu and game
    def to_menu(self, tmax=120, fast=None):
        """to the barbarian menu, after the list is read.
        (11/11, fast-loader branch) always the real START (out/start.prg, put in RAM by the monitor): it installs Krill's
        Loader (GAME cannot read the disk without it) and loads GAME, LOBBY and the hero list in a few emulated seconds.
        fast is ignored.
        The real boot is tested by BOOT-10/11 (tests/regression/boot)."""
        self.fast = False
        self.load(os.path.join(OUT, "start.prg"))          # (11/11) un solo START per i due dischi
        self.brk(self.AFTER_SCAN); self.pc(0x080d)
        self.go(tmax); self.delbrk()

    def menu_return(self, a, tmax=120):
        """leave the menu as if the player had chosen: A = 1 new game, 0 continue cur_slot -> main_loop"""
        rts = addr_after(listing("lobby"), "menu_main", r"^rts\b")
        self.pc(rts); self.cmd("r a=%02x" % a)
        self.brk(self.L["main_loop"])
        if os.environ.get("C64_REALMENU") != "1":       # (11/11) the module MENU written by the monitor, not from the 1541
            self.brk(self.L["ml_read"])
            self.go(tmax)
            if self.regs()["pc"] == self.L["ml_read"]:
                self.cmd("bank ram")
                for f in sorted(glob.glob(os.path.join(OUT, "menu_z*.prg"))):    # every zone (tools/build/pack_menu.py)
                    self.load(f)
                self.cmd("bank cpu")
                self.poke(self.L["ovl_cur"], 1)
                self.pc(self.L["ovl_town"])             # ovl_cur = 1: C = 0, rts
                self.go(tmax)
        else:
            self.go(tmax)
        self.delbrk()
        self.at_input = False

    # ---- input
    def frames(self, n=1, joy=0, fire=False, keys=None, tmax=30):
        """n frames holding joystick 'joy' (bit 0 up, 1 down, 2 left, 3 right, 4 fire). fire=True: a fresh fire press
        in the first frame. keys = {row: mask} for keynew in the first frame.
        Returns the list of cycles between one input read and the next (frame durations).
        Other breakpoints set by the test (watch()): a stop there is counted in self.hits[address] and the frame goes on;
        a stop on an address of self.until ends frames() early (self.stopped = that address)."""
        if not self.at_input:
            self.brk(self.RI); self.at_input = True
            self.last = self._go_frame(tmax)
        out = []
        for i in range(n):
            j = joy | (0x10 if fire and i == 0 else 0)
            new = j & ~self.joy & 0xff
            self.poke(self.L["joy"], j)
            self.poke(self.L["joynew"], new)
            if keys and i == 0:
                for r, msk in keys.items(): self.poke(self.L["keynew"] + r, msk)
            self.joy = j
            c = self._go_frame(tmax)
            out.append(c - self.last if c and self.last else 0)
            self.last = c
            if self.stopped is not None: break
        return out

    def watch(self, *addrs, until=()):
        """count the passages on addrs (self.hits) while frames() runs; until = addresses that end frames()"""
        for a in tuple(addrs) + tuple(until): self.brk(a)
        self.hits.update({a: 0 for a in addrs}); self.until = set(until)

    def unwatch(self):
        self.hits, self.until, self.stopped = {}, set(), None
        self.delbrk()
        if self.at_input: self.brk(self.RI)

    def _go_frame(self, tmax):
        self.stopped = None
        while True:
            c = self.go(tmax)
            if not self.hits and not self.until: return c
            pc = self.regs()["pc"]
            if pc in self.hits: self.hits[pc] += 1; continue
            if pc in self.until: self.stopped = pc
            return c

    def call_keep(self, a, regs="", tmax=30):
        """call routine a from the current stop and come back to it (pc and registers restored); returns the registers
        at the routine's return (dict pc, a, x, y, sp). For game routines called between two input reads."""
        r0 = self.regs()
        stub = 0x0340
        self.poke(stub, 0x20, a & 255, a >> 8, 0xea)
        self.brk(stub + 3); self.pc(stub)
        if regs: self.cmd("r " + regs)
        self.go(tmax)
        out = self.regs()
        self.delbrk()
        if self.at_input: self.brk(self.RI)
        for b in list(self.hits) + list(self.until): self.brk(b)
        self.cmd("r pc=%04x" % r0["pc"]); self.cmd("r a=%02x" % r0["a"]); self.cmd("r x=%02x" % r0["x"])
        self.cmd("r y=%02x" % r0["y"])
        return out

    def in_game(self):
        """stopped at an input read: True if it is the main loop one (no UI screen open)"""
        if not self.at_input: self.frames(1)
        sp = int(re.search(r"\.;[0-9a-f]{4} [0-9a-f]{2} [0-9a-f]{2} [0-9a-f]{2} ([0-9a-f]{2})", self.cmd("r")).group(1), 16)
        lo, hi = self.mem(0x0100 + sp + 1, 2)
        return lo + 256 * hi + 1 == self.RET_GAME

    def release_input(self):
        """remove the input breakpoint (the game runs on its own)"""
        if self.at_input:
            self.delbrk(); self.at_input = False

    def press_fire(self, settle=2):
        self.frames(1, fire=True); self.frames(settle)

    def run_stop(self):
        self.frames(1, keys={7: 0x80}); self.frames(1)

    def wait_main(self, tmax=60):
        """up to the next iteration of the main loop"""
        self.release_input()
        self.brk(self.L["main_loop"]); self.go(tmax); self.delbrk()

    # ---- state
    def ptile(self):
        L = self.L
        px, py = self.w16(L["px"]), self.w16(L["py"])
        return px >> 4, py >> 4

    def tile(self, tx, ty, w=48):
        return self.b(self.L["MAP"] + ty * w + tx)

    def teleport(self, tx, ty):
        """put the hero in the middle of the tile (px/py in pixels: tile = px/16)"""
        self.poke16(self.L["px"], tx * 16 + 8); self.poke16(self.L["py"], ty * 16 + 8)
