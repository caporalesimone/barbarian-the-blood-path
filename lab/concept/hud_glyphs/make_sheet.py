#!/usr/bin/env python3
"""Proposte di glifi per l'avviso "punti statistica da spendere" accanto al numero del livello nell'HUD (11/11, branch
feature/stat-points). 20 glifi 8x8 hires: nell'HUD (multicolor) un carattere hires accetta solo i colori 0-7, quindi le
tinte possibili sono rosso 2, ciano 3, viola 4, verde 5, blu 6 (scuro sul nero), giallo 7; il bianco 1 e' escluso su
richiesta del committente. Uscita: hud_glyphs.png (tabella ingrandita + riga dell'HUD simulata "LV 12" + glifo) e
glyphs.json (bitmap e colore, da copiare in tools/build/gen_gfx.py hud_glyph quando si sceglie).
Uso: python3 lab/concept/hud_glyphs/make_sheet.py"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "memory-map", "simulators")]
import gen_gfx as GG  # noqa: E402

PAL = {0: (0, 0, 0), 1: (255, 255, 255), 2: (129, 51, 56), 3: (117, 206, 200), 4: (142, 60, 151), 5: (86, 172, 77),
       6: (46, 44, 155), 7: (237, 241, 113)}
CNAME = {2: "red", 3: "cyan", 4: "purple", 5: "green", 6: "blue", 7: "yellow"}

G = [  # (id, nome, colore, 8 righe)
    ("plus1", "+1", 7, ["00000100", "00001100", "01000100", "11100100", "01000100", "00000100", "00001110", "00000000"]),
    ("arrow_open", "freccia aperta (carina)", 7, ["00011000", "00111100", "01111110", "11011011", "10011001", "00011000", "00011000", "00000000"]),
    ("arrow_slim", "freccia sottile", 7, ["00010000", "00111000", "01111100", "11010110", "00010000", "00010000", "00010000", "00000000"]),
    ("arrow_notch", "freccia con coda a coda di rondine", 5, ["00011000", "00111100", "01111110", "11111111", "00111100", "00111100", "00100100", "00000000"]),
    ("arrow_solid", "freccia piena (oggi)", 7, ["00011000", "00111100", "01111110", "11111111", "00011000", "00011000", "00011000", "00000000"]),
    ("chevron2", "doppio chevron", 7, ["00011000", "00111100", "01100110", "11000011", "00011000", "00111100", "01100110", "11000011"]),
    ("chevron_thin", "doppio chevron sottile", 3, ["00010000", "00101000", "01000100", "00000000", "00010000", "00101000", "01000100", "00000000"]),
    ("tri_up", "triangolo", 3, ["00000000", "00011000", "00111100", "01111110", "11111111", "00000000", "00000000", "00000000"]),
    ("star5", "stella", 7, ["00011000", "00011000", "11111111", "01111110", "00111100", "01100110", "11000011", "00000000"]),
    ("sparkle", "scintilla", 3, ["00010000", "00010000", "00111000", "11111110", "00111000", "00010000", "00010000", "00000000"]),
    ("plus_big", "piu' grande", 5, ["00011000", "00011000", "00011000", "11111111", "11111111", "00011000", "00011000", "00011000"]),
    ("crown", "corona", 7, ["00000000", "10011001", "11011011", "11111111", "11111111", "01111110", "01111110", "00000000"]),
    ("gem", "gemma", 3, ["00111100", "01111110", "11111111", "01111110", "00111100", "00011000", "00000000", "00000000"]),
    ("sword_up", "spada in su", 4, ["00011000", "00011000", "00011000", "00011000", "01111110", "00011000", "00011000", "00000000"]),
    ("flame", "fiamma", 2, ["00010000", "00011000", "00111000", "01111100", "01110110", "01110110", "00111100", "00000000"]),
    ("bang", "punto esclamativo", 2, ["00011000", "00011000", "00011000", "00011000", "00011000", "00000000", "00011000", "00000000"]),
    ("shield_plus", "scudo con piu'", 4, ["11111111", "11100111", "10000001", "11100111", "11100111", "01111110", "00111100", "00000000"]),
    ("heart", "cuore", 2, ["00000000", "01100110", "11111111", "11111111", "01111110", "00111100", "00011000", "00000000"]),
    ("rune_t", "runa Tiwaz", 4, ["00010000", "00111000", "01010100", "10010010", "00010000", "00010000", "00010000", "00000000"]),
    ("bars_up", "barre crescenti", 5, ["00000011", "00000011", "00001111", "00001111", "00111111", "00111111", "11111111", "00000000"]),
]
assert len(G) == 20 and all(len(r) == 8 and all(len(x) == 8 for x in r) for _, _, _, r in G)

S, CELL = 8, 8 * 8 + 0          # zoom 8: un pixel = 8x8
font = ImageFont.load_default()


def glyph_img(rows, col, z):
    im = Image.new("RGB", (8 * z, 8 * z), PAL[0])
    d = ImageDraw.Draw(im)
    for y, r in enumerate(rows):
        for x, b in enumerate(r):
            if b == "1":
                d.rectangle([x * z, y * z, x * z + z - 1, y * z + z - 1], fill=PAL[col])
    return im


def hud_char(ch):
    """carattere dell'HUD (font 5x7 di gen_gfx) come righe di bit"""
    return ["{:08b}".format(v) for v in GG.hud_glyph(ch)]


def hud_row(rows, col, z=3):
    """'LV 12' + glifo come nell'HUD: L V bianco? no: come il gioco (lettere 1 bianco, cifre 1)"""
    chars = [(hud_char("L"), 1), (hud_char("V"), 1), (None, 0), (hud_char("1"), 1), (hud_char("2"), 1), (rows, col)]
    im = Image.new("RGB", (8 * z * len(chars), 8 * z), PAL[0])
    for i, (r, c) in enumerate(chars):
        if r:
            im.paste(glyph_img(r, c, z), (i * 8 * z, 0))
    return im


COLS = 4
W, H = 300, 150
sheet = Image.new("RGB", (COLS * W + 20, ((len(G) + COLS - 1) // COLS) * H + 60), (24, 24, 24))
d = ImageDraw.Draw(sheet)
d.text((10, 10), "Glifi per 'punti da spendere' accanto al livello (HUD hires: colori 2-7, niente bianco) - 11/11", fill=(230, 230, 230), font=font)
for i, (gid, name, col, rows) in enumerate(G):
    x, y = 10 + (i % COLS) * W, 40 + (i // COLS) * H
    sheet.paste(glyph_img(rows, col, 8), (x, y))
    sheet.paste(hud_row(rows, col, 3), (x + 80, y + 8))
    d.text((x + 80, y + 40), "%2d %s" % (i + 1, gid), fill=(230, 230, 230), font=font)
    d.text((x + 80, y + 54), name, fill=(180, 180, 180), font=font)
    d.text((x + 80, y + 68), "colore %d %s" % (col, CNAME[col]), fill=PAL[col], font=font)
out = os.path.join(HERE, "hud_glyphs.png")
sheet.save(out)
json.dump([{"id": g, "name": n, "color": c, "rows": r} for g, n, c, r in G], open(os.path.join(HERE, "glyphs.json"), "w"), indent=1)
print(out)
