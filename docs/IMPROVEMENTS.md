# Review, impact and evaluation workbench (v2.1)

[Verified evaluation preview](images/evaluation-preview.png)

## Edit requirements before approval
Use **Edit requirements** on a revision awaiting review. Functional requirements,
actors, acceptance criteria, existing quality requirements and scope notes are
editable. IDs remain stable in the editor; additional requirements receive new
IDs. A save is a transaction with an expected content hash. Concurrent stale
edits are rejected instead of overwriting another reviewer's work.

The initial artifact and every saved before/after pair are retained. Open
**Activity → Requirement edit audit trail** to inspect the changes. Approval
records the approved hash and passes the saved requirements into the graph,
including after a restart. Completed and rejected revisions cannot be edited.

## Analyze requirement changes
Open **Impact → Propose a requirement change** against a completed revision.
Analyze the proposal before creating a new revision. The report distinguishes
added, removed and modified requirements and shows:

- Direct links to components, entities, endpoints and tasks.
- Endpoints using affected entities.
- Transitive downstream task dependencies, with explanations.
- Conservative flags for all records when scope, actors or NFRs change.
- New requirements without baseline links and documentation/validation refreshes.

The baseline stays unchanged. Creating the revision seeds its requirements and
pauses for review. All downstream design stages run again: this is conservative
regeneration, not selective code regeneration. Impact follows declared artifact
links, not a source-code dependency graph. Demo mode still uses fixed downstream
fixtures, so it does not establish design quality for the edited scope.

## Review business behavior and retrieved rules
The live critic must assess every functional requirement using actual endpoint
IDs. A satisfied claim without an existing linked endpoint is rejected as invalid
evidence. Missing, partial and uncertain behavior becomes a finding. The critic
also reviews every retrieved passage for conformance, conflict, non-applicability
or uncertainty, citing existing requirement/endpoint IDs.

Schema/reference checks reject invented evidence and incomplete review coverage.
They do not establish that a model's interpretation is correct. The Validation
view separates linked coverage from automated semantic coverage. Demo mode has no
LLM assessments and shows **Not assessed** rather than a fabricated semantic score.

## Compare generation strategies
Open **Evaluation** to start a single-prompt baseline or staged agent run, with
or without retrieval. A baseline generates the same six artifact contracts in
one model response, then uses the same critic and deterministic validator.
It deliberately skips human review; staged runs pause. Live runs consume provider
quota. A new experiment cannot start while a project has an active revision.

Measurements include strategy, model, prompt version, scope/source hashes,
generation time, wall time, input/output/reasoning tokens, attempts, linked and
semantic coverage and human rubric ratings. Demo/live filters keep fixture
results visibly separate. Human-edited or seeded scopes are flagged as confounders.
Both methods should use matching briefs, constraints and source corpora when
evaluating generation strategy. Human ratings are append-only observations, not
independent proof or automatically generated truth.

Generation timing excludes embeddings; wall time includes queueing and review.
Only completed-stage usage is accumulated, so failed-stage usage may be missing.
No monetary cost estimate is invented. Export measurements as JSON for analysis.

## Evaluate retrieval
Add documents under Knowledge. Under Evaluation, define one or more queries and
select expected documents **before** searching. Results persist the query set,
expected IDs, corpus hash, retrieved passages and embedding namespace.

Document-level ranking deduplicates passages from the same document. Precision@k
is unique relevant documents retrieved divided by k, even when fewer results are
returned. Recall@k divides by expected document count; reciprocal rank is 1/rank
of the first relevant document, or zero. MRR is the query mean. Labels cannot
refer to another project's documents. Source conformance measures whether the
design follows retrieved rules; retrieval relevance measures which rules were
retrieved. These are separate questions.

## Reproduce checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/evaluate_validator.py
.\.venv\Scripts\python.exe scripts/evaluate_retrieval.py
```

The offline retrieval report uses five synthetic policies and lexical queries:
P@3=0.3333, Recall@3=1.0, MRR=1.0. It is a small lexical baseline, not evidence of
general semantic search quality. The validator report detects 8/8 injected
structural faults and documents a semantic blind spot without a reviewer.

For an opt-in live integration check, configure the root `.env` with your Gemini
key and a model enabled for your account, then run:

```powershell
.\.venv\Scripts\python.exe scripts/verify_live.py --include-baseline
```

This sends synthetic library requirements and a synthetic policy to Gemini,
tests embeddings, retrieval, the review gate, staged and baseline generation,
validation, metrics and exports in an isolated temporary store. It writes
`docs/evaluation/live-verification.json` without credentials. It refuses to call
the provider if the key is missing. A completed workflow with findings remains
a design requiring review; no human rating is invented. Timeout does not cancel
an already in-flight provider request.

Five held-out domain briefs and policies are in `docs/evaluation/scenarios.json`.
Use them for repeated live trials and human review. Do not substitute fixture
results for a final report's live model evaluation.
