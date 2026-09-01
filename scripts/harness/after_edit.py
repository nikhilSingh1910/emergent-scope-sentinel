"""PostToolUse hook: compile + ruff the edited Python file of this repo. Reports, never blocks
on test results (TDD red is legitimate); a compile or lint error is fed back (exit 2)."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

from progress import ROOT


def main() -> None:
    payload = json.load(sys.stdin)
    raw = payload.get("tool_input", {}).get("file_path")
    if not raw or not raw.endswith(".py"):
        return
    path = Path(raw)
    try:
        path.resolve().relative_to(ROOT)
    except ValueError:
        return
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"compile error: {e}", file=sys.stderr)
        sys.exit(2)
    r = subprocess.run([sys.executable, "-m", "ruff", "check", str(path)],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout + r.stderr, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
