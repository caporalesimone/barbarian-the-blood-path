#!/usr/bin/env python3
"""Pubblica gli artefatti della build in out/releases/v<versione>/ (14/11, decisione del committente: una cartella per versione,
retention delle ultime N versioni). Copyright (c) 2026 - Simone Caporale
(15/11) Il meccanismo e' quello generico di Lab64 (c64publish: cartelle, manifest per il viewer, SHA-256, latest, retention);
qui restano solo le scelte del gioco: quali file, i loro nomi, le misure del gioco.

Uso (dalla radice del progetto, nel container lab64-tools: lab64 run python3 tools/build/publish.py ...):
    publish.py [--keep N] [--atlas] [--maps] [--tests] [--manual] [--release] [--only-manual]

  sempre      il disco (out/work/disk.d64 -> blood_path_v<V>_1541.d64) e le musiche .sid (music_sid_v<V>/)
  --atlas     anche l'atlante grafico (atlas/): solo se e' stato generato in QUESTA build
  --maps      anche le mappe RAM e disco (memory-map/): idem
  --tests     anche il report dei test (test_report.txt/.json): solo se i test sono girati in QUESTA build e sono passati
  --manual    anche i manuali PDF (out/work/manual/*.pdf -> <nome>_v<V>.pdf, una lingua per file): solo se generati in QUESTA build
  --release   il marchio "release" nel manifest (14/11: niente zip dei sorgenti)
  --only-manual  solo i manuali (./build.sh --manual: non c'e' una build nuova, il disco in out/ potrebbe essere di un'altra versione)
  --keep N    quante versioni tenere (default 5); le piu' vecchie (per data di pubblicazione) si cancellano
Le cartelle si fondono (ripubblicare la stessa versione sostituisce solo i gruppi richiesti); stessa versione con sorgenti diversi
(source_hash di version.yaml): la cartella riparte vuota."""
import argparse, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verinfo  # noqa: E402
import yaml  # noqa: E402
from c64publish import publish, metric  # noqa: E402  (Lab64)

OUT = os.path.join(ROOT, "out")


# Etichette dei gruppi di file, per la pagina del viewer (Lab64 non sa cosa sono: le legge dal manifest)
GROUP_LABELS = {"disk": "Disco 1541", "atlas": "Atlante grafico", "memory-map": "Mappe RAM e disco", "tests": "Report dei test",
                "manual": "Manuale PDF", "music": "Musiche (.sid)"}


def game_metrics():
    """misure del gioco: margini di memoria dalle etichette di out/work/game.lbl (stesse formule di tools/build/asm.sh), dimensioni di GAME"""
    ms = []
    p = os.path.join(OUT, "work", "game.lbl")
    if os.path.isfile(p):
        lb = {m.group(1): int(m.group(2), 16) for m in (re.match(r"(\w+)\s*=\s*\$([0-9a-f]+)", x) for x in open(p)) if m}
        if all(k in lb for k in ("SCR_H", "gfx_data", "FREE_RAM_END", "code2_end")):
            ms.append(metric("ram_free_8720", "RAM libera sotto $86F8", lb["SCR_H"] + 760 - lb["gfx_data"], "B", "up",
                             "codice del gioco fino allo schermo dell'HUD"))
            ms.append(metric("ram_free_9c00", "RAM libera blocco $9C00", lb["FREE_RAM_END"] + 1 - lb["code2_end"], "B", "up"))
    q = os.path.join(OUT, "work", "game.zx0")
    if os.path.isfile(q):
        prg = os.path.join(OUT, "work", "game.prg")
        ms.append(metric("game_zx0", "GAME compresso (zx0)", os.path.getsize(q) - 2, "B", "down",
                         ("non compresso: %d B" % (os.path.getsize(prg) - 2)) if os.path.isfile(prg) else ""))
    return ms


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
    v, branch = verinfo.current()
    ver = yaml.safe_load(open(os.path.join(ROOT, "version.yaml")))
    disk = "blood_path_v%s_1541.d64" % v
    # gruppi: nome -> lista di (sorgente, destinazione relativa alla cartella della versione)
    groups = {"disk": [("out/work/disk.d64", disk)],
              "music": [("out/work/sid", "music_sid_v%s" % v)]}      # (14/11) un .sid per brano (tools/build/gen_sid.py)
    if a.atlas:
        groups["atlas"] = [("out/work/atlas", "atlas")]
    if a.maps:
        groups["memory-map"] = [("out/work/memory-map", "memory-map")]
    if a.only_manual:
        groups = {}
        a.manual = True
    if a.tests:
        groups["tests"] = [("out/work/test_report.txt", "test_report.txt"), ("out/work/test_report.json", "test_report.json")]
    if a.manual:                                   # (15/11) tutti i manuali generati (una lingua per PDF)
        groups["manual"] = [(os.path.relpath(p, ROOT), "%s_v%s.pdf" % (os.path.splitext(os.path.basename(p))[0], v))
                            for p in sorted(glob.glob(os.path.join(OUT, "work", "manual", "*.pdf")))]
    metrics = info = None
    if not a.only_manual:
        metrics = game_metrics()
        mm = os.path.join(OUT, "work", "memory-map", "memmap.json")
        if a.maps and os.path.isfile(mm):          # (14/11) misure generiche della mappa automatica (lab64 map)
            metrics += json.load(open(mm)).get("metrics", [])
        info = [{"label": "salvataggi", "value": "v%s" % ver.get("save_version")}]
    publish(v, groups, labels=GROUP_LABELS, kinds={"music_sid_v%s" % v: "sid"}, root=ROOT, keep=a.keep, release=a.release,
            tests="out/work/test_report.json" if a.tests else None, metrics=metrics, info=info,
            build_seconds=None if a.only_manual else a.build_seconds, branch=branch, source_hash=ver.get("source_hash"),
            extra={"save_version": ver.get("save_version")}, expected=list(GROUP_LABELS),
            git_paths=("src", "data", "tools", "tests", "docs", "lab64.env", "version.yaml"))


if __name__ == "__main__":
    main()
