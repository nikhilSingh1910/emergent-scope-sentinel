"""Two lanes: hazard pages once at first mention with the parallel duty-HSE
addressee; non-hazard interrupts only on execution intent or at shift handover."""

from __future__ import annotations

from datetime import UTC, datetime


def _wi(key, mentions, hard=True):
    from sentinel.workitems import build_item

    return build_item(key, mentions, hard)


def _uncovered(mid, ts_str, hazard=False, execution=False, label="emergent_scope"):
    from sentinel.schemas import GuardSignals, T1Candidate, UncoveredItem

    return UncoveredItem(
        candidate=T1Candidate(message_id=mid, label=label, severity="medium",
                              evidence_span="x", certainty="medium"),
        guard=GuardSignals(message_id=mid,
                           hazard_hits=["stored_energy"] if hazard else [],
                           execution_hits=["doing it now"] if execution else [],
                           bypass=hazard),
        identifiers=[],
    )


def _ts(h, m=0):
    return datetime(2026, 9, 1, h, m, tzinfo=UTC)


def _times(*pairs):
    return {mid: _ts(h, m) for mid, (h, m) in pairs}


def test_hazard_pages_once_at_first_mention_with_parallel_hse():
    from sentinel.alerts import route

    wi = _wi("V2205", [_uncovered("m1", "", hazard=True), _uncovered("m2", "", hazard=True)])
    esc = route([wi], _times(("m1", (7, 0)), ("m2", (7, 30))), boundaries=[], resolved={})
    pages = [e for e in esc if e.lane == "hazard"]
    assert len(pages) == 1
    assert pages[0].message_id == "m1" and pages[0].ts == _ts(7, 0)
    assert set(pages[0].addressees) == {"duty_hse", "supervisor"}


def test_execution_intent_escalates_non_hazard_item():
    from sentinel.alerts import route

    wi = _wi("V4410", [_uncovered("m3", ""), _uncovered("m4", "", execution=True,
                                                        label="execution_intent")])
    esc = route([wi], _times(("m3", (8, 0)), ("m4", (9, 0))), boundaries=[], resolved={})
    assert [e.lane for e in esc] == ["execution_intent"]
    assert esc[0].addressees == ["supervisor"] and esc[0].ts == _ts(9, 0)


def test_hazard_paged_item_does_not_double_escalate_on_execution():
    from sentinel.alerts import route

    wi = _wi("V2205", [_uncovered("m1", "", hazard=True),
                       _uncovered("m2", "", execution=True, label="execution_intent")])
    esc = route([wi], _times(("m1", (7, 0)), ("m2", (7, 10))), boundaries=[], resolved={})
    assert [e.lane for e in esc] == ["hazard"]


def test_unresolved_item_escalates_at_shift_handover():
    from sentinel.alerts import route

    wi = _wi("HX88", [_uncovered("m5", "")], hard=True)
    esc = route([wi], _times(("m5", (18, 40))), boundaries=[_ts(6, 0), _ts(18, 0),
                                                           _ts(30 - 24, 0)], resolved={})
    handovers = [e for e in esc if e.lane == "handover"]
    assert len(handovers) == 0  # no boundary after 18:40 in the fixture day

    esc2 = route([wi], _times(("m5", (16, 0))), boundaries=[_ts(18, 0)], resolved={})
    assert [e.lane for e in esc2] == ["handover"]
    assert esc2[0].ts == _ts(18, 0) and esc2[0].addressees == ["supervisor"]


def test_resolved_item_does_not_escalate_at_handover():
    from sentinel.alerts import route

    wi = _wi("HX88", [_uncovered("m5", "")])
    esc = route([wi], _times(("m5", (16, 0))), boundaries=[_ts(18, 0)],
                resolved={"HX88": _ts(17, 0)})
    assert not [e for e in esc if e.lane == "handover"]


def test_handover_repeats_every_shift_until_resolved():
    """Nothing expires unseen: an undispositioned item rides every handover pack."""
    from datetime import timedelta

    from sentinel.alerts import route

    wi = _wi("HX88", [_uncovered("m5", "")])
    b1, b2 = _ts(18, 0), _ts(18, 0) + timedelta(hours=12)
    esc = route([wi], _times(("m5", (16, 0))), boundaries=[b1, b2], resolved={})
    assert [e.ts for e in esc if e.lane == "handover"] == [b1, b2]

    esc2 = route([wi], _times(("m5", (16, 0))), boundaries=[b1, b2],
                 resolved={"HX88": b1 + timedelta(hours=1)})
    assert [e.ts for e in esc2 if e.lane == "handover"] == [b1]
