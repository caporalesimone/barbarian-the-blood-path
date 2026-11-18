"""Module MENU with the village menus (11/11, TODO D13): inn AND shops (src/menu.asm) in three RAM zones, ZX0-compressed
zone by zone in one file (tools/build/pack_menu.py); GAME loads it once when entering the village (ovl_town) and it stays:
the theme prefetch writes straight into the theme cache ($ED00), no more into $F500. The shops left GAME (only the item
box of the dungeon chest, ch_item, stays). One VICE session for the in-game cases."""
import os
from c64test import test, check
from lib.c64 import ROOT, OUT, Game
from lib.play import new_game, fire_to, SMITH_DOOR, INN_DOOR

CHAIN = True
CPS = 985248


def prg(name):
    d = open(os.path.join(OUT, name), "rb").read()
    return d[0] | d[1] << 8, d[2:]


def zones():
    """every zone of the module (menu_z1..N.prg, N = MPARTS)"""
    n = len([f for f in os.listdir(OUT) if f.startswith("menu_z") and f.endswith(".prg")])
    return [prg("menu_z%d.prg" % k) for k in range(1, n + 1)]


def zones_ok(g):
    g.cmd("bank ram")
    bad = [k + 1 for k, (a, b) in enumerate(zones()) if g.mem(a, len(b)) != list(b)]
    g.cmd("bank cpu")
    return bad


def gcall(g, a, tmax=30):
    """call a routine from the stopped game and come back to the same point (cli; jmp pc): frames() can go on"""
    pc = g.regs()["pc"]
    c = g.call(a, tmax=tmax)
    g.poke(0x0350, 0x58, 0x4c, pc & 255, pc >> 8)
    g.pc(0x0350)
    g.at_input = False                               # (call() deleted the breakpoint of frames())
    return c


def setup(ctx):
    pass


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def game(ctx):
    if "g" not in ctx:
        g = ctx["g"] = Game()
        g.to_menu(); new_game(g); g.frames(3)
    return ctx["g"]


@test("MENU-10", "out/work/menu.prg (one file since 18/11): header (parts, source and destination), parts ZX0(zone k), ends at MR2_END, above ML_LO; shops out of GAME; the disks have MENU, no MENU1/OVLT/OVL2")
def menu_file(ctx):
    import sys, importlib.util, re
    sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "simulators")]
    import zx0dec
    G = {m.group(1): m.group(2) for m in re.finditer(r"^(\w+)\s*=\s*(\$?[0-9a-f]+)", open(os.path.join(OUT, "game.lbl")).read(), re.M)}
    num = lambda v: int(v[1:], 16) if v.startswith("$") else int(v)
    at, f = prg("menu.prg")
    check(at + len(f) == num(G["MR2_END"]) and at >= num(G["ML_LO"]), "menu.prg at $%04x-$%04x (MR2_END $%04x, ML_LO $%04x)" % (at, at + len(f), num(G["MR2_END"]), num(G["ML_LO"])))
    zs = {a: b for a, b in zones()}
    check(f[0] == len(zs), "header: %d parts, %d zones" % (f[0], len(zs)))
    starts = []
    for i in range(f[0]):
        src, dst = f[1 + 4 * i] | f[2 + 4 * i] << 8, f[3 + 4 * i] | f[4 + 4 * i] << 8
        check(dst in zs, "part %d: destination $%04x is not a zone" % (i + 1, dst))
        starts.append((src - at, dst))
    ends = [s for s, _ in starts[1:]] + [len(f)]
    for (off, dst), e in zip(starts, ends):
        check(zx0dec.zx0_decompress(bytes(f[off:e])) == zs[dst], "the part for $%04x is not its zone" % dst)
    lb = open(os.path.join(OUT, "game.lbl")).read()
    for name in ("enter_shop", "shop_buy", "shop_sell", "shop_repair", "sh_item", "gold_pay", "ov_stash"):
        check(not re.search(r"^%s\s*=" % name, lb, re.M), "%s is still in GAME" % name)
    spec = importlib.util.spec_from_file_location("dk", os.path.join(ROOT, "tests", "regression", "disks", "cases.py"))
    dk = importlib.util.module_from_spec(spec); spec.loader.exec_module(dk)
    for f in dk.D64:
        names = dk.directory(f)
        check("menu" in names and "menu1" not in names and "ovlt" not in names and "ovl2" not in names, "%s: %s" % (os.path.basename(f), names))


@test("MENU-11", "ovl_town from the disk (as at the village entry): every zone equal to the module, ovl_cur = 1, $01 back to $36, < 11 s")
def menu_load(ctx):
    g = game(ctx); L = g.L
    g.poke(L["ovl_cur"], 0)
    g.cmd("bank ram")
    for a, b in zones(): g.fill(a, a + len(b) - 1, 0)
    g.cmd("bank cpu")
    c0 = g.last                                      # clock of the last stop (the game is stopped there)
    c = gcall(g, L["ovl_town"], tmax=180)
    bad = zones_ok(g)
    check(not bad, "zones %s differ from out/work/menu_zK.prg" % bad)
    check(g.b(L["ovl_cur"]) == 1, "ovl_cur %d" % g.b(L["ovl_cur"]))
    check(g.b(1) & 7 == 6, "$01 = %02x after the unpack" % g.b(1))
    t = (c - c0) / CPS
    print("      ovl_town from the disk: %.2f s" % t)
    check(t < 11.0, "ovl_town took %.2f s (> 11 s)" % t)


@test("MENU-13", "smith, alchemist and inn open from the module in RAM: no read of the file MENU, KERNAL and IRQ back after RUN/STOP")
def menu_open(ctx):
    g = game(ctx); L = g.L
    g.watch(L["ml_read"])
    for name, door in (("smith", SMITH_DOOR), ("alchemist", None), ("inn", INN_DOOR)):
        if door is None:
            from lib.play import find
            al = find(g, L["T_DALCH"])
            check(al, "no alchemist door on the map")
            door = (al[0][0], al[0][1] + 1)
        fire_to(g, *door); g.frames(3, tmax=60)
        check(not g.in_game(), "%s: the screen did not open" % name)
        check(g.b(1) & 7 == 5, "%s: $01 = %02x in the menu (expected $35)" % (name, g.b(1)))
        g.run_stop(); g.frames(3)
        check(g.in_game(), "%s: RUN/STOP does not close the screen" % name)
        check(g.b(1) & 7 == 6 and g.b(0xd01a) & 1, "%s: after the exit $01 = %02x, raster IRQ %d" % (name, g.b(1), g.b(0xd01a) & 1))
    n = g.hits.get(L["ml_read"], 0)
    g.unwatch()
    check(n == 0, "file MENU read %d times" % n)
