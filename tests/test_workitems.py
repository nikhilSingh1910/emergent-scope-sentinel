"""Work items: hard-key clustering, the deterministic fold, and the amendment
path that closes the live-ledger loop (approved work suppresses later mentions)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


def _uncovered(mid, text, identifiers, equipment=None, label="emergent_scope",
               severity="medium", hazard=False, execution=False):
    from sentinel.schemas import GuardSignals, T1Candidate, UncoveredItem

    return UncoveredItem(
        candidate=T1Candidate(message_id=mid, label=label, severity=severity,
                              evidence_span=text[:40], equipment=equipment,
                              certainty="medium"),
        guard=GuardSignals(message_id=mid, unknown_tags=identifiers,
                           hazard_hits=["hot_work"] if hazard else [],
                           execution_hits=["doing it now"] if execution else [],
                           bypass=hazard),
        identifiers=identifiers,
    )


def test_cluster_merges_span_derived_ids_only():
    """Hard keys come from span-derived identifiers. A model-extracted equipment
    field groups its own soft item and can never join a hard-keyed one (B6)."""
    from sentinel.workitems import cluster

    items = cluster([
        _uncovered("m1", "V-2205 is shot", ["V2205"]),
        _uncovered("m2", "swapping v 2205 after lunch", ["V2205"]),
        _uncovered("m3", "cellar hatch hinge is bent", [], equipment="cellar hatch"),
        _uncovered("m4", "spare's ready for the valve", [], equipment="v 2205"),
    ])
    assert len(items) == 3
    v = next(i for i in items if i.key == "V2205")
    assert v.hard_keyed
    assert [m.candidate.message_id for m in v.mentions] == ["m1", "m2"]
    soft_ids = {i.mentions[0].candidate.message_id for i in items if not i.hard_keyed}
    assert soft_ids == {"m3", "m4"}


def test_model_equipment_cannot_merge_two_hazard_items():
    """One mis-extracted equipment field must not merge items, or the second
    hazard page vanishes (route pages once per item)."""
    from datetime import UTC, datetime

    from sentinel.alerts import route
    from sentinel.workitems import cluster

    items = cluster([
        _uncovered("m1", "hot work on V-2205 flange", ["V2205"], hazard=True),
        _uncovered("m2", "into the cellar to check", [], equipment="V2205", hazard=True),
    ])
    assert len(items) == 2
    t0 = datetime(2026, 9, 1, 7, 0, tzinfo=UTC)
    times = {"m1": t0, "m2": t0.replace(minute=30)}
    pages = [e for e in route(items, times, boundaries=[], resolved={})
             if e.lane == "hazard"]
    assert len(pages) == 2 and {p.message_id for p in pages} == {"m1", "m2"}


def test_soft_items_never_claim_a_hard_items_id():
    """Item identity is span-derived too: whatever the iteration order, a
    model-derived soft key must not take (or steal) the bare wi-KEY id that
    metrics and dispositions bind to."""
    from sentinel.workitems import cluster

    mentions = [
        _uncovered("m1", "V-2205 is shot", ["V2205"], hazard=True),
        _uncovered("m2", "spare's ready for it", [], equipment="v 2205"),
    ]
    for batch in (mentions, list(reversed(mentions))):
        items = cluster(batch)
        hard = next(i for i in items if i.hard_keyed)
        soft = next(i for i in items if not i.hard_keyed)
        assert hard.item_id == "wi-V2205"
        assert soft.item_id != "wi-V2205" and soft.item_id.startswith("wi-s-")


def test_fold_walks_the_legal_path():
    from sentinel.workitems import fold

    events = [
        {"type": "notify", "ts": "2026-09-01T06:20:00+00:00"},
        {"type": "acknowledge", "ts": "2026-09-01T06:30:00+00:00", "actor": "sup1"},
        {"type": "disposition", "ts": "2026-09-01T06:40:00+00:00", "actor": "sup1",
         "action": "approve_as_amendment"},
    ]
    assert fold([]) == "open"
    assert fold(events[:1]) == "notified"
    assert fold(events[:2]) == "acknowledged"
    assert fold(events) == "closed_by_amendment"


def test_fold_accepts_field_reality_forward_jumps():
    """The supervisor is in the channel: acknowledging or dispositioning before our
    page is normal. State moves forward, never back."""
    from sentinel.workitems import fold

    ack = {"type": "acknowledge", "ts": "2026-09-01T06:30:00+00:00"}
    late_notify = {"type": "notify", "ts": "2026-09-01T06:35:00+00:00"}
    assert fold([ack]) == "acknowledged"
    assert fold([ack, late_notify]) == "acknowledged"  # no regression
    assert fold([{"type": "disposition", "ts": "2026-09-01T06:40:00+00:00",
                  "action": "stop_work"}]) == "dispositioned"


def test_fold_rejects_close_before_disposition():
    from sentinel.workitems import fold

    with pytest.raises(ValueError):
        fold([{"type": "close", "ts": "2026-09-01T06:30:00+00:00"}])


def test_amendment_appends_row_and_suppresses_later_mentions():
    from sentinel.diff import diff
    from sentinel.guards import load_patterns, scan
    from sentinel.package import load_package
    from sentinel.schemas import Message, T1Candidate
    from sentinel.workitems import apply_amendment

    d = Path(tempfile.mkdtemp())
    (d / "package.json").write_text(json.dumps({
        "job_id": "J", "job_card": "c", "shift_end_hours_utc": [6, 18],
        "rows": [{"row_id": "t1", "artifact_type": "task", "identifiers": ["WO-1"],
                  "verb": "do", "equipment_class": "x", "source": {"doc": "w.md"},
                  "confidence": 0.9}],
    }), encoding="utf-8")
    (d / "patterns.json").write_text(json.dumps({
        "change_markers": ["swap"], "execution_markers": [],
        "hazard_classes": {}, "tag_regex": "\\b[A-Za-z]{1,4}[- ]?\\d{2,5}[A-Za-z]?\\b",
    }), encoding="utf-8")
    pkg = load_package(d)
    patterns = load_patterns(d / "patterns.json")

    pkg2 = apply_amendment(pkg, {
        "row_id": "a1", "artifact_type": "task", "identifiers": ["V-2205"],
        "verb": "replace", "equipment_class": "valve",
        "source": {"doc": "amendment", "span": "approved swap of V-2205"},
        "confidence": 1.0,
    })
    assert pkg is not pkg2 and len(pkg2.rows) == 2
    a1 = pkg2.rows[-1]
    assert a1.origin == "amendment" and "V2205" in pkg2.gazetteer

    msg = Message(id="m9", ts="2026-09-01T09:00:00+00:00", author_role="crew",
                  text="starting the V-2205 swap now")
    cand = T1Candidate(message_id="m9", label="execution_intent", severity="medium",
                       evidence_span="starting the V-2205 swap", certainty="high")
    res = diff([(msg, cand, scan(msg, patterns, pkg2.gazetteer))], pkg2)
    assert not res.uncovered and res.covered_log[0].row_id == "a1"
