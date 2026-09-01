"""Shared helpers for every hook: PROGRESS.md header, real-test detection, paths.

Lifted from the grounded-rfp-drafter harness; project-specific bits generalised (src/ package
root, empty module-to-test map until code exists).
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROGRESS = Path(os.environ.get("HARNESS_PROGRESS_FILE", ROOT / "PROGRESS.md"))
UNLOCK = ROOT / ".harness" / "unlock"  # present only when Nikhil is editing the harness
LAST_STAGE = ROOT / ".harness" / "last_stage"
SRC = ROOT / "src"
TESTS = Path(os.environ.get("HARNESS_TESTS_DIR", ROOT / "tests"))
LOCKED_DIRS = {"scripts", ".claude", ".githooks", ".harness"}

STAGES = [
    "PLAN", "PLAN_REVIEW", "PLAN_ADVERSARIAL", "PLAN_REQ_CHECK", "PLAN_FINAL",
    "CODE", "CODE_REVIEW", "CODE_ADVERSARIAL", "CODE_REQ_CHECK", "DONE",
]
# src module -> test file that pins it (default: tests/test_<module>.py)
TEST_MAP: dict[str, str] = {}
_HEADER = re.compile(r"^---\n(.*?)\n---", re.S)


@dataclass(frozen=True)
class Progress:
    task: str
    stage: str
    updated: datetime
    covered: frozenset[str]

    def at_least(self, stage: str) -> bool:
        return STAGES.index(self.stage) >= STAGES.index(stage)


def read(path: Path | None = None) -> Progress:
    text = (path or PROGRESS).read_text(encoding="utf-8")
    m = _HEADER.match(text)
    if not m:
        raise SystemExit("PROGRESS.md: missing '---' header block")
    fields = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    fields = {k.strip(): v.strip() for k, v in fields.items()}
    stage = fields.get("stage", "")
    if stage not in STAGES:
        raise SystemExit(f"PROGRESS.md: stage {stage!r} not in {STAGES}")
    updated = datetime.fromisoformat(fields["updated"])
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=UTC)
    covered = frozenset(x.strip() for x in fields.get("covered", "").split() if x.strip())
    return Progress(fields.get("current_task", ""), stage, updated, covered)


def test_path_for(src_file: Path) -> Path:
    rel = src_file.resolve().relative_to(SRC).with_suffix("")
    parts = [p for p in rel.parts if p != rel.parts[0] or len(rel.parts) == 1]
    stem = "_".join(parts) if len(rel.parts) == 1 else "_".join(rel.parts[1:])
    return TESTS / f"{TEST_MAP.get(stem, 'test_' + stem)}.py"


def _is_real_test(fn: ast.FunctionDef) -> bool:
    if not fn.name.startswith("test_"):
        return False
    for d in fn.decorator_list:
        if re.search(r"\b(skip|skipif|xfail)\b", ast.unparse(d)):
            return False
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call) and "raises" in ast.unparse(node.func):
            return True
    return False


def real_tests(path: Path) -> list[ast.FunctionDef]:
    """Test functions that actually assert something and are not skipped."""
    if not path.exists():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    return [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and _is_real_test(n)]


def task_section(task: str, text: str) -> str:
    """The log lines of one task: from its '### <task>' heading to the next heading."""
    m = re.search(rf"^### {re.escape(task)}\b.*?(?=^#{{2,3}} |\Z)", text, re.S | re.M)
    return m.group(0) if m else ""
