"""Mobilization seeding: package.json -> typed ledger rows + gazetteer + job card."""

from __future__ import annotations

import json

import pytest


@pytest.fixture()
def tiny_package(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "job_id": "JOB-A-7841",
        "job_card": "Workover on well A-12: replace charge pump P-310A under WO-7841.",
        "shift_end_hours_utc": [6, 18],
        "rows": [
            {"row_id": "t1", "artifact_type": "task", "identifiers": ["WO-7841", "P-310A"],
             "verb": "replace", "equipment_class": "pump",
             "source": {"doc": "work_plan.md", "page": 1}, "confidence": 0.95},
            {"row_id": "p1", "artifact_type": "permit", "identifiers": ["PTW-2214"],
             "verb": "authorize", "equipment_class": "",
             "source": {"doc": "permit_PTW-2214.md"}, "confidence": 0.9},
            {"row_id": "h1", "artifact_type": "jsa_hazard", "identifiers": [],
             "verb": "isolate", "equipment_class": "pump",
             "source": {"doc": "jsa.md", "page": 2}, "confidence": 0.35},
        ],
    }), encoding="utf-8")
    return tmp_path


def test_load_package_normalizes_and_builds_gazetteer(tiny_package):
    from sentinel.package import load_package

    pkg = load_package(tiny_package)
    assert pkg.job_id == "JOB-A-7841"
    ids = {i for row in pkg.rows for i in row.identifiers}
    assert ids == {"WO7841", "P310A", "PTW2214"}
    assert "P310A" in pkg.gazetteer and "PTW2214" in pkg.gazetteer
    assert pkg.job_card


def test_low_confidence_rows_marked_coarse_and_never_suppress(tiny_package):
    from sentinel.package import COARSE_CONFIDENCE, load_package

    pkg = load_package(tiny_package)
    h1 = next(r for r in pkg.rows if r.row_id == "h1")
    assert h1.confidence < COARSE_CONFIDENCE and h1.coarse is True
    suppressing = [r for r in pkg.rows if not r.coarse and r.identifiers]
    assert h1 not in suppressing
