"""PreToolUse hook for Edit/Write: gate by loop stage, TDD parity, and harness lock.

Reads the tool call JSON on stdin. Exit 2 blocks the tool and feeds the message back to the
model; exit 0 allows. Paths outside this repo are ignored, so the hook is safe to install at a
parent directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from progress import LOCKED_DIRS, ROOT, UNLOCK, read, real_tests, test_path_for

ALWAYS_EDITABLE = {"PROGRESS.md", "ENDGOAL.md", "CLAUDE.md", "README.md"}
FREE_DIRS = {"docs", "data", "fixtures", "eval", "out", "design"}


def block(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def decide(path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(ROOT)
    except ValueError:
        return None
    top = rel.parts[0]
    if top in LOCKED_DIRS and not UNLOCK.exists():
        return (f"Harness lock: {rel} is part of the enforcement harness. "
                f"Only Nikhil unlocks it (touch .harness/unlock).")
    if rel.name in ALWAYS_EDITABLE or top in FREE_DIRS or top in LOCKED_DIRS:
        return None
    p = read()
    if top == "tests":
        if not p.at_least("PLAN_FINAL"):
            return (f"Loop gate: tests may be written only after PLAN_FINAL; "
                    f"PROGRESS.md says task {p.task} is at {p.stage}.")
        return None
    if top == "src":
        if not p.at_least("CODE"):
            return (f"Loop gate: src/ edits allowed only from CODE stage; "
                    f"PROGRESS.md says task {p.task} is at {p.stage}. "
                    f"Finish the plan stages and update the header first.")
        if rel.name != "__init__.py" and rel.suffix == ".py":
            t = test_path_for(path)
            if not real_tests(t):
                return (f"TDD gate: write a failing test with a real assertion first. "
                        f"Expected {t.relative_to(ROOT)} before editing {rel}.")
    return None


def main() -> None:
    payload = json.load(sys.stdin)
    raw = payload.get("tool_input", {}).get("file_path")
    if not raw:
        return
    msg = decide(Path(raw))
    if msg:
        block(msg)


if __name__ == "__main__":
    main()
