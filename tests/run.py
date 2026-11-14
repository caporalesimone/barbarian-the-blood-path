#!/usr/bin/env python3
"""Test del gioco (10/11): dal 14/11 il motore e' quello di Lab64 (../lab64/test/run.py, in inglese): stesse opzioni.
Uso:  ../lab64/run.sh tools python3 tests/run.py [smoke|sanity|regression|all ...] [-k ID|prefisso ...] [--list] [--md]
Tetti di durata del gioco: C64_TEST_CAPS in lab64.env."""
import os, runpy, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("C64_TESTS", HERE)
L = os.environ.get("LAB64") or os.path.normpath(os.path.join(HERE, "..", "..", "lab64"))
sys.argv[0] = os.path.join(L, "test", "run.py")
runpy.run_path(sys.argv[0], run_name="__main__")
