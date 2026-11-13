"""Analysis of the assembled code (11/11, tools/build/asm_audit.py, out/asm_audit/analisi_assembly.md): GAME has no unreachable code
but the entries of the jump tables, the dead code found on 11/11 is gone, and the generated sources given to the
assembler carry their comments (tile names, item and monster indexes). Pure Python on the listings of the build."""
import json, os, re, subprocess, sys
from lib.runner import test, check
from lib.c64 import ROOT, OUT


@test("ASM-10", "tools/build/asm_audit.py: GAME code all reachable (but jump tables), no fill_rect / chst_hold any more")
def asm_reach(ctx):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build", "asm_audit.py")], cwd=ROOT, capture_output=True, text=True)
    check(r.returncode == 0, r.stderr[-300:])
    d = json.load(open(os.path.join(OUT, "asm_audit.json")))
    un = [x for x in d["game"]["unreached"] if "post_walls" not in x["src"] and "gen_dmain" not in x["src"]]
    check(not un, "unreachable code in GAME: %s" % ["$%04X %d B %s" % (x["a"], x["size"], x["src"]) for x in un])
    lb = open(os.path.join(OUT, "game.lbl")).read()
    for n in ("fill_rect", "chst_hold"):
        check(not re.search(r"^%s\s*=" % n, lb, re.M), "%s is back in GAME" % n)
    check(os.path.exists(os.path.join(OUT, "asm_audit", "analisi_assembly.md")), "out/asm_audit/analisi_assembly.md missing")


@test("ASM-11", "generated sources commented: every T_ tile constant with its description, item ids and monster types listed in db.asm")
def asm_comments(ctx):
    g = open(os.path.join(OUT, "gfx_consts.inc")).read().splitlines()
    t = [l for l in g if l.startswith("T_")]
    bare = [l for l in t if ";" not in l]
    check(t and not bare, "T_ constants without a comment: %s" % bare[:5])
    db = open(os.path.join(OUT, "db.asm")).read()
    check(re.search(r"^;\s+id: 0 none, 1 dagger", db, re.M), "item index list missing in db.asm")
    check(re.search(r"^;\s+tipo: 1 fallen", db, re.M), "monster type list missing in db.asm")
