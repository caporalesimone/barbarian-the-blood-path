#!/usr/bin/env python3
"""Test runner (10/11). Three suites in three folders:
  smoke/       a few fast tests on the happy path of the main features (VICE with shortcuts: memory, routines)
  sanity/      the tests of the feature in development; when the feature is done they move to smoke or regression
  regression/  all the corner cases, as close as possible to the real game (slow ones too)
In every suite one folder per feature; its cases.py registers the tests (ID, description); the other files of the
folder are scripts and data of that feature.
Usage: tests/run.py [smoke|sanity|regression|all ...] [-k ID|prefix ...] [--list] [--md]
Duration caps (CAPS): smoke 20 s, smoke + sanity 35 s, one smoke / sanity test 10 s (exit 1 with "TIME CAP" lines).
Report: on screen and in out/work/test_report.txt / out/work/test_report.json (ID, suite, result, time, reason).
Live status (14/11, for the viewer page): out/tmp/tests.json, rewritten after every test (state, current test, results so far)."""
import glob, importlib.util, json, os, re, sys, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import runner as R  # noqa: E402

SUITES = ["smoke", "sanity", "regression"]
# duration caps (12/11, rule of the project owner): they keep the build tests short. The sum of the times of the tests of
# the suites (setup included): smoke alone 20 s, smoke + sanity 35 s; one smoke or sanity test 10 s. Regression: no cap.
# TEST_CAP_SCALE=0.1 shrinks them (to try the check).
CAPS = {"test": 10.0, "smoke": 20.0, "smoke+sanity": 35.0}


def load(suite):
    mods = []
    for f in sorted(glob.glob(os.path.join(HERE, suite, "**", "cases.py"), recursive=True)):
        name = "%s.%s" % (suite, os.path.relpath(f, os.path.join(HERE, suite))[:-3].replace(os.sep, "."))
        n0 = len(R.REG)
        spec = importlib.util.spec_from_file_location(name, f)
        m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m
        spec.loader.exec_module(m)
        for t in R.REG[n0:]:
            t["suite"] = suite; t["module"] = name
        mods.append(m)
    return mods


def lock():
    """one test run at a time: VICE's remote monitor port (6510) is shared, two runs would talk to each other's VICE"""
    import fcntl
    os.makedirs(os.path.join(os.path.dirname(HERE), "out", "tmp"), exist_ok=True)
    f = open(os.path.join(os.path.dirname(HERE), "out", "tmp", ".test.lock"), "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another test run is active: waiting for it"); fcntl.flock(f, fcntl.LOCK_EX)
    return f


LIVE = os.path.join(os.path.dirname(HERE), "out", "tmp", "tests.json")
ST = {}


def live(**kw):
    """live status for the viewer page: atomic rewrite of out/tmp/tests.json (never fails the run)"""
    ST.update(kw, updated=round(time.time(), 1))
    try:
        with open(LIVE + ".tmp", "w") as f:
            json.dump(ST, f)
        os.replace(LIVE + ".tmp", LIVE)
    except OSError:
        pass


def check_caps(res, suites, filtered):
    """duration caps: one smoke / sanity test, the smoke suite, smoke + sanity (only for runs without -k)"""
    sc = float(os.environ.get("TEST_CAP_SCALE", "1"))
    err = []
    for r in res:
        if r["suite"] in ("smoke", "sanity") and r["time"] > CAPS["test"] * sc:
            err.append("%s took %.1f s (cap %.1f s per test)" % (r["id"], r["time"], CAPS["test"] * sc))
    if filtered: return err
    tm = lambda *s: sum(r["time"] for r in res if r["suite"] in s)
    if suites == ["smoke"] and tm("smoke") > CAPS["smoke"] * sc:
        err.append("smoke %.1f s (cap %.1f s)" % (tm("smoke"), CAPS["smoke"] * sc))
    if suites == ["smoke", "sanity"] and tm("smoke", "sanity") > CAPS["smoke+sanity"] * sc:
        err.append("smoke + sanity %.1f s (cap %.1f s)" % (tm("smoke", "sanity"), CAPS["smoke+sanity"] * sc))
    return err


def main():
    args = sys.argv[1:]
    _lk = None if ("--list" in args or "--md" in args) else lock()  # noqa: F841  (listing: no VICE, no lock)
    suites = [a for a in args if a in SUITES + ["all"]] or ["smoke"]
    if "all" in suites: suites = SUITES
    keys = [args[i + 1].upper() for i, a in enumerate(args) if a == "-k" and i + 1 < len(args)]
    mods = {}
    for s in suites:
        for m in load(s): mods[m.__name__] = m
    tests = [t for t in R.REG if not keys or any(t["id"] == k or t["id"].startswith(k) for k in keys)]
    ids = [t["id"] for t in R.REG]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print("duplicate IDs: " + ", ".join(dup)); sys.exit(2)
    if "--list" in args:
        for t in tests: print("%-14s %-10s %s" % (t["id"], t["suite"], t["desc"]))
        return
    if "--md" in args:                              # the list for docs/test.md ("Elenco"), one table per suite
        for su in SUITES:
            tl = [t for t in tests if t["suite"] == su]
            if not tl: continue
            print("### %s (%d)\n\n| ID | Test |\n|---|---|" % (su, len(tl)))
            for t in tl: print("| `%s` | %s |" % (t["id"], t["desc"]))
            print()
        return
    res, t_all = [], time.time()
    live(state="running", suites=suites, filter=keys, total=len(tests), started=round(t_all, 1), current=None, results=res)
    by_mod = {}
    for t in tests: by_mod.setdefault(t["module"], []).append(t)
    for mname, tl in by_mod.items():
        m, ctx = mods[mname], {}
        os.environ["C64_MEMPROBE_TAG"] = re.sub(r"\.cases$", "", mname)   # memory probe (C64_MEMPROBE=1): scenario name of the RAM dumps
        chain = getattr(m, "CHAIN", False)
        broken = None
        t0 = time.time()
        try:
            if hasattr(m, "setup"): m.setup(ctx)
            setup_err = setup_skip = None
        except R.Skip as e:                         # (14/11) a setup that cannot run (e.g. no vc64web daemon): SKIP, not FAIL
            setup_err, setup_skip = None, str(e)
        except Exception as e:
            setup_skip = None
            setup_err = "setup: %s" % (e,)
            if os.environ.get("TESTDEBUG"): traceback.print_exc()
        t_setup = time.time() - t0
        for i, t in enumerate(tl):
            r = dict(id=t["id"], suite=t["suite"], desc=t["desc"], module=mname)
            live(current=dict(id=t["id"], suite=t["suite"], desc=t["desc"], since=round(time.time(), 1)))
            t0 = time.time()
            if setup_skip:
                r.update(result="SKIP", reason="setup: " + setup_skip)
            elif setup_err:
                r.update(result="FAIL", reason=setup_err)
            elif broken:
                r.update(result="SKIP", reason="after the failure of %s" % broken)
            else:
                try:
                    t["fn"](ctx); r.update(result="PASS", reason="")
                except R.Skip as e:
                    r.update(result="SKIP", reason=str(e))
                except AssertionError as e:
                    r.update(result="FAIL", reason=str(e))
                except Exception as e:
                    r.update(result="FAIL", reason="%s: %s" % (type(e).__name__, e))
                    if os.environ.get("TESTDEBUG"): traceback.print_exc()
                if r["result"] == "FAIL" and chain: broken = t["id"]
            r["time"] = round(time.time() - t0 + (t_setup if i == 0 else 0), 2)
            res.append(r)
            live(results=res)
            print("  %-4s %-14s %6.2f s  %s%s" % (r["result"], r["id"], r["time"], r["desc"],
                                                 ("  -> " + r["reason"]) if r["reason"] else ""), flush=True)
        try:
            if hasattr(m, "teardown"): m.teardown(ctx)
        except Exception:
            pass
    tot = time.time() - t_all
    cap_err = check_caps(res, suites, filtered=bool(keys))
    n = {k: sum(1 for r in res if r["result"] == k) for k in ("PASS", "FAIL", "SKIP")}
    summary = "%s: %d test, %d PASS, %d FAIL, %d SKIP, %.1f s" % ("+".join(suites), len(res), n["PASS"], n["FAIL"], n["SKIP"], tot)
    print(summary)
    for e in cap_err: print("TIME CAP: " + e)
    live(state="fail" if n["FAIL"] or cap_err else "ok", current=None, seconds=round(tot, 1), caps=cap_err)
    out = os.path.join(os.path.dirname(HERE), "out", "work")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "test_report.txt"), "w") as f:
        f.write("%-14s %-10s %-5s %8s  %s\n" % ("ID", "SUITE", "RESULT", "TIME", "DESCRIPTION / REASON"))
        for r in res:
            f.write("%-14s %-10s %-5s %7.2fs  %s%s\n" % (r["id"], r["suite"], r["result"], r["time"], r["desc"],
                                                        ("\n%40s-> %s" % ("", r["reason"])) if r["reason"] else ""))
        f.write(summary + "\n")
    json.dump(dict(suites=suites, total_s=round(tot, 1), results=res), open(os.path.join(out, "test_report.json"), "w"), indent=1)
    sys.exit(1 if n["FAIL"] or cap_err else 0)


if __name__ == "__main__":
    main()
