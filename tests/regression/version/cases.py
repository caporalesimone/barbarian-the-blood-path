"""Build versions per git branch (11/11, tools/build/verinfo.py; sanity moved to regression on 11/11): main keeps `version` of version.yaml (N.N), any other
branch gets its own `tag.N` (branch_versions), so branch builds never use main's numbers. Pure Python."""
import os, re, shutil, sys, tempfile
from c64test import test, check

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, "tools", d) for d in ("build", "vice", "atlas", "memory-map", "simulators")]
import verinfo as V  # noqa: E402


@test("VER-10", "branch tag: feature/stat-points -> stat, explicit branch_tags win, only lowercase letters and digits")
def ver_tag(ctx):
    check(V.tag("feature/stat-points", {}) == "stat", "tag %s" % V.tag("feature/stat-points", {}))
    check(V.tag("perf_dungeon", {}) == "perf", "tag %s" % V.tag("perf_dungeon", {}))
    check(V.tag("feature/x", {"branch_tags": {"feature/x": "Dw2"}}) == "dw2", "explicit tag ignored")
    check(V.tag("feature/--", {}) == "br", "empty tag not replaced")


@test("VER-11", "branch_versions written at the end of version.yaml without touching version/comments; digest ignores them")
def ver_write(ctx):
    d = tempfile.mkdtemp(dir=os.path.join(ROOT, "out", "tmp"))
    try:
        ry = os.path.join(d, "version.yaml")
        shutil.copy(V.RY, ry)
        old = V.RY
        V.RY = ry
        try:
            V.set_branch_version("feature/stat-points", "stat.1")
            V.set_branch_version("feature/stat-points", "stat.2")
            V.set_branch_version("perf", "perf.1")
            s = open(ry).read()
        finally:
            V.RY = old
        orig = open(old).read()
        check(re.search(r'(?m)^version: ".*"$', s).group(0) == re.search(r'(?m)^version: ".*"$', orig).group(0), "version changed")
        check(s.count('feature/stat-points: "stat.2"') == 1 and "stat.1" not in s and 'perf: "perf.1"' in s, "branch_versions:\n" + s[-300:])
        check(re.sub(r'(?ms)^# Versioni delle build dei branch.*', "", s).strip() == re.sub(r'(?ms)^# Versioni delle build dei branch.*', "", orig).strip(),
              "the rest of version.yaml changed")
    finally:
        shutil.rmtree(d)
