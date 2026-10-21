# AI Software Planning & Engineering Assistant — rebuild

## Goal and assessment contribution
Transform an idea into an inspectable engineering blueprint through specialized,
context-sharing agents. The research question is whether explicit requirement
traceability and independent deterministic checks expose omissions that fluent
single-prompt generation conceals. A passing report means implemented checks
passed, not that an arbitrary software design is proven correct.

## Architecture decisions
- React / TypeScript workspace; FastAPI application boundary; Pydantic contracts.
- LangGraph state graph: requirements → human review → architecture → database →
  APIs → implementation → documentation → validation. Durable SQLite checkpoints.
- SQLite is the source of truth for projects, immutable run revisions, artifacts,
  events, and knowledge text. Qdrant stores derived vectors with project filters.
  A vector database complements transactional storage; it does not replace it.
- Gemini is the live generation and embedding provider. Explicit demo mode uses
  a food-delivery fixture and hashed lexical vectors, never masquerading as AI.
- Single-user localhost deployment. Optional bearer authentication; multi-user
  tenancy, OAuth and distributed workers are separate future work.
- One background worker serializes runs for predictable local checkpoint/storage
  ownership. Restarted work requires an explicit resume; no silent billed replay.

## Milestones and acceptance
1. Contracts, durable store, setup and project creation.
2. Structured provider, schema repair/retry and prompt versioning.
3. Durable supervised execution, review gate, events, failure recovery.
4. Requirement/entity/API/task traceability and deterministic consistency rules.
5. Project-scoped retrieval, source citations and immutable revision comparison.
6. Dashboard, artifact inspection, workflow graph and blueprint exports.
7. API integration tests, adversarial validation fixtures, build, browser QA,
   CI, Docker and final-year documentation.

## Evaluation methodology
Use several domains (food delivery, library, clinic, inventory, education), a
fixed prompt version and recorded model name. Record requirement coverage,
schema validity, validator findings, reviewer corrections, time and tokens.
Compare single prompt vs staged workflow with/without retrieved knowledge.
Inject missing endpoints, dangling references and dependency cycles to measure
validator detection. Report measured results separately from proposed studies.
The checked-in offline suite measures implemented invariants; live quality
evaluation requires a configured key and human-rated domain cases.

## Scope limits
No generated code execution, autonomous repository changes, deployment of user
ideas or claims that demo fixtures are novel designs. Knowledge is untrusted
context, not instructions. Keys stay on the backend. Exports are inert text/JSON.

## Implemented advanced extension (v2.1)
Audited requirement editing with optimistic concurrency; conservative change
propagation; requirement-seeded revisions; endpoint-backed semantic and retrieved
rule assessments; single-prompt/staged experiments with optional retrieval;
timing/token metrics, human rating collection and labeled retrieval evaluation.
See IMPROVEMENTS.md. Live quality claims remain contingent on actual model trials.
