"""Potion healing by PG level (15/11, TODO J4): the routine pot_heal (combat.asm) must give heal + A x level with the dungeon
column `heal` of data/items/items.tsv up to MAXLEVEL (20) and with the column `heal_abyss` above it (the Abyss, level = floor).
Only GAME is loaded in VICE (no game started), the real routine is called with c_lvl written to memory and the result is
read from mu0/mu1 (16 bit), then compared with the formula computed in Python from the table. Y must be preserved."""
import os, re, sys
from lib.c64 import Vice, labels, OUT, ROOT
from c64test import test, check

sys.path[:0] = [os.path.join(ROOT, "tools", "build")]
import items_db as I  # noqa: E402

LEVELS = (1, 8, 15, 20, 21, 40, 200, 255)
MAXLEVEL = 20


def setup(ctx):
    v = ctx["v"] = Vice()
    v.load(os.path.join(OUT, "game.prg"))
    ctx["L"] = labels("game")


def teardown(ctx):
    if "v" in ctx: ctx["v"].close()


def formula(expr, lvl):
    m = re.fullmatch(r"(?:(\d+)\*L\+)?(\d+)", str(expr).replace(" ", ""))
    return int(m.group(1) or 0) * lvl + int(m.group(2))


@test("POT-10", "pot_heal: dungeon column up to level 20, Abyss column (heal_abyss) from level 21, all potions, Y kept")
def pot_heal(ctx):
    v, L = ctx["v"], ctx["L"]
    pots = [r for r in I.load() if r["type"] == "potion"]
    check(len(pots) == 3, "expected 3 potions in items.tsv, found %d" % len(pots))
    bad = []
    for n, r in enumerate(pots):
        pid = L["I_POTR"] + n
        for lvl in LEVELS:
            v.poke(L["c_lvl"], lvl)
            col = r["heal"] if lvl <= MAXLEVEL else r["heal_abyss"]
            want = formula(col, lvl)
            v.call(L["pot_heal"], regs="y=%02x" % pid)
            out = v.regs()
            got = v.b(L["mu0"]) + 256 * v.b(L["mu1"])
            if got != want or out["y"] != pid or out["a"] != (want & 255):
                bad.append("%s L%d: %d (expected %d), y=%02x a=%02x" % (r["id"], lvl, got, want, out["y"], out["a"]))
    check(not bad, "; ".join(bad))
