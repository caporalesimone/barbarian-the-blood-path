#!/usr/bin/env python3
"""Pubblica gli artefatti della build in out/releases/v<versione>/ (14/11, decisione del committente: una cartella per versione,
retention delle ultime N versioni). Copyright (c) 2026 - Simone Caporale

Uso (dalla radice del progetto, nel container c64-builder):
    publish.py [--keep N] [--atlas] [--maps] [--tests] [--manual] [--release] [--only-manual]

  sempre      il disco (out/disk.d64 -> blood_path_v<V>_1541.d64)
  --atlas     anche l'atlante grafico (atlas/): solo se e' stato generato in QUESTA build
  --maps      anche le mappe RAM e disco (memory-map/): idem
  --tests     anche il report dei test (test_report.txt/.json): solo se i test sono girati in QUESTA build e sono passati
  --manual    anche il manuale PDF (Barbarian_Blood_Path_Manuale_v<V>.pdf): solo se e' stato generato in QUESTA build
  --release   il marchio "release" nel manifest (14/11: niente zip dei sorgenti)
  --only-manual  solo il manuale (./build.sh --manual: non c'e' una build nuova, il disco in out/ potrebbe essere di un'altra versione)
  --keep N    quante versioni tenere (default 5); le piu' vecchie (per data di pubblicazione) si cancellano

Le cartelle si fondono: ripubblicare la stessa versione sostituisce solo i gruppi di file richiesti in questa chiamata e
lascia gli altri (es. il manuale di una build precedente della stessa versione). manifest.json dice, per ogni file, quando e'
stato prodotto, la sua impronta SHA-256 (per una cartella: dell'elenco ordinato dei suoi file) e se i test sono girati. Si cancellano solo cartelle che contengono un manifest.json.
Aggiorna anche il collegamento relativo out/releases/latest -> v<V>."""
import argparse, datetime, hashlib, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verinfo  # noqa: E402
import yaml  # noqa: E402

OUT = os.path.join(ROOT, "out")
REL = os.path.join(OUT, "releases")
MANIFEST = "manifest.json"


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tree_sha256(path):
    """impronta di una cartella: SHA-256 dell'elenco ordinato (percorso relativo, SHA-256 del file)"""
    h = hashlib.sha256()
    for f in sorted(files_of(path)):
        h.update(("%s %s\n" % (os.path.relpath(f, path), sha256(f))).encode())
    return h.hexdigest()


def files_of(path):
    """tutti i file sotto path (o path stesso se e' un file), come percorsi relativi alla cartella della versione"""
    if os.path.isfile(path):
        yield path
    else:
        for d, _, fs in os.walk(path):
            for f in sorted(fs):
                yield os.path.join(d, f)


def remove(p):
    if os.path.isdir(p):
        shutil.rmtree(p)
    elif os.path.exists(p):
        os.remove(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--keep", type=int, default=5, help="versioni da tenere (default 5)")
    ap.add_argument("--atlas", action="store_true")
    ap.add_argument("--maps", action="store_true")
    ap.add_argument("--tests", action="store_true")
    ap.add_argument("--manual", action="store_true")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--only-manual", action="store_true")
    a = ap.parse_args()
    if a.keep < 1:
        sys.exit("publish: --keep deve essere >= 1")

    v, branch = verinfo.current()
    ver = yaml.safe_load(open(os.path.join(ROOT, "version.yaml")))
    vdir = os.path.join(REL, "v" + v)
    os.makedirs(vdir, exist_ok=True)
    mpath = os.path.join(vdir, MANIFEST)
    man = json.load(open(mpath)) if os.path.isfile(mpath) else {"files": {}}
    if man.get("source_hash") not in (None, ver.get("source_hash")):
        # stessa versione ma sorgenti diversi (build su branch, o versione non bumpata): i file di prima non valgono piu'
        for f in list(man["files"]):
            remove(os.path.join(vdir, f))
        man = {"files": {}}
    man.setdefault("built_at", now())

    # gruppi: nome -> lista di (sorgente, destinazione relativa alla cartella della versione)
    groups = {"disk": [("out/disk.d64", "blood_path_v%s_1541.d64" % v)]}
    if a.atlas:
        groups["atlas"] = [("out/atlas", "atlas")]
    if a.maps:
        groups["memory-map"] = [("out/memory-map", "memory-map")]
    if a.only_manual:
        groups = {}
        a.manual = True
    if a.tests:
        groups["tests"] = [("out/test_report.txt", "test_report.txt"), ("out/test_report.json", "test_report.json")]
    if a.manual:
        groups["manual"] = [("out/manual/Barbarian_Blood_Path_Manuale.pdf", "Barbarian_Blood_Path_Manuale_v%s.pdf" % v)]

    stamp = now()
    for g, items in groups.items():
        # sostituzione del gruppo: via i file vecchi di quel gruppo, poi la copia nuova
        for f in [f for f, m in man["files"].items() if m.get("group") == g]:
            remove(os.path.join(vdir, f))
            del man["files"][f]
        for src, dst in items:
            s = os.path.join(ROOT, src)
            if not os.path.exists(s):
                sys.exit("publish: manca %s (gruppo '%s')" % (src, g))
            d = os.path.join(vdir, dst)
            if os.path.isdir(d):
                shutil.rmtree(d)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
            fs = list(files_of(d))
            man["files"][dst] = {"group": g, "type": "dir" if os.path.isdir(d) else "file", "files": len(fs),
                                 "bytes": sum(os.path.getsize(f) for f in fs),
                                 "sha256": tree_sha256(d) if os.path.isdir(d) else sha256(d), "produced": stamp}

    tests = man.get("tests") or {"ran": False}
    if a.tests:
        r = json.load(open(os.path.join(OUT, "test_report.json")))
        res = [x["result"] for x in r["results"]]
        tests = {"ran": True, "suites": r.get("suites"), "total": len(res), "pass": res.count("PASS"),
                 "fail": res.count("FAIL"), "skip": res.count("SKIP"), "seconds": r.get("total_s"), "at": stamp}
    man.update({"version": v, "branch": branch, "save_version": ver.get("save_version"), "source_hash": ver.get("source_hash"),
                "updated_at": stamp, "tests": tests, "release": bool(man.get("release") or a.release),
                "missing": sorted({"disk", "atlas", "memory-map", "tests", "manual"} - {m["group"] for m in man["files"].values()})})
    with open(mpath, "w") as f:
        json.dump(man, f, indent=1, sort_keys=True)
        f.write("\n")

    # collegamento "latest" (relativo, cosi' funziona anche montato altrove)
    link = os.path.join(REL, "latest")
    if os.path.lexists(link):
        os.remove(link)
    os.symlink("v" + v, link)

    # retention: si tengono le ultime N per data di pubblicazione (built_at), la versione appena fatta sempre
    found = []
    for n in os.listdir(REL):
        p = os.path.join(REL, n, MANIFEST)
        if os.path.isfile(p) and not os.path.islink(os.path.join(REL, n)):
            found.append((json.load(open(p)).get("updated_at", ""), n))
    found.sort(reverse=True)
    keep = {n for _, n in found[:a.keep]} | {"v" + v}
    gone = [n for _, n in found if n not in keep]
    for n in gone:
        shutil.rmtree(os.path.join(REL, n))
    tot = sum(os.path.getsize(f) for f in files_of(vdir))
    print("publish: out/releases/v%s (%d voci, %.1f MB; manca: %s)%s" % (
        v, len(man["files"]), tot / 1e6, ", ".join(man["missing"]) or "nulla",
        ("; tolte per la retention (%d): %s" % (a.keep, " ".join(gone))) if gone else ""))


if __name__ == "__main__":
    main()
