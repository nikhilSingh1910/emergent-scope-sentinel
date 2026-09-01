"""T2, the only suppression point. Covered means: the raw message span carries an
identifier that exactly matches a non-coarse ledger row, and nothing else in the
message is unknown. Identifiers come from the T0 scan of the raw text (with span
offsets), never from model output; a model-minted equipment field cannot match."""

from __future__ import annotations

from sentinel.schemas import (
    CoveredLog,
    DiffResult,
    GuardSignals,
    Message,
    Package,
    T1Candidate,
    UncoveredItem,
)

_SEV = {"low": 0, "medium": 1, "high": 2}


def diff(items: list[tuple[Message, T1Candidate, GuardSignals]], pkg: Package) -> DiffResult:
    row_by_id: dict = {}
    for row in pkg.rows:  # first-declared row owns the receipt (stable attribution)
        if not row.coarse:
            for i in row.identifiers:
                row_by_id.setdefault(i, row)
    uncovered: list[UncoveredItem] = []
    covered: list[CoveredLog] = []
    for msg, cand, sig in items:
        suppressing = [i for i in sig.ledger_id_hits if i in row_by_id]
        known_but_coarse = [i for i in sig.ledger_id_hits if i not in row_by_id]
        if suppressing and not sig.unknown_tags and not known_but_coarse:
            covered.extend(CoveredLog(message_id=msg.id, row_id=row_by_id[i].row_id,
                                      identifier=i, span=sig.tag_spans[i])
                           for i in suppressing)
            continue
        uncovered.append(UncoveredItem(candidate=cand, guard=sig,
                                       identifiers=sig.unknown_tags + known_but_coarse))
    uncovered.sort(key=lambda u: (-_SEV[u.candidate.severity], -_SEV[u.candidate.certainty],
                                  -u.guard.signal_count(), u.candidate.message_id))
    return DiffResult(uncovered=uncovered, covered_log=covered)
