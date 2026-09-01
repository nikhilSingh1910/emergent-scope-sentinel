"""T0 deterministic guards. OR-only: a scan annotates every message with signals
and can set the hazard bypass; it never drops a message from the model's view."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from sentinel.schemas import GuardSignals, Message, norm_id


@dataclass(frozen=True)
class Patterns:
    change_markers: list[str]
    execution_markers: list[str]
    hazard_classes: dict[str, list[str]]
    tag_regex: re.Pattern


def load_patterns(path: Path) -> Patterns:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return Patterns(
        change_markers=[m.lower() for m in raw["change_markers"]],
        execution_markers=[m.lower() for m in raw["execution_markers"]],
        hazard_classes={k: [m.lower() for m in v] for k, v in raw["hazard_classes"].items()},
        tag_regex=re.compile(raw["tag_regex"]),
    )


# Spaced tag spellings ("v 2205") are real field usage; a stopword prefix ("at 350")
# is prose. Linguistic constants live in code; operator tag shapes live in patterns.
_SPACED = re.compile(r"\b([A-Za-z]{1,4}) (\d{2,5}[A-Za-z]?)\b")
_STOP_PREFIXES = {"a", "at", "to", "in", "on", "of", "is", "the", "for", "and", "by"}
_CANON = re.compile(r"\b[A-Za-z]{1,4}-?\d{2,5}[A-Za-z]?\b")


def first_tag(text: str) -> str | None:
    """First tag-like token by position, fused/hyphenated or spaced, stopword-filtered.
    Used by the mock backend so its reading matches T0's."""
    hits = [(m.start(), m.group(0)) for m in _CANON.finditer(text)]
    hits += [(m.start(), m.group(0)) for m in _SPACED.finditer(text)
             if m.group(1).lower() not in _STOP_PREFIXES]
    return min(hits)[1] if hits else None


def _tag_spans(text: str, tag_regex: re.Pattern) -> dict[str, tuple[int, int]]:
    spans: dict[str, tuple[int, int]] = {}
    for m in tag_regex.finditer(text):
        spans.setdefault(norm_id(m.group(0)), (m.start(), m.end()))
    for m in _SPACED.finditer(text):
        if m.group(1).lower() in _STOP_PREFIXES:
            continue
        spans.setdefault(norm_id(m.group(0)), (m.start(), m.end()))
    return spans


def scan(msg: Message, patterns: Patterns, gazetteer: set[str]) -> GuardSignals:
    text = msg.text.lower()
    spans = _tag_spans(msg.text, patterns.tag_regex)
    tags = list(spans)
    hazard = [cls for cls, markers in patterns.hazard_classes.items()
              if any(m in text for m in markers)]
    return GuardSignals(
        message_id=msg.id,
        marker_hits=[m for m in patterns.change_markers if m in text],
        execution_hits=[m for m in patterns.execution_markers if m in text],
        hazard_hits=hazard,
        ledger_id_hits=[t for t in tags if t in gazetteer],
        unknown_tags=[t for t in tags if t not in gazetteer],
        tag_spans=spans,
        attachment_present=msg.attachment_present,
        bypass=bool(hazard),
    )
