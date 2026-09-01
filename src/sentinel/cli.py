"""One command: replay a job's channel through the detection path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentinel.metrics import compute_metrics
from sentinel.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sentinel")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run the detection path over a job's fixtures")
    run.add_argument("--data", type=Path, required=True,
                     help="job dir with package.json, messages.jsonl[, dispositions.jsonl]")
    run.add_argument("--standards", type=Path, required=True,
                     help="dir with hazard_patterns.json (the standards-derived artifact)")
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--backend", choices=["mock", "replay", "live"], default="replay")
    run.add_argument("--record", action="store_true",
                     help="with --backend live: record fixtures for replay")
    run.add_argument("--baseline", action="store_true",
                     help="lexicon-only baseline, no model calls")
    run.add_argument("--fixtures", type=Path, default=None)
    met = sub.add_parser("metrics", help="score a run against gold expectations")
    met.add_argument("--run", type=Path, required=True)
    met.add_argument("--data", type=Path, required=True)
    met.add_argument("--gold", type=Path, required=True)
    met.add_argument("--baseline", type=Path, default=None)
    met.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.command == "metrics":
        report = compute_metrics(args.run, args.data, args.gold,
                                 baseline_dir=args.baseline)
        if args.out:
            args.out.write_text(json.dumps(report, indent=1), encoding="utf-8")
        print(json.dumps(report, indent=1))
        return 0
    summary = run_pipeline(args.data, args.standards, args.out,
                           backend_name=args.backend, fixtures_dir=args.fixtures,
                           record=args.record, baseline=args.baseline)
    print(json.dumps(summary, indent=1))
    return 0
