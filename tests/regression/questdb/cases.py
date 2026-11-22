"""Quest database (data/quests/next/quests.yaml, proposal of 22/11: the game does not read it yet). Data only, no emulator:
limits of the texts, characters of the 5-bit table (owner's rule H7), references to NPCs, monsters, quest items and uniques."""
import csv
import os
import re
import yaml
from c64test import test, check

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
OK = re.compile(r"^[a-z0-9 .,:'!?\-()+/%]*$")


def load():
    q = yaml.safe_load(open(os.path.join(ROOT, "data", "quests", "next", "quests.yaml")))
    uq = {u["name"] for u in csv.DictReader(open(os.path.join(ROOT, "data", "items", "next", "uniques.tsv")), delimiter="\t")}
    mon = {}
    for m in csv.DictReader(open(os.path.join(ROOT, "data", "monsters", "bestiary.tsv")), delimiter="\t"):
        mon.setdefault(int(m["chapter"]), set()).add(m["name"].lower())
    return q, uq, mon


@test("QUESTDB-NEXT-10", "quest database (data/quests/next): 12 chain steps, 15 side quests, 6 repeatable models; limits, 5-bit characters, references")
def questdb(ctx):
    q, uq, mon = load()
    bad = []
    qs = q["quests"]
    ids = [str(x["id"]) for x in qs]
    check(len(set(ids)) == len(ids), "duplicated ids")
    kinds = {k: [x for x in qs if x["kind"] == k] for k in ("chain", "side", "repeatable")}
    check([x["id"] for x in kinds["chain"]] == list(range(1, 13)), "chain: steps 1..12 in order")
    check(len(kinds["side"]) == 15 and len(kinds["repeatable"]) == 6, "%d side, %d repeatable" % (len(kinds["side"]), len(kinds["repeatable"])))
    npcs = {c: {v["chain"], *v["side"]} for c, v in q["npcs"].items()}
    given = set()
    for x in qs:
        i = x["id"]
        for f, lim in (("text", 600), ("done", 600), ("goal_text", 36)):
            s = x[f]
            if len(s) > lim: bad.append("%s: %s %d > %d" % (i, f, len(s), lim))
            if not OK.match(s.replace("{n}", "").replace("{t}", "").replace("{m}", "").replace("{l}", "").replace("{g}", "")):
                bad.append("%s: %s has characters outside the 5-bit table" % (i, f))
        titles = [x["title"]] if "title" in x else [t for ts in x["chapters"].values() for t in ts]
        for t in titles:
            if len(t) > 24 or not OK.match(t): bad.append("%s: title %r" % (i, t))
        g = x["goal"]
        if g["type"] not in "KBCIGPV": bad.append("%s: goal type %s" % (i, g["type"]))
        if x["kind"] == "repeatable":
            continue
        c = x["chapter"]
        if "{t}" in x["goal_text"]:       # the longest counter must fit: "12/12"
            n = len(x["goal_text"].replace("{n}", str(g["count"])).replace("{t}", str(g["count"])))
            if n > 36: bad.append("%s: goal_text with the counter %d > 36" % (i, n))
        for who in (x["giver"], x.get("turn_in", x["giver"])):
            if who not in npcs[c]: bad.append("%s: NPC %s not in chapter %d" % (i, who, c))
        if x["kind"] == "chain" and x["id"] % 3 == 1 and x["giver"] != q["npcs"][c]["chain"]:
            bad.append("%s: the first step of the chapter is not given by the chain NPC" % i)
        if g.get("monster") and g["monster"] not in mon[c]: bad.append("%s: monster %s not in chapter %d" % (i, g["monster"], c))
        if g.get("item") and g["item"] not in q["quest_items"]: bad.append("%s: quest item %s" % (i, g["item"]))
        if "after" in x and x["after"] not in ids: bad.append("%s: after %s" % (i, x["after"]))
        u = x["reward"].get("unique")
        if u:
            if u not in uq: bad.append("%s: unique %s not in uniques.tsv" % (i, u))
            if u in given: bad.append("%s: unique %s given twice" % (i, u))
            given.add(u)
    for u, s in q["unique_sources"].items():
        if u not in uq: bad.append("unique_sources: %s" % u)
    rest = uq - given - set(q["unique_sources"])
    if rest: bad.append("uniques with no source: %s" % sorted(rest))
    skills = [x["reward"]["skill"] for x in kinds["chain"] if "skill" in x["reward"]]
    check(skills == ["whirlwind", "battle cry", "rage", "smash", "frenzy"], "skills of the chain: %s" % skills)
    purses = [x["reward"]["purse"] for x in kinds["chain"] if "purse" in x["reward"]]
    check(purses == [1000, 3000, 5000, 10000], "purse steps: %s" % purses)
    check(not bad, "; ".join(bad[:5]) + (" (+%d)" % (len(bad) - 5) if len(bad) > 5 else ""))


T5X = "0123456789?-+!,'()>%"


def t5(s):
    """the 5-bit text of the game (macro t5, src/common/macros.inc): 1-26 letters, 27 space, 28 ':', 29 '.', 30 '/',
    31 + index in T5X; 0 at the end; 3 symbols in a 16-bit word, high byte first"""
    y = []
    for ch in s:
        if "a" <= ch <= "z": y.append(ord(ch) - 96)
        else: y += {" ": [27], ":": [28], ".": [29], "/": [30]}.get(ch) or [31, T5X.index(ch)]
    y.append(0)
    while len(y) % 3: y.append(0)
    out = bytearray()
    for i in range(0, len(y), 3):
        w = y[i] * 1024 + y[i + 1] * 32 + y[i + 2]
        out += bytes([w >> 8, w & 255])
    return bytes(out)


@test("QUESTDB-NEXT-11", "quest texts at 5 bits (H7): bytes and disk blocks of every quest file (title, goal, text, done), with and without ZX0; every file <= 1000 B")
def questdb_size(ctx):
    import shutil, subprocess, tempfile
    q, _, _ = load()
    zx0 = shutil.which("zx0")
    rows, tot_b, tot_z, bad = [], 0, 0, []
    for x in q["quests"]:
        parts = [x.get("title") or "", x["goal_text"], x["text"], x["done"]]
        if x["kind"] == "repeatable":
            parts[0] = "/".join(t for ts in x["chapters"].values() for t in ts)
        parts = [p.replace("{n}", "").replace("{t}", "").replace("{m}", "").replace("{l}", "").replace("{g}", "") for p in parts]
        raw = b"".join(t5(p) for p in parts) + bytes(16)                     # + ~16 B of header (reward, goal)
        z = len(raw)
        if zx0:
            with tempfile.TemporaryDirectory() as d:
                a, b = os.path.join(d, "a"), os.path.join(d, "b")
                open(a, "wb").write(raw)
                subprocess.run([zx0, "-f", a, b], capture_output=True)
                if os.path.exists(b): z = os.path.getsize(b)
        plain = sum(len(p) + 1 for p in parts) + 16
        blocks = (len(raw) + 2 + 253) // 254
        rows.append((str(x["id"]), plain, len(raw), z, blocks))
        tot_b += blocks; tot_z += (z + 2 + 253) // 254
        if len(raw) > 1000: bad.append("%s: %d B" % (x["id"], len(raw)))
    print("      %d files: %d B as screen codes, %d B at 5 bits, %d B with ZX0; disk %d blocks (5 bits), %d blocks (ZX0)%s" % (
        len(rows), sum(r[1] for r in rows), sum(r[2] for r in rows), sum(r[3] for r in rows), tot_b, tot_z, "" if zx0 else " (no zx0: not measured)"))
    print("      biggest: " + ", ".join("%s %d B" % (r[0], r[2]) for r in sorted(rows, key=lambda r: -r[2])[:5]))
    check(not bad, "quest files over 1000 B: %s" % bad)
