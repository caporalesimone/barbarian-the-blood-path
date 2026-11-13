"""Test registry and report (10/11). Every test has an upper-case ID (AREA-NN, e.g. SHOP-01) and a short description.

    from lib.runner import test, check, Skip

    @test("SHOP-01", "buy: gold and pack")
    def shop_buy(ctx): check(cond, "failure reason")

A module (cases.py) may define setup(ctx) / teardown(ctx): they run once before the first and after the last of its
selected tests (e.g. one VICE session for all the game smoke tests). CHAIN = True in the module: the tests are a
sequence (happy path) and after a failure the following ones are skipped with the reason.
script(id, desc, argv): a test that runs an external program (exit 0 = pass; FAIL/error lines = reason)."""
import subprocess, sys, time

REG = []


class Skip(Exception):
    pass


class Fail(AssertionError):
    pass


def test(tid, desc, slow=False):
    def deco(f):
        REG.append(dict(id=tid, desc=desc, fn=f, module=f.__module__, slow=slow))
        return f
    return deco


def check(cond, reason):
    if not cond:
        raise Fail(reason)


def script(tid, desc, argv, timeout=900, cwd=None):
    def run(ctx):
        t = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, cwd=cwd, text=True)
        if t.returncode != 0:
            out = [l.strip() for l in t.stdout.splitlines() if l.strip()]
            lines = [l for l in out if "FAIL" in l or "rror" in l or "ATTENZ" in l]
            msg = "; ".join((lines or out[-3:] or ["exit %d" % t.returncode])[-4:])
            raise Fail("".join(ch if ch.isprintable() else " " for ch in msg)[:400])
    run.__name__ = "script_" + tid.replace("-", "_")
    REG.append(dict(id=tid, desc=desc, fn=run, module=sys._getframe(1).f_globals["__name__"], slow=True))
