#!/usr/bin/env python3
"""Centred version (09/11, rule of the owner: the release always checks it). Static test, no VICE:
1. VER_X of out/version.inc = (40 - len("version " + VERSION)) // 2;
2. every "version ", VERSION in the sources is placed with VER_X: `#at VER_X,...` within the 5 lines before (GAME,
   LOBBY) or `.byte VER_X, ...` (text table of the loader BARBARIAN)."""
import os, re, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
inc = open(os.path.join(ROOT, "out", "version.inc")).read()
ver = re.search(r'VERSION = "([^"]+)"', inc).group(1)
vx = int(re.search(r"VER_X = (\d+)", inc).group(1))
err = []
want = (40 - len("version " + ver)) // 2
if vx != want:
    err.append(f"version.inc: VER_X = {vx}, expected {want} for 'version {ver}'")
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, "src/**/*.asm"), recursive=True)):
    L = open(f).read().split("\n")
    for i, l in enumerate(L):
        if re.search(r'"version ",\s*VERSION', l) and not l.lstrip().startswith(";"):
            n += 1
            prev = "\n".join(L[max(0, i - 5):i])
            if not re.search(r"#at\s+VER_X\s*,|\.byte\s+VER_X\s*,", prev):
                err.append(f"{os.path.relpath(f, ROOT)}:{i + 1}: 'version' not placed with VER_X")
if n == 0:
    err.append("nessuna stringa 'version' trovata nei sorgenti")
for e in err:
    print("ERRORE:", e)
print(f"version {ver}: colonna {vx}, {n} schermate controllate")
sys.exit(1 if err else 0)
