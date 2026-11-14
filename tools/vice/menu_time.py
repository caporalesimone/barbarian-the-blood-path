#!/usr/bin/env python3
"""Cronometro del modulo MENU (11/11, docs/prestazioni.md sezione "Menu del villaggio"): tempi emulati (VICE, 1541
emulata, contatore di cicli) di
  1) ovl_town dal disco (quello che succede all'ingresso nel villaggio se il modulo non c'e': dopo l'avvio o il LOBBY);
  2) apertura di fabbro, alchimista e locanda con il modulo in memoria (dal Fire alla schermata disegnata).
Uso: python3 tools/vice/menu_time.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tests"))
from lib.c64 import Game  # noqa: E402
from lib.play import new_game, find, INN_DOOR, SMITH_DOOR  # noqa: E402
CPS = 985248

g = Game()
try:
    g.to_menu(); new_game(g); g.frames(3)
    L = g.L
    pc = g.regs()["pc"]
    g.poke(L["ovl_cur"], 0)
    c0 = g.last
    c = g.call(L["ovl_town"], tmax=180)
    print("1) ovl_town from the disk (file MENU, %d B): %.2f s" % (os.path.getsize(os.path.join(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "out", "work", "menu.prg")) - 2, (c - c0) / CPS))
    g.poke(0x0350, 0x58, 0x4c, pc & 255, pc >> 8); g.pc(0x0350); g.at_input = False
    al = find(g, L["T_DALCH"])[0]
    for name, door in (("smith", SMITH_DOOR), ("alchemist", (al[0], al[1] + 1)), ("inn", INN_DOOR)):
        g.teleport(*door); g.frames(3)
        t0 = g.last
        g.frames(1, fire=True)
        n = 0
        while g.in_game() and n < 50:
            g.frames(1); n += 1
        g.frames(2)
        print("2) %-10s open: %.2f s" % (name, (g.last - t0) / CPS))
        g.run_stop(); g.frames(3)
finally:
    g.close()
