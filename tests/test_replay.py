"""The drift pin. The recorded live run must replay offline forever; the committed
report is the single number source, and any prompt or model edit after recording
becomes a loud ReplayMiss here, never a silent divergence."""

from __future__ import annotations

import json

import pytest

from util import DATA, EVAL, ROOT, STANDARDS

pytestmark = pytest.mark.skipif(
    not list((ROOT / "fixtures" / "replay").glob("*.json")),
    reason="recording pending: no replay fixtures yet (needs API credits)",
)


@pytest.fixture(scope="module")
def replay_report(tmp_path_factory):
    from sentinel.metrics import compute_metrics
    from sentinel.pipeline import run_pipeline

    base = tmp_path_factory.mktemp("replaypin")
    summary = run_pipeline(DATA, STANDARDS, base / "run", backend_name="replay")
    run_pipeline(DATA, STANDARDS, base / "base", baseline=True)
    report = compute_metrics(base / "run", DATA, EVAL / "gold" / "expectations.jsonl",
                             baseline_dir=base / "base")
    return summary, report


@pytest.mark.req("S05")
def test_recorded_run_replays_offline(replay_report):
    summary, _ = replay_report
    assert summary["backend"] == "replay" and summary["windows"] > 0


@pytest.mark.req("S05")
def test_replay_is_headline_eligible(replay_report):
    _, report = replay_report
    assert report["headline_eligible"] is True


def test_zero_suppression_holds_on_recorded_output(replay_report):
    """A code invariant, not a model-quality number: nothing the model wrote may
    ever have suppressed anything, whatever else the recorded run did."""
    _, report = replay_report
    assert report["checks"]["zero_suppression"] is True


@pytest.mark.req("S05")
def test_report_matches_the_committed_number_source(replay_report):
    """Whole-dict equality with eval/report_recorded.json: the README quotes that
    file, and this test is why it can be trusted."""
    _, report = replay_report
    committed = json.loads((EVAL / "report_recorded.json").read_text(encoding="utf-8"))
    assert report == committed
