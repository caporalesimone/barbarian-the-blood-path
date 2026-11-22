#!/usr/bin/env python3
"""PROPOSAL (22/11, owner's request, not used by the build): a better hero sprite, more walk frames and looks that follow the
equipment. Draws out/work/proposals/hero_proposal.png from the pixel grids below (multicolor 12x21: '.' transparent,
'1' brown = sprite multicolor 0, '2' sprite colour, '3' light grey = sprite multicolor 1).
Usage (in the lab64-tools container): python3 lab/proposte/hero_proposal.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
from PIL import Image, ImageDraw
import gen_gfx as G
import hero as H

SC = 4
BG = (60, 110, 50)

# ---- new base, front view: horned helm with a nose guard, eyes, bare chest with a strap, fur kilt, skin legs, boots
DOWN = [
    ".3........3.",
    ".33......33.",
    "..33333333..",
    "..33333333..",
    "..32233223..",
    "..21233212..",
    "...222222...",
    "...221122...",
    "..12222221..",
    ".2212222122.",
    ".2221221222.",
    ".22.1221.22.",
    ".22.2112.22.",
    ".22111111.2.",
    "...131131...",
    "...111111...",
]
LEGS_D = {
    "stand": ["...22..22...", "...22..22...", "...22..22...", "..111..111..", "..111..111.."],
    "left":  ["...22..22...", "...22..22...", "...22..11...", "..111..11...", "..111......."],
    "right": ["...22..22...", "...22..22...", "...11..22...", "...11..111..", ".......111.."],
}
UP = [
    ".3........3.",
    ".33......33.",
    "..33333333..",
    "..33333333..",
    "..33333333..",
    "..11111111..",
    "...111111...",
    "...222222...",
    "..12222221..",
    ".2221221222.",
    ".2222112222.",
    ".22.2112.22.",
    ".22.1221.22.",
    ".22111111.2.",
    "...111111...",
    "...111111...",
]
SIDE = [                        # facing left; the right view is the mirror
    "...3........",
    "...33.......",
    "..333333....",
    "..333333....",
    "..233222....",
    "..212222....",
    "..222222....",
    "...21122....",
    "...122221...",
    "..1222221...",
    "..2122222...",
    "..22.1222...",
    "..22.2122...",
    "...2111112..",
    "....13111...",
    "....11111...",
]
LEGS_S = {
    "pass":   ["....222.....", "....222.....", "....222.....", "...1111.....", "...1111....."],
    "wide":   ["...22.22....", "..22...22...", "..22...22...", ".111...111..", ".111........"],
    "wide2":  ["...22.22....", "..22...22...", "..22...22...", ".111...111..", ".......111.."],
}

# ---- looks by equipment: rows 8..13 of the front view (torso and arms), and the shield / weapon in the hands
TORSO = {
    "no armor (bare chest, strap)": None,
    "leather / studded": ["..11111111..", ".2211311122.", ".2211111122.", ".22.1311.22.", ".22.1111.22.", ".22111111.2."],
    "mail / plate": ["..33333333..", ".2233333322.", ".2231331322.", ".22.3333.22.", ".22.3113.22.", ".22111111.2."],
}


def with_rows(base, rows, at):
    out = list(base)
    out[at:at + len(rows)] = rows
    return out


def shield(rows):
    """round shield on the left of the picture (the hero's right arm), rows 9..13"""
    out = [list(r) for r in rows]
    for y, s in zip(range(9, 14), ("333.", "3113", "3113", "3113", "333.")):
        for x, c in enumerate(s):
            if c != ".":
                out[y][x] = c
    return ["".join(r) for r in out]


def weapon(rows, kind):
    """weapon in the other hand (right side of the picture), rows 4..13"""
    out = [list(r) for r in rows]
    shape = {"sword": [(11, y, "3") for y in range(4, 12)] + [(10, 12, "1"), (11, 12, "1"), (11, 13, "1")],
             "axe": [(11, y, "1") for y in range(5, 14)] + [(10, 5, "3"), (10, 6, "3"), (9, 5, "3"), (10, 4, "3"), (11, 4, "3")],
             "mace": [(11, y, "1") for y in range(7, 14)] + [(10, 4, "3"), (11, 4, "3"), (10, 5, "3"), (11, 5, "3"), (10, 6, "3"), (11, 6, "3")]}[kind]
    for x, y, c in shape:
        out[y][x] = c
    return ["".join(r) for r in out]


def frame(top, legs):
    rows = top + legs
    assert len(rows) == 21 and all(len(r) == 12 for r in rows), (len(rows), [r for r in rows if len(r) != 12])
    return rows


def mirror(rows):
    return [r[::-1] for r in rows]


def put(img, rows, ox, oy, col=10, sc=SC):
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == ".":
                continue
            rgb = G.C64[{"1": 9, "2": col, "3": 15}[c]]
            for yy in range(sc):
                for xx in range(2 * sc):
                    img.putpixel((ox + x * 2 * sc + xx, oy + y * sc + yy), rgb)


def main():
    CW, CH = 24 * SC + 14, 21 * SC + 10
    rows_out = []
    old_d, old_u, old_l = H.DOWN, H.UP, H.LEFT
    rows_out.append(("today: 2 frames per direction (8 sprites)",
                     [old_d, old_d[:16] + H.DOWN_W, old_u, old_u[:16] + H.DOWN_W, old_l, old_l[:16] + H.LEFT_W,
                      mirror(old_l), mirror(old_l[:16] + H.LEFT_W)]))
    d = {k: frame(DOWN, v) for k, v in LEGS_D.items()}
    u = {k: frame(UP, v) for k, v in LEGS_D.items()}
    s = {k: frame(SIDE, v) for k, v in LEGS_S.items()}
    rows_out.append(("proposal: walk cycle of 4 steps, 3 sprites per direction (12 sprites, +256 B)",
                     [d["left"], d["stand"], d["right"], u["left"], u["stand"], u["right"], s["wide"], s["pass"], s["wide2"],
                      mirror(s["wide"]), mirror(s["pass"]), mirror(s["wide2"])]))
    eq = []
    for name, t in TORSO.items():
        top = DOWN if t is None else with_rows(DOWN, t, 8)
        eq.append(frame(top, LEGS_D["stand"]))
    eq.append(shield(frame(DOWN, LEGS_D["stand"])))
    for k in ("sword", "axe", "mace"):
        eq.append(weapon(frame(with_rows(DOWN, TORSO["mail / plate"], 8), LEGS_D["stand"]), k))
    eq.append(weapon(shield(frame(with_rows(DOWN, TORSO["leather / studded"], 8), LEGS_D["stand"])), "sword"))
    rows_out.append(("equipment: no armor, leather, mail/plate, shield, sword, axe, mace, leather+shield+sword", eq))
    W = max(len(f) for _, f in rows_out) * CW + 20
    img = Image.new("RGB", (W, len(rows_out) * (CH + 22) + 10), (25, 25, 25))
    dr = ImageDraw.Draw(img)
    for i, (title, frames) in enumerate(rows_out):
        oy = 8 + i * (CH + 22)
        dr.text((10, oy), title, fill=(230, 230, 230))
        for j, f in enumerate(frames):
            ox = 10 + j * CW
            dr.rectangle([ox, oy + 14, ox + CW - 6, oy + 14 + CH - 2], fill=BG if j % 2 == 0 else (110, 80, 40))
            put(img, f, ox + 4, oy + 18)
    out = os.path.join(ROOT, "out", "work", "proposals")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, "hero_proposal.png"))
    print("ok:", os.path.join(out, "hero_proposal.png"))


if __name__ == "__main__":
    main()
