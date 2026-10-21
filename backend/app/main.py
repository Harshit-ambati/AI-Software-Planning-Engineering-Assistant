import hmac
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .config import Settings
from .evaluation import evaluate_retrieval, run_metrics
from .exports import compare, json_export, markdown, openapi
from .impact import analyze_impact
from .memory import Memory
from .models import (
    CreateProject,
    CreateRun,
    EditRequirements,
    ImpactInput,
    KnowledgeInput,
    RatingInput,
    RetrievalEvaluation,
    SearchInput,
)
from .provider import Provider
from .store import Store, uid
from .workflow import Workflow


def create_app(settings=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        store = Store(settings.data_dir)
        provider = Provider(settings)
        memory = Memory(settings, provider, store)
        workflow = Workflow(settings, store, provider, memory)
        app.state.store, app.state.provider = store, provider
        app.state.memory, app.state.workflow = memory, workflow
        yield
        workflow.close()
        memory.close()
        if provider.client:
            provider.client.close()

    app = FastAPI(title="Engineering Blueprint API", version="2.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins.split(","),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    def authorize(request: Request):
        if settings.app_access_token:
            actual = request.headers.get("authorization", "")
            if not hmac.compare_digest(actual.encode(), ("Bearer " + settings.app_access_token).encode()):
                raise HTTPException(401, "Valid workspace access token required.")

    api = APIRouter(prefix="/api", dependencies=[Depends(authorize)])

    def store():
        return app.state.store

    def project(project_id):
        value = store().project(project_id)
        if not value:
            raise HTTPException(404, "Project not found.")
        return value

    def run(run_id):
        value = store().run(run_id)
        if not value:
            raise HTTPException(404, "Revision not found.")
        return value

    def ready():
        if settings.ai_provider == "gemini" and not settings.gemini_api_key:
            raise HTTPException(503, "Set GEMINI_API_KEY in the root .env and restart the backend.")

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "2.1.0"}

    @api.get("/config")
    def config():
        return dict(
            provider=settings.ai_provider,
            model=app.state.provider.model,
            live_ready=settings.ai_provider == "gemini" and bool(settings.gemini_api_key),
            memory="semantic" if settings.ai_provider == "gemini" else "lexical demo",
            review_policy="Human review enabled by default",
        )

    @api.get("/projects")
    def list_projects():
        return store().projects()

    @api.post("/projects", status_code=201)
    def add_project(payload: CreateProject):
        if len(store().projects()) >= 200:
            raise HTTPException(409, "Local workspace limit: 200 projects.")
        return store().create_project(payload)

    @api.get("/projects/{project_id}")
    def get_project(project_id: str):
        return project(project_id)

    @api.post("/projects/{project_id}/runs", status_code=202)
    def add_run(project_id: str, payload: CreateRun):
        project(project_id)
        ready()
        if payload.strategy == "single_prompt" and (payload.review_required or payload.requirements_seed is not None):
            raise HTTPException(
                422, "A single-prompt experiment requires review_required=false and no requirement seed."
            )
        if payload.requirements_seed is not None and not payload.parent_run_id:
            raise HTTPException(422, "A requirement-seeded revision requires a parent revision.")
        if payload.parent_run_id:
            parent = run(payload.parent_run_id)
            if parent["project_id"] != project_id:
                raise HTTPException(400, "Parent revision must belong to this project.")
        try:
            value = store().create_run(project_id, payload, settings.ai_provider, app.state.provider.model)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        app.state.workflow.enqueue(value["id"])
        return value

    @api.post("/runs/{run_id}/review/requirements")
    def edit_requirements(run_id: str, payload: EditRequirements):
        run(run_id)
        try:
            store().edit_requirements(run_id, payload)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        return run(run_id)

    @api.get("/runs/{run_id}/review/history")
    def review_history(run_id: str):
        run(run_id)
        return store().review_history(run_id)

    @api.post("/runs/{run_id}/analysis/impact")
    def impact(run_id: str, payload: ImpactInput):
        value = run(run_id)
        if "requirements" not in value["artifacts"]:
            raise HTTPException(409, "Requirements are not available yet.")
        return analyze_impact(value["artifacts"], payload.requirements.model_dump())

    @api.get("/projects/{project_id}/evaluations")
    def evaluations(project_id: str):
        owner = project(project_id)
        return dict(
            runs=[run_metrics(run(item["id"]), store().ratings(item["id"])) for item in owner["runs"]],
            retrieval=store().evaluations(project_id),
        )

    @api.get("/runs/{run_id}/evaluation/ratings")
    def ratings(run_id: str):
        run(run_id)
        return store().ratings(run_id)

    @api.post("/runs/{run_id}/evaluation/ratings", status_code=201)
    def rate(run_id: str, payload: RatingInput):
        value = run(run_id)
        if value["status"] not in ("passed", "needs_attention"):
            raise HTTPException(409, "Rate a completed revision.")
        store().rate(run_id, payload)
        return store().ratings(run_id)

    @api.post("/projects/{project_id}/evaluation/retrieval", status_code=201)
    def retrieval_evaluation(project_id: str, payload: RetrievalEvaluation):
        project(project_id)
        ready()
        valid = {doc["id"] for doc in store().knowledge(project_id)}
        if any(
            not set(q.expected_document_ids) <= valid
            or len(set(q.expected_document_ids)) != len(q.expected_document_ids)
            for q in payload.queries
        ):
            raise HTTPException(422, "Expected documents must be unique and belong to this project's source library.")
        try:
            result = evaluate_retrieval(app.state.memory, project_id, payload, app.state.provider)
        except Exception:
            raise HTTPException(
                502, "Retrieval evaluation failed. Check the embedding provider and vector index."
            ) from None
        return store().save_evaluation(project_id, "retrieval", payload.model_dump(), result)

    @api.get("/runs/{run_id}")
    def get_run(run_id: str):
        return run(run_id)

    @api.post("/runs/{run_id}/{action}", status_code=202)
    def transition(run_id: str, action: Literal["approve", "resume", "reject"]):
        value = run(run_id)
        if action == "reject":
            if not store().claim(run_id, ["awaiting_review"]):
                raise HTTPException(409, "Only a revision awaiting review can be rejected.")
            store().status(run_id, "rejected")
            store().event(run_id, "review", "rejected")
            return run(run_id)
        ready()
        if value["provider"] != settings.ai_provider or value["model"] != app.state.provider.model:
            raise HTTPException(
                409, "Provider/model changed. Restore the original configuration to resume, or start a new revision."
            )
        allowed = ["awaiting_review"] if action == "approve" else ["failed", "interrupted"]
        if not store().claim(run_id, allowed):
            raise HTTPException(409, f"Cannot {action} this revision in its current state.")
        app.state.workflow.enqueue(run_id, action)
        return run(run_id)

    @api.get("/projects/{project_id}/knowledge")
    def list_knowledge(project_id: str):
        project(project_id)
        return store().knowledge(project_id)

    @api.post("/projects/{project_id}/knowledge", status_code=201)
    def add_knowledge(project_id: str, payload: KnowledgeInput):
        project(project_id)
        ready()
        if len(store().knowledge(project_id)) >= 30:
            raise HTTPException(409, "Local project limit: 30 knowledge documents.")
        doc_id = uid()
        try:
            chunks = app.state.memory.ingest(project_id, doc_id, payload.title, payload.content)
        except Exception:
            raise HTTPException(
                502, "Knowledge indexing failed. Check embedding provider and vector store; document was not saved."
            ) from None
        store().add_knowledge(project_id, payload.title, payload.content, doc_id)
        return dict(id=doc_id, title=payload.title, chunks=chunks)

    @api.post("/projects/{project_id}/knowledge/search")
    def search_knowledge(project_id: str, payload: SearchInput):
        project(project_id)
        ready()
        try:
            return app.state.memory.search(project_id, payload.query)
        except Exception:
            raise HTTPException(502, "Knowledge search failed. Check embedding provider and vector store.") from None

    @api.post("/projects/{project_id}/knowledge/reindex")
    def reindex(project_id: str):
        project(project_id)
        ready()
        docs = store().knowledge(project_id)
        try:
            for doc in docs:
                app.state.memory.ingest(project_id, doc["id"], doc["title"], doc["content"])
        except Exception:
            raise HTTPException(
                502, "Reindex failed. SQL source documents remain intact; retry when the provider is available."
            ) from None
        return {"indexed": len(docs)}

    @api.get("/runs/{run_id}/compare/{before_id}")
    def compare_runs(run_id: str, before_id: str):
        after, before = run(run_id), run(before_id)
        if after["project_id"] != before["project_id"]:
            raise HTTPException(400, "Compare revisions within the same project.")
        return compare(before, after) | {
            "impact": analyze_impact(before["artifacts"], after["artifacts"].get("requirements", {}))
        }

    @api.get("/runs/{run_id}/export/{format}")
    def export(run_id: str, format: Literal["json", "markdown", "openapi"]):
        value = run(run_id)
        owner = project(value["project_id"])
        extension = "md" if format == "markdown" else "json"
        if format == "openapi":
            if "apis" not in value["artifacts"]:
                raise HTTPException(409, "API artifact is not available yet.")
            from .validation import validate

            invalid = validate(value["artifacts"])["findings"]
            if any(
                f["artifact"] == "apis" and f["rule"] in ("DUPLICATE_ROUTE", "INVALID_PATH", "DUPLICATE_ID")
                for f in invalid
            ):
                raise HTTPException(
                    409,
                    "Resolve duplicate or invalid API operations in a new revision before OpenAPI export. JSON and Markdown remain available for review.",
                )
            import json

            content, media = json.dumps(openapi(owner, value), indent=2), "application/json"
        elif format == "markdown":
            content, media = markdown(owner, value), "text/markdown"
        else:
            content, media = json_export(owner, value), "application/json"
        return Response(
            content,
            media_type=media,
            headers={
                "Content-Disposition": f'attachment; filename="blueprint-v{value["version"]}-{format}.{extension}"'
            },
        )

    app.include_router(api)
    return app


app = create_app()
