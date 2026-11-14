"""Build smoke tests (static, < 2 s): memory margin, save version, centred version string, manual source, graphics
atlas. They read the files produced by the build in out/work/."""
import os, re, subprocess, sys
from lib.c64 import ROOT, labels
from c64test import test, check


@test("BUILD-01", "memory margin positive (code below $8720 >= 128 B, total >= 256 B)")
def margin(ctx):
    L = labels("game")
    m1 = L["SCR_H"] + 800 - L["gfx_data"]; m2 = L["FREE_RAM_END"] + 1 - L["code2_end"]
    check(m1 >= 128 and m2 >= 0 and m1 + m2 >= 256, "margin %d B + %d B" % (m1, m2))


@test("BUILD-02", "SAVE_VER in the PRG = save_version in version.yaml")
def savever(ctx):
    want = int(subprocess.check_output([sys.executable, os.path.join(ROOT, "tools", "build", "gen_version.py"), "--print", "save_version"], cwd=ROOT))
    got = labels("game").get("SAVE_VER")
    check(got == want, "version.yaml %s, PRG %s" % (want, got))


@test("BUILD-03", "\"version x.y\" centred in the loader, start menu and game menu")
def vercenter(ctx):
    t = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "test_version_center.py")], capture_output=True, text=True)
    check(t.returncode == 0, (t.stdout + t.stderr).strip().splitlines()[-1] if (t.stdout + t.stderr).strip() else "exit %d" % t.returncode)


@test("BUILD-04", "manual: images and placeholders of the source")
def manual(ctx):
    M = os.path.join(ROOT, "docs", "manual"); h = open(os.path.join(M, "manuale_src.html")).read(); bad = []
    for f in re.findall(r'src="img/([^"]+)"', h):
        if not os.path.exists(os.path.join(M, "shots", f)): bad.append("missing shots/" + f)
    for f in re.findall(r'src="mon/([^"]+)"', h):
        if not os.path.exists(os.path.join(M, "mon", f)): bad.append("missing mon/" + f)
    for p in ("{{MONSTER_ROWS}}", "{{MIN_ROW}}", "{{MAX_ROW}}"):
        if p not in h: bad.append("missing placeholder " + p)
    check(not bad, "; ".join(bad))


@test("BUILD-05", "graphics atlas: names, ids, sample dungeon, groups")
def atlas(ctx):
    t = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "atlas", "gen_atlas.py"), "--check"], capture_output=True, text=True, cwd=ROOT)
    check(t.returncode == 0, (t.stdout + t.stderr).strip().splitlines()[-1] if (t.stdout + t.stderr).strip() else "exit %d" % t.returncode)
