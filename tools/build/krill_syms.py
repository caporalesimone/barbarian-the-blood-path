#!/usr/bin/env python3
"""out/work/krill/loadersymbols.inc (sintassi ca65) -> out/work/krill.inc (64tass): indirizzi del loader con prefisso krill_
(64tass non distingue maiuscole e minuscole nei nomi). Legge anche le dimensioni dei tre PRG."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(ROOT, "out/work/krill/loadersymbols.inc")).read()
out = ["; generato da tools/build/krill_syms.py (Krill's Loader r194): non modificare"]
want = ("install", "loadraw", "save", "uninstall", "loader_zp_first", "loader_zp_last", "plugin_zp_last",
        "loadaddrlo", "loadaddrhi", "endaddrlo", "endaddrhi")
got = {}
for m in re.finditer(r"^(\w+)\s*=\s*(\$[0-9a-fA-F]+|\d+)", src, re.M):
    n, v = m.group(1), m.group(2)
    if n in want:
        got[n] = v
        out.append("krill_%s = %s" % (n, v))
for n in ("install", "loadraw", "save"):
    if n not in got:
        sys.exit("krill_syms: manca %s in loadersymbols.inc" % n)
for n, f in (("install", "install"), ("loader", "loader"), ("save", "save")):
    out.append("KRILL_%s_LEN = %d" % (n.upper(), os.path.getsize(os.path.join(ROOT, "out/work/krill/%s.prg" % f)) - 2))
open(os.path.join(ROOT, "out/work/krill.inc"), "w").write("\n".join(out) + "\n")
