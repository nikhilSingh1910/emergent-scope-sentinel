# ENDGOAL.md: Emergent Scope Sentinel (Ententia design exercise)

## What we are building and for whom

Ententia's take-home. A large energy operator runs field jobs (workovers,
maintenance, remediation). Each job's **planned scope** is safety-reviewed up
front: approved scope, permits, JSA hazards, controls, all in a job package
available at or before mobilization. In the field, crews surface **emergent
scope** (a degraded valve to swap, a stuck tool to recover) in the job's
free-text Microsoft Teams channel, mixed with operational chatter; that work
has not been through planning, permitting or hazard review, so new hazards
enter the job without formal visibility.

Goal: design an AI system that detects this emerging risk from the chat
signals early enough for humans to intervene. **Stop-work authority stays
with people.** Part 1 (the design) is primary; Part 2 (a focused implemented
slice) is optional and encouraged: "evidence that your design choices survive
contact with code."

Source of the brief: the assignment email, mirrored verbatim at
`docs/assignment.txt`. **On any doubt,
the verbatim brief wins over this file's paraphrase.** No hard deadline; a
code walkthrough is planned early next week, sooner if finished sooner.

## Givens (the brief's own assumptions; the design must honor them)

- **G01** A job package per job (work plan, permits, JSA, controls) exists at
  or before mobilization.
- **G02** Enterprise safety standards and historical learnings exist, shared
  across jobs.
- **G03** One chat channel per job (Microsoft Teams), free text, near real
  time, noisy.
- **G04** Scale: roughly 10^2 to 10^3 concurrent jobs.

## Requirements

Part 1, the design document (each id must be visibly satisfied in the doc):

- **R01** A short design document with an architecture diagram for a system
  that meets the goal.
- **R02** Decides what matters and defends the choices.
- **R03** States what we would build, what we would skip, and why.
- **R04** States its assumptions explicitly (beyond the brief's givens).
- **R05** States the tradeoffs considered.
- **R06** Names the failure modes we are worried about.
- **R07** States what we would validate before committing to the design.
- **R08** Honors G01-G04 (uses the job package, the standards and learnings,
  the per-job channel; works at 10^2-10^3 concurrent jobs).
- **R09** Keeps stop-work authority with people: the system surfaces and
  escalates; humans decide. No autonomous stop-work action anywhere.

Part 2, the focused slice (optional, encouraged):

- **S01** One focused slice of the design, chosen for being the most
  interesting to make concrete, implemented and runnable.
- **S02** Self-generated sample data: a synthetic job package and ~30-80
  chat messages.
- **S03** The chat contains a planted "Job B" scenario: emergent, unreviewed
  work surfacing informally inside the job's channel, which the slice must
  catch (interpretation recorded below; confirm in the README).
- **S04** Repo or zip with a README.
- **S05** The slice demonstrates the design's core claim with a measurable
  outcome (not a complete system).

## Deliverables

- **D01** Design doc as a PDF.
- **D02** Architecture diagram, any format.
- **D03** Code repo or zip with README (if Part 2 is done).
- **D04** Half a page: what we would do with another week, and what we chose
  not to do.

## Interpretations to state in the design (not facts until confirmed)

- **I01** "Planted Job B scenario" read as: within Job A's channel, messages
  gradually reveal a second, unplanned piece of work (in effect a job of its
  own) proceeding without review; the slice must surface it before the crew
  executes it. Alternative reading (an adjacent job's work bleeding into Job
  A's channel) is planted too, in 3-5 messages, and the README states both
  readings and what the slice does with each; the primary reading is
  unchanged (amended 2026-08-31 at lock-in verification).
- **I02** "Early enough for humans to intervene" read as minutes, not
  seconds: the intervention loop is human (supervisor, HSE), so latency
  budget is set by human response time, not by streaming micro-latency.
- **I03** Teams is assumed reachable via Graph API change notifications or
  export; the design treats the transport as a replaceable adapter.

## Out of scope

- Autonomous stop-work or any actuation; permit-system write access;
  fine-tuning custom models; multi-channel correlation beyond the stated
  one-channel-per-job model (noted as an extension).

## Revisions (append-only, dated)

- 2026-08-31: I01 amended at lock-in verification: the alternative Job B
  reading (adjacent-job bleed) is planted alongside the primary, since
  adjacent-job work surfacing mid-mobilization is exactly how emergent
  scope appears in the field; the README states both. Part 2 re-aimed at
  the thin end-to-end detection path, and the doc's page budget, mandatory
  section names, and arithmetic amendments recorded in docs/DECISIONS.md,
  "Lock-in verification (2026-08-31)".
