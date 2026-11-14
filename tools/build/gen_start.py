#!/usr/bin/env python3
"""Dati di START (src/start.asm, file START e LORE): sprite delle lettere di PRESS SPACE (dal font della UI, out/work/gfx/uifont.bin),
tavolozze dei colori e onda. Uscita: out/work/start_data.inc. La musica del titolo e' un brano di tools/build/songs.py
(PLAYLIST["title"], compilato da tools/build/gen_music.py in out/work/sid_title.inc) suonato da src/common/sid_player.inc."""
import math, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LETTERS = "PRESAC"                 # ordine degli sprite (indice = posizione in questa stringa)
SIN_A = 7                           # ampiezza dell'onda di PRESS / SPACE (pixel; stessa costante in start.asm)

VSCALE = [3, 2, 3, 2, 3, 2, 3, 2]       # righe del glifo 8x8 -> 20 righe dello sprite (x2,5); in larghezza x3 = 24


def font():
    """lettere di PRESS SPACE dal font della UI del gioco (out/work/gfx/uifont.bin, 'Reliquia 05 cero', tools/build/gen_font.py):
    ogni glifo 8x8 ingrandito x3 in larghezza e x2,5 in altezza (24 x 20), in grassetto (ogni riga OR la stessa spostata di 1), riga 21 vuota (06/11 sera: stesso stile
    delle schermate del gioco; prima un font disegnato a mano in data/loader_font.txt)"""
    ui = open(os.path.join(ROOT, "out", "work", "gfx", "uifont.bin"), "rb").read()
    out = bytearray()
    for ch in LETTERS:
        code = ord(ch) - 64                      # codici schermo 1..26 = a..z
        rows = []
        for y, k in enumerate(VSCALE):
            b = ui[code * 8 + y]
            b |= b >> 1                          # grassetto (tratti di 2 pixel): si legge sopra l'immagine del titolo
            v = 0
            for x in range(8):
                if b & (0x80 >> x):
                    v |= 7 << (21 - 3 * x)
            rows += [v] * k
        rows.append(0)
        assert len(rows) == 21
        for v in rows:
            out += bytes([(v >> 16) & 255, (v >> 8) & 255, v & 255])
        out.append(0)
    return out


def bytes_line(lbl, data):
    out = [lbl]
    for i in range(0, len(data), 16):
        out.append("        .byte " + ",".join("$%02x" % b for b in data[i:i+16]))
    return out

def main():
    L = ["; generato da tools/build/gen_start.py - non modificare", ""]
    L += bytes_line("ld_spr", font())
    # tre tavolozze di prova (06/11 sera: "fuoco freddo" bocciata); START sceglie con -D LDCOL=0/1/2
    PALS = [[2, 2, 10, 10, 8, 8, 7, 7, 1, 1, 7, 7, 8, 8, 10, 10],     # A sangue: rosso, arancio, giallo, bianco
            [9, 9, 8, 8, 7, 7, 1, 1, 1, 1, 7, 7, 8, 8, 9, 9],          # B oro antico
            [11, 11, 12, 12, 15, 15, 1, 7, 1, 15, 15, 12, 12, 11, 11, 11]]  # C acciaio, con un lampo giallo
    for i, p in enumerate(PALS):
        L += bytes_line("ld_col%d" % i, p * 2)
    # onda di PRESS / SPACE: 64 voci, ampiezza SIN_A pixel (byte con segno)
    L += bytes_line("ld_sin", [round(SIN_A * math.sin(2 * math.pi * i / 64)) & 255 for i in range(64)])
    open(os.path.join(ROOT, "out", "work", "start_data.inc"), "w").write("\n".join(L) + "\n")

if __name__ == "__main__":
    main()
