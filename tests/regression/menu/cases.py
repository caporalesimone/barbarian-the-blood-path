"""Menu regression tests: the "new barbarian" screen typed with real keys (11/11, from tools/nametest.py, removed;
PG-NEW-10 in regression/saves covers the field logic: here the full 12-character name, WASD as letters, the result).
The keys are written at the exit of read_input (the menu reads them through ui_input -> read_input, like the game);
the key matrix comes from the menu's own table (keymap: index = row * 8 + bit, value = character code)."""
from lib.c64 import Game, addr_after, listing
from lib.runner import test, check

NAME = "black thorne"                                    # project rule: 12 characters with a space
STUB = 0x0340


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    M = g.M
    km = g.mem(M["keymap"], 64)
    ctx["key"] = {c: (i // 8, 1 << (i % 8)) for i, c in enumerate(km) if c}
    ctx["ret"] = STUB + 3


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def code(ch):
    """character -> code written by the menu: letters a..z = 1..26, space and digits = their screen code"""
    return ord(ch) - 96 if "a" <= ch <= "z" else ord(ch)


def start_entry(ctx):
    """jsr name_entry from a stub; frames() stops early when it returns (stub+3)"""
    g, M = ctx["g"], ctx["g"].M
    g.unwatch(); g.release_input()
    g.poke(STUB, 0x20, M["name_entry"] & 255, M["name_entry"] >> 8, 0xea)
    g.pc(STUB)
    g.frames(3)
    g.watch(until=(ctx["ret"],))


def type_text(ctx, text):
    g = ctx["g"]
    for ch in text:
        r, m = ctx["key"][code(ch)]
        g.frames(1, keys={r: m}); g.frames(1)


def key(ctx, row, mask):
    ctx["g"].frames(1, keys={row: mask}); ctx["g"].frames(1)


@test("PG-NEW-11", "new barbarian typed with keys: DEL, WASD as letters, ENTER to seed, ENTER to start, fire = start")
def name_typed(ctx):
    g, M = ctx["g"], ctx["g"].M
    start_entry(ctx)
    check(g.b(M["nfield"]) == 0 and g.b(M["nedit"]) == 1, "the screen does not start on the name field")
    type_text(ctx, "blackx")
    key(ctx, 0, 0x01)                                       # DEL: removes the x
    type_text(ctx, NAME[5:] + "zz")                         # beyond 12 characters: ignored
    nb = g.mem(M["namebuf"], 12)
    check(nb == [code(c) if c != " " else 0x20 for c in NAME], "name %s" % nb)
    check(g.b(M["nfield"]) == 0, "a key moved the cursor while typing the name (nfield %d)" % g.b(M["nfield"]))
    key(ctx, 0, 0x02)                                       # ENTER: name accepted -> seed
    check(g.b(M["nfield"]) == 1, "ENTER does not move to the seed (nfield %d)" % g.b(M["nfield"]))
    type_text(ctx, "wasd0129")                              # W/A/S/D are letters here; 0 is refused; 6 characters
    sb = g.mem(M["seedbuf"], 6)
    want = [code(c) + 9 for c in "wasd"] + [1, 2]
    check(sb == want and g.b(M["slen"]) == 6, "seed %s len %d (expected %s)" % (sb, g.b(M["slen"]), want))
    check(g.b(M["nfield"]) == 1, "W/A/S/D moved the cursor while typing the seed")
    key(ctx, 0, 0x02)                                       # ENTER: seed accepted -> cursor on start
    check(g.b(M["nfield"]) == 2 and g.b(M["nedit"]) == 0, "nfield %d nedit %d (expected 2, 0)" % (g.b(M["nfield"]), g.b(M["nedit"])))
    g.frames(1, fire=True)
    if g.stopped is None: g.frames(3)
    check(g.stopped == ctx["ret"], "fire on start does not leave the screen")
    check(g.regs()["a"] == 1, "name_entry returns A=%d (expected 1: start)" % g.regs()["a"])
    g.unwatch()


@test("PG-NEW-12", "new barbarian: empty name refused by ENTER, RUN/STOP leaves with A=0")
def name_exit(ctx):
    g, M = ctx["g"], ctx["g"].M
    start_entry(ctx)
    key(ctx, 0, 0x02)                                       # ENTER on an empty name: stays on the name
    check(g.b(M["nfield"]) == 0, "an empty name was accepted")
    g.frames(1, keys={7: 0x80})
    if g.stopped is None: g.frames(3)
    check(g.stopped == ctx["ret"], "RUN/STOP does not leave the screen")
    check(g.regs()["a"] == 0, "name_entry returns A=%d (expected 0)" % g.regs()["a"])
    g.unwatch()
