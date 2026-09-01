"""PostToolUse hook: PROGRESS.md may advance one stage at a time, with a log line per stage.

Keeps the previously seen stage in .harness/last_stage. Blocks (exit 2) when the stage jumped
more than one step forward, or when the task section has no `<STAGE>` entry for the new stage.
Going backwards or opening a new task at PLAN is allowed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from progress import LAST_STAGE, PROGRESS, STAGES, read, task_section


def decide(prev: str | None) -> str | None:
    p = read()
    text = PROGRESS.read_text(encoding="utf-8")
    section = task_section(p.task, text)
    if not section:
        return f"PROGRESS.md: no '### {p.task}' section for the current task."
    if prev and prev.startswith(p.task + "@"):
        prev_stage = prev.split("@", 1)[1]
        jump = STAGES.index(p.stage) - STAGES.index(prev_stage)
        if jump > 1:
            return (f"Loop gate: stage jumped {prev_stage} -> {p.stage}. "
                    f"Advance one stage at a time and log each.")
    logged = re.search(rf"\b{p.stage}\b", section) is not None
    if p.stage != "PLAN" and not logged and "ceremony skipped" not in section:
        return f"Loop gate: stage is {p.stage} but the task log has no '{p.stage}' entry."
    return None


def main() -> None:
    payload = json.load(sys.stdin)
    raw = payload.get("tool_input", {}).get("file_path", "")
    if not raw or Path(raw).resolve() != PROGRESS.resolve():
        return
    prev = LAST_STAGE.read_text().strip() if LAST_STAGE.exists() else None
    msg = decide(prev)
    if msg:
        print(msg, file=sys.stderr)
        sys.exit(2)
    p = read()
    LAST_STAGE.parent.mkdir(exist_ok=True)
    LAST_STAGE.write_text(f"{p.task}@{p.stage}")


if __name__ == "__main__":
    main()
