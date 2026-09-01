"""Shared test helpers: repo paths and loaders."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "job_a"
STANDARDS = ROOT / "data" / "standards"
EVAL = ROOT / "eval"


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def build_tiny_job(base: Path) -> tuple[Path, Path]:
    """A minimal but complete job: planned pump swap (covered), emergent valve (Job B in
    miniature), hazard moment, execution intent, amendment closing the loop."""
    job = base / "job"
    std = base / "standards"
    job.mkdir(parents=True, exist_ok=True)
    std.mkdir(parents=True, exist_ok=True)
    (std / "hazard_patterns.json").write_text(json.dumps({
        "change_markers": ["swap", "might as well", "while we're here", "shot",
                           "looking rough"],
        "execution_markers": ["starting", "doing it now"],
        "hazard_classes": {"hot_work": ["hot work", "weld", "grind"],
                           "stored_energy": ["under pressure", "energized"]},
        "tag_regex": "\\b[A-Za-z]{1,4}-?\\d{2,5}[A-Za-z]?\\b",
    }), encoding="utf-8")
    (job / "package.json").write_text(json.dumps({
        "job_id": "JOB-TINY", "job_card": "Workover on well A-12: replace charge pump "
        "P-310A under WO-7841.", "shift_end_hours_utc": [6, 18],
        "rows": [{"row_id": "t1", "artifact_type": "task",
                  "identifiers": ["WO-7841", "P-310A"], "verb": "replace",
                  "equipment_class": "pump", "source": {"doc": "work_plan.md"},
                  "confidence": 0.95}],
    }), encoding="utf-8")
    msgs = [
        {"id": "m1", "ts": "2026-09-01T06:05:00+00:00", "author_role": "crew",
         "text": "morning, mud check done, all quiet"},
        {"id": "m2", "ts": "2026-09-01T06:06:00+00:00", "author_role": "crew",
         "text": "pump's looking rough, swapping P-310A this morning per WO-7841"},
        {"id": "m3", "ts": "2026-09-01T06:30:00+00:00", "author_role": "crew",
         "text": "that cellar valve V-2205 is shot, might as well swap it too"},
        {"id": "m4", "ts": "2026-09-01T06:40:00+00:00", "author_role": "crew",
         "text": "V-2205 flange will need hot work to free it"},
        {"id": "m5", "ts": "2026-09-01T06:50:00+00:00", "author_role": "crew",
         "text": "starting the V-2205 swap now"},
        {"id": "m6", "ts": "2026-09-01T07:30:00+00:00", "author_role": "crew",
         "text": "V-2205 swap done, new gasket in"},
    ]
    (job / "messages.jsonl").write_text(
        "\n".join(json.dumps(m) for m in msgs) + "\n", encoding="utf-8")
    (job / "dispositions.jsonl").write_text("\n".join(json.dumps(d) for d in [
        {"ts": "2026-09-01T07:00:00+00:00", "item_key": "V2205", "actor": "sup1",
         "action": "acknowledge"},
        {"ts": "2026-09-01T07:10:00+00:00", "item_key": "V2205", "actor": "sup1",
         "action": "approve_as_amendment",
         "row": {"row_id": "a1", "artifact_type": "task", "identifiers": ["V-2205"],
                 "verb": "replace", "equipment_class": "valve",
                 "source": {"doc": "amendment", "span": "approved V-2205 swap"},
                 "confidence": 1.0}},
    ]) + "\n", encoding="utf-8")
    return job, std
