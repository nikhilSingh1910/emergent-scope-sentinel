"""Commit gate: current task DONE, every stage logged in order with substance, src/tests parity."""

from __future__ import annotations

import re
import sys

from progress import PROGRESS, ROOT, SRC, STAGES, read, real_tests, task_section, test_path_for

MIN_ENTRY_CHARS = 40


def stage_problems(section: str) -> list[str]:
    problems, last_pos = [], -1
    for s in STAGES:
        m = re.search(rf"\b{s}\b(.*)", section)
        if not m:
            problems.append(f"missing {s}")
            continue
        if m.start() < last_pos:
            problems.append(f"{s}: logged out of order")
        last_pos = m.start()
        entry = section[m.end():].split("\n- ", 1)[0]
        if len((m.group(1) + entry).strip()) < MIN_ENTRY_CHARS:
            problems.append(f"{s}: entry too thin (< {MIN_ENTRY_CHARS} chars)")
    return problems


def main() -> int:
    p = read()
    problems: list[str] = []
    if p.stage != "DONE":
        problems.append(f"task {p.task} is at {p.stage}, not DONE")
    section = task_section(p.task, PROGRESS.read_text(encoding="utf-8"))
    if "ceremony skipped" not in section:
        problems += stage_problems(section)
    if SRC.exists():
        for mod in SRC.rglob("*.py"):
            if mod.name != "__init__.py" and not real_tests(test_path_for(mod)):
                problems.append(f"{mod.relative_to(ROOT)} has no real test")
    if problems:
        print("loop gate failed:\n  " + "\n  ".join(problems))
        return 1
    print("loop gate ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
