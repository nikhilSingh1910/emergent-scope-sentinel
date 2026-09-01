"""End to end on the mock backend: seed -> T0 -> windows -> T1 -> T2 -> work items ->
escalations, with the amendment closing the live-ledger loop mid-run."""

from __future__ import annotations

import pytest

from util import build_tiny_job, load_json, load_jsonl


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    from sentinel.pipeline import run_pipeline

    base = tmp_path_factory.mktemp("tiny")
    job, std = build_tiny_job(base)
    out = base / "out"
    summary = run_pipeline(job, std, out, backend_name="mock")
    return out, summary


def test_artifacts_written(run):
    out, summary = run
    for name in ("work_items.json", "escalations.json", "covered_log.json",
                 "trace.jsonl", "costs.json", "run_summary.json"):
        assert (out / name).exists(), name
    assert summary["backend"] == "mock"


def test_planned_work_is_covered_and_emergent_is_not(run):
    out, _ = run
    covered = load_json(out / "covered_log.json")
    covered_msgs = {c["message_id"] for c in covered}
    assert "m2" in covered_msgs  # planned pump swap, phrased like emergent work
    items = load_json(out / "work_items.json")
    v = next(i for i in items if i["key"] == "V2205")
    assert {m["candidate"]["message_id"] for m in v["mentions"]} >= {"m3"}


def test_amendment_makes_later_mentions_covered(run):
    out, _ = run
    covered = load_json(out / "covered_log.json")
    m6 = [c for c in covered if c["message_id"] == "m6"]
    assert m6 and m6[0]["row_id"] == "a1"


def test_hazard_pages_once_and_execution_does_not_double_page(run):
    out, _ = run
    esc = load_json(out / "escalations.json")
    lanes = [e["lane"] for e in esc if e["item_id"] == "wi-V2205"]
    assert lanes.count("hazard") == 1 and "execution_intent" not in lanes


def test_fold_reaches_closed_by_amendment(run):
    out, _ = run
    items = load_json(out / "work_items.json")
    v = next(i for i in items if i["key"] == "V2205")
    assert v["state"] == "closed_by_amendment"


def test_zero_suppression_receipts_hold(run, tmp_path):
    """Every suppression names an identifier at a literal span of the raw message."""
    from sentinel.schemas import norm_id

    out, _ = run
    covered = load_json(out / "covered_log.json")
    job, _std = build_tiny_job(tmp_path)  # deterministic builder: same message texts
    texts = {m["id"]: m["text"] for m in load_jsonl(job / "messages.jsonl")}
    assert covered
    for c in covered:
        s, e = c["span"]
        assert norm_id(texts[c["message_id"]][s:e]) == c["identifier"]


def test_trace_has_one_line_per_window_and_costs_counted(run):
    out, _ = run
    trace = load_jsonl(out / "trace.jsonl")
    assert trace and all("window_id" in t and "reason" in t for t in trace)
    costs = load_json(out / "costs.json")
    assert costs["totals"]["calls"] == len([t for t in trace if t["called_model"]])
    assert costs["totals"]["calls"] > 0


def test_duplicate_message_ids_fail_loudly(tmp_path):
    """A silently deduplicated message is failure mode 1 (silent miss)."""
    from sentinel.pipeline import run_pipeline

    job, std = build_tiny_job(tmp_path)
    lines = (job / "messages.jsonl").read_text(encoding="utf-8").splitlines()
    (job / "messages.jsonl").write_text("\n".join([*lines, lines[0]]) + "\n",
                                        encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate message id"):
        run_pipeline(job, std, tmp_path / "o", backend_name="mock")


def test_naive_disposition_timestamp_fails_loudly(tmp_path):
    from sentinel.pipeline import run_pipeline

    job, std = build_tiny_job(tmp_path)
    text = (job / "dispositions.jsonl").read_text(encoding="utf-8")
    naive = text.replace("2026-09-01T07:00:00+00:00", "2026-09-01T07:00:00")
    assert naive != text  # the fixture timestamp we target must exist
    (job / "dispositions.jsonl").write_text(naive, encoding="utf-8")
    with pytest.raises(ValueError, match="timezone-aware"):
        run_pipeline(job, std, tmp_path / "o", backend_name="mock")


def test_replay_miss_on_attempt_one_tries_attempt_two():
    """A live run that succeeded on attempt 2 recorded only attempt 2; replay must
    walk the same attempt sequence instead of dying on attempt 1."""
    from sentinel.llm import Completion, ReplayMiss
    from sentinel.pipeline import _complete_with_retries
    from sentinel.schemas import Usage

    class TwoAttemptStub:
        def complete(self, wid, prompt, attempt=1, *, system="", tool=None):
            if attempt == 1:
                raise ReplayMiss("no recording for attempt 1")
            return Completion(data={"candidates": []}, key="k", model="m",
                              backend="replay", usage=Usage(model="m"))

    c = _complete_with_retries(TwoAttemptStub(), "w000", "u", "s")
    assert c.backend == "replay"


def test_early_acknowledge_before_page_does_not_crash(tmp_path):
    from sentinel.pipeline import run_pipeline

    job, std = build_tiny_job(tmp_path)
    text = (job / "dispositions.jsonl").read_text(encoding="utf-8")
    early = text.replace("2026-09-01T07:00:00+00:00", "2026-09-01T06:10:00+00:00")
    assert early != text  # the fixture timestamp we target must exist
    (job / "dispositions.jsonl").write_text(early, encoding="utf-8")
    summary = run_pipeline(job, std, tmp_path / "o", backend_name="mock")
    assert summary["work_items"] > 0


def test_baseline_mode_runs_without_model_calls(tmp_path):
    from sentinel.pipeline import run_pipeline

    job, std = build_tiny_job(tmp_path)
    out = tmp_path / "base_out"
    summary = run_pipeline(job, std, out, backend_name="mock", baseline=True)
    costs = load_json(out / "costs.json")
    assert costs["totals"]["calls"] == 0 and summary["baseline"] is True
    items = load_json(out / "work_items.json")
    assert any(i["key"] == "V2205" for i in items)  # lexicon still catches the tag


def test_digest_shows_visibility_from_first_mention(run):
    """The non-hazard lane's digest: every work item, visible from its first
    mention, with its state. This is the intervention-window evidence."""
    out, _ = run
    digest = load_json(out / "digest.json")
    v = next(d for d in digest if d["key"] == "V2205")
    assert v["first_mention_id"] == "m3"
    assert v["first_mention_ts"].endswith("06:30:00+00:00")
    assert v["state"] == "closed_by_amendment"
    assert v["minutes_visible"] >= 0


def test_handover_pack_lists_open_items_per_boundary(run):
    """The pack uses the same open-at-boundary predicate as the handover
    escalation. In the tiny fixture the amendment resolved V2205 at 07:10, so
    the 18:00 pack is empty: the system working, recorded."""
    out, _ = run
    pack = load_json(out / "handover_pack.json")
    entry = next(p for p in pack if p["boundary_ts"].endswith("18:00:00+00:00"))
    assert entry["open_items"] == []
