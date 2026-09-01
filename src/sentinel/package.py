"""Mobilization seeding: package.json -> typed ledger rows, gazetteer, job card.

The slice seeds from a canonical JSON (PDF parsing is design v1, out of slice
scope). Rows under COARSE_CONFIDENCE are forced coarse; coarse rows never
suppress anywhere downstream.
"""

from __future__ import annotations

import json
from pathlib import Path

from sentinel.schemas import LedgerRow, Package

COARSE_CONFIDENCE = 0.6


def load_package(data_dir: Path) -> Package:
    raw = json.loads((Path(data_dir) / "package.json").read_text(encoding="utf-8"))
    rows = []
    for r in raw["rows"]:
        row = LedgerRow(**r)
        if row.confidence < COARSE_CONFIDENCE and not row.coarse:
            row = row.model_copy(update={"coarse": True})
        rows.append(row)
    gazetteer = {i for row in rows for i in row.identifiers}
    return Package(job_id=raw["job_id"], job_card=raw["job_card"],
                   shift_end_hours_utc=raw.get("shift_end_hours_utc", []),
                   rows=rows, gazetteer=gazetteer)
