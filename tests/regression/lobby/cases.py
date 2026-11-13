"""Start menu renamed LOBBY (11/11, TODO D13): file `lobby` on the disks (5-character name, set_name), src/lobby.asm,
loaded at $C000 by START and by GAME (load_menu) when the player goes back to the start menu. The name MENU is kept for
the village menus module."""
import os
from lib.runner import test, check
from lib.c64 import ROOT, OUT


@test("LOBBY-10", "both disks have the file LOBBY (start menu) and START loads it by the 5-character name")
def lobby_disk(ctx):
    import importlib.util
    spec = importlib.util.spec_from_file_location("dk", os.path.join(ROOT, "tests", "regression", "disks", "cases.py"))
    dk = importlib.util.module_from_spec(spec); spec.loader.exec_module(dk)
    for p in dk.D64:
        names = dk.directory(p)
        check("lobby" in names, "%s: no lobby in %s" % (os.path.basename(p), names))
    lst = open(os.path.join(OUT, "start.lst")).read()
    check('"lobby"' in lst.lower(), "START does not name the file lobby")


@test("LOBBY-11", "GAME load_menu reads LOBBY from the disk into $C000: same bytes as out/lobby.prg")
def lobby_load(ctx):
    from lib.c64 import Game
    from lib.play import new_game
    g = Game()
    try:
        g.to_menu(); new_game(g); g.frames(3)
        L = g.L
        lp = open(os.path.join(OUT, "lobby.prg"), "rb").read()[2:]
        g.poke(0xC000, *([0] * 64))
        g.call(L["load_menu"], tmax=120)
        check(g.mem(0xC000, len(lp)) == list(lp), "RAM at $C000 differs from out/lobby.prg after load_menu")
        check(g.b(L["ovl_cur"]) == 0, "ovl_cur not cleared (LOBBY covers OVLT)")
    finally:
        g.close()
