#!/usr/bin/env python3
"""Pubblica gli artefatti della build in out/releases/v<versione>/ (14/11, decisione del committente: una cartella per versione,
retention delle ultime N versioni). Copyright (c) 2026 - Simone Caporale

Uso (dalla radice del progetto, nel container lab64-tools):
    publish.py [--keep N] [--atlas] [--maps] [--tests] [--manual] [--release] [--only-manual]

  sempre      il disco (out/work/disk.d64 -> blood_path_v<V>_1541.d64)
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
import argparse, datetime, hashlib, json, os, re, shutil, subprocess, sys

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


def git_info():
    """commit, ramo e oggetto del lavoro da cui nasce la build; dirty = ci sono modifiche non committate (la build le contiene)"""
    def g(*a):
        return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, text=True, timeout=20).stdout.strip()
    try:
        return {"commit": g("rev-parse", "--short", "HEAD"), "subject": g("log", "-1", "--format=%s"),
                "dirty": bool(g("status", "--porcelain", "--", "src", "data", "tools", "tests", "docs", "lab64.env", "version.yaml"))}
    except Exception:
        return {}


# Etichette dei gruppi di file, per la pagina del viewer (Lab64 non sa cosa sono: le legge dal manifest)
GROUP_LABELS = {"disk": "Disco 1541", "atlas": "Atlante grafico", "memory-map": "Mappe RAM e disco", "tests": "Report dei test",
                "manual": "Manuale PDF"}


def metric(mid, label, value, unit="", better=None, hint=""):
    """una misura del progetto nel formato del viewer (../lab64/README.md, "Manifest per il viewer"):
    better = "up" (piu' alto e' meglio), "down" (piu' basso e' meglio) o None"""
    return {"id": mid, "label": label, "value": value, "unit": unit, "better": better, "hint": hint}


def game_metrics():
    """misure del gioco: margini di memoria dalle etichette di out/work/game.lbl (stesse formule di tools/build/asm.sh), dimensioni di GAME"""
    ms = []
    p = os.path.join(OUT, "work", "game.lbl")
    if os.path.isfile(p):
        lb = {m.group(1): int(m.group(2), 16) for m in (re.match(r"(\w+)\s*=\s*\$([0-9a-f]+)", x) for x in open(p)) if m}
        if all(k in lb for k in ("SCR_H", "gfx_data", "FREE_RAM_END", "code2_end")):
            ms.append(metric("ram_free_8720", "RAM libera sotto $8720", lb["SCR_H"] + 800 - lb["gfx_data"], "B", "up",
                             "codice del gioco fino allo schermo dell'HUD"))
            ms.append(metric("ram_free_9c00", "RAM libera blocco $9C00", lb["FREE_RAM_END"] + 1 - lb["code2_end"], "B", "up"))
    q = os.path.join(OUT, "work", "game.zx0")
    if os.path.isfile(q):
        prg = os.path.join(OUT, "work", "game.prg")
        ms.append(metric("game_zx0", "GAME compresso (zx0)", os.path.getsize(q) - 2, "B", "down",
                         ("non compresso: %d B" % (os.path.getsize(prg) - 2)) if os.path.isfile(prg) else ""))
    return ms


def d64_info(path):
    """blocchi liberi e directory di un .d64 da 35 tracce (BAM e directory alla traccia 18)"""
    d = open(path, "rb").read()
    spt = lambda tr: 21 if tr <= 17 else 19 if tr <= 24 else 18 if tr <= 30 else 17
    off = lambda tr, s: (sum(spt(x) for x in range(1, tr)) + s) * 256
    bam = off(18, 0)
    free = sum(d[bam + 4 * tr] for tr in range(1, 36) if tr != 18)
    total = sum(spt(tr) for tr in range(1, 36) if tr != 18)
    # PETSCII -> testo: $41-$5A (maiuscole sul C64) in minuscolo come le scrive il gioco, $C1-$DA in maiuscolo
    pet = lambda b: chr(b + 32) if 0x41 <= b <= 0x5A else chr(b - 128) if 0xC1 <= b <= 0xDA else chr(b) if 0x20 <= b < 0x7F else "?"
    files, tr, s, seen = [], 18, 1, set()
    while tr and (tr, s) not in seen and 1 <= tr <= 35:
        seen.add((tr, s))
        o = off(tr, s)
        for i in range(8):
            e = d[o + 32 * i: o + 32 * i + 32]
            if e[2] & 7 and e[2]:
                files.append({"name": "".join(pet(b) for b in e[5:21] if b != 0xA0), "type": ["DEL", "SEQ", "PRG", "USR", "REL"][e[2] & 7] if (e[2] & 7) < 5 else "?",
                              "blocks": e[30] + 256 * e[31]})
        tr, s = d[o], d[o + 1]
    return {"blocks_total": total, "blocks_free": free, "blocks_used": total - free, "files": files}


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
    ap.add_argument("--build-seconds", type=int, default=None, help="durata del passo di build (la misura build.sh)")
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
    groups = {"disk": [("out/work/disk.d64", "blood_path_v%s_1541.d64" % v)]}
    if a.atlas:
        groups["atlas"] = [("out/work/atlas", "atlas")]
    if a.maps:
        groups["memory-map"] = [("out/work/memory-map", "memory-map")]
    if a.only_manual:
        groups = {}
        a.manual = True
    if a.tests:
        groups["tests"] = [("out/work/test_report.txt", "test_report.txt"), ("out/work/test_report.json", "test_report.json")]
    if a.manual:
        groups["manual"] = [("out/work/manual/Barbarian_Blood_Path_Manuale.pdf", "Barbarian_Blood_Path_Manuale_v%s.pdf" % v)]

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
        r = json.load(open(os.path.join(OUT, "work", "test_report.json")))
        res = [x["result"] for x in r["results"]]
        tests = {"ran": True, "suites": r.get("suites"), "total": len(res), "pass": res.count("PASS"),
                 "fail": res.count("FAIL"), "skip": res.count("SKIP"), "seconds": r.get("total_s"), "at": stamp}
    stats = man.get("stats") or {}
    if not a.only_manual:
        stats["metrics"] = game_metrics()
        mm = os.path.join(OUT, "work", "memory-map", "memmap.json")
        if a.maps and os.path.isfile(mm):          # (14/11) misure generiche della mappa automatica (../lab64/memmap/c64map.py)
            stats["metrics"] += json.load(open(mm)).get("metrics", [])
        stats["info"] = [{"label": "salvataggi", "value": "v%s" % ver.get("save_version")}]
        stats["disk"] = d64_info(os.path.join(vdir, "blood_path_v%s_1541.d64" % v))
        stats["git"] = git_info()
        if a.build_seconds is not None:
            stats["build_seconds"] = a.build_seconds
    if a.tests:
        stats["test_seconds"] = tests.get("seconds")
    man.update({"schema": 1, "groups": GROUP_LABELS, "stats": stats, "version": v, "branch": branch, "save_version": ver.get("save_version"), "source_hash": ver.get("source_hash"),
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
