#!/usr/bin/env python3
"""Font TrueType della pagina del viewer ricavato dal generatore di caratteri del C64 (14/11). Copyright (c) 2026 - Simone Caporale
Gira solo nello stage viewer-font di toolchain/docker/Dockerfile (python3-fonttools non entra nell'immagine finale).
  c64font.py <chargen 4096 byte> <uscita.ttf>
Usa il secondo set del chargen (minuscole e maiuscole): ogni carattere 8x8 diventa un glifo di quadrati (128 unita' per pixel,
em = 1024; la riga 7 e' sotto la linea di base, come le gambe di g, p, y sul C64). Codici dello schermo -> ASCII:
  1-26 a-z, 65-90 A-Z, 32-63 come l'ASCII, 0 @, 27 [, 29 ], 30 ^ (freccia su), 31 _ (freccia a sinistra), 28 sterlina."""
import sys
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

PX, EM = 128, 1024


def glyph(rows):
    pen = TTGlyphPen(None)
    for y, bits in enumerate(rows):
        x = 0
        while x < 8:
            if bits & (0x80 >> x):
                x0 = x
                while x < 8 and bits & (0x80 >> x):
                    x += 1
                top, bot = (7 - y) * PX, (6 - y) * PX          # riga 0 in alto; la riga 7 va da -128 a 0
                pen.moveTo((x0 * PX, bot)); pen.lineTo((x0 * PX, top)); pen.lineTo((x * PX, top)); pen.lineTo((x * PX, bot)); pen.closePath()
            else:
                x += 1
    return pen.glyph()


def main(src, dst):
    rom = open(src, "rb").read()
    if len(rom) != 4096:
        sys.exit("chargen: servono 4096 byte")
    cs = rom[2048:]                                           # set 2: minuscole/maiuscole
    chars = {}
    for code in range(128):
        if 1 <= code <= 26:
            ch = chr(ord("a") + code - 1)
        elif 65 <= code <= 90:
            ch = chr(code)
        elif 32 <= code <= 63:
            ch = chr(code)
        else:
            ch = {0: "@", 27: "[", 28: "£", 29: "]", 30: "^", 31: "_"}.get(code)
        if ch:
            chars[ch] = cs[code * 8: code * 8 + 8]
    # simboli che il C64 non ha: si prendono in prestito forme vicine
    extra = {"{": "(", "}": ")", "|": "!", "`": "'", "~": "-", "\\": "/"}
    for k, v in extra.items():
        chars.setdefault(k, chars[v])
    # lettere accentate dell'italiano: la lettera senza accento (il C64 non le ha)
    for k, v in {"à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u", "È": "E", "À": "A"}.items():
        chars[k] = chars[v]
    names = {ch: "u%04X" % ord(ch) for ch in chars}
    order = [".notdef"] + sorted(names.values())
    fb = FontBuilder(EM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(ch): n for ch, n in names.items()})
    glyphs = {".notdef": glyph([0x7E, 0x42, 0x42, 0x42, 0x42, 0x42, 0x7E, 0])}
    for ch, n in names.items():
        glyphs[n] = glyph(chars[ch])
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({n: (EM, 0) for n in order})
    fb.setupHorizontalHeader(ascent=7 * PX, descent=-PX)
    fb.setupNameTable({"familyName": "C64 Viewer", "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=7 * PX, sTypoDescender=-PX, usWinAscent=7 * PX, usWinDescent=PX)
    fb.setupPost(isFixedPitch=1)
    fb.save(dst)


if __name__ == "__main__":
    main(*sys.argv[1:3])
