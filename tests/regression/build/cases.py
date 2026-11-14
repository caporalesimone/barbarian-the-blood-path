import os, sys
from lib.runner import script
from lib.c64 import ROOT
H = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
"""Test variants of the build (used for screenshots and tests): they must assemble."""
from lib.runner import test, check  # noqa: E402
import subprocess  # noqa: E402


def variant(tid, desc, env):
    @test(tid, desc)
    def f(ctx):
        e = dict(os.environ); e.update(env)
        t = subprocess.run([os.path.join(ROOT, "tools", "build", "asm.sh"), "test"], cwd=ROOT, env=e, capture_output=True, text=True)
        check(t.returncode == 0, (t.stdout + t.stderr).strip().splitlines()[-1] if (t.stdout + t.stderr).strip() else "exit %d" % t.returncode)


variant("BUILD-10", "variant: saved hero details (TESTUI=2)", {"NOKEYS": "1", "TESTUI": "2"})
variant("BUILD-11", "variant: game menu (TESTUI=25)", {"NOKEYS": "1", "TESTUI": "25"})
variant("BUILD-12", "variant: Fire on stairs (TESTFIRE)", {"TESTFIRE": "10", "TESTSP": "0"})
variant("BUILD-13", "variant: skill change (TESTSK)", {"TESTSK": "1", "TESTSP": "0"})


def teardown(ctx):
    """the variants overwrite out/work/game.*: restore the normal build for the tests that follow"""
    subprocess.run([os.path.join(ROOT, "tools", "build", "asm.sh")], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
