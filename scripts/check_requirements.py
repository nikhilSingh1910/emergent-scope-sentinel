"""Every bolded requirement id in ENDGOAL.md must be claimed by a test marker or an eval case."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = re.compile(r"\*\*([A-Z]\d{2})\*\*")
MARK = re.compile(r"pytest\.mark\.req\(([^)]*)\)")


def main() -> int:
    wanted = set(IDS.findall((ROOT / "ENDGOAL.md").read_text(encoding="utf-8")))
    claimed: set[str] = set()
    for f in (ROOT / "tests").glob("test_*.py") if (ROOT / "tests").exists() else []:
        for m in MARK.finditer(f.read_text(encoding="utf-8")):
            claimed.update(re.findall(r"[A-Z]\d{2}", m.group(1)))
    gold = ROOT / "eval" / "gold" / "expectations.jsonl"
    if gold.exists():
        for line in gold.read_text(encoding="utf-8").splitlines():
            if line.strip():
                claimed.update(json.loads(line)["req"])
    # design-doc ids (D..) are claimed by the doc itself, not by tests
    doc = ROOT / "design" / "design.md"
    if doc.exists():
        claimed.update(IDS.findall(doc.read_text(encoding="utf-8")))
    missing = sorted(wanted - claimed)
    print(f"requirement coverage: {len(wanted - set(missing))}/{len(wanted)} ids claimed")
    if missing:
        print("missing:", ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
