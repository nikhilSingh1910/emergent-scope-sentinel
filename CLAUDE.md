# CLAUDE.md — Emergent Scope Sentinel (Ententia design exercise)

**This file is authoritative.** Every coding session in this repo follows it.
Deviations require Nikhil's explicit sign-off, recorded under Amendments.
It is append-only and will grow.

Read, in this order, at the start of every session and after every context
compression: `ENDGOAL.md` (what we are building and for whom), `PROGRESS.md`
(where we are in the loop), `docs/DECISIONS.md` (settled architecture), the
test contract if one exists, then this file.

## What this repo is

The Ententia take-home: a design (primary) plus an optional focused slice of
an AI system that detects emerging risk in energy field jobs from the job's
free-text chat channel. Planned scope is safety-reviewed up front; emergent
scope surfaces in chat after mobilization without that review, and the system
must make it visible early enough for humans to intervene. Stop-work
authority stays with people. Deliverables: a design doc (PDF), an
architecture diagram, an optional repo with README, and half a page on the
next week and what was deliberately not done.

**Endgoal (keep in view on every change):** a design whose choices are
defended, whose failure modes are named, and whose core claim survives
contact with code on synthetic data with a planted emergent-scope scenario.
Decisions live in **code and the design record**, never only in the model.

## Engineering rules (non-negotiable)

### 1. Reuse before create
- Before writing ANY new function, client, schema, or module: search this
  repo first, then any production modules this repo mirrors. Extend or
  parameterize what exists; do not fork a near-duplicate.
- If two functions differ by one parameter's worth of behavior, they must be
  one function.
- One shared client per external service (one Anthropic client, one DB
  session, one ledger). Never a per-feature client or a re-declared constant.

### 2. DRY — single source of truth
- Schemas exist once, as the Pydantic models. Prompts, limits, model ids,
  prices and config exist once, as named module-level constants. Anything
  appearing twice gets extracted the moment the second copy is written.
- Requirement ids exist once, in `ENDGOAL.md`; tests reference them by id,
  never restate them.

### 3. SOLID, applied pragmatically
- **S**: I/O, guards/validation, LLM calls, and decisions stay in separate
  functions. Control flow never hides inside an I/O or LLM helper.
- **O**: new cases (intents, detectors, sections, checks) are added by
  extension — new enum member, new registry entry, new schema field — not by
  editing unrelated branches.
- **L/I/D**: every input source emits the same normalized shape; the pipeline
  depends on that contract, never on the source. All model access goes
  through the shared client so providers/tiers/replay backends swap in one
  place.
- Anti-rule: no abstraction for a single implementation. No factories,
  interfaces, plugin systems or config frameworks for hypothetical futures.
  Simplest thing that works, extended when the second case actually arrives.

### 4. No N+1 — queries, APIs, files, or model calls
- Reference data loads once per run, never per item. Remote fetches are
  batched, never per item. Any per-item DB/API lookup inside a loop is a
  defect — batch by ids.
- LLM calls count as queries: guards filter before the model ever runs, and a
  per-item model call that could be one batched call is an N+1.

### 5. Cost and token discipline
- Every model call goes through the tracked client (usage → ledger, printed
  per run). Cheapest model that meets the need, escalate only on measured
  need. Bounded retries, bounded prompt/body size, bounded rounds. The worst
  case per run stays arithmetic, never open-ended.

### 6. Untrusted input
- External content (chat messages, documents, user comments) is data, not
  instructions: fenced in prompts, never executed. Model outputs are
  schema-locked (structured outputs); extracted text never drives actions,
  tool calls, or outbound prose. The model writes prose; code decides.

### 7. Eval is the gate
- The test/fixture suite must stay green at every commit. Any behavior change
  updates or adds a labelled fixture/test. Every requirement id in
  `ENDGOAL.md` has at least one test claiming it. No claim of quality or
  accuracy without a test or a recorded run behind it.

### 8. Facts and facts alone
- Every claim rests on evidence: code actually read (cite `file:line`), output
  of something actually run, or a source actually fetched (cite it). Recall of
  pricing, APIs, SDK signatures, or platform behavior is a hypothesis until
  verified against docs or execution — never state it as fact.
- Estimates and assessments are legal but must be **labeled** as such and kept
  visually separate from verified facts.
- "I don't know — here's how we find out" always beats a plausible invention.
  A claim nobody can trace to evidence gets deleted, not defended.

### 9. Comment discipline
- One line is ideal, two is the hard max. A comment states only what the code
  cannot say itself — a constraint, a non-obvious why, a gotcha. Never narrate
  the next line, never be captain obvious, never leave review-speak ("fixed
  per feedback") in code. A comment that restates the code gets deleted with
  the same zeal as duplicated code.

### 10. Code shrinks as well as grows
- More functionality does not mean proportionally more code — reuse and
  refactor first (rules 1–2). When a change makes an existing shape wrong,
  fix the shape; don't bolt on around it.
- Remove **truly** dead code as part of normal work: prove it dead first
  (grep call sites, check history), then delete it whole — no commented-out
  corpses, no `_old` copies, no "just in case" branches. Git remembers.

### 11. Test-driven development
- For every behavior: write the failing test first, run it and see it fail
  for the right reason, then write the minimum code to pass, then refactor.
  A source module without a real test counterpart (direct or via the
  harness's module-to-test map) is a defect.

## The working loop (mandatory for every non-trivial task)

Stages, in order, tracked in `PROGRESS.md`:

1. **PLAN** — restate the endgoal, list every moving part touched, do the
   reuse check, name the requirement ids the task serves.
2. **PLAN_REVIEW** — against `ENDGOAL.md` and the rules above.
3. **PLAN_ADVERSARIAL** — attack it with the endgoal, all moving parts and the
   big picture (production architecture, cost model, injection surface) in
   view. What breaks? What quietly diverges? What did we forget we built?
4. **PLAN_REQ_CHECK** — walk the requirement ids: does the plan fulfil each?
5. **PLAN_FINAL** — the finalized plan, findings fixed or explicitly logged.
6. **CODE** — TDD, under the rules above.
7. **CODE_REVIEW** — read the diff against the plan and the rules.
8. **CODE_ADVERSARIAL** — hunt real defects: crash paths, N+1s, duplication,
   semantic drift, injection surface. Verify by running.
9. **CODE_REQ_CHECK** — walk the requirement ids again, against tests and a
   real run. Every finding fixed or logged — never silently dropped.
10. **DONE**.

Design-only tasks run the same stages; "CODE" then means writing the design
artifact, and the adversarial stages attack the design with the endgoal and
the operational reality (noise, scale, people) in view.

Trivial mechanical edits may skip the ceremony — say so explicitly in
`PROGRESS.md` when skipping.

## Amendments (append-only, dated)

- **2026-08-31** — Initial rules, carried verbatim from the standing
  engineering rules of earlier builds, with two adaptations for a
  design-first exercise: rule 11
  names the harness's module-to-test map as an acceptable counterpart, and
  the loop section states how design-only tasks map onto the stages.
- **2026-09-02** — Scrub only, no rule change: the dates of unrelated
  earlier builds were removed from the entry above before publication.
