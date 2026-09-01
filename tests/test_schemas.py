"""Shapes are the single source of truth; identifier normalization lives beside them."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


@pytest.fixture(scope="module")
def schemas():
    import sentinel.schemas as s

    return s


def test_norm_id_collapses_variants(schemas):
    assert schemas.norm_id("V-2205") == "V2205"
    assert schemas.norm_id("v 2205") == "V2205"
    assert schemas.norm_id("LOTO-22") == "LOTO22"
    assert schemas.norm_id("ptw-2214") == "PTW2214"


def test_ledger_row_shape(schemas):
    row = schemas.LedgerRow(
        row_id="r1", artifact_type="task", identifiers=["WO-7841", "P-310A"],
        verb="replace", equipment_class="pump",
        source={"doc": "work_plan.md", "page": 1, "span": "Replace charge pump P-310A"},
        confidence=0.92,
    )
    assert row.identifiers == ["WO7841", "P310A"]  # normalized at validation
    assert row.coarse is False and row.origin == "package"


def test_low_confidence_rows_can_be_coarse_but_default_is_not(schemas):
    row = schemas.LedgerRow(row_id="r2", artifact_type="jsa_hazard", identifiers=[],
                            verb="", equipment_class="", source={"doc": "jsa.md"},
                            confidence=0.3, coarse=True)
    assert row.coarse is True


def test_t1_candidate_rejects_unknown_certainty(schemas):
    with pytest.raises(ValidationError):
        schemas.T1Candidate(message_id="m1", label="emergent_scope", severity="high",
                            evidence_span="swap the valve", certainty="certain")


def test_t1_labels_include_execution_intent_and_chatter(schemas):
    for label in ("emergent_scope", "execution_intent", "hazard_mention",
                  "status_chatter", "other"):
        c = schemas.T1Candidate(message_id="m1", label=label, severity="low",
                                evidence_span="x", certainty="low")
        assert c.label == label


def test_message_defaults(schemas):
    m = schemas.Message(id="m1", ts="2026-09-01T06:10:00+00:00", author_role="crew",
                        text="rigging up now")
    assert m.attachment_present is False and m.ts.tzinfo is not None
