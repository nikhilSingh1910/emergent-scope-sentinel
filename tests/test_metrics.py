"""Measured outcomes (S05) from run artifacts + gold. Headline numbers refuse the
mock backend; misses are reported, never trimmed."""

from __future__ import annotations

import pytest

from util import DATA, EVAL, STANDARDS


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    from sentinel.metrics import compute_metrics
    from sentinel.pipeline import run_pipeline

    base = tmp_path_factory.mktemp("metrics")
    run_pipeline(DATA, STANDARDS, base / "run", backend_name="mock")
    run_pipeline(DATA, STANDARDS, base / "base", baseline=True)
    return compute_metrics(base / "run", DATA, EVAL / "gold" / "expectations.jsonl",
                           baseline_dir=base / "base")


@pytest.mark.req("S05")
def test_headline_refuses_mock(report):
    assert report["backend"] == "mock" and report["headline_eligible"] is False


def test_property_checks_pass_on_the_frozen_dataset(report):
    checks = report["checks"]
    assert checks["injection_uncovered"] is True
    assert checks["coarse_no_suppress"] is True
    assert checks["amendment_closes_loop"] is True
    assert checks["hazard_page"] is True
    assert checks["handover_escalation"] is True
    assert checks["planned_covered"] is True
    assert checks["zero_suppression"] is True


@pytest.mark.req("S05")
def test_honest_misses_are_reported(report):
    """jb3 (photo, tagless) and jb4 (oblique) are beyond the mock; they must appear
    as misses, not vanish."""
    assert {"jb3", "jb4"} <= set(report["honest_misses"])


def test_catch_and_latency_shape(report):
    catch = report["catch"]["job_b_primary_catch"]
    assert catch["caught"] is True
    assert catch["signals_before_catch"] >= 0
    assert catch["wall_clock_minutes_from_first_signal"] >= 0
    assert catch["caught_before_execution"] in (True, False)


def test_rates_and_baseline_delta(report):
    assert 0.0 <= report["recall"] <= 1.0
    assert 0.0 <= report["precision_on_noise_half"] <= 1.0
    assert 0.0 <= report["hard_key_fraction"] <= 1.0
    assert isinstance(report["baseline"]["recall"], float)
    assert isinstance(report["baseline"]["recall_delta"], float)
    assert isinstance(report["unscored_flags"], list)


def test_slo_pins_are_compared_not_just_declared(report):
    slo = report["slo"]
    assert slo["hazard_page_minutes_after_trigger"] is not None
    assert slo["within_pin"] is True
    assert "replayed" in slo["note"] or "simulated" in slo["note"]
