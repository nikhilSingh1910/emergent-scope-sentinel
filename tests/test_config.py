"""The pins exist once, in config, and match the design doc's stated numbers."""

from __future__ import annotations


def test_window_pins_match_the_design_doc():
    from sentinel import config

    assert config.WINDOW_N == 10
    assert config.WINDOW_T_SECONDS == 120


def test_slo_pins_match_the_design_doc():
    from sentinel import config

    assert config.SLO_HAZARD_PAGE_MINUTES == 5
    assert config.SLO_NONHAZARD_ROW_MINUTES == 15


def test_model_and_bounds():
    from sentinel import config

    assert config.T1_MODEL.startswith("claude-")
    assert 1 <= config.MAX_ATTEMPTS <= 3
    assert config.T1_MODEL in config.PRICES_PER_MTOK
