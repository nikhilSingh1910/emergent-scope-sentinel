"""Window assembly: N messages or T seconds, whichever first; hazard bypass gets an
immediate single-message window. All time comes from message timestamps (replay is
deterministic; there is no wall clock anywhere in the pipeline)."""

from __future__ import annotations

from sentinel.config import WINDOW_N, WINDOW_T_SECONDS
from sentinel.schemas import GuardSignals, Message, Window


def assemble(messages: list[Message], signals: dict[str, GuardSignals]) -> list[Window]:
    out: list[Window] = []
    pending: list[Message] = []

    def flush(reason: str) -> None:
        if pending:
            out.append(Window(window_id=f"w{len(out):03d}",
                              message_ids=[m.id for m in pending], reason=reason))
            pending.clear()

    for msg in sorted(messages, key=lambda m: (m.ts, m.id)):
        if signals[msg.id].bypass:
            out.append(Window(window_id=f"w{len(out):03d}", message_ids=[msg.id],
                              reason="bypass"))
            continue
        if pending and (msg.ts - pending[0].ts).total_seconds() >= WINDOW_T_SECONDS:
            flush("timer")
        pending.append(msg)
        if len(pending) >= WINDOW_N:
            flush("count")
    flush("end")
    return out
