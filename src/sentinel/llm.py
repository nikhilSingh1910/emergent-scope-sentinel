"""The one model client: live Anthropic calls, replay of committed fixtures, or an
offline mock. Replay keys hash model + normalized prompt + attempt, so a prompt edit
after recording is an explicit miss. Pattern lifted from a prior build of mine."""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path

from sentinel.config import T1_MAX_TOKENS, T1_MODEL
from sentinel.guards import first_tag
from sentinel.prompts import T1_TOOL
from sentinel.schemas import Usage

_MSG = re.compile(r'<msg id="([^"]+)"[^>]*>(.*?)</msg>', re.S)


class ReplayMiss(Exception):
    """The replay store has no recorded answer for this exact prompt."""


class ModelOutputError(Exception):
    """The live model returned no usable tool call."""


def normalize_prompt(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def replay_key(model: str, prompt: str, attempt: int) -> str:
    blob = f"{model}\n{normalize_prompt(prompt)}\n{attempt}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _full(system: str, prompt: str) -> str:
    return f"{system}\n\n{prompt}" if system else prompt


@dataclass(frozen=True)
class Completion:
    data: dict
    usage: Usage
    key: str
    model: str
    backend: str


class ReplayBackend:
    name = "replay"

    def __init__(self, fixtures_dir: Path):
        self.fixtures_dir = Path(fixtures_dir)

    def complete(self, window_id: str, prompt: str, attempt: int = 1, *,
                 model: str = T1_MODEL, system: str = "", tool: dict | None = None,
                 ) -> Completion:
        key = replay_key(model, _full(system, prompt), attempt)
        path = self.fixtures_dir / f"{key}.json"
        if not path.exists():
            raise ReplayMiss(f"{window_id}: no recording for attempt {attempt} "
                             f"(key {key[:12]}); run with --backend live --record")
        data = json.loads(path.read_text(encoding="utf-8"))
        usage = Usage(model=data.get("model", model), **data.get("usage", {}))
        return Completion(data=data["response"], usage=usage, key=key,
                          model=usage.model, backend=self.name)


class LiveBackend:
    name = "live"

    def __init__(self, fixtures_dir: Path, record: bool = False, client=None):
        self.fixtures_dir = Path(fixtures_dir)
        self.record = record
        if client is None:
            import anthropic  # lazy: replay and mock need neither the package nor a key

            client = anthropic.Anthropic()
        self._client = client

    def complete(self, window_id: str, prompt: str, attempt: int = 1, *,
                 model: str = T1_MODEL, system: str = "", tool: dict | None = None,
                 ) -> Completion:
        tool = tool or T1_TOOL
        key = replay_key(model, _full(system, prompt), attempt)
        params: dict = {
            "model": model, "max_tokens": T1_MAX_TOKENS, "tools": [tool],
            "tool_choice": {"type": "tool", "name": tool["name"]},
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            params["system"] = system
        response = self._client.messages.create(**params)
        block = next((b for b in response.content
                      if getattr(b, "type", "") == "tool_use" and b.name == tool["name"]),
                     None)
        if block is None or not isinstance(block.input, dict):
            raise ModelOutputError(f"{window_id}: no {tool['name']} call "
                                   f"({response.stop_reason})")
        usage = Usage(model=model, input_tokens=response.usage.input_tokens,
                      output_tokens=response.usage.output_tokens)
        if self.record:
            self.fixtures_dir.mkdir(parents=True, exist_ok=True)
            (self.fixtures_dir / f"{key}.json").write_text(json.dumps({
                "key": key, "window": window_id, "model": model, "attempt": attempt,
                "request": {"system": system, "user": prompt},
                "response": block.input,
                "usage": {"input_tokens": usage.input_tokens,
                          "output_tokens": usage.output_tokens},
            }, indent=1, ensure_ascii=False), encoding="utf-8")
        return Completion(data=block.input, usage=usage, key=key, model=model,
                          backend=self.name)


class MockBackend:
    """Deterministic, offline, deliberately dumb: a candidate for every fenced message
    carrying a tag-like token. Exists to run the plumbing; headline metrics refuse it."""

    name = "mock"

    def complete(self, window_id: str, prompt: str, attempt: int = 1, *,
                 model: str = T1_MODEL, system: str = "", tool: dict | None = None,
                 ) -> Completion:
        key = replay_key(model, _full(system, prompt), attempt)
        candidates = []
        for mid, raw in _MSG.findall(prompt):
            text = html.unescape(raw)
            tag = first_tag(text)
            if tag is None:
                continue
            lower = text.lower()
            label = ("execution_intent"
                     if any(w in lower for w in ("now", "starting", "about to"))
                     else "emergent_scope")
            candidates.append({"message_id": mid, "label": label, "severity": "medium",
                               "evidence_span": text[:60], "equipment": tag,
                               "action": None, "location": None, "certainty": "low"})
        data = {"candidates": candidates}
        usage = Usage(model=f"mock:{model}", input_tokens=len(prompt) // 4,
                      output_tokens=len(json.dumps(data)) // 4)
        return Completion(data=data, usage=usage, key=key, model=usage.model,
                          backend=self.name)


def make_backend(name: str, fixtures_dir: Path | None = None, record: bool = False):
    if name == "replay":
        return ReplayBackend(fixtures_dir)
    if name == "live":
        return LiveBackend(fixtures_dir, record=record)
    if name == "mock":
        return MockBackend()
    raise ValueError(f"unknown backend {name!r}; use live, replay or mock")
