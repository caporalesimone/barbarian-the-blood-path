"""Bestiary (sanity moved to regression on 11/11; 11/11, data/monsters/bestiary.tsv, tools/build/bestiary.py, docs/bestiario.md): the table is the source of the
monsters; the game takes the rows implemented = yes (today's 9 monsters, out/work/db.asm unchanged), every chapter has its own
bestiary (base, strong variants of its bases, one boss), the final boss is in the last story chapter. Pure Python."""
import os, re, sys, tempfile
from lib.runner import test, check

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "memory-map", "simulators")]
import bestiary as B  # noqa: E402
import chapters_db as CD  # noqa: E402


@test("BEST-10", "every chapter of chapters.yaml (but the Abyss) has base monsters, their strong variants and one boss = its final map boss")
def best_chapters(ctx):
    rows = B.load()
    D = CD.load()
    for ch in D["chapters"]:
        if not ch.get("final"):
            continue
        rs = [r for r in rows if r["chapter"] == ch["id"]]
        base = [r["id"] for r in rs if r["tier"] == "base"]
        strong = [r for r in rs if r["tier"] == "strong"]
        boss = [r["id"] for r in rs if r["tier"] in ("boss", "final")]
        check(len(base) >= 3, "chapter %d: %d base monsters" % (ch["id"], len(base)))
        check(strong and all(r["strong_of"] in base for r in strong), "chapter %d: strong variants %s" % (ch["id"], [r["id"] for r in strong]))
        check(ch["final"]["boss"] in boss, "chapter %d: final map boss %s not in its bestiary %s" % (ch["id"], ch["final"]["boss"], boss))
    lor = [r for r in rows if r["id"] == "lord_of_ruin"][0]
    last = [c for c in D["chapters"] if c.get("final")][-1]
    check(lor["chapter"] == last["id"], "Lord of Ruin in chapter %d, last story chapter %d" % (lor["chapter"], last["id"]))


@test("BEST-11", "the game = the table: monster types of out/work/db.asm are the rows implemented = yes, in order")
def best_game(ctx):
    rows = B.game_rows()
    db = open(os.path.join(ROOT, "out", "work", "db.asm")).read()
    n = int(re.search(r"^N_MTYPES\s*=\s*(\d+)", db, re.M).group(1))
    check(n == len(rows) == 9, "N_MTYPES %d, implemented rows %d" % (n, len(rows)))
    check(rows[-1]["id"] == "lord_of_ruin" and "final" in rows[-1]["flags"], "the last game monster is %s" % rows[-1]["id"])
    tiers = [r["tier"] for r in rows]
    check(tiers == sorted(tiers, key=("base", "strong", "final").index), "game order base/strong/final: %s" % tiers)


@test("BEST-12", "the checker refuses a wrong bestiary: strong_of of another chapter, unknown tier, duplicate id")
def best_refuse(ctx):
    lines = open(B.TSV).read().splitlines()
    head, rows = lines[0], lines[1:]
    c = B.COLUMNS.index
    strong2 = next(l for l in rows if l.split("\t")[c("tier")] == "strong" and l.split("\t")[c("chapter")] == "2")
    base1 = next(l for l in rows if l.split("\t")[c("id")] == "fallen")
    cases = []
    x = strong2.split("\t"); x[c("strong_of")] = "fallen"; cases.append(("strong_of in chapter 1", [head, base1, "\t".join(x)]))
    x = base1.split("\t"); x[c("tier")] = "elite"; cases.append(("tier elite", [head, "\t".join(x)]))
    cases.append(("duplicate", [head, base1, base1]))
    for what, ls in cases:
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, dir=os.path.join(ROOT, "out", "tmp")) as f:
            f.write("\n".join(ls) + "\n")
        try:
            B.load(f.name)
            check(False, "%s: accepted" % what)
        except ValueError:
            pass
        finally:
            os.unlink(f.name)
