# AI Software Planning & Engineering Assistant

**Forma** is an engineering blueprint workspace: turn a software idea into
structured requirements, architecture, data design, API contracts, an
implementation plan, documentation and a traceable validation report.

This is a fresh implementation for a final-year project, in the original
[GitHub repository](https://github.com/Harshit-ambati/AI-Software-Planning-Engineering-Assistant).
Earlier commits remain in history. Generated blueprints are design proposals;
the system does not generate or execute the applications described in them.

[Verified responsive validation view](docs/images/validation-preview.png)

## Run locally

Requires Python **3.12+** and Node **22+**. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open [the workspace](http://127.0.0.1:5173) and
[the API reference](http://127.0.0.1:8000/docs).
On macOS/Linux use `.venv/bin/python` in place of the Windows executable.
`scripts/start.ps1` starts both servers on Windows once dependencies are installed.

Default **demo mode** makes no external model calls. Use the demonstration brief
to explore a fixed food-delivery example. It intentionally does **not** generate
novel designs from arbitrary prompts. The banner and exports record this.

## Live AI mode

Edit the root `.env` locally; never commit it:

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-3.8-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

Select models enabled for your account, then restart the backend. Each stage uses
a separately versioned prompt and a Pydantic JSON schema, with up to three
attempts for invalid structured output/transient provider failures. Missing keys
produce an explicit error; live mode never silently falls back to demo. Live
requests incur the provider's usage charges. Source documents and project briefs
are sent to the configured provider during live generation and embedding.

## A complete workflow

1. Create a project and describe the problem, actors and constraints.
2. Inspect extracted requirements. Approve to continue, or choose **Revise scope**
   to reject that revision and start another with a refined brief.
3. Inspect each artifact and the execution history as the supervisor progresses.
4. Review findings and the requirement-to-component/entity/endpoint/task matrix.
5. Export Markdown, JSON or a draft OpenAPI 3.1 specification.
6. Add project knowledge before a new revision; relevant passages are retrieved
   and saved with stable source IDs. Compare adjacent revisions in Traceability.

## What is implemented

- React/TypeScript workspace with responsive artifact views and a React Flow graph.
- FastAPI input validation and explicit optional single-user bearer authentication.
- LangGraph supervisor, specialized generation stages, independent critique and
  human review using durable SQLite checkpoints.
- Persistent project/run/artifact/event history; immutable completed revisions.
- Failure recovery from checkpoints without regenerating completed artifacts.
- Qdrant vectors: local persistent mode by default, optional server URL. Gemini
  semantic embeddings in live mode; clearly labeled hashed lexical baseline offline.
- Project-filtered retrieval, source snapshots and SQL-to-vector reindexing.
- Deterministic coverage/reference/route/schema-field/dependency checks, plus live
  LLM semantic critique. A linked requirement is not proof of semantic correctness.
- Prompt hash/version, model identity, token counts, attempts and stage timing.
- Exported request/response JSON schemas, CI and automated integration tests.
- Audited requirement editing, explainable change-impact analysis and seeded revisions.
- A single-prompt baseline, evaluation workbench, human ratings and retrieval benchmarks.
- Endpoint-backed semantic assessments and source-rule conformance review in live mode.

See [the v2.1 improvement guide](docs/IMPROVEMENTS.md) for review/editing,
experiment controls, metric definitions and the opt-in live verification command.

## Storage and deployment boundaries

`data/` contains the workspace SQL database, graph checkpoints and local Qdrant
index. Stop the backend before backing up the entire directory. SQL owns source
documents; vectors are a derived index. Changing embedding models creates a
separate collection: click **Rebuild vector index** for existing documents.

Run **one API process** (one worker). The local execution queue is intentionally
serialized. After an unexpected restart, running/queued revisions become
`interrupted`; explicitly resume them. Human approval checkpoints remain paused.
Restore the original provider/model configuration to resume an existing run.

This is a single-user local application. Set `APP_ACCESS_TOKEN` before any shared
network deployment, and enter that token in Workspace settings. There is no
multi-user account isolation, distributed worker queue or public hosting setup.
Keep it bound to localhost. The Vite dev server proxies `/api` to the backend.

## Docker

```powershell
docker compose up --build
```

Open [the containerized workspace](http://127.0.0.1:8080). The API and frontend
ports bind to localhost. Data lives in named volumes. The optional Qdrant service
can be enabled with `docker compose --profile vector-server up --build`; set
`QDRANT_URL=http://qdrant:6333` in `.env` before starting it. Local Qdrant mode
already supports persistent retrieval without running that service.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check backend
cd frontend
npm run build
npm run lint
```

The automated suite runs offline with isolated temporary databases. See
[verification evidence](docs/VERIFICATION.md) for the tested boundaries and live
limitations. For academic scope, evaluation design and architecture decisions,
read [the project plan](docs/PROJECT_PLAN.md) and
[the final-year guide](docs/FINAL_YEAR_GUIDE.md).

## Implementation references

The provider follows Google's [structured output documentation](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
and [embedding API](https://ai.google.dev/gemini-api/docs/embeddings). Human review
uses LangGraph's [interrupt/checkpoint workflow](https://docs.langchain.com/oss/python/langgraph/interrupts).
The configurable generation default follows Google's current
[model guidance](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash).
