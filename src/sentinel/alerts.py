"""Two lanes. Suppression governs whether a row exists; this module governs which rows
interrupt. Hazard classes page once, at first mention, with the unconditional parallel
duty-HSE addressee (the supervisor may be directing the drift). Non-hazard rows
interrupt only on execution intent or when unresolved at a shift handover."""

from __future__ import annotations

from datetime import datetime

from sentinel.schemas import Escalation, WorkItem

HAZARD_ADDRESSEES = ["duty_hse", "supervisor"]
SUPERVISOR_ONLY = ["supervisor"]


def open_at(boundary: datetime, open_ts: datetime, done_ts: datetime | None) -> bool:
    """The one open-at-boundary predicate, shared by the handover escalation and
    the handover pack so the two can never disagree."""
    return boundary > open_ts and (done_ts is None or done_ts > boundary)


def route(items: list[WorkItem], times: dict[str, datetime],
          boundaries: list[datetime], resolved: dict[str, datetime]) -> list[Escalation]:
    out: list[Escalation] = []
    for wi in items:
        mentions = sorted(wi.mentions, key=lambda u: (times[u.candidate.message_id],
                                                      u.candidate.message_id))
        hazard = next((u for u in mentions if u.guard.hazard_hits), None)
        if hazard is not None:
            mid = hazard.candidate.message_id
            out.append(Escalation(item_id=wi.item_id, lane="hazard",
                                  addressees=HAZARD_ADDRESSEES, ts=times[mid],
                                  message_id=mid))
        else:
            execu = next((u for u in mentions if u.guard.execution_hits
                          or u.candidate.label == "execution_intent"), None)
            if execu is not None:
                mid = execu.candidate.message_id
                out.append(Escalation(item_id=wi.item_id, lane="execution_intent",
                                      addressees=SUPERVISOR_ONLY, ts=times[mid],
                                      message_id=mid))
        open_ts = times[mentions[0].candidate.message_id]
        done_ts = resolved.get(wi.key)
        for boundary in sorted(boundaries):  # every handover until resolved
            if open_at(boundary, open_ts, done_ts):
                out.append(Escalation(item_id=wi.item_id, lane="handover",
                                      addressees=SUPERVISOR_ONLY, ts=boundary))
    return out
