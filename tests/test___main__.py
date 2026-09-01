"""python -m sentinel is the entry point; bare invocation explains itself."""

from __future__ import annotations

import os
import subprocess
import sys

from util import ROOT


def test_module_entry_point_prints_usage():
    r = subprocess.run([sys.executable, "-m", "sentinel"], cwd=ROOT,
                       env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                       capture_output=True, text=True)
    assert r.returncode != 0 and "usage" in (r.stderr + r.stdout).lower()
