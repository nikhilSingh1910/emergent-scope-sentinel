"""The CLI is the cold-run surface: one command, mock backend, artifacts on disk."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from util import ROOT, build_tiny_job


def test_cli_run_mock(tmp_path):
    job, std = build_tiny_job(tmp_path)
    out = tmp_path / "out"
    r = subprocess.run(
        [sys.executable, "-m", "sentinel", "run", "--data", str(job), "--standards",
         str(std), "--out", str(out), "--backend", "mock"],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr[-2000:]
    assert (out / "run_summary.json").exists()
    summary = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["backend"] == "mock" and summary["windows"] > 0


def test_cli_rejects_unknown_backend(tmp_path):
    job, std = build_tiny_job(tmp_path)
    r = subprocess.run(
        [sys.executable, "-m", "sentinel", "run", "--data", str(job), "--standards",
         str(std), "--out", str(tmp_path / "o"), "--backend", "nope"],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True, text=True,
    )
    assert r.returncode != 0
