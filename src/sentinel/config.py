"""Pins from the design doc, once. The slice measures them; it does not tune them."""

from __future__ import annotations

WINDOW_N = 10
WINDOW_T_SECONDS = 120
SLO_HAZARD_PAGE_MINUTES = 5
SLO_NONHAZARD_ROW_MINUTES = 15

T1_MODEL = "claude-haiku-4-5"
T1_MAX_TOKENS = 1024
MAX_ATTEMPTS = 2

# $ per MTok (input, output); published prices as of 2026-08-31, for the run cost line.
PRICES_PER_MTOK = {"claude-haiku-4-5": (1.0, 5.0), "claude-sonnet-5": (2.0, 10.0)}
