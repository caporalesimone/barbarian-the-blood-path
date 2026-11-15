#!/usr/bin/env python3
"""Genera out/work/gfx/uifont.bin (1024 byte): charset UI 'Reliquia 05 cero', codici schermo 0..127.
  0..63   glifi normali (lettere/cifre dal font Reliquia, punteggiatura mancante dalla ROM)
  28,30,31,59,60,0 = cornici (H,V,TL,TR,BL,BR)
  91..95 = icone chiave/oro (una moneta, 08/11)/freccia (93, 15/11)/pozione/pergamena
  64..127 versioni invertite (inv = $40 in ui_putc); 124..126 = barre di avanzamento
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
full = cs + [[b ^ 0xFF for b in g] for g in cs]  # 64..127 = inverso
# barre di avanzamento (stessi glifi ROM usati prima: $65 $61 $e7)
full[0x7c] = rom_glyph(0x65)
full[0x7d] = rom_glyph(0x61)
full[0x7e] = rom_glyph(0xe7)
# icone (codici 91..95, nel blocco 'inverso' non usato dalla UI): chiave, moneta (08/11: prima un mucchio di 2 car.), pozione, pergamena
ICON = {
    91: [0x38, 0x44, 0x44, 0x38, 0x10, 0x18, 0x10, 0x18],
    92: [0x3C, 0x66, 0xDB, 0xDF, 0xDF, 0xDB, 0x66, 0x3C],   # moneta con la C incisa (08/11, scelta del committente)
    94: [0x18, 0x18, 0x3C, 0x7E, 0xFF, 0xFF, 0x7E, 0x3C],
    95: [0x3C, 0x7E, 0x42, 0x5A, 0x42, 0x5A, 0x7E, 0x3C],
}
ICON.update({
    34: [0x7E, 0xFF, 0xFF, 0x7E, 0x18, 0x18, 0x18, 0x18],   # martello (fabbro)
    35: [0x7E, 0xFF, 0xE7, 0xE7, 0xFF, 0x7E, 0x3C, 0x18],   # scudo (categoria scudi; era anche l'icona dell'armaiolo, tolto il 09/11)
    36: [0x3C, 0x18, 0x18, 0x3C, 0x7E, 0xFF, 0xFF, 0x7E],   # ampolla (alchimista)
    # equipaggiamento (08/11, casa): codici 97-100 del blocco inverso, non usati dalla UI (le linguette invertite usano
    # solo lettere, spazio, cifre e '/'); lo scudo e' il 35
    97: [0x03, 0x07, 0x0E, 0x5C, 0x38, 0x30, 0x48, 0x80],   # spada
    98: [0x66, 0xFF, 0xFF, 0x7E, 0x7E, 0x66, 0x7E, 0x3C],   # armatura
    99: [0x18, 0x3C, 0x42, 0x81, 0x81, 0x81, 0x42, 0x3C],   # anello
    100: [0x3C, 0x7E, 0xDB, 0xDB, 0x7E, 0x3C, 0x3C, 0x24],  # teschio (09/11, schermata di morte)
    101: [0x6C, 0xFC, 0x87, 0xA5, 0xA5, 0xA7, 0x84, 0xFC],  # boccale (09/11, titolo della locanda)
    93: [0x00, 0x08, 0x0C, 0x7E, 0x0C, 0x08, 0x00, 0x00],   # freccia a destra (15/11, schermata C: "73 -> 81")
})
for c, g in ICON.items():
    full[c] = g
out = bytes(b for g in full for b in g)
assert len(out) == 1024
open(os.path.join(ROOT, "out", "work", "gfx", "uifont.bin"), "wb").write(out)
print("ok uifont")
