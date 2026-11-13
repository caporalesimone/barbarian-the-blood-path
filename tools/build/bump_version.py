#!/usr/bin/env python3
"""Versione automatica: a ogni build con cambiamenti il numero minore di version.yaml cresce di 1 (regola del
committente, 06/11: ogni disco consegnato ha una versione sua, scritta nel nome del file).
"Cambiamenti" = impronta SHA-1 dei sorgenti veri (src/ senza i file generati, data/, tools/ senza i simulatori, tests/,
version.yaml senza le righe version e source_hash) diversa da quella dell'ultima build, scritta in version.yaml (source_hash,
13/11: prima in un file a parte, .build_hash). I file generati dai tools non contano: cambiano solo se cambiano i loro sorgenti.
Uso: python3 tools/build/bump_version.py   (lo chiama build.sh prima di gen_version.py; stampa la versione)"""
import hashlib, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = {"db.asm", "final_map.inc", "gfx_consts.inc", "start_data.inc", "music_tab.inc", "sid_freq.inc",
       "town_places.inc", "version.inc"}
VY = os.path.join(ROOT, "version.yaml")


def digest():
    h = hashlib.sha1()
    for top in ("src", "data", "tools", "tests"):
        base = os.path.join(ROOT, top)
        for dp, dn, fn in sorted(os.walk(base)):
            dn[:] = sorted(d for d in dn if d not in ("__pycache__",) and not (top == "tools" and d == "simulators"))
            for f in sorted(fn):
                if top == "src" and f in GEN:
                    continue
                if f.endswith((".pyc",)):
                    continue
                p = os.path.join(dp, f)
                h.update(os.path.relpath(p, ROOT).encode())
                h.update(open(p, "rb").read())
    ry = open(VY).read()
    ry = re.sub(r'(?ms)^# Versioni delle build dei branch.*', "", ry)     # (11/11) versioni dei branch: in fondo, non contano
    ry = re.sub(r'(?m)^source_hash:.*$', "", ry)                         # (13/11) l'impronta stessa non conta
    h.update(re.sub(r'(?m)^version:.*$', "", ry).encode())
    return h.hexdigest()


def main():
    ry_p = os.path.join(ROOT, "version.yaml")
    ry = open(ry_p).read()
    v = re.search(r'(?m)^version: "(\d+)\.(\d+)"', ry)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import verinfo
    cur, br = verinfo.current()          # (11/11) su un branch la versione e' tag.n (branch_versions)
    d = digest()
    m = re.search(r'(?m)^source_hash: "([0-9a-f]*)"', ry)
    old = m.group(1) if m else ""
    if d != old:
        if old:                                  # (prima build in assoluto: si tiene la versione scritta)
            if br == "main":
                nv = "%s.%d" % (v.group(1), int(v.group(2)) + 1)
                ry = ry.replace(v.group(0), 'version: "%s"' % nv)
                open(ry_p, "w").write(ry)
            else:
                t, n = cur.rsplit(".", 1)
                nv = "%s.%d" % (t, int(n) + 1)
                verinfo.set_branch_version(br, nv)
            print(nv, "(cambiamenti: versione aumentata%s)" % ("" if br == "main" else ", branch " + br))
        else:
            print(cur, "(prima impronta)")
        ry = open(ry_p).read()                   # (ri)letto: puo' essere cambiato qui sopra o da verinfo
        if re.search(r'(?m)^source_hash:', ry):
            ry = re.sub(r'(?m)^source_hash:.*$', 'source_hash: "%s"' % d, ry)
        else:
            ry = re.sub(r'(?m)^(version:.*)$', lambda mv: mv.group(1) + '\n\n# Impronta dei sorgenti dell\'ultima build (tools/build/bump_version.py): non si modifica a mano.\nsource_hash: "%s"' % d, ry, count=1)
        open(ry_p, "w").write(ry)
    else:
        print(cur, "(nessun cambiamento)")


if __name__ == "__main__":
    main()
