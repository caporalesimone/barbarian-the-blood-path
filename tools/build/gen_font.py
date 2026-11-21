#!/usr/bin/env python3
"""Genera out/work/gfx/uifont.bin (UIF_N x 8 byte): charset UI 'Reliquia 05 cero'.
  0..63   glifi normali (lettere/cifre dal font Reliquia, punteggiatura mancante dalla ROM); gli altri programmi (BARBARIAN,
          START, LORE, HELP) usano solo questi 64
  28,30,31,59,60,0 = cornici (H,V,TL,TR,BL,BR); 34,35,36 = martello, scudo, ampolla
  64..79  (21/11 sera, richiesta del committente) icone tutte di seguito: 64 spazio invertito (cursore dei campi del LOBBY), 65
          chiave, 66 moneta, 67 freccia, 68 pozione, 69 pergamena, 70 spada, 71 armatura, 72 anello, 73 teschio, 74 boccale,
          75 spunta, 76 cintura, 77 separatore, 78 barra di scorrimento, 79 zaino. Prima stavano sparse fra 91 e 107 nel blocco
          "inverso" 64..127 (le lettere invertite non le usava nessuno, le barre 124-126 nemmeno dall'11/11): il font finisce a
          UIF_N e i 384 byte dopo (codici 80..127, mai mostrati) sono RAM libera per i dati (src/game.asm gd_font).
Caricato a $B800 da copy_gfx (VIC bank 2, D018=$DE con schermo a $B400)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "font"))   # (11/11) sorgenti del font in tools/font/
import reliquia as R

from vicemon import ROMS_C64  # noqa: E402  (Lab64: cartella delle ROM del C64)
rom = open(os.path.join(ROMS_C64, "chargen-901225-01.bin"), "rb").read()
var = dict(R.V)["05 cero"]
font = R.build(var)

def rom_glyph(code):
    return list(rom[code * 8:code * 8 + 8])

def g2b(g):
    return [sum(b << (7 - i) for i, b in enumerate(row)) for row in g]

cs = [rom_glyph(c) for c in range(64)]          # base: ROM (punteggiatura, simboli)
for c in range(1, 27):
    cs[c] = g2b(font[chr(64 + c)])
for ch in "0123456789 !',-./:?":
    code = ord(ch) if ch != "'" else 39
    if ch in font:
        cs[code] = g2b(font[ch])
cs[32] = [0] * 8
# glifi cornice (codici 28,30,31,59,60,0): H V TL TR BL BR
BOX = {28: [0,0,0,0xFF,0xFF,0,0,0], 30: [0x18]*8,
       31: [0,0,0,0x1F,0x1F,0x18,0x18,0x18], 59: [0,0,0,0xF8,0xF8,0x18,0x18,0x18],
       60: [0x18,0x18,0x18,0x1F,0x1F,0,0,0], 0: [0x18,0x18,0x18,0xF8,0xF8,0,0,0]}
for c, g in BOX.items():
    cs[c] = g
# (21/11 sera) icone di seguito da 64: niente blocco invertito, niente barre di avanzamento (tolte l'11/11 sera)
UIF_N = 80
full = cs + [[0] * 8 for _ in range(UIF_N - 64)]
ICON = {
    64: [0xFF] * 8,                                          # spazio invertito: cursore dei campi nome e seme (LOBBY)
    65: [0x38, 0x44, 0x44, 0x38, 0x10, 0x18, 0x10, 0x18],   # chiave
    66: [0x3C, 0x66, 0xDB, 0xDF, 0xDF, 0xDB, 0x66, 0x3C],   # moneta con la C incisa (08/11, scelta del committente)
    67: [0x00, 0x08, 0x0C, 0x7E, 0x0C, 0x08, 0x00, 0x00],   # freccia a destra (15/11, schermata C: "73 -> 81")
    68: [0x18, 0x18, 0x3C, 0x7E, 0xFF, 0xFF, 0x7E, 0x3C],   # pozione
    69: [0x3C, 0x7E, 0x42, 0x5A, 0x42, 0x5A, 0x7E, 0x3C],   # pergamena
    34: [0x7E, 0xFF, 0xFF, 0x7E, 0x18, 0x18, 0x18, 0x18],   # martello (fabbro)
    35: [0x7E, 0xFF, 0xE7, 0xE7, 0xFF, 0x7E, 0x3C, 0x18],   # scudo (categoria scudi)
    36: [0x3C, 0x18, 0x18, 0x3C, 0x7E, 0xFF, 0xFF, 0x7E],   # ampolla (alchimista)
    70: [0x03, 0x07, 0x0E, 0x5C, 0x38, 0x30, 0x48, 0x80],   # spada
    71: [0x66, 0xFF, 0xFF, 0x7E, 0x7E, 0x66, 0x7E, 0x3C],   # armatura
    72: [0x18, 0x3C, 0x42, 0x81, 0x81, 0x81, 0x42, 0x3C],   # anello
    73: [0x3C, 0x7E, 0xDB, 0xDB, 0x7E, 0x3C, 0x3C, 0x24],   # teschio (09/11, schermata di morte)
    74: [0x6C, 0xFC, 0x87, 0xA5, 0xA5, 0xA7, 0x84, 0xFC],   # boccale (09/11, titolo della locanda)
    75: [0x00, 0x01, 0x03, 0x06, 0x8C, 0xD8, 0x70, 0x20],   # spunta: oggetto indossato
    76: [0x00, 0x00, 0xFF, 0x81, 0xBD, 0x81, 0xFF, 0x00],   # cintura: posto della cintura
    77: [0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00],   # separatore sottile fra i blocchi di una lista
    78: [0x3C, 0x3C, 0x3C, 0x3C, 0x3C, 0x3C, 0x3C, 0x3C],   # cursore della barra di scorrimento (sulla cornice destra)
    79: [0x3C, 0x42, 0xFF, 0xC3, 0xDB, 0xC3, 0xFF, 0x7E],   # zaino: oggetto nello zaino
}
for c, g in ICON.items():
    full[c] = g
out = bytes(b for g in full for b in g)
assert len(out) == UIF_N * 8
open(os.path.join(ROOT, "out", "work", "gfx", "uifont.bin"), "wb").write(out)
print("ok uifont")
