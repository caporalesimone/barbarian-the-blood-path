"""Chapters (11/11, docs/wiki/capitoli.md, docs/wiki/quests.md 3.8; sanity moved to regression on 11/11): data/chapters.yaml
gives every chapter its LOCAL levels 1..n (they restart in every chapter) and the GLOBAL depth 1..255 that drives the
difficulty (tools/build/chapters_db.py); the balancing simulators work by chapter (tools/simulators/chapters.py). Pure Python, no VICE."""
import contextlib, io, os, sys
from c64test import test, check

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools", "simulators"))
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "simulators")]


@test("CHAP-10", "chapters.yaml: local levels restart at 1, global depth = previous levels + local, the Abyss fills up to 255")
def chap_data(ctx):
    import chapters_db as CD
    D = CD.load()
    chs = D["chapters"]
    check(chs[0]["first_depth"] == 1, "chapter 1 starts at depth %d" % chs[0]["first_depth"])
    for a, b in zip(chs, chs[1:]):
        check(b["first_depth"] == a["last_depth"] + 1, "chapter %d starts at depth %d (previous ends at %d)" % (b["id"], b["first_depth"], a["last_depth"]))
    check(chs[-1]["last_depth"] == D["global_max"] == 255, "last depth %d, global_max %d" % (chs[-1]["last_depth"], D["global_max"]))
    c2 = chs[1]
    check(CD.depth(c2, 1) == chs[0]["n_levels"] + 1, "chapter 2 level 1 = depth %d (expected %d)" % (CD.depth(c2, 1), chs[0]["n_levels"] + 1))
    ch, loc = CD.locate(chs, CD.depth(chs[3], 3))
    check(ch["id"] == chs[3]["id"] and loc == 3, "locate(depth of chapter 4 level 3) = chapter %s level %d" % (ch["id"], loc))
    fin = [c for c in chs if c.get("final") and c["final"].get("boss") == "lord_of_ruin"]
    check(len(fin) == 1 and fin[0] is [c for c in chs if c.get("final")][-1], "the final boss is not on the last story chapter")
    check(fin[0]["last_depth"] == 20, "the throne room at depth %d (today 20)" % fin[0]["last_depth"])


@test("CHAP-11", "tools/simulators/chapters.py: every generated level of a chapter at its global depth with the chapter's bestiary, the chapter boss")
def chap_sim(ctx):
    import chapters as C
    with contextlib.redirect_stdout(io.StringIO()):
        rows = C.report([1, 2, 5], fights=4, step=80)
    c1 = [r for r in rows if r["chapter"] == 1 and "final" not in r]
    n1 = C.chapter(1)["n_levels"]
    check([r["level"] for r in c1] == list(range(1, n1)), "chapter 1 levels %s" % [r["level"] for r in c1])
    c2 = [r for r in rows if r["chapter"] == 2 and "final" not in r]
    check(c2[0]["level"] == 1 and c2[0]["depth"] == n1 + 1, "chapter 2 first row %s" % c2[0])
    g = C.groups(C.chapter(2), c2[0]["depth"])
    check(all(m in [b["id"] for b in C.bestiary(C.chapter(2))] for v in g.values() for m in v), "chapter 2 fights monsters of other chapters: %s" % g)
    bosses = {r["chapter"]: r["boss"] for r in rows if "boss" in r}
    check(bosses.get(1) == "hollow_abbot" and bosses.get(2) == "mother_stitch", "chapter bosses %s" % bosses)
    ab = [r for r in rows if r["chapter"] == 5]
    check(ab and ab[-1]["depth"] == 255 and all(0 <= r["chest_level"] <= 255 for r in ab), "Abyss rows %s" % ab[-1:])
