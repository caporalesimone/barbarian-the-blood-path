"""Decorations of the generated levels (19/11, owner's request; docs/wiki/dungeon.md "Arredi dei piani"): the level code of
the theme files GFX1, 3, 5, 7 (src/game/ovl_decor.asm, OVJ_DECOR) puts themed furniture on the floor right after the
generation: solid pieces only where they cannot cut a passage, walkable pieces anywhere. One VICE session (CHAIN).
Screenshots: out/work/decor/level<n>.png (to look at, not compared)."""
import collections, os
from c64test import test, check
from lib.c64 import Game, ROOT
from lib.play import new_game
import gen_gfx as GG, decor_gfx as DG

CHAIN = True
SHOTS = os.path.join(ROOT, "out", "work", "decor")
SEEDS = ([10, 23, 24, 10, 23, 24], [1, 2, 3, 4, 5, 6], [35, 0, 17, 9, 28, 3])
LEVELS = ((2, 1), (7, 2), (12, 3), (17, 4))           # (level, chapter)
T = GG.TID
DEC = {T[n] for n in ("FREE9", "FREE10", "FREE11", "GRASSA", "GRASSB")}


def setup(ctx):
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)
    g.poke(g.L["godmode"], 1)
    os.makedirs(SHOTS, exist_ok=True)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def enter(g, lv, ch, seed):
    L = g.L
    g.poke(L["c_seedt"], *seed)
    g.poke(L["c_chap"], ch); g.poke(L["c_unl"], 4)
    g.call_keep(L["change_level"], regs="a=%02x,x=00" % lv, tmax=150); g.frames(2)
    return list(g.mem(L["MAP"], 2304))


def walk_set(g):
    sol = g.mem(g.L["solidtab"], 48)
    return lambda t: t < 48 and not sol[t] & 1


@test("DECOR-10", "levels 2, 7, 12, 17 (chapters 1-4), 3 seeds: solid and walkable furniture on every level; every walkable tile "
      "still reachable from the stairs; no monster on a solid tile; the same map when the level is entered again; chapter 4: "
      "the furniture is mirrored like the citadel (but where the mirrored tile is a stair or a chest)")
def decor(ctx):
    g = ctx["g"]; L = g.L
    for seed in SEEDS:
        for lv, ch in LEVELS:
            m = enter(g, lv, ch, seed)
            ok = walk_set(g)
            c = collections.Counter(m)
            nsol = sum(c[T[n]] for n in ("FREE9", "FREE10", "FREE11"))
            nwk = c[T["GRASSA"]] + c[T["GRASSB"]]
            check(nsol >= 3 and nwk >= 5, "level %d seed %s: %d solid, %d walkable pieces" % (lv, seed, nsol, nwk))
            st = next(i for i, t in enumerate(m) if t == T["STAIRSU"])
            seen, todo = {st}, [st]
            while todo:
                i = todo.pop()
                for j in (i - 1, i + 1, i - 48, i + 48):
                    if 0 <= j < 2304 and j not in seen and ok(m[j]):
                        seen.add(j); todo.append(j)
            lost = [(i % 48, i // 48) for i in range(2304) if ok(m[i]) and i not in seen]
            check(not lost, "level %d seed %s: walkable tiles cut off by the furniture: %s" % (lv, seed, lost[:8]))
            bad = [k for k in range(g.b(L["lb_cnt"])) if g.b(L["malive"] + k) and not ok(m[g.b(L["miy"] + k) * 48 + g.b(L["mix"] + k)])]
            check(not bad, "level %d seed %s: monsters on a solid tile: %s" % (lv, seed, bad))
            if ch in DG.MIRROR:
                asym = [(x, y) for y in range(48) for x in range(24) if (m[y * 48 + x] in DEC or m[y * 48 + 47 - x] in DEC)
                        and m[y * 48 + x] != m[y * 48 + 47 - x]
                        and not ({m[y * 48 + x], m[y * 48 + 47 - x]} & {T["STAIRSU"], T["STAIRSD"], T["CHEST"], T["PORTAL"]})]
                check(not asym, "level %d seed %s: furniture not mirrored at %s" % (lv, seed, asym[:6]))
            if seed is SEEDS[0]:
                g.screenshot(os.path.join(SHOTS, "level%d.png" % lv))
        m2 = enter(g, LEVELS[0][0] + 1, 1, seed)
        m3 = enter(g, LEVELS[0][0], 1, seed)
        m1 = enter(g, LEVELS[0][0], 1, seed)
        check(m3 == m1, "seed %s: level %d differs when entered again" % (seed, LEVELS[0][0]))
