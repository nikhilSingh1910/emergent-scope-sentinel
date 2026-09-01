"""One model client, three backends. Replay keys pin model + normalized prompt +
attempt; a prompt edit after recording is an explicit miss, never a silent one."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


def test_replay_key_is_stable_and_attempt_sensitive():
    from sentinel.llm import replay_key

    k1 = replay_key("claude-haiku-4-5", "sys\n\nuser", 1)
    k2 = replay_key("claude-haiku-4-5", "sys\n\nuser", 1)
    k3 = replay_key("claude-haiku-4-5", "sys\n\nuser", 2)
    assert k1 == k2 != k3 and len(k1) == 64


def test_replay_backend_misses_loudly(tmp_path):
    from sentinel.llm import ReplayBackend, ReplayMiss

    with pytest.raises(ReplayMiss):
        ReplayBackend(tmp_path).complete("w000", "no such recording", system="s")


def test_replay_backend_returns_recorded_fixture(tmp_path):
    from sentinel.config import T1_MODEL
    from sentinel.llm import ReplayBackend, replay_key

    key = replay_key(T1_MODEL, "s\n\nu", 1)
    (tmp_path / f"{key}.json").write_text(json.dumps({
        "response": {"candidates": []},
        "usage": {"input_tokens": 11, "output_tokens": 3},
        "model": T1_MODEL,
    }), encoding="utf-8")
    c = ReplayBackend(tmp_path).complete("w000", "u", system="s")
    assert c.data == {"candidates": []} and c.backend == "replay"
    assert c.usage.input_tokens == 11


def test_mock_backend_is_deterministic_and_offline():
    from sentinel.llm import MockBackend

    user = ('<messages><msg id="m1" author="crew" ts="t">V-2205 is shot, swap it</msg>'
            '<msg id="m2" author="crew" ts="t">coffee break</msg></messages>')
    a = MockBackend().complete("w000", user, system="s")
    b = MockBackend().complete("w000", user, system="s")
    assert a.data == b.data
    ids = [c["message_id"] for c in a.data["candidates"]]
    assert "m1" in ids and "m2" not in ids


def test_mock_reads_spaced_tags_but_not_stopword_prefixes():
    """Model-like: 'v 2205' is equipment; 'at 350 psi' is not a tag."""
    from sentinel.llm import MockBackend

    user = ('<messages><msg id="m1" author="crew" ts="t">starting on v 2205 now</msg>'
            '<msg id="m2" author="crew" ts="t">test holding at 350 psi</msg>'
            '<msg id="m3" author="crew" ts="t">mud tanks at 60 percent</msg></messages>')
    data = MockBackend().complete("w000", user, system="s").data
    by_id = {c["message_id"]: c for c in data["candidates"]}
    assert "m2" not in by_id and "m3" not in by_id
    assert by_id["m1"]["equipment"] == "v 2205"
    assert by_id["m1"]["label"] == "execution_intent"


def test_live_backend_records_fixture_with_injected_client(tmp_path):
    from sentinel.llm import LiveBackend
    from sentinel.prompts import T1_TOOL

    fake_response = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", name=T1_TOOL["name"],
                                 input={"candidates": []})],
        stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )

    class FakeMessages:
        def create(self, **kwargs):
            return fake_response

    fake_client = SimpleNamespace(messages=FakeMessages())
    be = LiveBackend(tmp_path, record=True, client=fake_client)
    c = be.complete("w000", "user text", system="sys text")
    assert c.data == {"candidates": []} and c.backend == "live"
    recorded = list(tmp_path.glob("*.json"))
    assert len(recorded) == 1 and c.key in recorded[0].name


def test_backend_factory():
    from sentinel.llm import MockBackend, make_backend

    assert isinstance(make_backend("mock"), MockBackend)
    with pytest.raises(ValueError):
        make_backend("nope")
