#!/usr/bin/env python3
"""Schermata iniziale: converte data/title_src.png in bitmap multicolor C64 (160x200, celle 4x8:
sfondo comune + 3 colori per cella). Uscite: out/title_preview.png, out/title.koa (formato Koala:
bitmap 8000 + schermo 1000 + colore 1000 + sfondo 1)."""
import os, itertools
import numpy as np
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
PAL = np.array([(0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189), (139, 63, 150), (85, 160, 73),
                (64, 49, 141), (191, 206, 114), (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80),
                (120, 120, 120), (148, 224, 137), (120, 105, 196), (159, 159, 159)], float)   # palette VICE ("colodore")
BG = 0                                       # sfondo comune: nero

def dist(a, p):                              # distanza "redmean" (approssima la percezione meglio dell'RGB puro)
    rm = (a[..., None, 0] + p[None, :, 0]) / 2
    d = a[..., None, :] - p[None, :, :]
    return (2 + rm / 256) * d[..., 0] ** 2 + 4 * d[..., 1] ** 2 + (2 + (255 - rm) / 256) * d[..., 2] ** 2

def convert(src):
    im = Image.open(src).convert("RGB").resize((160, 200), Image.LANCZOS)
    a = np.asarray(im, float)
    err = dist(a, PAL)                                                          # 200x160x16
    others = [c for c in range(16) if c != BG]
    triples = np.array(list(itertools.combinations(others, 3)))                # 455x3
    out = np.zeros((200, 160), int)
    cells = []
    for cy in range(25):
        for cx in range(40):
            e = err[cy * 8:cy * 8 + 8, cx * 4:cx * 4 + 4].reshape(32, 16)      # 32 pixel x 16 colori
            cand = np.concatenate([np.repeat(e[:, BG][None, :], len(triples), 0)[..., None],
                                   e[:, triples].transpose(1, 0, 2)], -1)        # 455x32x4
            tot = cand.min(-1).sum(-1)
            t = triples[tot.argmin()]
            cols = [BG] + list(t)
            idx = cand[tot.argmin()].argmin(-1)
            out[cy * 8:cy * 8 + 8, cx * 4:cx * 4 + 4] = np.array(cols)[idx].reshape(8, 4)
            cells.append((cols, idx.reshape(8, 4)))
    return out, cells

def koala(cells):
    bm, scr, col = bytearray(), bytearray(), bytearray()
    for cols, idx in cells:
        scr.append((cols[1] << 4) | cols[2]); col.append(cols[3])
        for y in range(8):
            v = 0
            for x in range(4):
                v = (v << 2) | int(idx[y, x])          # 00 sfondo, 01 schermo alto, 10 schermo basso, 11 colore
            bm.append(v)
    return bytes(bm) + bytes(scr) + bytes(col) + bytes([BG])

def main():
    out, cells = convert(os.path.join(ROOT, "data", "title_src.png"))
    img = Image.fromarray(PAL[out].astype(np.uint8)).resize((320, 200), Image.NEAREST)
    img.resize((960, 600), Image.NEAREST).save(os.path.join(ROOT, "out", "title_preview.png"))
    data = koala(cells)
    open(os.path.join(ROOT, "out", "title.koa"), "wb").write(data)
    bm, scr, col = data[:8000], data[8000:9000], data[9000:10000]
    # TITLE su disco: per ogni riga di caratteri r: 40 B schermo, 40 B colore, poi 8 righe di pixel
    # (40 B ciascuna). Cosi' il gioco disegna l'immagine riga per riga mentre carica.
    t = bytearray([0x00, 0xe0])
    for r in range(25):
        t += scr[r*40:r*40+40] + col[r*40:r*40+40]
        for l in range(8):
            t += bytes(bm[(r*40+c)*8+l] for c in range(40))
    assert len(t) == 10002
    open(os.path.join(ROOT, "out", "title.prg"), "wb").write(t)
    print("title: %d byte (file TITLE ordinato per righe)" % len(data))

if __name__ == "__main__":
    main()
