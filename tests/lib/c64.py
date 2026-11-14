"""Shared test library for VICE (10/11): fast remote monitor (no fixed delays: it waits for the prompt or the stop),
program labels, simulated input and game start.

Protocol: the VICE remote monitor (port 6510) runs one command per line and answers with the prompt "(C:$xxxx) ";
several lines in one send are not all executed, so every command waits for its prompt. "x" (continue) answers only at
the next stop ("Stop on ..."): the stop line holds the C64 cycle counter, used to measure frame durations.

Input: the game reads joystick and keyboard only in read_input (menus too, via ui_input). A stop on the final rts of
read_input lets the test write joy / joynew / keynew as if the player had pressed them: the fastest way and the
closest to the real game (everything else runs as usual)."""
import glob, os, re, shutil, signal, socket, subprocess, sys, time

# (14/11) the generic VICE library is Lab64's (py/vicemon.py): Vice, labels, listing, addr_after, ROMS, FRAME, ... come from there
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("C64_ROOT", ROOT)
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "memory-map", "simulators")]
from vicemon import *  # noqa: E402,F401,F403
from vicemon import OUT, ROMS, FRAME, PROMPT, STOP, MonitorError, Vice, drain, sync, settle  # noqa: E402,F401


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
        (11/11, fast-loader branch) always the real START (out/work/start.prg, put in RAM by the monitor): it installs Krill's
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
