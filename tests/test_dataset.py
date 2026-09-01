"""The C2 dataset spec, asserted: counts, noise floor, both Job B readings, the
injection attempt, id variants, and a shift boundary inside the timeline."""

from __future__ import annotations

from datetime import datetime

import pytest

from util import DATA, EVAL, STANDARDS, load_json, load_jsonl


@pytest.fixture(scope="module")
def msgs():
    return load_jsonl(DATA / "messages.jsonl")


@pytest.fixture(scope="module")
def gold():
    return {g["case"]: g for g in load_jsonl(EVAL / "gold" / "expectations.jsonl")}


@pytest.mark.req("S02")
def test_counts_and_noise_floor(msgs, gold):
    assert 30 <= len(msgs) <= 80
    noise = set(gold["noise_precision"]["noise_ids"])
    assert noise <= {m["id"] for m in msgs}
    assert len(noise) / len(msgs) >= 0.5


@pytest.mark.req("S03")
def test_both_job_b_readings_planted(msgs, gold):
    ids = {m["id"] for m in msgs}
    primary = gold["job_b_primary_catch"]["emergent_ids"]
    bleed = gold["adjacent_bleed"]["emergent_ids"]
    assert len(primary) >= 6 and set(primary) <= ids
    assert len(bleed) >= 2 and set(bleed) <= ids


def test_id_variants_exercise_normalization(msgs):
    text = " ".join(m["text"] for m in msgs)
    assert "V-2205" in text and "V2205" in text and "v 2205" in text


def test_injection_attempt_present_and_golded(msgs, gold):
    inj = next(m for m in msgs if m["id"] == gold["injection_uncovered"]["message_id"])
    assert "covered under" in inj["text"]


def test_timeline_crosses_a_shift_boundary(msgs):
    pkg = load_json(DATA / "package.json")
    times = sorted(datetime.fromisoformat(m["ts"]) for m in msgs)
    hours = {t.hour for t in times}
    boundary = max(pkg["shift_end_hours_utc"])
    assert times[0].hour < boundary <= max(hours)


def test_dispositions_parse_and_amendment_has_row():
    disp = load_jsonl(DATA / "dispositions.jsonl")
    amend = [d for d in disp if d["action"] == "approve_as_amendment"]
    assert amend and amend[0]["row"]["identifiers"] == ["V-2205"]


def test_package_documents_exist():
    for name in ("work_plan.md", "permit_PTW-2214.md", "permit_LOTO-88.md", "jsa.md",
                 "package.json"):
        assert (DATA / name).exists(), name
    assert (STANDARDS / "hazard_patterns.json").exists()


def test_attachment_flag_present_somewhere(msgs):
    assert any(m.get("attachment_present") for m in msgs)
