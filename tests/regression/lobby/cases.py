"""Start menu renamed LOBBY (11/11, TODO D13): file `lobby` on the disks (5-character name, set_name), src/lobby.asm,
loaded at $C000 by START and by GAME (load_menu) when the player goes back to the start menu. The name MENU is kept for
the village menus module."""
import os
from c64test import test, check
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


@test("LOBBY-11", "GAME load_menu reads LOBBY from the disk into $C000: same bytes as out/work/lobby.prg")
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
        check(g.mem(0xC000, len(lp)) == list(lp), "RAM at $C000 differs from out/work/lobby.prg after load_menu")
        check(g.b(L["ovl_cur"]) == 0, "ovl_cur not cleared (LOBBY covers OVLT)")
    finally:
        g.close()


@test("LOBBY-12", "main menu plays Demon's Eye (file SND_MENU in the buffer of the place, player running); leaving it fades to silence, then music_town loads the village song")
def lobby_music(ctx):
    """15/11, TODO E3: the main menu starts Demon's Eye with the game's player (ui_menu, after menu_draw -> mus_place, 16/11), frames run from ui_input;
    lb_leave (exit to the game) fades out before the village song replaces the buffer."""
    import songs
    from lib.c64 import Game
    g = Game()
    try:
        L, M = g.L, g.M
        game = songs.game_files(songs.PLAYLIST)
        menu = game.index(songs.PLAYLIST["title"])
        read = lambda n: open(os.path.join(OUT, "snd", n + ".bin"), "rb").read()
        eye, tavern = read(songs.PLAYLIST["title"]), read(songs.PLAYLIST["town"][0])
        g.to_menu()                                          # stopped after scan_slots in ui_menu: the page is not drawn yet
        check(g.b(L["mus_want"]) == 0 and g.b(L["snd_cur"]) != menu + 1,
              "music already requested before the page is drawn (16/11: it starts when the list is on screen)")
        g.frames(1, tmax=60)                                 # runs to the first input read: page drawn, then the song is requested
        check(g.b(L["snd_cur"]) == menu + 1, "buffer of the place holds song %d, not SND_MENU %d" % (g.b(L["snd_cur"]) - 1, menu))
        check(g.mem(L["SND_LBUF"], len(eye)) == list(eye), "SND_LBUF differs from %s.bin" % songs.PLAYLIST["title"])
        check(g.b(L["mus_want"]) == 1, "music_request(MUS_LVL) not made (mus_want %d)" % g.b(L["mus_want"]))
        g.frames(40)                                         # the menu loop (ui_input -> sfx_update -> music_update)
        check(g.b(L["mus_trk"]) == 1 and g.b(L["sp_on"]), "player not running in the menu (mus_trk %d, sp_on %d)" % (g.b(L["mus_trk"]), g.b(L["sp_on"])))
        check(g.b(L["snd_cur"]) == menu + 1, "buffer changed while the menu was running")
        g.call(M["lb_leave"], tmax=60)                       # exit to the game: blocking fade to silence
        check(g.b(L["mus_trk"]) == 0 and g.b(L["mus_fo"]) == 0 and g.b(L["mus_want"]) == 0,
              "after lb_leave: mus_trk %d, mus_fo %d, mus_want %d" % (g.b(L["mus_trk"]), g.b(L["mus_fo"]), g.b(L["mus_want"])))
        g.poke(L["c_chap"], 1)                               # (no hero loaded here: chapter 1)
        g.call(L["music_town"], tmax=60)                    # as load_location does, after the fade
        check(g.b(L["snd_cur"]) == game.index(songs.PLAYLIST["town"][0]) + 1, "village song not in the buffer after music_town")
        check(g.mem(L["SND_LBUF"], len(tavern)) == list(tavern), "SND_LBUF differs from the village song")
    finally:
        g.close()
