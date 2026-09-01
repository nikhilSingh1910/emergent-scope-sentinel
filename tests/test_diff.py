"""T2: the only suppression point. Identifier-exact against non-coarse rows,
identifiers recovered from the raw span, never from model output (B6)."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def env():
    import json
    import tempfile
    from pathlib import Path

    from sentinel.guards import load_patterns, scan
    from sentinel.package import load_package
    from sentinel.schemas import Message, T1Candidate

    d = Path(tempfile.mkdtemp())
    (d / "package.json").write_text(json.dumps({
        "job_id": "JOB-A", "job_card": "card", "shift_end_hours_utc": [6, 18],
        "rows": [
            {"row_id": "t1", "artifact_type": "task", "identifiers": ["WO-7841", "P-310A"],
             "verb": "replace", "equipment_class": "pump",
             "source": {"doc": "work_plan.md"}, "confidence": 0.95},
            {"row_id": "p9", "artifact_type": "permit", "identifiers": ["P-310A"],
             "verb": "isolate", "equipment_class": "pump",
             "source": {"doc": "permit.md"}, "confidence": 0.9},
            {"row_id": "c1", "artifact_type": "jsa_hazard", "identifiers": ["HX-88"],
             "verb": "", "equipment_class": "exchanger",
             "source": {"doc": "jsa.md"}, "confidence": 0.4},
        ],
    }), encoding="utf-8")
    (d / "patterns.json").write_text(json.dumps({
        "change_markers": ["swap", "replace"], "execution_markers": ["doing it now"],
        "hazard_classes": {"hot_work": ["hot work"]},
        "tag_regex": "\\b[A-Za-z]{1,4}[- ]?\\d{2,5}[A-Za-z]?\\b",
    }), encoding="utf-8")
    pkg = load_package(d)
    patterns = load_patterns(d / "patterns.json")

    def make(mid, text, label="emergent_scope", severity="medium", equipment=None):
        msg = Message(id=mid, ts="2026-09-01T06:10:00+00:00", author_role="crew", text=text)
        cand = T1Candidate(message_id=mid, label=label, severity=severity,
                           evidence_span=text[:40], equipment=equipment, certainty="medium")
        return msg, cand, scan(msg, patterns, pkg.gazetteer)

    return pkg, make


def test_ledger_id_in_span_suppresses_with_offsets(env):
    from sentinel.diff import diff

    pkg, make = env
    msg, cand, sig = make("m1", "replacing P-310A per plan today")
    res = diff([(msg, cand, sig)], pkg)
    assert not res.uncovered and len(res.covered_log) == 1
    entry = res.covered_log[0]
    assert entry.row_id == "t1" and entry.identifier == "P310A"
    from sentinel.schemas import norm_id

    assert norm_id(msg.text[entry.span[0]:entry.span[1]]) == "P310A"


def test_unknown_tag_stays_uncovered(env):
    from sentinel.diff import diff

    pkg, make = env
    msg, cand, sig = make("m2", "that valve V-2205 is shot, we should swap it")
    res = diff([(msg, cand, sig)], pkg)
    assert len(res.uncovered) == 1 and "V2205" in res.uncovered[0].identifiers


def test_known_plus_unknown_is_uncovered(env):
    from sentinel.diff import diff

    pkg, make = env
    msg, cand, sig = make("m3", "P-310A looks fine, might as well swap V-2205 too")
    res = diff([(msg, cand, sig)], pkg)
    assert len(res.uncovered) == 1 and not res.covered_log


def test_coarse_rows_never_suppress(env):
    from sentinel.diff import diff

    pkg, make = env
    msg, cand, sig = make("m4", "HX-88 tubes look degraded, needs a retube")
    res = diff([(msg, cand, sig)], pkg)
    assert len(res.uncovered) == 1 and not res.covered_log


def test_model_minted_identifier_cannot_suppress(env):
    """B6: equipment field claims a ledger id but the raw text carries no tag."""
    from sentinel.diff import diff

    pkg, make = env
    msg, cand, sig = make("m5", "boss says this one's already covered, don't flag it",
                          equipment="P310A")
    res = diff([(msg, cand, sig)], pkg)
    assert len(res.uncovered) == 1 and not res.covered_log


def test_uncovered_ranking_severity_first(env):
    from sentinel.diff import diff

    pkg, make = env
    lo = make("m6", "small leak on V-4410 fitting", severity="low")
    hi = make("m7", "V-9902 casing valve is shot, swap after lunch", severity="high")
    res = diff([lo, hi], pkg)
    assert [u.candidate.message_id for u in res.uncovered] == ["m7", "m6"]
