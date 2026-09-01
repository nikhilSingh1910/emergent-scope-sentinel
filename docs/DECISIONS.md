# Decisions (append-only, dated)

Each entry: the question, the decision, why, what was rejected. Contested
choices are argued by advocate subagents with a rebuttal round and an
adversarial judge; decided by the main session with the full record in view.
Detail and timestamps: `PROGRESS.md`.

## D001 (2026-08-31) Detection core: tiered scope-conformance against a live per-job ledger

- **Question.** Classify each message in isolation, or diff described work
  against the job's approved scope?
- **Decision.** A tiered pipeline over a live per-job **scope ledger**
  (baseline seeded at mobilization + amendments + supervisor dispositions
  written back). T0: deterministic guards, free, on every message — marker
  lexicon, ledger identifiers, unknown-tag signals, composed **OR-only**
  (guards may add candidates, never suppress). T1: one schema-locked
  cheap-model call **per job window** (N messages or T seconds, not per
  message): combined classify + extract emitting accumulable relational
  evidence `{label incl. execution-intent, severity, evidence_span,
  equipment?, action?, location?, certainty}`. T2: deterministic diff
  against the ledger — **the only place suppression may occur**, and only
  on closed-set identifier match. T3: strong-model dossier on the top
  slice, with standards/learnings retrieval; clause citations only above a
  coverage threshold, else stamped unverified. Ships day one with an empty
  ledger (the classifier floor, honestly labeled); package extraction earns
  suppression per measured coverage decile.
- **Why.** "Emergent" is relational — the same sentence is planned in one
  job and unreviewed in another — so the reference must exist; but
  model-extracted text may never drive suppression (an injected "covered
  under LOTO-22" must die against the closed set), so the reference's
  authority is deterministic. The judge's line holds: package quality
  decides, not architecture.
- **Rejected.** Classify-in-isolation as the whole answer (cannot name the
  missing permit; its "scope abstract" was a covert, unmeasured parse);
  per-candidate semantic entailment as a gate; AND-composed guards
  (reintroduce the silent miss); separate classify and extract calls.

## D002 (2026-08-31) Alerting: work-item fold, disposition-before-execution, no corroboration counting

- **Question.** Stateless per-message alerts, or a per-job risk state
  machine — and when does a signal interrupt a human?
- **Decision.** One row per `(job, work_item)` plus an append-only mention
  log; status is a deterministic, versioned, replayable fold: `open ->
  notified -> acknowledged(shift, role) -> dispositioned(ledger verdict) ->
  closed | closed_by_amendment`. Routing is deterministic: never-suppress
  hazard classes (well control, energy isolation, H2S, lifting, confined
  space, stuck tool) and any hazard unmatched by controls page at **first
  mention** — @mention in the job thread **plus a parallel duty-HSE
  addressee outside the job hierarchy, unconditionally** (the supervisor
  may be the one directing the emergent work); low certainty renders as a
  question at the same weight, never withheld. Non-hazard scope drift
  creates a ledger row without interrupting and escalates on
  execution-intent or at **shift handover — the risk page is the handover
  artifact, and the outgoing supervisor dispositions open items to close
  the shift**. Unacked 15 min pages HSE; acks expire with the shift; a
  different hazard class never merges into an acknowledged item; ledger
  amendments close matching items and mute re-fires. No corroboration
  counting anywhere. The rollout ladder gates the delivery surface: shadow
  = ledger only; assisted = system proposes, human dispositions; autonomous
  = system may disposition non-hazard drift only, never hazard classes.
- **Why.** The supervisor is *in* the channel: for drift, the alert's value
  is record creation, and the safety property is **disposition before
  execution**, not notification. Corroboration counts proxy chattiness,
  not risk (quiet night crews corroborate least and carry most).
  Severity picks the lane; certainty may raise interrupt probability
  within it, never lower it. Mute rate is instrumented from shadow day one.
- **Rejected.** Stateless per-message alerting (its dedup key, TTL and
  rolling window were the state machine minus the ack timer); confidence
  gates that withhold severe-but-uncertain signals; learned suppression
  (doctrine: deterministic only); the 30-minute digest tier (a pull
  surface with a push name); median pings per channel as the fatigue
  metric (use p90 interrupts per supervisor-shift, summed across their
  concurrent jobs).

## D003 (2026-08-31) Grounding plane: the ledger is the only record; shallow rows, ranked not binary

- **Question.** Structured scope registry extracted at mobilization, or
  RAG over the raw package at query time?
- **Decision.** One record: the ledger. Mobilization extraction only
  **seeds** it: shallow typed rows `{artifact_type: task|permit|jsa_hazard,
  identifiers, verb, equipment_class, doc+page+span, confidence}`, a
  lexical gazetteer of identifier-shaped tokens, and an index card (docs,
  pages, OCR confidence, term set) as the reviewable artifact. Review
  happens at the **planner desk before mobilization** (never a wellsite
  tablet), covers only low-confidence and high-consequence rows, and is a
  trust-and-label step, not the accuracy control. Coarse or open-ended
  rows are non-suppressing forever. Retrieval (hybrid BM25 + dense; one
  shared store filtered by job; standards and learnings in a shared
  namespace) runs only after an item ranks uncovered, to attach evidence
  to the dossier — never to decide coverage. **"Covered" exists in v1 only
  as a deterministic identifier-exact match** to a specific row or a
  closed amendment; everything else is a ranked per-job list; the single
  abstain ("insufficient identifiers to link") ranks mid-list and is never
  dropped. Historical learnings compile offline into hazard patterns
  (verb x equipment class) that raise severity and never suppress;
  standards are retrieved once per alert as citation. Package revisions
  land as versioned ledger amendments on the supervisor path, and open
  items against the old baseline re-evaluate.
- **Why.** Index-time extraction errors are unfalsifiable (a wrong row is
  a silent false negative for the job's life behind a clean audit trail);
  judge-time errors sit beside the raw span the judge reads — so buy
  semantic depth at judge time and keep the binary surface tiny. A ranked
  list makes both sides' feared failures recoverable; a wrong binary does
  not. Retrieval cannot prove a negative, and under the deterministic-only
  rule it may not say "covered" at all.
- **Rejected.** A deep semantic registry as the suppression engine; RAG
  deciding coverage; a second writable scope store beside the ledger;
  wellsite confirmation screens (rubber-stamp laundering); query expansion
  from the message's own identifiers as the primary retrieval path
  (paraphrase-dependent by construction).

## D004 (2026-08-31) Platform: Postgres truth, push-signal + 60s-ceiling reconciler, credential-split workers

- **Question.** Boring tech (poll + Postgres) or event-driven streaming?
- **Decision.** Both advocates converged and the judge's verified facts
  fixed the rest. Postgres is the single truth: jobs, versioned
  job_packages, **append-only `message_versions` keyed `(graph_id,
  etag)`**, channel_cursors, ingest_gaps, `analysis_tasks` as job-window
  rows, work_items + mention log, groundings citing `(graph_id, etag)`,
  risk_assessments, alerts with dispositions, model_calls with cost. One
  tenant-wide Graph change-notification subscription
  (`/teams/getAllMessages`; treated as a signal only — a fetcher pulls by
  id with its own token; validationToken + clientState verified;
  `lifecycleNotificationUrl` handling `reauthorizationRequired` and
  `subscriptionRemoved`) over a per-channel delta reconciler with a **hard
  60-second ceiling** — the poll is the *sole* loss detector because no
  `missed` lifecycle event exists for chatMessage; cadence adapts only
  downward (job phase, package hazard class), never volume-keyed backoff,
  because quiet is where emergent scope surfaces first. Workers claim
  job-window tasks via `SELECT ... FOR UPDATE SKIP LOCKED` (single writer
  per job window, visible queue depth as backpressure); processes are
  split by credential (ingestor: Graph only, insert-only; extract: model
  key, no alert write; risk: no Graph token; notifier: Teams write only)
  to contain injection blast radius. A new etag on a grounded span
  **reopens** the work item; deletes tombstone the body keeping hash and
  disposition. Attachments are out of scope in v1 but persisted as
  `attachment_present` so the blind spot is a visible row. Alerts are
  durable rows with delivery attempts; the ledger page is the notifier
  fallback; system-health paging rides a separate ops rotation from safety
  alerts. `fold_version` is stamped and replayed on upgrade; ordering is
  `(createdDateTime, graph_id)` with `received_at` kept apart; chat PII
  gets a TTL, row-level access, and a written rule that the ledger is not
  an HR evidence source; DR is numeric RPO/RTO with a drilled failover.
  Protected-API approval (weekly-reviewed Microsoft form) is a schedule
  risk; the named pilot fallback is a Teams bot installed per job team
  under resource-specific consent (receives channel messages without the
  tenant-wide protected grant) — to verify at build.
- **Why.** Measured arithmetic (~5 msg/s realistic worst case against a
  minutes budget) kills the broker, and the event-driven advocate honored
  its pre-committed kill rule; what remained were verified Microsoft
  facts: no `missed` event, unmetered Teams APIs since 2025-08-25,
  mandatory lifecycle URL, 4,320-minute max subscription, silent edit
  redelivery. The worst uncaught defect was insert-only ingestion
  silently dropping edits under grounded alerts.
- **Rejected.** A broker/streaming v1; volume-keyed poll backoff; a
  single-process analyzer with one credential set; insert-only message
  storage; any cost line based on the dead per-message metering.

## Synthesis (2026-08-31, main session with full context)

Cross-axis harmonizations ruled here: T1 runs per job window everywhere
(detection, grounding and platform each assumed it; now stated once);
`execution-intent` is a first-class T1 label because D002 escalates on it;
D003's "registry" IS D001's ledger — one store, one write path; the four
decisive experiments merge into one validation program (coverage-decile
suppression audit; disposition-before-execution vs p90 interrupts per
supervisor-shift; paraphrase-invariant recall with a zero-suppression hard
gate; the soak with a killed subscription and an edited grounded span), all
under held-out, supervisor-authored plants and mute-rate instrumentation
from shadow day one. Reuse lineage, stated for the design doc: guards-first
tiering and the human loop are the email-triage pipeline's skeleton; ledger
grounding, deterministic-only suppression and planted-trap evals are the
RFP drafter's discipline; the rollout ladder is standing doctrine. The
genuinely novel components — the work-item fold and the
disposition-before-execution loop — are where Part 2 should aim.

## Research amendments (2026-08-31, three web-grounded rounds, verified by the main session)

After Nikhil challenged whether the debate had used the web, ML best
practice and our accumulated project experience, three cited research
rounds ran (grounding/retrieval; streaming-detection ML incl. our
production repos; HSE domain prior art). Amendments below; sources in the
session record. Where rounds disagreed, the main session ruled.

**D001 amendments.**
- [adopt] T1 output schema: `certainty` is a three-bucket enum, never a
  0-100 number (structured outputs cannot validate numeric ranges;
  verbalized confidence is anti-informative at the tails);
  `evidence_span` precedes `label` in field order; one cache breakpoint
  after the shared system prompt with the per-job gazetteer outside it;
  Haiku's minimum cacheable prefix is 4,096 tokens and fails silently
  below — the prompt is padded past it and the cache hit rate asserted in
  evals. Verified pricing 2026-08-31: haiku-4-5 $1/$5 per MTok (cache
  read 0.1x), sonnet-5 $2/$10.
- [adopt] The T1 model call stays (spans are the product); a fine-tuned
  encoder classifier is a later cost optimisation trained from shadow
  labels — an addition, never a replacement.
- [adopt] From a production email-triage pipeline: "use the model to extract
  fields, use code to score them" — T2's diff score is deterministic
  weighted signals with per-signal `{points, max, why}`, and **gaps beat
  confidence**: a missing permit or control routes to escalation
  regardless of certainty. The eval gate imports its drift pinning
  (model + prompt hash + dataset hash) and a hallucination-rate tolerance
  that may never rise.

**D002 amendments.**
- [adopt] Clustering v1: blocking with deterministic keys — normalized
  equipment id (V-114 -> V114) as the hard key, gazetteer terms soft
  keys; hard key + bounded time window merges deterministically;
  everything else opens a new work-item and enters a per-job
  ambiguous-link queue resolved by one batched adjudication call (no
  per-link model calls). Membership is never mutated: an append-only
  mention-to-work-item assignment log; a split emits new ids recording
  the parent, and ack history stays attached to the mentions that
  justified it. Production precedent: a recorded merge bug in that
  pipeline (a lenient "does not contradict" rule let two distinct records
  overwrite each other) is this design's wrong-merge crux, already
  paid for once.
- [adopt] Clustering gates: pairwise-F1 precision (a wrong merge costs
  n*m pairs) with CEAF reported for interpretability; MUC excluded (it
  rewards over-merging); B3 usable only as B3-precision. Re-alerts on an
  already-raised work-item are event-level false positives with repeat
  rate as its own metric — the split side has a measured price
  (acceptance falls ~30% per additional repeat), so default-to-split is
  bounded, not free.
- [adopt] Interrupt budget in published units: hazard-tier pages <= 2
  per human per 12-hour shift; total advisories under EEMUA 191 /
  ISA-18.2 rates (<1 per 10 min sustained; >10 in 10 min is a flood with
  defined behaviour; recurring alarm rationalization as a named
  process); hazard-tier precision floor ~85-90% because response rates
  converge on precision (probability matching) — below the floor the
  pager trains itself out of the workforce, true positives included.
- [adopt] Anti-inhibit rule: suppression or muting of hazard paging is a
  logged, attributed, time-bounded action, never a silent config
  (Deepwater Horizon's general alarm ran inhibited for a year). Flags
  attach to work-items, never named individuals — no per-person counts,
  no performance reporting off flags (stop-work authority fails through
  fear of reprisal, not ignorance).
- [adopt] Mute/snooze/dismiss telemetry ships from shadow day one,
  labeled a hypothesis under test, not a validated gate.

**D003 amendments.**
- [adopt] Per-job store: dense-only + full-corpus cross-encode (at ~300
  rows the reranker covers everything; first-stage recall is moot);
  hybrid BM25+dense survives only as an option for the shared
  standards/learnings namespace. The production-proven stack transfers:
  voyage-class embeddings, pool -> cross-encode -> trim with graceful
  degradation, clause-level unit = one vector per ledger row, idempotent
  uuid5(job:row) point ids.
- [adopt] Isolation: per-job (or per-operator) collection PLUS metadata
  filter — defense in depth; a filter-only shared store makes one query
  bug a cross-job ledger leak that silently suppresses a real alert.
- [adopt] Parsing: digital PDFs via a layout parser, scans via a modern
  OCR model routed by a text-sufficiency check; two production traps
  fixed at import: an OCR-disabled deployment workaround (silently yields
  empty text on scans; assert non-empty per page) and the
  table-stripping logic (right for contracts, inverted for JSAs, whose
  hazard/control tables are the payload; document-type switch).
- [adopt] Certainty from independent signals only: deterministic
  match/no-match, a small cross-encoder NLI score over the ranked list
  (never suppression), structural extraction checks. The abstain
  threshold is calibrated; main-session ruling on a cross-round
  conflict: conformal calibration applies only to the high-volume
  non-hazard ranking threshold (it collapses on rare classes); hazard
  classes stay deterministic never-suppress and need no calibration.
- [adopt] No chunking inside a job: 10-50 pages is 5-25k tokens; whole
  sections are stuffed; chunking effort is reserved for the shared
  standards namespace. Contextual retrieval and late chunking rejected
  at this corpus size.
- [adopt] Ledger row names align to IOGP 577's own field list (permit
  number and duration, JSA task -> hazards -> controls, roles,
  isolations, SIMOPS, close-out) and key on CMMS identifiers (work
  order id, functional location/asset id); there is no public JSA/PTW
  schema, so the eCoW/CMMS API path is designed first with PDF parsing
  as the long tail (large operators run permit systems of record).
- [validated, no change] Deterministic-only suppression and
  retrieve-only-after-uncovered are current best practice, not
  conservatism: embedding retrieval is provably dimensionality-capped,
  absence queries are a documented RAG failure mode, and
  retrieval-state lock-in produces confident wrongness.

**Design-doc framing (domain round).**
- [adopt] Vocabulary: emergent scope vs discovery scope, both governed
  by change control; the MOC trigger is "not a replacement-in-kind";
  temporary change is a distinct disposition outcome; the field-level
  action is permit suspension -> JSA/permit review -> re-authorization;
  roles named properly (person in charge, permit issuer, performing
  authority, area authority). Problem statement quantified: ~23% average
  scope growth on large turnarounds, ~8% top quartile.
- [adopt] Thesis: IOGP 577 already requires stopping when scope or
  conditions change and re-authorizing the permit before resuming, and
  forbids field changes to permits without re-submittal — the system is
  a detection layer for a rule that already exists. The assisted tier is
  framed as a Start Work Check aid; the system never holds stop-work
  authority.
- [adopt] Compliance hooks: SEMS 30 CFR 250 Subpart S (JSA 250.1911,
  MOC 250.1912, SWA 250.1930) and company MOC standards — NOT OSHA PSM
  1910.119, which exempts well drilling and servicing; CCPS as
  methodology. System metrics report in the API RP 754 Tier 4 slot.
  Outputs are routing decisions, never risk predictions (near-zero
  incident base rates make prediction claims indefensible).
- [adopt] Shift-handover grounding: HSE's handover guidance and the
  Cullen Report's Piper Alpha finding; the design formalizes an existing
  permit-revalidation checkpoint, it does not invent a ritual.

**Validation program additions.** F-latency with its penalty constant
re-derived for wall-clock minutes and F plus latency reported on separate
axes; DET-style threshold-independent curves; a retrospective replay
number is never presented as an online claim; shadow-tier exit gates
expressed in alarm-management units (sustained rate under budget, zero
floods, measured precision on dispositioned items).

## Lock-in verification (2026-08-31, pre-PLAN_FINAL)

Three independent read-only agents ran before lock-in: an endgoal audit
(the verbatim brief against this record, line by line), a blind red team
(required to commit its own architecture from the brief alone, unrevised,
before reading ours), and a simulated walkthrough evaluator. Their reports
were verified here with full context; conflicts between them are ruled
below. This section binds T002 (design doc) and T003 (slice).

### Verdicts

- **Best approach: yes.** The blind design independently converged on the
  same shape (deterministic gate, windowed extraction, diff against the
  package, tiered alerts, poll + Postgres + reconciler) and on comparison
  conceded three of its four deliberate differences: gate-as-filter loses
  to add-never-suppress guards (a lexicon filter on informal chat is a
  silent false-negative machine); a deep structured scope object as the
  comparison target loses to shallow rows with ranked, non-binary coverage
  (one extraction error becomes a permanent, unfalsifiable miss behind a
  clean audit trail); corroboration counting loses to none (quiet night
  crews corroborate least and carry most). It kept one win, the explicit
  build/skip boundary, adopted below (A2). The only family it judged
  competitive is the no-ML workflow tool (a "declare emergent scope"
  affordance plus the disposition ledger and the handover artifact); that
  tool is contained in this design and the doc will say so: it is what the
  system degrades into with an empty ledger, which turns the overbuild
  attack into a designed property.
- **Serves the endgoal: architecture yes; deliverable not yet.** The
  audit found every brief clause served by the record except the ones the
  brief grades hardest: a short doc, a diagram, a findable build/skip
  list, and a slice that catches the plant. None exists yet, and the
  record's default compression path is transcription. The amendments
  below close the gap.

### Rulings on cross-agent conflicts (main session, full context)

1. **Part 2 aim.** The earlier synthesis pointed the slice at the
   work-item fold and disposition loop; the audit calls that state
   plumbing that never detects; the red team wanted the fold proven. The
   brief's own words win ("planted Job B scenario ... the slice must
   catch it"): the slice is the thin end-to-end detection path (package
   seed, T0 guards, one T1 window call, T2 diff, work-item row,
   escalation record), with the minimal fold (open, notified,
   acknowledged, dispositioned) as the work-item's written state. The
   headline is the catch; the fold rides along. Supersedes the synthesis
   note's Part 2 aim.
2. **Never-suppress vs the interrupt budget** (the evaluator's sharpest
   attack, seconded by the red team). Not a contradiction, but the record
   never did the arithmetic: suppression governs row creation, budgets
   govern interrupts, and the doc must show the numbers. Amendment B1.
3. **Cache padding.** Padding every T1 call up to the 4,096-token Haiku
   cacheable minimum costs more than it saves (red team estimate at our
   verified prices: order $100+/day). Ruling: never pad. Structure the T1
   prompt so the shared prefix (instructions, schema, job lexicon) is
   naturally long for jobs where it can be; where it stays short, run
   uncached; revisit with token counts measured in the slice.
4. **CMMS-first.** The D003 amendment bullet that designed the eCoW/CMMS
   API path first, with PDF parsing as the long tail, quietly added an
   assumption the brief never granted; the brief gives documents. Ruling
   (supersedes that bullet): parsing the job package documents is
   primary; CMMS/eCoW identifier alignment is an integration note, not a
   dependency.

### Amendments A: doc shape (binds T002; "short" is itself graded)

- **A1** Page budget 6-8 pages plus appendices. Page 1 is the whole
  design: one-line thesis ("emergent scope is a diff against approved
  scope, not a property of a message"), two-line problem with the ~23%
  turnaround figure, the diagram, three decisions at one line each,
  build/skip bullets, three failure modes, a validate-first line, a
  week-one line.
- **A2** Mandatory sections named in the brief's own words: Assumptions;
  What we'd build, what we'd skip, and why; Tradeoffs (each stating what
  the chosen side costs, not only what was rejected); Failure modes; What
  we'd validate before committing. Plus a four-line "given, where used"
  table for G01-G04 (the audit found G02's use hardest to locate).
- **A3** The body keeps the IOGP 577 thesis ("a detection layer for a
  rule that already exists") and demotes the rest of the compliance
  stack, Graph lifecycle minutiae, clustering metric comparisons, parsing
  trap detail, and price minutiae to one-line appendix items. Credential
  split, fold replay detail, DR, PII TTL: a single "productionization"
  appendix list, out of the body.
- **A4** The doc opens with the dumb version and its measured failure: a
  per-message classifier that pages a human. It fails because "emergent"
  is undecidable without the reference, because its alert arithmetic
  collapses at 10^2-10^3 jobs, and because model output would end up
  driving suppression (injection). The slice reports the lexicon-only
  baseline number so T1's existence is earned by a recall delta, not
  asserted.
- **A5** The doc names the no-ML workflow tool as the degrade-into state
  (verdicts above) and states stop-work-stays-human once in the thesis
  and once in the rollout ladder, not three times.
- **A6** Scrub rule for every shareable artifact: no employer or client
  names, no personal paths; prior-project evidence phrased generically
  ("a production document-intelligence platform", "a production email
  triage pipeline"). This file is an internal working record; it ships
  only after the same scrub, or not at all.

### Amendments B: design deltas

- **B1 (D001+D002)** Two-lane alert arithmetic, explicit in the doc.
  Hazard lane: page at first mention, recall-biased, 85-90% precision
  floor, budget of at most 2 pages per human per 12h shift, duty-HSE
  roster sharded by asset/region so the budget holds at 10^3 jobs; pages
  are per work-item hazard-class first mention, deduplicated by cluster,
  never per message. Non-hazard lane: never interrupts at first mention;
  row plus digest plus handover pack; interrupts only on execution-intent
  or unresolved-at-handover. "Early" for this lane means before
  execution: the disposition gate is the intervention point. Suppression
  (identifier-exact only) governs whether a row exists; budgets govern
  which rows interrupt; EEMUA/ISA rates apply to the interrupt surface
  only. The doc carries a worked example with stated assumptions
  (messages per job-day, windows, rows, interrupts).
- **B2 (D001)** Window pinned: T1 fires at N=10 messages or T=120
  seconds, whichever first; a T0 hazard-marker hit bypasses the window
  with an immediate single-message T1 call. SLOs stated and measured in
  the slice as distributions: hazard time-to-page at most 5 minutes from
  message arrival; non-hazard time-to-row at most 15 minutes. The pins
  are defended defaults, not tuned truths; the slice reports measured
  values.
- **B3 (D002)** The batched LLM adjudicator sits under the same
  pairwise-F1 precision gate as deterministic links, because hard-key
  coverage in informal chat may be low; the slice measures and reports
  the hard-key fraction. If it is low, the adjudicator is the primary
  clusterer and is gated as such.
- **B4 (D003+D004)** One sizing-and-cost paragraph in the doc,
  assumptions labeled as estimates: at 10^3 jobs and an assumed 100-300
  messages per job-day, order 10^5 messages/day and order 10^4 T1 window
  calls/day lands in low tens of dollars/day on the small model; T3
  dossiers only on escalations, order 10^2/day on the large model, a few
  dollars/day. Graph delta reconciliation at the 60s ceiling is ~17
  requests/second sustained across 10^3 channels: verify against
  published Teams service limits at build; if throttled, stagger polls
  inside the ceiling and use $batch. Unmetered is not unthrottled.
- **B5 (D001/D004)** Attachments: v1 keeps the deterministic
  attachment_present signal (raises certainty, never suppresses); the
  another-week half page names the first extension: one vision call on
  attachments inside hazard-gated windows, because "degraded valve" is
  often a photo plus four words.

### Amendments C: slice and dataset (binds T003)

- **C1** Slice per ruling 1. Transport is a replayed JSONL fixture, no
  Teams integration; no clustering adjudicator and no T3 inside the
  slice.
- **C2** Dataset: 30-80 messages, at least half operational chatter and
  noise, including planned-work confusables as negative controls (planned
  work phrased the way emergent work sounds). Primary Job B plant per
  I01: a second piece of work revealed gradually across 6-10 messages
  inside Job A's channel. Plus 3-5 messages of the alternative reading
  (an adjacent job's work bleeding into this channel); the README states
  both readings and what the slice does with each. ENDGOAL I01 revised
  accordingly.
- **C3** Circularity defense: plant and paraphrase fixtures are generated
  from seed material disjoint from the lexicon's sources; the paraphrase
  set is frozen before any detector tuning; results report at least one
  honest miss. Supervisor-authored held-out plants remain the production
  answer and stay under validate-before-committing.
- **C4** Measured outcomes (S05): catch latency for the plant (messages
  from first signal, and wall clock), lexicon-only vs T0+T1 recall delta,
  precision on the noise half, a zero-suppression check (nothing the
  model wrote suppressed anything), and the hard-key coverage fraction
  (B3).
- **C5** Scale honesty: the merged validation program (coverage deciles,
  conformal calibration, DET curves, F-latency) is explicitly sized
  beyond an 80-message set; in the doc it lives under "what we'd validate
  before committing", and the slice claims only what 80 messages can
  support. The mismatch, stated, is the answer.

### Post-artifact adversarial fixes (2026-08-31, CODE_ADVERSARIAL)

An adversarial reviewer (evaluator + fact-checker + linter personas)
attacked the written doc; all findings verified in the main session and
fixed in design/design.md. The ones that refine the record itself:

- **B6 (refines D001's T2):** the identifier used for the T2 coverage
  match is recovered deterministically from the raw message span (regex
  over the gazetteer), never taken from a model output field. Closes the
  mis-extraction path to suppression (model writes V-114, crew wrote
  V-115) that "extracted text never drives suppression" alone left open.
- **Arithmetic corrections:** T1 windows are timer-flushed at field chat
  rates (mean gap 5-14 min exceeds the 120 s timer), so calls land near
  messages/2-3, not messages/10: 0.3-1.5 x 10^5 calls/day, $50-250/day,
  one band stated everywhere; hazard pages 1-3 per DAY = 0.5-1.5 per 12h
  shift (unit slip fixed; the <=2 budget now holds on paper, no flood-rule
  hand-wave needed); T3 dossier priced by token count (~$1.50/day).
- **Cache-padding ruling strengthened:** at 5-14 min gaps most cache
  entries outlive the 5-minute TTL, so padded calls would mostly be cache
  writes at a premium; padding stays dead.
- Doc-only fixes: 23% figure attributed to plant turnarounds explicitly;
  G02's compiled hazard patterns now do visible work in 3.4 (with the
  base-rate/specificity honesty sentence); ~600 words of duplication cut
  (tradeoffs/failure-mode restatements, appendix A compressions); heading
  "The design in brief"; consistency and cadence nits.
