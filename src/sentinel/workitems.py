"""Work items: one row per piece of work, not per message. Hard keys are span-derived
identifiers; the soft key (model-extracted equipment text) only groups mentions and can
never suppress. The fold is deterministic and replayable; amendments append to the
ledger, which is how approved emergent work becomes covered for later mentions."""

from __future__ import annotations

from sentinel.package import COARSE_CONFIDENCE
from sentinel.schemas import LedgerRow, Package, UncoveredItem, WorkItem, norm_id

# The fold is rank-monotonic: the supervisor is in the channel and may acknowledge
# or disposition before our page arrives; state moves forward, never back.
_RANK = {"open": 0, "notified": 1, "acknowledged": 2, "dispositioned": 3,
         "closed": 4, "closed_by_amendment": 4}
_EVENT_TARGET = {"notify": "notified", "acknowledge": "acknowledged",
                 "disposition": "dispositioned"}


def build_item(key: str, mentions: list[UncoveredItem], hard_keyed: bool) -> WorkItem:
    return WorkItem(item_id=f"wi-{norm_id(key) or 'misc'}", key=key,
                    hard_keyed=hard_keyed, mentions=mentions)


def cluster(uncovered: list[UncoveredItem]) -> list[WorkItem]:
    """Hard keys are span-derived identifiers, nothing else (B6): a model-extracted
    equipment field groups only its own soft item (namespaced with ~) and can never
    join a hard-keyed one, so one mis-extraction cannot merge two items or silence
    the second item's hazard page."""
    groups: dict[str, tuple[bool, list[UncoveredItem]]] = {}
    for u in uncovered:
        if u.identifiers:
            hard, key = True, u.identifiers[0]
        else:
            eq = (u.candidate.equipment or "").strip()
            hard, key = False, "~" + (eq or u.candidate.evidence_span).lower().strip()
        was_hard, mentions = groups.get(key, (False, []))
        mentions.append(u)
        groups[key] = (was_hard or hard, mentions)
    items: list[WorkItem] = []
    seen: dict[str, int] = {}
    for key, (hard, mentions) in groups.items():
        # soft ids get their own namespace: a model-derived key can never claim
        # the bare wi-KEY id that metrics and dispositions bind to, whatever
        # the iteration order
        base = (f"wi-{norm_id(key)}" if hard
                else f"wi-s-{norm_id(key) or 'misc'}")
        n = seen.get(base, 0)
        seen[base] = n + 1
        items.append(WorkItem(item_id=base if n == 0 else f"{base}-{n + 1}",
                              key=key, hard_keyed=hard, mentions=mentions))
    return items


def fold(events: list[dict]) -> str:
    state = "open"
    for ev in events:
        if ev["type"] == "close":
            if _RANK[state] < _RANK["dispositioned"]:
                raise ValueError(f"illegal close from {state!r}")
            state = "closed" if state == "dispositioned" else state
            continue
        target = _EVENT_TARGET.get(ev["type"])
        if target is None:
            raise ValueError(f"unknown event type {ev['type']!r}")
        if _RANK[target] > _RANK[state]:
            state = target
        if state == "dispositioned" and ev.get("action") == "approve_as_amendment":
            state = "closed_by_amendment"
    return state


def apply_amendment(pkg: Package, row_raw: dict) -> Package:
    row = LedgerRow(**{**row_raw, "origin": "amendment"})
    if row.confidence < COARSE_CONFIDENCE and not row.coarse:
        row = row.model_copy(update={"coarse": True})
    return Package(job_id=pkg.job_id, job_card=pkg.job_card,
                   shift_end_hours_utc=pkg.shift_end_hours_utc,
                   rows=[*pkg.rows, row], gazetteer=pkg.gazetteer | set(row.identifiers))
