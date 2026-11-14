#!/bin/bash
# Project tests, run by ./build.sh inside the container lab64-tools (13/11). Usage: tests/run_tests.sh [--all]
#   debug (default): smoke + sanity (fast; lab64 test smoke sanity)
#   release (RELEASE=1) or --all: smoke + sanity + regression (all the corner cases, slow ones too)
# Single suites / tests (host): lab64 test regression, lab64 test -k SAVE-1, lab64 test all --list
# Report: out/work/test_report.txt and out/work/test_report.json (ID, suite, result, time, reason).
cd "$(dirname "${BASH_SOURCE[0]}")/.."
SUITES="smoke sanity"
if [ "${RELEASE:-0}" = "1" ] || [ "$1" = "--all" ]; then SUITES="smoke sanity regression"; fi
if ! command -v x64sc >/dev/null 2>&1; then echo "x64sc (VICE) missing: run in the container lab64-tools (lab64 run ...)"; exit 1; fi
lab64 test $SUITES
RC=$?
# the normal build must be the one left in out/ (some tests assemble test variants)
tools/build/asm.sh >/dev/null 2>&1 && tools/build/mkdisk.sh >/dev/null || { echo "final rebuild FAILED"; RC=1; }
if [ $RC -ne 0 ]; then echo "TESTS FAILED (see out/work/test_report.txt)"; exit 1; fi
echo "all tests passed"
