#!/usr/bin/env python3
"""Capitoli (11/11): data/chapters.yaml con i piani di ogni capitolo; qui si calcolano i due contatori (docs/wiki/capitoli.md):
il piano LOCALE riparte da 1 a ogni capitolo (quello che vede il giocatore), la PROFONDITA' GLOBALE 1..255
(somma dei piani dei capitoli precedenti + piano locale) regola la difficolta'. L'ultimo capitolo con `levels: rest`
(l'Abisso) prende i piani che restano fino a global_max. Letto da tools/simulators/chapters.py, tools/atlas/gen_atlas.py e dai test.
Uso: python3 tools/build/chapters_db.py   (stampa capitoli, piani locali e profondita')"""
import os, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YML = os.path.join(ROOT, "data", "chapters.yaml")


def load(path=YML):
    d = yaml.safe_load(open(path))
    gmax = d.get("global_max", 255)
    chs, depth = [], 0
    for i, ch in enumerate(d["chapters"]):
        n = ch["levels"]
        if n == "rest":
            if i != len(d["chapters"]) - 1:
                raise ValueError("chapters.yaml: 'levels: rest' only for the last chapter")
            n = gmax - depth
        if not isinstance(n, int) or n < 1:
            raise ValueError("chapters.yaml: chapter %s: levels %r" % (ch["id"], ch["levels"]))
        c = dict(ch)
        c["n_levels"] = n
        c["first_depth"], c["last_depth"] = depth + 1, depth + n
        depth += n
        chs.append(c)
    if depth > gmax:
        raise ValueError("chapters.yaml: %d levels in all, more than global_max %d" % (depth, gmax))
    if len({c["id"] for c in chs}) != len(chs):
        raise ValueError("chapters.yaml: duplicate chapter ids")
    return dict(global_max=gmax, today=d.get("today", {}), chapters=chs)


def depth(ch, local):
    """profondita' globale del piano locale `local` (1..n_levels) del capitolo"""
    if not 1 <= local <= ch["n_levels"]:
        raise ValueError("chapter %s has levels 1..%d, not %d" % (ch["id"], ch["n_levels"], local))
    return ch["first_depth"] + local - 1


def locate(chapters, d):
    """(capitolo, piano locale) della profondita' globale d"""
    for ch in chapters:
        if ch["first_depth"] <= d <= ch["last_depth"]:
            return ch, d - ch["first_depth"] + 1
    raise ValueError("depth %d outside the chapters" % d)


if __name__ == "__main__":
    try:
        D = load()
    except ValueError as e:
        print("ERROR", e); sys.exit(1)
    for ch in D["chapters"]:
        f = ch.get("final") or {}
        print("chapter %d %-22s local 1..%-3d depth %3d..%-3d final map: %s" % (
            ch["id"], ch["name"], ch["n_levels"], ch["first_depth"], ch["last_depth"],
            "%s (boss %s)" % (f.get("name"), f.get("boss")) if f else "-"))
