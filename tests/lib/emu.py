"""Second emulator for the tests (13/11): vc64web (VirtualC64 in WebAssembly) driven through its headless daemon.

VICE stays the only authoritative reference of the project (CLAUDE.md): this emulator is used to check that the game
also runs on a different core (drive 1541-II, Krill's Loader, save plugin, raster split of the HUD, joystick/keyboard
input) and for scenarios played with a bot from the real disk. A result obtained here is never a measure of the game:
cycles and timing are confirmed in VICE.

The package lives in toolchain/vc64web-custom (docs: docs/emulatore.md). Since 13/11 the daemon runs in its own container,
c64-emu-vc64web (node, Playwright, Chromium, ffmpeg and the page already built in the image): ./build.sh --release (or
--emu) starts it and passes its address in EMU_URL (e.g. http://c64-emu-vc64web:7064) to the tests, which run in
c64-emu-vice. Without EMU_URL the tests are SKIP with the reason, not FAIL. The disk is sent to the daemon in base64
(no shared folder); each test starts a fresh machine (`start`).

    e = Emu(); e.boot()                       # real disk, LOAD"*",8 / POKE 1020,1 / RUN -> LOBBY menu
    e.run_script(text); e.run_loop(js, frames=600); e.peek("cur_level"); e.close()
"""
import base64, json, os, shutil, subprocess, sys, time, urllib.request
from lib.c64 import ROOT, OUT
from lib.runner import Skip

URL = os.environ.get("EMU_URL", "").rstrip("/")         # daemon of the container c64-emu-vc64web
LOBBY_MENU = 0xC00C                                   # menu_main of out/lobby.lbl (module LOBBY at $C000)


def ensure_built():
    """the daemon must be reachable (./build.sh --emu / --release start the container c64-emu-vc64web)"""
    if not URL: raise Skip("EMU_URL not set: the vc64web daemon (container c64-emu-vc64web) is not running (./build.sh --emu)")


class Emu:
    def __init__(self):
        self.proc = None
        ensure_built()
        t0 = time.time()
        while True:
            try:
                self._http("GET", "/ping", timeout=2); break
            except Exception:
                if time.time() - t0 > 60:
                    raise Skip("the vc64web daemon does not answer at %s" % URL)
                time.sleep(0.3)
        self.call("start", {})
        self.call("pause")

    # ---- transport (same protocol as headless/c64-batch)
    def _http(self, method, url, body=None, timeout=900):
        r = urllib.request.Request(URL + url, method=method,
                                   data=json.dumps(body).encode() if body is not None else None,
                                   headers={"content-type": "application/json"})
        with urllib.request.urlopen(r, timeout=timeout) as f:
            return json.loads(f.read().decode())

    def call(self, method, *args, timeout=900):
        r = self._http("POST", "/call", {"method": method, "args": list(args)}, timeout)
        if not r.get("ok"):
            raise RuntimeError("emulator %s: %s %s" % (method, r.get("code", ""), r.get("error", "")))
        return r.get("value")

    def close(self):
        """the daemon is shared (container): nothing to stop; the next test starts a fresh machine"""
        try: self.call("pause", timeout=10)
        except Exception: pass

    # ---- memory and screen (labels of out/game.lbl once loaded)
    def peek(self, a, n=1):
        v = self.call("peek", a, n)
        return v if n > 1 else (v[0] if isinstance(v, list) else v)

    def word(self, a): return self.call("peekWord", a)
    def regs(self): return self.call("regs")
    def frames(self, n, fast=False): return self.call("runFrames", n, {"fast": True} if fast else {})
    def screenshot(self, path):
        d = self.call("screenshot")
        with open(path, "wb") as f: f.write(base64.b64decode(d.split(",")[-1]))
    def state_hash(self): return self.call("stateHash")["hash"]

    def load_labels(self, name, set=None):
        """labels of out/NAME.lbl. The modules that share addresses (LOBBY and GAME both use $C000) must go in separate
        sets: set="lobby" -> read as "lobby:nvalid" (docs/emulatore.md); without set they replace each other."""
        with open(os.path.join(OUT, name), "r") as f:
            return self.call("loadLabels", f.read(), {"set": set, "activate": False} if set else {})

    def load_encoding(self, name, path):
        """named screen encoding from a 64tass .cdef file (the HUD one: out/gfx_consts.inc, block .enc "hud")"""
        with open(path, "r") as f: return self.call("loadEncoding", name, f.read())

    # ---- running
    def run_script(self, text):
        return self.call("runScript", text)

    def run_loop(self, code, frames, every=2):
        """a bot in the page (api runLoop): exact steps, same state + same bot = same result; the result has the state"""
        return self.call("runLoop", code, {"frames": frames, "every": every})

    def until(self, cond, step=200, limit=8000, fast=True):
        """cond() true, checked every `step` frames (fast = warp: only for loading, never for a bot)"""
        n = 0
        while not cond():
            if n >= limit: return False
            self.frames(step, fast=fast); n += step
        return True

    def at_pc(self, addr, timeout=3000):
        r = self.call("runUntil", {"pc": addr, "timeoutFrames": timeout})
        return r.get("reason") == "pc"

    def to_main_loop(self, timeout=3000):
        """after the save of a new hero (Krill plugin) the game enters the village: main_loop of out/game.lbl"""
        self.call("resume")
        ok = self.at_pc("main_loop", timeout)
        self.call("pause")
        return ok

    # ---- the real boot: disk image in the drive, BARBARIAN with POKE 1020,1 (no menu) -> START -> LOBBY
    def boot(self, disk=None, tmax=9000):
        """returns the number of emulated frames until the LOBBY menu. The image is a copy in the browser: the file of
        the disk is never written (the saved heroes live in that copy only)."""
        disk = disk or os.path.join(OUT, "disk.d64")
        with open(disk, "rb") as f: b64 = base64.b64encode(f.read()).decode()
        self.call("resume")
        self.call("loadFile", "disk.d64", b64, {"autoload": False})
        self.frames(150)
        self.call("sendText", 'LOAD"*",8\n')
        self.frames(700, fast=True)                       # BARBARIAN: ~10 emulated seconds
        self.call("sendText", "POKE 1020,1\n")
        self.call("sendText", "RUN\n")
        lobby = open(os.path.join(OUT, "lobby.prg"), "rb").read()
        sig = list(lobby[0x0c + 2:0x0c + 2 + 16])         # first bytes of menu_main
        t0 = self.call("cycles")

        def ready():                                      # the module LOBBY is in RAM (loaded by START through Krill)
            return self.peek(LOBBY_MENU, 16) == sig
        ok = self.until(ready, step=150, limit=tmax)
        self.frames(200, fast=True)                       # the menu is drawn and waits for the player
        self.call("pause")
        return ok, int((self.call("cycles") - t0) / 19656)
