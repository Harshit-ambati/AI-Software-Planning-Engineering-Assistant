# Verification record

Date: 21 October 2026. Local Windows environment: Python 3.14.2, Node 24.13.0.
CI additionally targets Ubuntu, Python 3.12 and Node 22. Remote CI status must
be checked independently; adding a workflow does not establish that it passed.

## Tested boundaries

| Boundary | Evidence |
|---|---|
| API contracts and execution | 14 passing pytest tests with isolated SQL/vector databases |
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

The deterministic fault injection report is produced by
`python scripts/evaluate_validator.py`. It includes a semantic counterexample
that passes deterministic link checks, to make the validator's limits visible.

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
