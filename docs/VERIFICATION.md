# Verification record

Date: 21 October 2026. Local Windows environment: Python 3.14.2, Node 24.13.0.
CI additionally targets Ubuntu, Python 3.12 and Node 22. Both jobs passed for
implementation commit `43dcf7e` in
[GitHub Actions run 39560741330](https://github.com/Harshit-ambati/AI-Software-Planning-Engineering-Assistant/actions/runs/39560741330).

## Tested boundaries

| Boundary | Evidence |
|---|---|
| API contracts and execution | 25 passing pytest tests with isolated SQL/vector databases |
| Durable human review | Close/recreate application, approve saved revision, finish all stages |
| Failed-stage resume | Inject database-agent failure, resume, assert requirements ran once |
| Startup recovery | Running state becomes interrupted; explicit resume completes |
| Revision integrity | Rejected revision stays unchanged; second revision has a new version |
| Project isolation | Knowledge from one project cannot be retrieved in another |
| Schema enforcement | Invalid Gemini-shaped responses retry and fail without fixture fallback |
| Error handling | Permanent provider error stops; transient error retries; upstream body is hidden |
| Traceability checks | Missing endpoint, broken entity reference, duplicate route, dependency cycle detected |
| Exports | Markdown contains project data; OpenAPI includes path parameters and response schemas; invalid routes are refused |
| Browser workflow | Create demo project → inspect requirements → approve → all seven artifacts → traceability |
| Browser retrieval | Save synthetic policy → Qdrant index → search → passage with source ID and similarity |
| Browser console | No error-level entries during the verified flow |
| Frontend | TypeScript and Vite production build; ESLint; formatted source |
| Backend static checks | Ruff checks pass |
| Compose definition | `docker compose config --quiet` passes |
| Editable requirements | Saved edits reach downstream generation; stale/concurrent edits and post-completion writes are rejected |
| Review audit | Original requirements and every saved before/after pair persist with hashes |
| Change impact | Direct requirement links, affected-entity endpoints and transitive task dependencies are reported |
| Baseline experiments | One bundle generation plus independent critic; demo measurements explicitly labeled |
| Semantic review evidence | Invented endpoint/citation references are rejected; missing behavior and source conflicts become findings |
| Human ratings | Completed runs accept bounded 1–5 ratings; metrics report saved observations |
| Retrieval evaluation | Project-local relevance labels, deduplicated documents, P@k/Recall/MRR and persisted reports |
| Existing-data migration | Older run tables are extended without losing projects or revisions |
| SQLite cleanup | Connections close at transaction completion, including on Windows |
| Browser improvements | Impact preview → seeded revision → edit acceptance criteria → approve → baseline → labeled retrieval evaluation |

The deterministic fault injection report is produced by
`python scripts/evaluate_validator.py`. It includes a semantic counterexample
that passes deterministic link checks, to make the validator's limits visible.

The five-policy lexical retrieval baseline (`scripts/evaluate_retrieval.py`)
measured P@3=0.3333, Recall@3=1.0 and MRR=1.0. These are small offline fixtures,
not a broad semantic retrieval benchmark. Live verification has an opt-in script
and remains pending until a Gemini key is configured.

## Not verified

- Live Gemini network generation and semantic embeddings require a configured
  key. Provider contract/retry tests use controlled mocks and are labeled as such.
- Docker image startup was not tested because Docker Desktop's Linux engine was
  unavailable. Compose syntax validation is not a container runtime test.
- Multi-user isolation, production deployment, broad accessibility conformance,
  load/cost targets and independent research evaluation are not established.
- Browser verification used the local responsive workspace, not a public host.

An upstream Google SDK Python 3.14 deprecation warning is present in local tests;
it does not fail the suite. The recommended Docker/CI interpreter is Python 3.12.
