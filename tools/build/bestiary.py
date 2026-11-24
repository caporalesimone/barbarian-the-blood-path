#!/usr/bin/env python3
"""Bestiario (11/11): data/monsters/bestiary.tsv e' la sorgente dei mostri, come monstdat.tsv di Diablo/DevilutionX
(assets/txtdata/monsters/monstdat.tsv + unique_monstdat.tsv). Una riga per mostro, un capitolo per riga: ogni capitolo
ha il suo bestiario che sostituisce quello del capitolo precedente (docs/wiki/bestiario.md). Colonne: data/monsters/README.md.

Nel gioco di oggi (un solo "capitolo" di 20 piani) entrano solo le righe con implemented = yes, nell'ordine del file
(base, forti, finale: il tipo del mostro = posizione); le altre sono concept. merge_rules(R) / merge_balance(B) rimettono
i mostri nelle sezioni `monsters` di rules.yaml (combattimento) e balance.yaml (spawn, colore, velocita', bottino) che
leggono tools/build/gen_db.py, tools/manual/gen_manual.py e tools/simulators/: out/work/db.asm identico a prima.
Uso: python3 tools/build/bestiary.py   (controlla la tabella e stampa i bestiari per capitolo)"""
import csv, os, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TSV = os.path.join(ROOT, "data", "monsters", "bestiary.tsv")
COLUMNS = ["id", "chapter", "tier", "strong_of", "name", "floor", "level", "hp", "ac", "att", "dmg", "save", "xp", "speed",
           "color", "loot_level_bonus", "flags", "ai", "sprite", "implemented", "notes"]
TIERS = ("base", "strong", "boss", "final")
INTS = ("chapter", "floor", "level", "speed", "color", "loot_level_bonus")
FORMULAS = ("hp", "ac", "att", "dmg", "save", "xp")     # (24/11) formule (tools/build/mon_stats.py), dmg = dadi + formula
FLAGS = ("strong", "final", "stun_immune", "chapter_boss")


def load(path=TSV):
    rows, seen = [], set()
    with open(path, newline="") as f:
        rd = csv.reader(f, delimiter="\t")
        if next(rd) != COLUMNS:
            raise ValueError("bestiary.tsv: columns differ from %s" % COLUMNS)
        for n, c in enumerate(rd, 2):
            if not c or not "".join(c).strip():
                continue
            if len(c) != len(COLUMNS):
                raise ValueError("bestiary.tsv line %d: %d cells" % (n, len(c)))
            r = dict(zip(COLUMNS, (x.strip() for x in c)))
            if r["id"] in seen:
                raise ValueError("bestiary.tsv line %d: duplicate id %s" % (n, r["id"]))
            seen.add(r["id"])
            if r["tier"] not in TIERS:
                raise ValueError("bestiary.tsv line %d (%s): tier %s" % (n, r["id"], r["tier"]))
            if r["implemented"] not in ("yes", "no"):
                raise ValueError("bestiary.tsv line %d (%s): implemented yes/no" % (n, r["id"]))
            for k in INTS:
                r[k] = int(r[k])
            r["flags"] = [x for x in r["flags"].split(",") if x]
            for fl in r["flags"]:
                if fl not in FLAGS:
                    raise ValueError("bestiary.tsv line %d (%s): flag %s" % (n, r["id"], fl))
            if (r["tier"] == "strong") != bool(r["strong_of"]):
                raise ValueError("bestiary.tsv line %d (%s): strong_of only (and always) for tier strong" % (n, r["id"]))
            if not 0 <= r["color"] <= 15:
                raise ValueError("bestiary.tsv line %d (%s): colour 0..15" % (n, r["id"]))
            rows.append(r)
    ids = {r["id"]: r for r in rows}
    for r in rows:
        if r["strong_of"] and (r["strong_of"] not in ids or ids[r["strong_of"]]["chapter"] != r["chapter"]):
            raise ValueError("bestiary.tsv (%s): strong_of %s not a base monster of the same chapter" % (r["id"], r["strong_of"]))
    return rows


def game_rows(rows=None):
    """i tipi del gioco nel capitolo 1 (righe implemented = yes del capitolo 1 e il boss finale), nell'ordine del file:
    tipo 1..9. (24/11) Le righe implemented = yes di un capitolo con own_stats (data/chapters.yaml) sono i suoi tipi 1..8
    (tools/build/mon_stats.py type_rows)"""
    return [r for r in (rows or load()) if r["implemented"] == "yes" and (r["chapter"] == 1 or r["tier"] == "final")]


def rules_entry(r):
    e = {k: r[k] for k in ("id", "chapter", "floor", "level", "hp", "ac", "att", "dmg", "save", "xp")}
    for fl in ("strong", "final", "stun_immune"):
        if fl in r["flags"]:
            e[fl] = True
    return e


def balance_entry(r):
    e = {"tier": r["tier"]}
    if r["strong_of"]:
        e["strong_of"] = r["strong_of"]
    e.update(color=r["color"], speed=r["speed"], loot_level_bonus=r["loot_level_bonus"])
    return e


def merge_rules(R, rows=None):
    R["monsters"] = {r["id"]: rules_entry(r) for r in game_rows(rows)}
    return R


def merge_balance(B, rows=None):
    B["monsters"] = {r["id"]: balance_entry(r) for r in game_rows(rows)}
    return B


def load_balance(root=ROOT):
    B = yaml.safe_load(open(os.path.join(root, "data", "balance.yaml")))
    return merge_balance(B, load(os.path.join(root, "data", "monsters", "bestiary.tsv")))


def by_chapter(rows=None):
    out = {}
    for r in rows or load():
        out.setdefault(r["chapter"], []).append(r)
    return out


if __name__ == "__main__":
    try:
        rows = load()
    except ValueError as e:
        print("ERROR", e); sys.exit(1)
    for ch, rs in sorted(by_chapter(rows).items()):
        print("== chapter %d" % ch)
        for r in rs:
            print("  %-22s %-6s %-26s depth %3d  hp %-12s ac %-7s att %-11s dmg %-14s xp %-13s %s" % (
                r["id"], r["tier"], r["name"], r["floor"], r["hp"], r["ac"], r["att"], r["dmg"], r["xp"],
                "" if r["implemented"] == "yes" else "(concept)"))
