"""Cheats for the tests (15/11, request of the project owner): the entry "cheats" of the game menu (RUN/STOP), only in builds
assembled with CHEATS=1 (debug and test builds; tools/build/asm.sh), src/game/cheats.asm. Five actions: god mode on/off,
level up (the normal level-up path), respec token, next level (stairs; boss level -> boss killed, back to the village;
village -> first level), next chapter (unlock + chap_travel, which saves). Everything through the real menus (RUN/STOP,
joystick, Fire) in one VICE session, tests in order (CHAIN). In a build without cheats (CHEATS=0, the release) the VICE
tests are SKIP and CHEAT-22 checks that the release assembly has no cheat code."""
import os, re, subprocess
from c64test import test, check, Skip
from lib.c64 import Game, ROOT, labels
from lib.play import new_game, U, D

CHAIN = True
CH = {"god": 0, "level": 1, "respec": 2, "next_level": 3, "next_chapter": 4}


def setup(ctx):
    if "cheat_menu" not in labels("game"):
        return                                       # release build (CHEATS=0): only CHEAT-22 runs
    g = ctx["g"] = Game()
    g.to_menu()
    new_game(g); g.frames(3)


def teardown(ctx):
    if "g" in ctx: ctx["g"].close()


def need(ctx):
    if "g" not in ctx: raise Skip("build without cheats (CHEATS=0)")
    return ctx["g"], ctx["g"].L


def text(g, x, y, n):
    """screen codes of the UI screen -> text (a-z, digits, space, ':', '>')"""
    out = ""
    for c in g.mem(g.L["SCR_A"] + 40 * y + x, n):
        out += chr(c + 96) if 1 <= c <= 26 else chr(c) if c in (32, 58, 62) or 48 <= c <= 57 else "?"
    return out


def open_cheats(g):
    """from the game: RUN/STOP (game menu), up = last entry ('cheats', wrap), Fire: the cheat menu"""
    g.run_stop(); g.frames(2)
    g.frames(1, joy=U); g.frames(1)
    g.press_fire(settle=2)


def cheat(g, what, leave=False):
    """one action of the cheat menu; leave=False: back in the game with RUN/STOP twice (cheat menu -> game menu -> game) and
    returns the message of row 23; leave=True (the action changes place): wait until the game runs again"""
    open_cheats(g)
    for _ in range(CH[what]): g.frames(1, joy=D); g.frames(1)
    g.press_fire(settle=2)
    msg = text(g, 1, 23, 20).strip()
    if leave:
        for _ in range(40):
            if g.in_game(): break
            g.frames(5, tmax=60)
        check(g.in_game(), "after '%s' the game does not resume" % what)
        g.frames(2)
        return ""
    g.run_stop(); g.frames(2)
    g.run_stop(); g.frames(2)
    check(g.in_game(), "RUN/STOP twice from the cheat menu does not go back to the game")
    return msg


def hero_saved(g, *names):
    """the values of the hero on disk (save-0N): wipe them in RAM and read the hero back (load_char, as PG-SAVE-01)"""
    L = g.L
    for n in names: g.poke(L[n], 0)
    g.call_keep(L["load_char"], tmax=60)
    return [g.b(L[n]) for n in names]


@test("CHEAT-10", "game menu: 4th entry 'cheats'; the cheat menu lists god mode (off), level up, respec token, next level, next chapter")
def menu(ctx):
    g, L = need(ctx)
    g.run_stop(); g.frames(2)
    check(text(g, 15, 14, 6) == "cheats", "game menu row 14: %r, expected 'cheats'" % text(g, 15, 14, 6))
    g.run_stop(); g.frames(2)
    open_cheats(g)
    got = [text(g, 13, 8 + 2 * i, 15).rstrip() for i in range(5)]
    exp = ["> god mode: off", "  level up", "  respec token", "  next level", "  next chapter"]
    check(got == exp, "cheat menu %s, expected %s" % (got, exp))
    check(text(g, 17, 4, 6) == "cheats", "title %r" % text(g, 17, 4, 6))
    g.run_stop(); g.frames(2)
    check(text(g, 15, 14, 6) == "cheats", "RUN/STOP from the cheat menu: not back in the game menu")
    g.run_stop(); g.frames(2)
    check(g.in_game(), "RUN/STOP from the game menu does not resume the game")


@test("CHEAT-11", "god mode on: no damage (hurt_player); god mode off: damage again")
def god(ctx):
    g, L = need(ctx)
    def hit():
        hp = g.w16(L["c_hp"])
        g.poke(L["cb_dl"], 5, 0); g.call_keep(L["hurt_player"])
        return hp - g.w16(L["c_hp"])
    open_cheats(g)
    g.press_fire(settle=2)
    check(text(g, 25, 8, 3) == "on ", "after Fire the entry shows %r, expected 'on'" % text(g, 25, 8, 3))
    g.run_stop(); g.frames(2); g.run_stop(); g.frames(2)
    check(g.b(L["godmode"]) == 1, "godmode = %d after 'on'" % g.b(L["godmode"]))
    check(hit() == 0, "god mode on: the hero lost hp")
    cheat(g, "god")
    check(g.b(L["godmode"]) == 0, "godmode = %d after 'off'" % g.b(L["godmode"]))
    check(hit() == 5, "god mode off: 5 damage not taken")
    g.call_keep(L["hp_full"])


@test("CHEAT-12", "level up: level + 1, xp = threshold of that level, stat points of pl_pts, hp max up and full; message 'level N'")
def level_up(ctx):
    g, L = need(ctx)
    lv, hpm = g.b(L["c_lvl"]), g.w16(L["hpmax"])
    p0 = g.call_keep(L["pts_avail"])["a"]
    msg = cheat(g, "level")
    lv1 = g.b(L["c_lvl"])
    check(lv1 == lv + 1, "level %d -> %d" % (lv, lv1))
    thr = g.b(L["xp_n0"] + lv - 1) + 256 * g.b(L["xp_n1"] + lv - 1) + 65536 * g.b(L["xp_n2"] + lv - 1)
    xp = g.w16(L["c_xp"]) + 65536 * g.b(L["c_xp"] + 2)
    check(xp == thr, "xp %d, expected the threshold %d of level %d" % (xp, thr, lv1))
    p1 = g.call_keep(L["pts_avail"])["a"]
    dp = g.b(L["pl_pts"] + lv1) - g.b(L["pl_pts"] + lv)
    check(p1 - p0 == dp, "stat points %d -> %d, pl_pts gives +%d" % (p0, p1, dp))
    check(g.w16(L["hpmax"]) > hpm and g.w16(L["c_hp"]) == g.w16(L["hpmax"]),
          "hp max %d -> %d, hp %d" % (hpm, g.w16(L["hpmax"]), g.w16(L["c_hp"])))
    check(msg == "level %d" % lv1, "message %r" % msg)


@test("CHEAT-13", "respec token: +1, message 'tokens N'")
def respec(ctx):
    g, L = need(ctx)
    r = g.b(L["c_resp"])
    msg = cheat(g, "respec")
    check(g.b(L["c_resp"]) == r + 1, "tokens %d -> %d" % (r, g.b(L["c_resp"])))
    check(msg == "tokens %d" % (r + 1), "message %r" % msg)


@test("CHEAT-14", "level up at the maximum level (PL_MAXLVL): nothing changes, message 'limit reached'")
def level_max(ctx):
    g, L = need(ctx)
    lv = g.b(L["c_lvl"])
    g.poke(L["c_lvl"], L["PL_MAXLVL"])
    xp = g.mem(L["c_xp"], 3)
    msg = cheat(g, "level")
    check(g.b(L["c_lvl"]) == L["PL_MAXLVL"] and g.mem(L["c_xp"], 3) == xp, "level or xp changed at the maximum level")
    check(msg == "limit reached", "message %r" % msg)
    g.poke(L["c_lvl"], lv)


@test("CHEAT-15", "next level in the village: the first level of the chapter (as the crypt)")
def village_down(ctx):
    g, L = need(ctx)
    cheat(g, "next_level", leave=True)
    check(g.b(L["cur_level"]) == 1, "level %d, expected 1" % g.b(L["cur_level"]))


@test("CHEAT-16", "next level in a level of the chapter: the next level (as the stairs down)")
def stairs(ctx):
    g, L = need(ctx)
    cheat(g, "next_level", leave=True)
    check(g.b(L["cur_level"]) == 2, "level %d, expected 2" % g.b(L["cur_level"]))


@test("CHEAT-17", "next level on level 4 -> boss level 5; there: boss killed (c_unl = 2, exit open), back to village 1 at the crypt")
def boss(ctx):
    g, L = need(ctx)
    g.call_keep(L["change_level"], regs="a=04,x=00", tmax=150); g.frames(3)
    cheat(g, "next_level", leave=True)
    check(g.b(L["cur_level"]) == 5, "level %d, expected the boss level 5" % g.b(L["cur_level"]))
    check(g.b(L["c_unl"]) == 1, "c_unl %d before the boss" % g.b(L["c_unl"]))
    cheat(g, "next_level", leave=True)
    check(g.b(L["cur_level"]) == 0 and g.b(L["c_chap"]) == 1, "level %d chapter %d, expected village 1"
          % (g.b(L["cur_level"]), g.b(L["c_chap"])))
    check(g.b(L["c_unl"]) == 2, "c_unl %d, expected 2 (exit of the village open: c_unl > c_chap)" % g.b(L["c_unl"]))
    tx, ty = g.ptile()
    check(any(g.tile(tx + dx, ty + dy) == L["T_TSTAIRS"] for dx in (-1, 0, 1) for dy in (-2, -1, 0, 1)),
          "hero at %d,%d, not at the crypt" % (tx, ty))


@test("CHEAT-18", "next chapter from a level (village 1 -> level 1 -> village 2): unlocked, saved in village 2, no portal back")
def chapter_from_level(ctx):
    g, L = need(ctx)
    cheat(g, "next_level", leave=True)
    check(g.b(L["cur_level"]) == 1, "level %d, expected 1" % g.b(L["cur_level"]))
    cheat(g, "next_chapter", leave=True)
    got = [g.b(L[n]) for n in ("c_chap", "cur_level", "pend_lvl", "c_unl")]
    check(got == [2, 0, 0, 2], "chapter, level, pend_lvl, c_unl %s, expected [2, 0, 0, 2]" % got)
    check(hero_saved(g, "c_chap", "c_loc", "c_unl") == [2, 0, 2], "hero on disk not in village 2")


@test("CHEAT-19", "next chapter in a village (village 2 -> 3, then 4): c_unl follows, hero saved there")
def chapter(ctx):
    g, L = need(ctx)
    for c in (3, 4):
        cheat(g, "next_chapter", leave=True)
        got = [g.b(L["c_chap"]), g.b(L["cur_level"]), g.b(L["c_unl"])]
        check(got == [c, 0, c], "chapter, level, c_unl %s, expected [%d, 0, %d]" % (got, c, c))
    check(hero_saved(g, "c_chap", "c_loc") == [4, 0], "hero on disk not in village 4")


@test("CHEAT-20", "next level in the throne room (level 20): as the final boss killed (c_won, c_unl 5, respec gift), village 4")
def throne(ctx):
    g, L = need(ctx)
    g.call_keep(L["change_level"], regs="a=14,x=00", tmax=150); g.frames(3)
    r = g.b(L["c_resp"])
    cheat(g, "next_level", leave=True)
    got = [g.b(L[n]) for n in ("cur_level", "c_chap", "c_unl", "c_won")]
    check(got == [0, 4, 5, 1], "level, chapter, c_unl, c_won %s, expected [0, 4, 5, 1]" % got)
    check(g.b(L["c_resp"]) == r + L["RESP_FINAL"], "respec tokens %d -> %d" % (r, g.b(L["c_resp"])))


@test("CHEAT-21", "village 5 (last): next chapter and next level do nothing, message 'limit reached'")
def limits(ctx):
    g, L = need(ctx)
    cheat(g, "next_chapter", leave=True)
    check(g.b(L["c_chap"]) == 5, "chapter %d, expected 5" % g.b(L["c_chap"]))
    for what in ("next_chapter", "next_level"):
        msg = cheat(g, what)
        got = [g.b(L["c_chap"]), g.b(L["cur_level"])]
        check(got == [5, 0], "%s in village 5: chapter, level %s" % (what, got))
        check(msg == "limit reached", "%s: message %r" % (what, msg))


@test("CHEAT-22", "GAME assembled with the release flags (tools/build/asm.sh release-game): no cheat code")
def release(ctx):
    t = subprocess.run([os.path.join(ROOT, "tools", "build", "asm.sh"), "release-game"], cwd=ROOT, capture_output=True, text=True)
    check(t.returncode == 0, "release-game: " + ((t.stdout + t.stderr).strip().splitlines() or ["exit %d" % t.returncode])[-1])
    lbl = open(os.path.join(ROOT, "out", "tmp", "release_game.lbl")).read()
    sym = dict(re.findall(r"^(\w+)\s*=\s*(\S+)", lbl, re.M))
    bad = [n for n in ("cheat_menu", "mod_cheats", "gm3", "ct_god") if n in sym]
    check(not bad, "release assembly has the labels %s" % bad)
    prg = open(os.path.join(ROOT, "out", "tmp", "release_game.prg"), "rb").read()
    check(bytes([3, 8, 5, 1, 20, 19, 0]) not in prg, "the text 'cheats' is in the release GAME")
