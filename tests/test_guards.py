"""T0 guards: OR-only signals, never suppression; patterns load from standards data."""

from __future__ import annotations

import json

import pytest


@pytest.fixture(scope="module")
def patterns(tmp_path_factory):
    p = tmp_path_factory.mktemp("std") / "hazard_patterns.json"
    p.write_text(json.dumps({
        "change_markers": ["while we're here", "might as well", "swap", "shot"],
        "execution_markers": ["doing it now", "starting on"],
        "hazard_classes": {
            "hot_work": ["weld", "grind", "hot work"],
            "stored_energy": ["pressurized", "under pressure", "energized"],
        },
        "tag_regex": "\\b[A-Za-z]{1,4}-?\\d{2,5}[A-Za-z]?\\b",
    }), encoding="utf-8")
    from sentinel.guards import load_patterns

    return load_patterns(p)


def _msg(text, id="m1"):
    from sentinel.schemas import Message

    return Message(id=id, ts="2026-09-01T06:10:00+00:00", author_role="crew", text=text)


def test_marker_and_ledger_and_unknown_tag_hits(patterns):
    from sentinel.guards import scan

    gazetteer = {"P310A", "PTW2214", "WO7841"}
    sig = scan(_msg("while we're here, might as well swap V-2205, P-310A looks fine"),
               patterns, gazetteer)
    assert "while we're here" in sig.marker_hits
    assert "P310A" in sig.ledger_id_hits
    assert "V2205" in sig.unknown_tags


def test_hazard_marker_sets_bypass(patterns):
    from sentinel.guards import scan

    sig = scan(_msg("line is still under pressure, need hot work on the flange"),
               patterns, set())
    assert sig.hazard_hits and sig.bypass is True


def test_guards_never_suppress(patterns):
    """Every message yields a signal object; nothing is dropped, only annotated."""
    from sentinel.guards import scan

    sig = scan(_msg("quiet morning, coffee's cold"), patterns, set())
    assert sig is not None
    assert not sig.marker_hits and not sig.unknown_tags and sig.bypass is False


def test_spaced_tags_are_span_derived_but_stopword_prefixes_are_not(patterns):
    """'v 2205' is a real field spelling and must be a span-derived identifier;
    'at 350' and 'at 60' are prose, never tags."""
    from sentinel.guards import scan
    from sentinel.schemas import norm_id

    sig = scan(_msg("that v 2205 seat's about gone"), patterns, {"V2205"})
    assert sig.ledger_id_hits == ["V2205"]
    s, e = sig.tag_spans["V2205"]
    assert norm_id("that v 2205 seat's about gone"[s:e]) == "V2205"

    quiet = scan(_msg("test holding at 350 psi, tanks at 60 percent"), patterns, set())
    assert not quiet.unknown_tags and not quiet.ledger_id_hits
