"""Bot, layer 1: the emulator. One VICE (x64sc, warp) driven through its remote monitor on TCP (Lab64's vicemon, the same
library as the tests): the bot stops the game at every input read (the rts of read_input), writes joystick and keys as if the
player had pressed them and lets the frames run. Only the two calls of read_input are patched: the game runs its own code.

Speed: warp mode; a step of n frames costs one write and one "go" (see Emu)."""
import os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))                  # tests/
from lib.c64 import Game                                    # noqa: E402
from lib import play as P                                   # noqa: E402

UP, DOWN, LEFT, RIGHT, FIRE = 1, 2, 4, 8, 16
# keys: (row of keynew, mask), as read by handle_keys (src/game/game.asm)
KEYS = dict(slash=(3, 0x20), whirlwind=(4, 0x04), battle_cry=(4, 0x20), smash=(5, 0x04), rage=(3, 0x40), frenzy=(4, 0x40),
            potion1=(7, 0x01), potion2=(7, 0x08), potion3=(1, 0x01), potion4=(1, 0x08), scroll=(2, 0x01),
            inventory=(4, 0x02), runstop=(7, 0x80))


HOOK = 0x03a0                                               # input hook: $03A0-$03D3 ($0334-$0394 is the game's trampoline)
V_JOY, V_PREV, V_KROW, V_KMASK, V_CNT, V_MAIN = 0x03f0, 0x03f1, 0x03f2, 0x03f3, 0x03f4, 0x03f5


class Emu:
    """The input goes through a HOOK written in the cassette buffer: the three calls of read_input of the game (main loop,
    ui_input, nav_init) are patched to call it. After the game's own read_input it replaces joystick and keys with the bot's and
    counts the frames: the monitor stops the machine only when the counter of the step reaches 0 (one breakpoint, on the
    hook's nop), so several frames run at warp speed with no monitor traffic. V_MAIN tells if the read came from the main
    loop (1) or from a screen (0)."""

    def __init__(self, seed=None, name=None):
        self.g = Game()
        self.L = self.g.L
        self.frames = 0                                    # emulated frames played (50 a second)
        self.t0 = time.time()
        self.seed = seed or P.SEED
        self.name = name or P.NAME
        self.prev = 0

    def start(self):
        """START, the barbarian menu, a new barbarian in the village of chapter 1; then the input hook"""
        g = self.g
        g.to_menu()
        g.poke(g.M["namebuf"], *self.name); g.poke(g.M["seedbuf"], *self.seed); g.poke(g.M["cur_slot"], 0)
        g.menu_return(1)
        g.frames(3)
        g.release_input()
        self.install()

    def install(self):
        g, L = self.g, self.L
        ri, kn = L["read_input"], L["keynew"]
        lo = lambda a: a & 255
        hi = lambda a: a >> 8
        code = [0xa9, 1, 0x2c, 0xa9, 0, 0x8d, lo(V_MAIN), hi(V_MAIN), 0x20, lo(ri), hi(ri),
                0xad, lo(V_PREV), hi(V_PREV), 0x49, 0xff, 0x2d, lo(V_JOY), hi(V_JOY), 0x85, L["joynew"],
                0xad, lo(V_JOY), hi(V_JOY), 0x85, L["joy"], 0x8d, lo(V_PREV), hi(V_PREV),
                0xad, lo(V_KMASK), hi(V_KMASK), 0xf0, 11, 0xae, lo(V_KROW), hi(V_KROW), 0x9d, lo(kn), hi(kn),
                0xa9, 0, 0x8d, lo(V_KMASK), hi(V_KMASK),
                0xce, lo(V_CNT), hi(V_CNT), 0xd0, 1, 0xea, 0x60]
        assert L["joy"] < 256 and L["joynew"] < 256
        g.poke(HOOK, *code)
        g.poke(V_JOY, 0, 0, 0, 0, 0, 1)
        self.stop_at = HOOK + len(code) - 2                 # the nop
        import re
        lst = open(os.path.join(os.path.dirname(HERE), "..", "out", "work", "game.lst")).read()
        sites = [int(m.group(1), 16) for m in re.finditer(r"^\.([0-9a-f]{4})\t\t(?:20|4c) %02x %02x\tj(?:sr|mp)" % (lo(ri), hi(ri)), lst, re.M)]
        main = self.g.RET_GAME - 3
        # the main loop (jsr), ui_input (its final jmp) and nav_init (the keys already down when a screen opens)
        assert len(sites) == 3 and main in sites, "calls of read_input: %s (expected 3, the main loop among them)" % sites
        for a in sites:
            h = HOOK if a == main else HOOK + 3
            g.poke(a + 1, lo(h), hi(h))
        g.brk(self.stop_at)

    def close(self):
        self.g.close()

    # ---- one step
    def step(self, joy=0, key=None, n=1):
        """n frames with the joystick `joy`; `key` (a name of KEYS) pressed in the first one"""
        r, m = KEYS[key] if key else (0, 0)
        self.g.poke(V_JOY, joy, self.prev, r, m, n)
        self.prev = joy
        self.g.go(60)
        self.frames += n

    def tap_fire(self, settle=2):
        self.step(0); self.step(FIRE); self.step(0, n=settle)

    def in_game(self):
        """the last input read came from the main loop (no screen open)"""
        return self.g.b(V_MAIN) == 1

    # ---- memory
    def b(self, a): return self.g.b(a)
    def w(self, a): return self.g.w16(a)
    def mem(self, a, n): return self.g.mem(a, n)
    def poke(self, a, *v): self.g.poke(a, *v)

    def call(self, name, regs=""):
        keep = self.g.mem(0x0340, 4)                        # call_keep puts its stub in the game's trampoline: put it back
        r = self.g.call_keep(self.L[name], regs=regs)
        self.g.poke(0x0340, *keep)
        self.g.brk(self.stop_at)                            # (call_keep clears the breakpoints)
        return r

    def seconds(self):
        """emulated seconds played (PAL: 50 frames a second; the frames spent inside disk loads are not counted)"""
        return self.frames / 50.0
