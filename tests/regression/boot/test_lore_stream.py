#!/usr/bin/env python3
"""LORE story layout (15/11): line spacing in the generated stream (out/work/ldat_raw.bin, tools/build/gen_lore.py).
The paragraphs of data/lore.txt come out of the automatic wrap (columns 2-37) as rows of text; since 15/11 the rows of a
paragraph are LINE_GAP empty rows apart (1 = one blank row) and two paragraphs are at least PARA_GAP empty rows apart (2).
Checks, decoding the stream exactly as the C64 does (no image or VICE needed):
  - no two text rows are adjacent (never zero blank rows between them), titles and centred lines included;
  - inside a paragraph exactly LINE_GAP blank rows, between paragraphs and next to images at least PARA_GAP;
  - the paragraphs found in the stream have the same number of rows as the wrap of data/lore.txt (same text, same order);
  - the size limits: the stream ends under TBUF ($6000, src/common/boot.asm) and the compressed LDAT too;
  - no 8-bit row counter in scroll.asm: LR_NROWS is only informative (the stream is read with a 16-bit pointer lp).
Usage: tests/regression/boot/test_lore_stream.py   (needs out/work from a build)."""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import gen_lore as GL  # noqa: E402

fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)


inc = open(os.path.join(ROOT, "out", "work", "lore.inc")).read()
val = lambda k: int(re.search(r"^%s\s*=\s*(\$?[0-9a-fA-F]+)" % k, inc, re.M).group(1).replace("$", "0x"), 0)
raw = open(os.path.join(ROOT, "out", "work", "ldat_raw.bin"), "rb").read()
mem = bytearray(65536)
mem[GL.LD_DST:GL.LD_DST + len(raw)] = raw
p = val("LR_ROWS")
rows = []                                           # (characters, colours) of every row of the stream
while mem[p] != 0xFE:
    n = mem[p]; p += 1
    for _ in range(n):                              # events: SHAPES 5 B, SPRITE 8, SPLIT 3, STOP 2
        p += {0: 5, 1: 8, 2: 3, 3: 2}[mem[p]]
    data = bytearray()
    while len(data) < 80:
        b = mem[p]
        if b == 0xFF: data += bytes([mem[p + 2]]) * mem[p + 1]; p += 3
        else: data.append(b); p += 1
    assert len(data) == 80
    rows.append((bytes(data[:40]), bytes(data[40:])))
check(len(rows) == val("LR_NROWS"), "the stream has LR_NROWS = %d rows" % val("LR_NROWS"))


def kind(r):
    ch, co = r
    cells = [i for i in range(40) if ch[i] != 32 or co[i] >= 8]
    if not cells: return "blank"
    if all(co[i] < 8 for i in cells): return "text"        # text in high resolution (colour < 8)
    return "image"                                          # images (and sprite rows, empty) have multicolour cells


def first_col(r):
    return next(i for i in range(40) if r[0][i] != 32)


k = [kind(r) for r in rows]
# non-blank rows with the blank rows between them (sprite rows are blank rows for the screen: sprites are not characters)
idx = [i for i, x in enumerate(k) if x != "blank"]
gaps = [(a, b, b - a - 1) for a, b in zip(idx, idx[1:])]
check(not any(k[a] == "text" and k[b] == "text" and g == 0 for a, b, g in gaps),
      "no two rows of text without a blank row between them")
inside, between = [], []
for a, b, g in gaps:
    if k[a] == "text" and k[b] == "text" and first_col(rows[a]) == GL.MARGIN and first_col(rows[b]) == GL.MARGIN:
        (inside if g == GL.LINE_GAP else between).append((a, b, g))
check(all(g >= GL.PARA_GAP for a, b, g in between),
      "paragraph to paragraph: at least %d blank rows (smallest %d)" % (GL.PARA_GAP, min([g for a, b, g in between] or [99])))
para = lambda i: k[i] == "text" and first_col(rows[i]) == GL.MARGIN            # a row of a paragraph (titles are centred)
near_img = [(a, b, g) for a, b, g in gaps if (para(a) and k[b] == "image") or (k[a] == "image" and para(b))]
check(near_img and all(g >= GL.PARA_GAP for a, b, g in near_img),
      "paragraph text above and below images: at least %d blank rows (%d cases)" % (GL.PARA_GAP, len(near_img)))
# the paragraphs of the stream (runs of margin rows LINE_GAP apart) = the wrap of lore.txt, in order
runs, cur = [], []
for a in [i for i in idx if k[i] == "text" and first_col(rows[i]) == GL.MARGIN]:
    if cur and a - cur[-1] - 1 == GL.LINE_GAP: cur.append(a)
    else:
        if cur: runs.append(len(cur))
        cur = [a]
runs.append(len(cur))
paras, cp = [], []
for ln in open(os.path.join(ROOT, "data", "lore.txt")):
    ln = ln.rstrip("\n")
    if ln.startswith(";"): continue
    if ln.startswith("@") or not ln.strip():
        if cp: paras.append(len(GL.wrap(" ".join(cp)))); cp = []
    else: cp.append(ln.strip())
check(runs == paras, "%d paragraphs: rows per paragraph in the stream = wrap of data/lore.txt" % len(paras))
check(len(inside) == sum(runs) - len(runs),
      "%d rows of text in %d paragraphs: %d line gaps of exactly %d blank row" % (sum(runs), len(runs), len(inside), GL.LINE_GAP))
# limits
end = GL.LD_DST + len(raw)
tbuf = int(re.search(r"^TBUF\s+=\s+\$([0-9a-f]+)", open(os.path.join(ROOT, "src", "common", "boot.asm")).read(), re.M).group(1), 16)
check(end <= tbuf and val("LD_AT") + val("LD_LEN") <= tbuf,
      "LDAT unpacked ends at $%04x and packed at $%04x, under TBUF $%04x (margin %d B)" % (end, val("LD_AT") + val("LD_LEN"), tbuf, tbuf - max(end, val("LD_AT") + val("LD_LEN"))))
sc = open(os.path.join(ROOT, "src", "lore", "scroll.asm")).read()
check("LR_NROWS" not in sc, "scroll.asm does not use LR_NROWS (no 8-bit row counter): %d rows are fine" % len(rows))
print("LORE stream test: %s" % ("all ok" if not fails else "%d failures" % len(fails)))
sys.exit(1 if fails else 0)
