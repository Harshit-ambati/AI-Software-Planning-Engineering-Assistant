import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .models import STAGES
from .validation import validate

logger = logging.getLogger(__name__)


class State(TypedDict, total=False):
    run_id: str
    project_id: str
    brief: str
    constraints: str
    review_required: bool
    artifacts: dict
    sources: list
    approved: bool


class Workflow:
    def __init__(self, settings, store, provider, memory):
        self.settings, self.store, self.provider, self.memory = settings, store, provider, memory
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="blueprint")
        store.recover()

    def graph(self, saver):
        graph = StateGraph(State)

        def retrieve(state):
            run_id = state["run_id"]
            saved = self.store.run(run_id)["artifacts"].get("sources")
            sources = saved if saved is not None else self.memory.search(state["project_id"], state["brief"])
            self.store.artifact(run_id, "sources", sources)
            self.store.event(run_id, "memory", "completed", {"citations": [s["citation"] for s in sources]})
            return {"sources": sources}

        def review(state):
            if state["review_required"]:
                approved = interrupt({"kind": "requirements_review", "message": "Review requirements before design."})
                if approved is not True:
                    raise RuntimeError("Requirements were not approved.")
            self.store.event(state["run_id"], "review", "approved")
            return {"approved": True}

        def stage_node(stage):
            def execute(state):
                run_id = state["run_id"]
                self.store.event(run_id, stage, "running")
                start = time.monotonic()
                # Durable artifact writes close the crash window before a graph checkpoint.
                saved = self.store.run(run_id)["artifacts"].get(stage)
                if saved is not None:
                    content, meta = saved, {"reused": True}
                else:
                    context = dict(
                        brief=state["brief"],
                        constraints=state["constraints"],
                        upstream=state.get("artifacts", {}),
                        sources=state.get("sources", []),
                    )
                    content, meta = self.provider.generate(stage, context)
                    self.store.artifact(run_id, stage, content)
                self.store.event(
                    run_id, stage, "completed", meta | {"duration_ms": round(1000 * (time.monotonic() - start))}
                )
                return {"artifacts": state.get("artifacts", {}) | {stage: content}}

            return execute

        def validation(state):
            run_id = state["run_id"]
            self.store.event(run_id, "validation", "running")
            critique = self.store.run(run_id)["artifacts"].get("critique")
            if critique is None:
                critique, meta = self.provider.generate(
                    "critique",
                    dict(
                        brief=state["brief"],
                        constraints=state["constraints"],
                        blueprint=state["artifacts"],
                        sources=state.get("sources", []),
                    ),
                )
                self.store.artifact(run_id, "critique", critique)
                self.store.event(run_id, "critique", "completed", meta)
            report = validate(state["artifacts"], critique)
            self.store.artifact(run_id, "validation", report)
            self.store.event(run_id, "validation", "completed", {"status": report["status"]})
            return {"artifacts": state["artifacts"] | {"validation": report}}

        graph.add_node("retrieve", retrieve)
        graph.add_node("review", review)
        for stage in STAGES[:-1]:
            graph.add_node(stage, stage_node(stage))
        graph.add_node("validation", validation)
        chain = [START, "retrieve", "requirements", "review", *STAGES[1:], END]
        for source, target in zip(chain, chain[1:]):
            graph.add_edge(source, target)
        return graph.compile(checkpointer=saver)

    def enqueue(self, run_id, action="start"):
        self.executor.submit(self.execute, run_id, action)

    def execute(self, run_id, action="start"):
        run = self.store.run(run_id)
        self.store.status(run_id, "running")
        self.store.event(run_id, "supervisor", "running", {"action": action})
        try:
            with SqliteSaver.from_conn_string(str(self.settings.data_dir / "checkpoints.sqlite")) as saver:
                graph = self.graph(saver)
                config = {"configurable": {"thread_id": run_id}}
                checkpoint = graph.get_state(config)
                if action == "approve":
                    value = Command(resume=True)
                elif checkpoint.values:
                    value = None
                else:
                    value = dict(
                        run_id=run_id,
                        project_id=run["project_id"],
                        brief=run["brief"],
                        constraints=run["constraints_text"],
                        review_required=bool(run["review_required"]),
                        artifacts={},
                    )
                graph.invoke(value, config)
                state = graph.get_state(config)
                if state.next:
                    status = "awaiting_review"
                else:
                    status = state.values["artifacts"]["validation"]["status"]
                self.store.status(run_id, status)
                self.store.event(run_id, "supervisor", status)
        except Exception as exc:
            # Do not persist raw provider/network exceptions: they can contain secrets or prompts.
            safe = (
                str(exc)
                if isinstance(exc, RuntimeError)
                else f"{type(exc).__name__}: execution failed; check server configuration and connectivity."
            )
            safe = safe.replace(self.settings.gemini_api_key, "[redacted]") if self.settings.gemini_api_key else safe
            logger.warning("Run %s failed (%s)", run_id, type(exc).__name__)
            self.store.status(run_id, "failed", safe[:500])
            self.store.event(run_id, "supervisor", "failed", {"message": safe[:500]})

    def close(self):
        self.executor.shutdown(wait=True)
