#!/usr/bin/env python3
"""Legge version.yaml e scrive out/work/version.inc (VERSION, SAVE_VER, VER_X = colonna di "version x.y" centrata).
Uso: gen_version.py            -> scrive out/work/version.inc
     gen_version.py --print version|save_version"""
import os, re, sys, yaml
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
d = yaml.safe_load(open(os.path.join(ROOT, "version.yaml")))
s = d["save_version"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verinfo  # noqa: E402
v, _br = verinfo.current()             # (11/11) su un branch: tag.n (branch_versions), su main: version
if not re.fullmatch(r"[a-z0-9]+\.\d+", v):
    sys.exit(f"version.yaml: version '{v}' non valida (formato N.N o tag.N, minuscole e cifre)")
if not isinstance(s, int) or not 1 <= s <= 255:
    sys.exit(f"version.yaml: save_version {s!r} non valida (intero 1..255)")
if len(sys.argv) == 3 and sys.argv[1] == "--print":
    print({"version": v, "save_version": s}[sys.argv[2]])
    sys.exit(0)
import glob  # noqa: E402
_kz = glob.glob(os.path.join(ROOT, "src", "third-party", "krill", "loader-v*.zip"))
if len(_kz) != 1:
    sys.exit("src/third-party/krill: serve un solo loader-vNNN.zip (versione di Krill's Loader)")
kv = re.fullmatch(r".*loader-(v\d+)\.zip", _kz[0]).group(1)       # (16/11) "v194": dal nome dell'archivio ufficiale
vline = "version " + v + " - loader by krill " + kv
open(os.path.join(ROOT, "out", "work", "version.inc"), "w").write(
    f'; generato da tools/build/gen_version.py da version.yaml - non modificare\nVERSION = "{v}"\nSAVE_VER = ${s:02x}\n'
    f'; colonna di "version x.y" centrata su 40 colonne (09/11; tests/smoke/build/test_version_center.py)\n'
    f'VER_X = {(40 - len("version " + v)) // 2}\n'
    f'; (16/11) riga del menu iniziale: "version x.y - loader by krill vNNN" centrata (unica riga con la versione, oltre al menu di gioco)\n'
    f'KRILL_VER = "{kv}"\n'
    f'VER_LX = {(40 - len(vline)) // 2}\n')
