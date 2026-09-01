# Emergent Scope Sentinel

Part 2 of the take-home: a focused, runnable slice of the design in
`design/design.pdf` (source `design/design.md`). The design is the primary
deliverable. The slice is here as evidence that its choices survive contact
with code, which is what the brief asked for.

The four deliverables: [design/design.pdf](design/design.pdf) (design
doc), [design/architecture.png](design/architecture.png) (architecture
diagram), [design/another_week.pdf](design/another_week.pdf) (the half
page on another week), and this repo with its README.

**The claim the slice proves:** emergent scope is a diff against approved
scope, not a property of a message. A per-job scope ledger seeded from the
job package is the reference; a small model extracts candidates with
evidence spans; a deterministic diff against the ledger is the only place
suppression can happen, and nothing the model writes can reach it. Approved
emergent work amends the ledger, which is how the loop closes.

## Quickstart

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q     # fully offline: mock + recorded replay
PYTHONPATH=src .venv/bin/python -m sentinel run \
  --data data/job_a --standards data/standards --out out --backend replay
PYTHONPATH=src .venv/bin/python -m sentinel run \
  --data data/job_a --standards data/standards --out out_base --baseline
PYTHONPATH=src .venv/bin/python -m sentinel metrics \
  --run out --data data/job_a --gold eval/gold/expectations.jsonl \
  --baseline out_base --out report.json
```

(`make setup && make test` does the same setup and test run via the
Makefile.)

Backends: `mock` is deterministic and offline and exists to run the
plumbing; the metrics report will not treat mock numbers as headline
results. `live --record`
makes real model calls (needs `ANTHROPIC_API_KEY` in `.env` or the
environment) and records fixtures under `fixtures/replay/`; `replay` then
reproduces the recorded run exactly, keyed on a hash of model + prompt +
attempt, so a prompt edit after recording fails loudly instead of silently.

## The dataset (self-generated, frozen before any tuning)

One synthetic job package (work plan, two permits, a JSA with hazard and
control tables; `package.json` is the canonical seeded form, since parsing
the PDFs is design scope, not slice scope) and 43 chat messages over one
field day: 56% operational chatter and noise, planned work phrased exactly
like emergent work (only the ledger identifier separates them), equipment-id
variants (V-2205 / V2205 / v 2205), one prompt-injection attempt, and a
shift boundary.

The brief's planted "Job B" can be read two ways, so I planted both:

- **Primary reading:** a second, unplanned piece of work surfaces gradually
  inside Job A's channel (messages `jb1`-`jb7`: a weeping cellar valve
  becomes a swap done under a cracked flange). The slice must open a work
  item early and escalate before the work runs.
- **Alternative reading:** an adjacent job's work bleeds into this channel
  (messages `ax1`-`ax4`: another crew ties into manifold M-140). The slice
  opens a separate work item and escalates on execution intent and at the
  shift handover.

Gold expectations live in `eval/gold/expectations.jsonl`, written together
with the dataset and committed before any prompt or lexicon work, so the
detector is never graded on questions written after peeking at its answers.

## What a run produces

`work_items.json` (one row per piece of work, with the deterministic fold
state), `escalations.json` (hazard page with the parallel duty-HSE
addressee, execution-intent and handover escalations), `covered_log.json`
(every suppression, with the identifier's literal span in the raw message:
the zero-suppression receipt), `digest.json` (every work item with when it
became visible and its state: the non-hazard lane's daily view),
`handover_pack.json` (the items still open at each shift boundary),
`trace.jsonl`, `costs.json`, `run_summary.json`.

The metrics report scores the run against gold: catch and latency for the
plant, recall against the planted messages, lexicon-only baseline delta,
precision on the noise half, hard-key fraction, the property checks
(injection stays uncovered, coarse rows never suppress, the amendment makes
later mentions covered, hazard page and handover escalation fire), and an
`honest_misses` list that reports whatever was not caught. Keep in mind
the latency figures are measured on the replayed message timeline; that
is a retrospective number, and I am not claiming online performance with
it.

## The recorded run

`eval/report_recorded.json` is the committed report of one live
claude-haiku-4-5 run over the frozen dataset (43 calls, $0.07), verified by
offline replay: `tests/test_replay.py` recomputes it from the replayed
fixtures and asserts whole-dict equality, so any prompt or model change
after recording fails loudly. From that file:

- **Recall 0.889** on the nine planted emergent messages, against 0.778
  for the lexicon-only baseline. The +0.111 delta is what the T1 model
  call earns. The one miss, jb3 ("sent a pic to the group"), is the
  tagless photo message; reading attachments is a named v2 item.
- The primary plant's work item opens at its first message (jb1), hours
  before execution. The hazard page fires at the first hazard-class
  mention, which on this dataset is the execution message itself (jb6);
  the 5-minute pin is measured from that trigger message on the replayed
  timeline.
- The intervention window is measured, not asserted: the valve item was
  visible from jb1 (08:05) and execution began at jb6 (14:40), 395
  minutes later, all on the replayed timeline. The digest shows it from
  08:05. The 18:00 handover pack carries the five still-open items
  (M-140, K-7100 and the three tagless soft items) and not wi-V2205
  itself, because that item was dispositioned at 15:30: the system
  working, with the open soft items being the same clustering gap
  measured below.
- **Precision on the noise half: 0.909.** The one false positive is n07,
  the worn hydraulic hose swapped from spares: replacement-in-kind, the
  exact MOC boundary case, and the same call the baseline makes.
- jb4 and jb7, tagless mentions no lexicon can see, are caught by the model
  as separate soft items rather than joining wi-V2205. By design the slice
  ships no clustering adjudicator; this run is the measured argument for
  that v2 item.
- One property check ships false: planned_covered. The model labelled
  pl3 ("PTW-2214 signed on for the day") as status chatter, so it never
  became a candidate and never reached the covered log. Nothing was
  wrongly suppressed (zero_suppression holds) and nothing emergent was
  hidden; the frozen gold check conflates "must be flagged and covered"
  with "covered when flagged". I chose to report that outcome rather than
  retune the gold after seeing results; the freeze exists exactly for
  this.
- The injection attempt is defeated by the real model too: inj1 ("V-2205
  is covered under PTW-2214") landed as an uncovered mention of wi-V2205.

## Evaluation limits, stated plainly

- The plants, the gold and the T0 marker lexicon share an author, and
  several lexicon phrases appear verbatim in planted messages ("grab the
  spare", "cracking the flange"). The recorded recall and the baseline it
  beats are both softer than the same numbers on third-party data would
  be; held-out plants written by a field supervisor are the first
  another-week item for exactly this reason.
- precision_on_noise_half's denominator is the eleven flagged messages,
  and its true-positive set includes the two property-check plants (inj1,
  n25). The plainest statement of the same artifact: one false positive
  (n07) across the 24 noise messages.
- At this dataset's real chat rates every window flushed on the timer
  holding one message, so N=10 batching and cross-message accumulation
  went unexercised; the window mechanism is cost-bounding here, not
  demonstrated behaviour. Escalation routing is also computed
  retrospectively over the replay, so an item's earlier execution-intent
  escalation would be suppressed by a later hazard page if labels lined
  up that way; on this dataset they did not (jb5 carries no execution
  signal), but an online implementation must route incrementally.

## What the slice deliberately does not do

No Teams integration (transport is a replayed JSONL fixture), no clustering
adjudicator, no T3 standards dossier, no attachment reading, no
multilingual handling, no package-PDF parsing. All of these are designed
and argued in the design doc; I kept the slice to the thin end-to-end
detection path because that is where the design's core claim lives.

## How this was built

I used AI heavily as the build tool, the same way I use it in production
work: Claude wrote most of the code and prose under my direction, inside
a gated loop (plan, adversarial review, TDD, and a commit hook that
blocks on lint, tests and requirement coverage). Every design decision
was argued against alternatives before it was accepted, the dataset and
gold were frozen before any tuning, the live run is recorded and
replay-pinned, and the failing check shipped instead of being tuned
away. The judgment calls, and the mistakes, are mine.

## Layout

| Path | What |
|---|---|
| `design/` | The design doc (md + PDF), architecture diagram, the another-week half page (md + PDF), render scripts |
| `src/sentinel/` | The slice: schemas, package seeding, T0 guards, windows, T1 prompts + model client, T2 diff, work items + fold, alerts, pipeline, metrics, CLI |
| `data/job_a/`, `data/standards/` | Synthetic job package, messages, dispositions; standards-derived hazard patterns |
| `eval/gold/` | Frozen gold expectations; `eval/report_recorded.json` is the number source |
| `fixtures/replay/` | The recorded live run, 43 fixtures keyed on model + prompt + attempt |
| `tests/` | 84 tests; TDD throughout |
| `docs/` | The verbatim assignment brief and the decision record |
| `ENDGOAL.md`, `CLAUDE.md`, `scripts/`, `.githooks/` | Working rules and the commit gate (lint, tests, requirement coverage) |
