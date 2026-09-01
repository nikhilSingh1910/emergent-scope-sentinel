"""T1 window assembly: N/T flush, hazard bypass, deterministic ordering, no wall clock."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


def _msgs(specs):
    from sentinel.schemas import Message

    t0 = datetime(2026, 9, 1, 6, 0, 0, tzinfo=UTC)
    return [Message(id=mid, ts=t0 + timedelta(seconds=dt), author_role="crew", text=text)
            for mid, dt, text in specs]


def _sig(msg, bypass=False):
    from sentinel.schemas import GuardSignals

    return GuardSignals(message_id=msg.id, bypass=bypass,
                        hazard_hits=["hot_work"] if bypass else [])


@pytest.fixture(scope="module")
def windows_mod():
    import sentinel.windows as w

    return w


def test_orders_by_ts_then_id(windows_mod):
    msgs = _msgs([("m2", 5, "b"), ("m1", 5, "a"), ("m0", 0, "z")])
    sigs = {m.id: _sig(m) for m in msgs}
    wins = windows_mod.assemble(list(reversed(msgs)), sigs)
    flat = [mid for w in wins for mid in w.message_ids]
    assert flat == ["m0", "m1", "m2"]


def test_count_flush_at_n(windows_mod):
    from sentinel.config import WINDOW_N

    msgs = _msgs([(f"m{i:02d}", i, f"text {i}") for i in range(WINDOW_N + 2)])
    sigs = {m.id: _sig(m) for m in msgs}
    wins = windows_mod.assemble(msgs, sigs)
    assert [len(w.message_ids) for w in wins] == [WINDOW_N, 2]
    assert wins[0].reason == "count" and wins[1].reason == "end"


def test_timer_flush(windows_mod):
    from sentinel.config import WINDOW_T_SECONDS

    msgs = _msgs([("m0", 0, "a"), ("m1", 30, "b"), ("m2", WINDOW_T_SECONDS + 80, "c")])
    sigs = {m.id: _sig(m) for m in msgs}
    wins = windows_mod.assemble(msgs, sigs)
    assert [w.message_ids for w in wins] == [["m0", "m1"], ["m2"]]
    assert wins[0].reason == "timer" and wins[1].reason == "end"


def test_hazard_bypass_is_its_own_immediate_window(windows_mod):
    msgs = _msgs([("m0", 0, "a"), ("m1", 10, "hot work needed"), ("m2", 20, "c")])
    sigs = {m.id: _sig(m) for m in msgs}
    sigs["m1"] = _sig(msgs[1], bypass=True)
    wins = windows_mod.assemble(msgs, sigs)
    bypass = [w for w in wins if w.reason == "bypass"]
    assert len(bypass) == 1 and bypass[0].message_ids == ["m1"]
    other = [mid for w in wins if w.reason != "bypass" for mid in w.message_ids]
    assert other == ["m0", "m2"]
