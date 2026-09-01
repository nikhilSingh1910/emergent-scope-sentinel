"""Measured outcomes from run artifacts against gold. Two standing rules from the
plan's adversarial pass: headline numbers refuse the mock backend, and misses are
reported, never trimmed."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sentinel.config import SLO_HAZARD_PAGE_MINUTES
from sentinel.schemas import norm_id


def _load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _caught_ids(work_items: list[dict]) -> set[str]:
    return {m["candidate"]["message_id"] for i in work_items for m in i["mentions"]}


def compute_metrics(run_dir: Path, data_dir: Path, gold_path: Path,
                    baseline_dir: Path | None = None) -> dict:
    run_dir = Path(run_dir)
    summary = _load(run_dir / "run_summary.json")
    items = _load(run_dir / "work_items.json")
    escalations = _load(run_dir / "escalations.json")
    covered = _load(run_dir / "covered_log.json")
    messages = {m["id"]: m for m in _load_jsonl(Path(data_dir) / "messages.jsonl")}
    gold = {g["case"]: g for g in _load_jsonl(gold_path)}

    caught = _caught_ids(items)
    covered_ids = {c["message_id"] for c in covered}
    primary = gold["job_b_primary_catch"]
    emergent = list(dict.fromkeys(primary["emergent_ids"]
                                  + gold["adjacent_bleed"]["emergent_ids"]))
    noise = set(gold["noise_precision"]["noise_ids"])

    expected_uncovered = {gold["injection_uncovered"]["message_id"],
                          gold["coarse_no_suppress"]["message_id"]}
    tp_ids = caught & (set(emergent) | expected_uncovered)
    fp_ids = caught & noise
    unscored = sorted(caught - tp_ids - fp_ids)
    mentions = [m for i in items for m in i["mentions"]]

    def ts(mid: str) -> datetime:
        return datetime.fromisoformat(messages[mid]["ts"])

    catch: dict = {}
    order = primary["emergent_ids"]
    hit = [mid for mid in order if mid in caught]
    if hit:
        first = hit[0]
        catch[primary["case"]] = {
            "caught": True,
            "first_caught": first,
            "signals_before_catch": order.index(first),
            "wall_clock_minutes_from_first_signal":
                round((ts(first) - ts(order[0])).total_seconds() / 60, 1),
            "caught_before_execution": ts(first) < ts(primary["execution_id"]),
        }
    else:
        catch[primary["case"]] = {"caught": False}

    def esc(lane: str, key: str, by_message: str | None = None) -> bool:
        return any(e["lane"] == lane and e["item_id"] == f"wi-{key}"
                   and (by_message is None or e["message_id"] == by_message)
                   for e in escalations)

    def zero_suppression() -> bool:
        for c in covered:
            s, e = c["span"]
            if norm_id(messages[c["message_id"]]["text"][s:e]) != c["identifier"]:
                return False
        return True  # vacuously true when nothing was suppressed

    amend = gold["amendment_closes_loop"]
    checks = {
        "injection_uncovered": (gold["injection_uncovered"]["message_id"] in caught
                                and gold["injection_uncovered"]["message_id"]
                                not in covered_ids),
        "coarse_no_suppress": (gold["coarse_no_suppress"]["message_id"] in caught
                               and gold["coarse_no_suppress"]["message_id"]
                               not in covered_ids),
        "amendment_closes_loop": any(c["message_id"] == amend["message_id"]
                                     and c["row_id"] == amend["expect_row"]
                                     for c in covered),
        "hazard_page": esc("hazard", gold["hazard_page"]["item_key"],
                           gold["hazard_page"]["by_message"]),
        "handover_escalation": esc("handover", gold["handover_escalation"]["item_key"]),
        "planned_covered": set(gold["planned_covered"]["covered_ids"]) <= covered_ids,
        "zero_suppression": zero_suppression(),
    }

    page = next((e for e in escalations if e["lane"] == "hazard"
                 and e["item_id"] == f"wi-{gold['hazard_page']['item_key']}"), None)
    page_minutes = (round((datetime.fromisoformat(page["ts"])
                           - ts(page["message_id"])).total_seconds() / 60, 1)
                    if page else None)
    slo = {"hazard_page_minutes_after_trigger": page_minutes,
           "pin_minutes": SLO_HAZARD_PAGE_MINUTES,
           "within_pin": page_minutes is not None
           and page_minutes <= SLO_HAZARD_PAGE_MINUTES,
           "note": "replayed timeline: page ts equals trigger message ts by construction"}

    report = {
        "backend": summary["backend"],
        "headline_eligible": summary["backend"] in {"live", "replay"}
                             and not summary["baseline"],
        "recall": round(len(caught & set(emergent)) / len(emergent), 3),
        "precision_on_noise_half": (round(len(tp_ids) / (len(tp_ids) + len(fp_ids)), 3)
                                    if tp_ids | fp_ids else 1.0),
        "unscored_flags": unscored,
        "hard_key_fraction": round(
            sum(1 for m in mentions if m["identifiers"]) / len(mentions), 3)
            if mentions else 0.0,
        "honest_misses": sorted(set(emergent) - caught),
        "catch": catch,
        "checks": checks,
        "slo": slo,
        "usd_estimate": summary.get("usd_estimate", 0.0),
    }
    if baseline_dir is not None:
        b_caught = _caught_ids(_load(Path(baseline_dir) / "work_items.json"))
        b_recall = round(len(b_caught & set(emergent)) / len(emergent), 3)
        report["baseline"] = {"recall": b_recall,
                              "recall_delta": round(report["recall"] - b_recall, 3),
                              "false_positives_on_noise": sorted(b_caught & noise)}
    return report
