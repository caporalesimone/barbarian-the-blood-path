#!/usr/bin/env python3
"""Versione della build secondo il branch di git (11/11, regola del committente: le build dei branch hanno una
versione loro, per non bruciare i numeri di main). Su `main` (o fuori da git): `version` di version.yaml (N.N).
Su un altro branch: `<tag>.<n>` in `branch_versions` di version.yaml; tag = `branch_tags[branch]` o, in mancanza,
la prima parola dell'ultima parte del nome (feature/stat-points -> "stat"); n cresce a ogni build con cambiamenti.
La versione e' solo testo nel gioco (VERSION in out/version.inc): lettere minuscole e cifre."""
import os, re, subprocess
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RY = os.path.join(ROOT, "version.yaml")


def branch():
    try:
        b = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                           timeout=10).stdout.strip()
    except Exception:
        return "main"
    return b if b and b != "HEAD" else "main"


def tag(b, d=None):
    d = d if d is not None else yaml.safe_load(open(RY))
    t = (d.get("branch_tags") or {}).get(b) or re.split(r"[-_]", b.split("/")[-1])[0]
    t = re.sub(r"[^a-z0-9]", "", t.lower()) or "br"
    return t


def current():
    """(versione, branch): la versione da mostrare per il branch attuale"""
    d = yaml.safe_load(open(RY))
    b = branch()
    if b == "main":
        return str(d["version"]), b
    bv = (d.get("branch_versions") or {}).get(b)
    return (str(bv) if bv else "%s.0" % tag(b, d)), b


def set_branch_version(b, v):
    """scrive branch_versions[b] = v in version.yaml senza perdere i commenti"""
    s = open(RY).read()
    line = '  %s: "%s"' % (b, v)
    pat = re.compile(r'(?m)^  %s: ".*"$' % re.escape(b))
    if pat.search(s):
        s = pat.sub(line, s)
    elif re.search(r"(?m)^branch_versions:", s):
        s = re.sub(r"(?m)^branch_versions:.*$", lambda m: m.group(0) + "\n" + line, s, count=1)
    else:
        s = s.rstrip("\n") + ("\n\n# Versioni delle build dei branch (tools/build/verinfo.py): tag.n, non bruciano i numeri di main.\n"
                              "branch_versions:\n" + line + "\n")
    open(RY, "w").write(s)
