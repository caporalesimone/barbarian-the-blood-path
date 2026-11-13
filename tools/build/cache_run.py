#!/usr/bin/env python3
"""Build incrementale (11/11): esegue un passo della build solo se i suoi ingressi sono cambiati.
Uso: tools/build/cache_run.py NOME --in file|cartella ... --out file ... -- comando ...
Impronta SHA-1 di ingressi (contenuto dei file, ricorsivo nelle cartelle) + comando, salvata in out/.cache/NOME;
se l'impronta e' uguale e le uscite esistono il comando non gira ("NOME: invariato"). Variabili d'ambiente che
cambiano il risultato: aggiungerle con --env NOME."""
import hashlib, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def files(p):
    if os.path.isdir(p):
        for dp, dn, fn in sorted(os.walk(p)):
            dn[:] = sorted(d for d in dn if d != "__pycache__")
            for f in sorted(fn):
                if not f.endswith(".pyc"):
                    yield os.path.join(dp, f)
    elif os.path.exists(p):
        yield p


def main(a):
    name = a[0]
    i = a.index("--")
    opts, cmd = a[1:i], a[i + 1:]
    ins, outs, envs, cur = [], [], [], None
    for o in opts:
        if o in ("--in", "--out", "--env"):
            cur = {"--in": ins, "--out": outs, "--env": envs}[o]
        else:
            cur.append(o)
    h = hashlib.sha1(" ".join(cmd).encode())
    for e in envs:
        h.update(("%s=%s" % (e, os.environ.get(e, ""))).encode())
    for p in ins:
        for f in files(os.path.join(ROOT, p)):
            h.update(os.path.relpath(f, ROOT).encode())
            h.update(open(f, "rb").read())
    d = h.hexdigest()
    st = os.path.join(ROOT, "out", ".cache", name)
    if os.path.exists(st) and open(st).read() == d and all(os.path.exists(os.path.join(ROOT, o)) for o in outs):
        print("%s: invariato" % name)
        return 0
    r = subprocess.run(cmd, cwd=ROOT).returncode
    if r == 0:
        os.makedirs(os.path.dirname(st), exist_ok=True)
        open(st, "w").write(d)
    return r


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
