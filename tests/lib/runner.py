"""Test registry (10/11): since 14/11 it is Lab64's (../lab64/py/c64test.py). This module keeps `from lib.runner import ...`
working in the cases.py files: same objects (REG, test, check, Skip, Fail, script)."""
import os, sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.environ.get("LAB64") or os.path.normpath(os.path.join(_ROOT, "..", "lab64")), "py"))
from c64test import REG, Skip, Fail, test, check, script  # noqa: E402,F401
