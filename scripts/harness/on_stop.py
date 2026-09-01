"""Stop hook: the tree must agree with the loop stage before a turn ends.

Git-based, no clock. Blocks (exit 2) when: src/ or tests/ changed but PROGRESS.md did not;
src/ changed while stage < CODE; tests/ changed while stage < PLAN_FINAL; a src module lacks a
real test; pytest is red from CODE_REVIEW onward.
"""

from __future__ import annotations

import subprocess
import sys

from progress import ROOT, SRC, read, real_tests, test_path_for


def changed(*paths: str) -> list[str]:
    r = subprocess.run(["git", "status", "--porcelain", "--", *paths],
                       cwd=ROOT, capture_output=True, text=True)
    return [line[3:] for line in r.stdout.splitlines()]


def main() -> None:
    p = read()
    problems: list[str] = []
    src_changed, tests_changed = changed("src"), changed("tests")
    if (src_changed or tests_changed) and not changed("PROGRESS.md"):
        problems.append("code changed but PROGRESS.md has no uncommitted entry; log the step.")
    if src_changed and not p.at_least("CODE"):
        problems.append(f"src/ changed while stage is {p.stage} (< CODE).")
    if tests_changed and not p.at_least("PLAN_FINAL"):
        problems.append(f"tests/ changed while stage is {p.stage} (< PLAN_FINAL).")
    if SRC.exists():
        for mod in SRC.rglob("*.py"):
            if mod.name != "__init__.py" and not real_tests(test_path_for(mod)):
                problems.append(f"{mod.relative_to(ROOT)} has no real test in "
                                f"{test_path_for(mod).relative_to(ROOT)}.")
    if p.at_least("CODE_REVIEW"):
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode not in (0, 5):
            tail = "\n".join(r.stdout.splitlines()[-15:])
            problems.append(f"stage {p.stage} but pytest is red:\n{tail}")
    if problems:
        print("Stop blocked:\n  " + "\n  ".join(problems), file=sys.stderr)
        sys.exit(2)
    print(f"[harness] task={p.task} stage={p.stage}")


if __name__ == "__main__":
    main()
