"""The thin end-to-end path: seed -> T0 -> windows -> T1 -> T2 -> work items ->
escalations. All time comes from message timestamps (deterministic replay); the
package evolves mid-run as amendments land, which is how approved emergent work
becomes covered for later mentions."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import ValidationError

from sentinel.alerts import route
from sentinel.config import MAX_ATTEMPTS, PRICES_PER_MTOK
from sentinel.diff import diff
from sentinel.guards import load_patterns, scan
from sentinel.llm import ModelOutputError, ReplayMiss, make_backend
from sentinel.package import load_package
from sentinel.prompts import T1_TOOL, build_t1_prompt
from sentinel.schemas import Message, T1Candidate
from sentinel.windows import assemble
from sentinel.workitems import apply_amendment, cluster, fold

ROOT = Path(__file__).resolve().parents[2]
SCOPE_LABELS = {"emergent_scope", "execution_intent", "hazard_mention"}
FAR_FUTURE = datetime(9999, 1, 1, tzinfo=UTC)


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _boundaries(messages: list[Message], hours: list[int]) -> list[datetime]:
    if not messages or not hours:
        return []
    stamps = [m.ts.astimezone(UTC) for m in messages]
    first = min(stamps).date()
    days = (max(stamps).date() - first).days
    return [datetime(d.year, d.month, d.day, h, tzinfo=UTC)
            for n in range(days + 1)
            for d in [first + timedelta(days=n)]
            for h in sorted(hours)]


def _baseline_candidates(msgs: list[Message], sigs: dict) -> list[T1Candidate]:
    out = []
    for m in msgs:
        s = sigs[m.id]
        if not (s.marker_hits or s.unknown_tags or s.hazard_hits or s.execution_hits):
            continue
        label = ("hazard_mention" if s.hazard_hits
                 else "execution_intent" if s.execution_hits else "emergent_scope")
        out.append(T1Candidate(message_id=m.id, label=label, severity="medium",
                               evidence_span=m.text[:60], certainty="low"))
    return out


def _usd(calls: list[dict]) -> float:
    total = 0.0
    for c in calls:
        pin, pout = PRICES_PER_MTOK.get(c["model"], (0.0, 0.0))
        total += c["input_tokens"] * pin / 1e6 + c["output_tokens"] * pout / 1e6
    return round(total, 4)


def _complete_with_retries(backend, window_id: str, user: str, system: str):
    """Bounded attempts. A ReplayMiss on attempt 1 walks on to attempt 2, matching a
    live run that only succeeded (and so only recorded) on its second attempt."""
    last: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return backend.complete(window_id, user, attempt, system=system,
                                    tool=T1_TOOL)
        except (ModelOutputError, ReplayMiss) as err:
            last = err
    raise last


def run_pipeline(job_dir: Path, standards_dir: Path, out_dir: Path, *,
                 backend_name: str = "replay", fixtures_dir: Path | None = None,
                 record: bool = False, baseline: bool = False) -> dict:
    job_dir, out_dir = Path(job_dir), Path(out_dir)
    pkg = load_package(job_dir)
    patterns = load_patterns(Path(standards_dir) / "hazard_patterns.json")
    messages = sorted((Message(**m) for m in _load_jsonl(job_dir / "messages.jsonl")),
                      key=lambda m: (m.ts, m.id))
    by_id = {m.id: m for m in messages}
    if len(by_id) != len(messages):
        dupes = sorted({m.id for m in messages
                        if sum(x.id == m.id for x in messages) > 1})
        raise ValueError(f"duplicate message id(s) in messages.jsonl: {dupes}")
    backend = None if baseline else make_backend(
        backend_name, fixtures_dir or ROOT / "fixtures" / "replay", record)

    dispositions = []
    for d in _load_jsonl(job_dir / "dispositions.jsonl"):
        when = datetime.fromisoformat(d["ts"])
        if when.tzinfo is None:
            raise ValueError(f"dispositions.jsonl ts must be timezone-aware: {d['ts']!r}")
        dispositions.append((when, d))
    dispositions.sort(key=lambda x: x[0])
    events_by_key: dict[str, list[dict]] = {}
    resolved: dict[str, datetime] = {}
    di = 0

    def apply_until(ts: datetime) -> None:
        nonlocal pkg, di
        while di < len(dispositions) and dispositions[di][0] <= ts:
            when, rec = dispositions[di]
            if rec["action"] == "approve_as_amendment" and rec.get("row"):
                pkg = apply_amendment(pkg, rec["row"])
            ev: dict = {"ts": rec["ts"], "actor": rec.get("actor")}
            if rec["action"] == "acknowledge":
                ev["type"] = "acknowledge"
            else:
                ev.update(type="disposition", action=rec["action"])
                resolved.setdefault(rec["item_key"], when)
            events_by_key.setdefault(rec["item_key"], []).append(ev)
            di += 1

    windows = assemble(messages, {m.id: scan(m, patterns, pkg.gazetteer)
                                  for m in messages})
    uncovered_all, covered_all, trace, calls = [], [], [], []
    invalid = dropped = 0

    for w in windows:
        msgs_w = [by_id[i] for i in w.message_ids]
        apply_until(msgs_w[0].ts)
        sigs_w = {m.id: scan(m, patterns, pkg.gazetteer) for m in msgs_w}
        if baseline:
            cands = _baseline_candidates(msgs_w, sigs_w)
            called = False
        else:
            system, user = build_t1_prompt(pkg, msgs_w)
            completion = _complete_with_retries(backend, w.window_id, user, system)
            calls.append({"window": w.window_id, "model": completion.model,
                          "backend": completion.backend,
                          "input_tokens": completion.usage.input_tokens,
                          "output_tokens": completion.usage.output_tokens})
            called = True
            cands = []
            for c in completion.data.get("candidates", []):
                try:
                    cand = T1Candidate(**c)
                except ValidationError:
                    invalid += 1
                    continue
                if cand.label not in SCOPE_LABELS:
                    continue
                if cand.message_id not in sigs_w:
                    dropped += 1  # model named a message outside this window
                    continue
                cands.append(cand)
        res = diff([(by_id[c.message_id], c, sigs_w[c.message_id]) for c in cands], pkg)
        uncovered_all.extend(res.uncovered)
        covered_all.extend(res.covered_log)
        trace.append({"window_id": w.window_id, "reason": w.reason,
                      "message_ids": w.message_ids, "called_model": called,
                      "n_candidates": len(cands), "n_uncovered": len(res.uncovered),
                      "n_covered": len(res.covered_log)})
    apply_until(FAR_FUTURE)

    items = cluster(uncovered_all)
    times = {m.id: m.ts for m in messages}
    escalations = route(items, times, _boundaries(messages, pkg.shift_end_hours_utc),
                        resolved)
    states = {}
    for wi in items:
        evs = list(events_by_key.get(wi.key, []))
        mine = [e for e in escalations if e.item_id == wi.item_id]
        if mine:
            evs.append({"type": "notify", "ts": min(e.ts for e in mine).isoformat()})
        elif evs:  # dispositioned from the digest: the digest is the notification
            evs.append({"type": "notify", "ts": min(e["ts"] for e in evs)})
        evs.sort(key=lambda e: (e["ts"], e["type"] != "notify"))
        states[wi.item_id] = fold(evs)

    out_dir.mkdir(parents=True, exist_ok=True)
    _write = lambda name, obj: (out_dir / name).write_text(  # noqa: E731
        json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
    _write("work_items.json", [{**wi.model_dump(mode="json"),
                                "state": states[wi.item_id]} for wi in items])
    _write("escalations.json", [e.model_dump(mode="json") for e in escalations])
    _write("covered_log.json", [c.model_dump(mode="json") for c in covered_all])
    _write("costs.json", {"calls": calls, "totals": {
        "calls": len(calls),
        "input_tokens": sum(c["input_tokens"] for c in calls),
        "output_tokens": sum(c["output_tokens"] for c in calls),
        "usd_estimate": _usd(calls)}})
    (out_dir / "trace.jsonl").write_text(
        "\n".join(json.dumps(t) for t in trace) + "\n", encoding="utf-8")
    summary = {"backend": backend_name if not baseline else "none",
               "baseline": baseline, "windows": len(windows),
               "messages": len(messages), "work_items": len(items),
               "escalations": len(escalations), "covered": len(covered_all),
               "uncovered_mentions": len(uncovered_all),
               "invalid_candidates": invalid, "dropped_out_of_window": dropped,
               "usd_estimate": _usd(calls),
               "timeline": [messages[0].ts.isoformat(),
                            messages[-1].ts.isoformat()] if messages else []}
    _write("run_summary.json", summary)
    return summary
