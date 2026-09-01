"""Every shape in the slice, once. Identifier normalization lives here because
three modules (package, guards, diff) must agree on it exactly."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, field_validator

_NON_ALNUM = re.compile(r"[^A-Z0-9]")


def norm_id(raw: str) -> str:
    """V-2205, v 2205 and V2205 are the same tag."""
    return _NON_ALNUM.sub("", raw.upper())


class Source(BaseModel):
    doc: str
    page: int | None = None
    span: str | None = None


class LedgerRow(BaseModel):
    row_id: str
    artifact_type: Literal["task", "permit", "jsa_hazard"]
    identifiers: list[str]
    verb: str
    equipment_class: str
    source: Source
    confidence: float
    coarse: bool = False
    origin: Literal["package", "amendment"] = "package"

    @field_validator("identifiers")
    @classmethod
    def _normalize(cls, v: list[str]) -> list[str]:
        return [norm_id(i) for i in v]


class Package(BaseModel):
    job_id: str
    job_card: str
    shift_end_hours_utc: list[int]
    rows: list[LedgerRow]
    gazetteer: set[str]


class Message(BaseModel):
    id: str
    ts: AwareDatetime
    author_role: Literal["crew", "supervisor", "other"]
    text: str
    attachment_present: bool = False


class GuardSignals(BaseModel):
    message_id: str
    marker_hits: list[str] = Field(default_factory=list)
    execution_hits: list[str] = Field(default_factory=list)
    hazard_hits: list[str] = Field(default_factory=list)
    ledger_id_hits: list[str] = Field(default_factory=list)
    unknown_tags: list[str] = Field(default_factory=list)
    tag_spans: dict[str, tuple[int, int]] = Field(default_factory=dict)
    attachment_present: bool = False
    bypass: bool = False

    def signal_count(self) -> int:
        return (len(self.marker_hits) + len(self.execution_hits) + len(self.hazard_hits)
                + len(self.unknown_tags) + int(self.attachment_present))


class T1Candidate(BaseModel):
    message_id: str
    label: Literal["emergent_scope", "execution_intent", "hazard_mention",
                   "status_chatter", "other"]
    severity: Literal["low", "medium", "high"]
    evidence_span: str
    equipment: str | None = None
    action: str | None = None
    location: str | None = None
    certainty: Literal["low", "medium", "high"]


class Usage(BaseModel):
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class Window(BaseModel):
    window_id: str
    message_ids: list[str]
    reason: Literal["count", "timer", "bypass", "end"]


class CoveredLog(BaseModel):
    """Suppression receipt: the identifier's literal location in the raw message,
    so the zero-suppression check can prove no model-minted string suppressed."""

    message_id: str
    row_id: str
    identifier: str
    span: tuple[int, int]


class UncoveredItem(BaseModel):
    candidate: T1Candidate
    guard: GuardSignals
    identifiers: list[str] = Field(default_factory=list)


class DiffResult(BaseModel):
    uncovered: list[UncoveredItem] = Field(default_factory=list)
    covered_log: list[CoveredLog] = Field(default_factory=list)


class WorkItem(BaseModel):
    item_id: str
    key: str
    hard_keyed: bool
    mentions: list[UncoveredItem]


class Escalation(BaseModel):
    item_id: str
    lane: Literal["hazard", "execution_intent", "handover"]
    addressees: list[str]
    ts: AwareDatetime
    message_id: str | None = None
