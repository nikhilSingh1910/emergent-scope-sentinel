# Another week, and what we chose not to do

Nikhil Singh, 2026-09-02. Every number here comes from the committed
`eval/report_recorded.json`.

**With another week.** The first thing I would do is get held-out plants
written by someone who is not me: a field supervisor writes new emergent
scenarios and paraphrases, frozen before any tuning. The slice cannot
validate itself against its own author, and this is the validation I want
most. Next, the clustering adjudicator. The recorded run did catch the
tagless mentions jb4 and jb7, but as separate soft items, because I only
let span-derived identifiers merge work items; one batched adjudication
call gated on pairwise-F1 precision is now a measured need and not a
guess. Then attachment reading: the run's only miss (recall 0.889) is
jb3, a photo message whose text carries no tag, so one vision call inside
hazard-gated windows is the obvious fix. After that, shadow mode on real
traffic, to replace the estimated base rates in the alert arithmetic with
measured ones before anyone gets paged. And finally package-PDF parsing,
so the ledger seeds from the actual documents rather than the canonical
JSON the slice uses.

**What we chose not to do.** Streaming infrastructure and brokers: a
60-second human loop does not need them, and the kill rule we
pre-committed to fired. The T3 standards dossier and its retrieval.
Semantic "covered" matching, where one embedding mistake can silently
kill a real alert. Live Teams integration, fine-tuning, dashboards. And
no retuning after seeing results: the report ships with planned_covered
false, because the model read one planned permit sign-on as chatter, and
with the lexicon baseline at 0.778 against the system's 0.889. That
+0.111 delta is what the model call earns, measured against a dataset and
gold that were frozen before the recording and never touched after it.
