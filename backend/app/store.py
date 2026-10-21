import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid4())


class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "workspace.sqlite"
        with self.db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS projects (
                  id TEXT PRIMARY KEY, name TEXT, brief TEXT, constraints_text TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), version INTEGER,
                  brief TEXT, constraints_text TEXT, review_required INTEGER, provider TEXT,
                  model TEXT, status TEXT, created_at TEXT, updated_at TEXT, error TEXT,
                  UNIQUE(project_id, version));
                CREATE TABLE IF NOT EXISTS artifacts (
                  run_id TEXT REFERENCES runs(id), stage TEXT, content TEXT,
                  PRIMARY KEY(run_id, stage));
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT REFERENCES runs(id),
                  stage TEXT, status TEXT, detail TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS knowledge (
                  id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id),
                  title TEXT, content TEXT, created_at TEXT);
            """)

    @contextmanager
    def db(self):
        with sqlite3.connect(self.path, timeout=30) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            yield db

    def projects(self):
        with self.db() as db:
            return [
                dict(row)
                for row in db.execute("""SELECT p.*,
                (SELECT count(*) FROM runs r WHERE r.project_id=p.id) run_count,
                (SELECT status FROM runs r WHERE r.project_id=p.id ORDER BY version DESC LIMIT 1) status
                FROM projects p ORDER BY created_at DESC""")
            ]

    def create_project(self, payload):
        project_id = uid()
        with self.db() as db:
            db.execute(
                "INSERT INTO projects VALUES (?,?,?,?,?)",
                (project_id, payload.name.strip(), payload.brief.strip(), payload.constraints, now()),
            )
        return self.project(project_id)

    def project(self, project_id):
        with self.db() as db:
            row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["runs"] = [
                dict(r)
                for r in db.execute("SELECT * FROM runs WHERE project_id=? ORDER BY version DESC", (project_id,))
            ]
            return result

    def create_run(self, project_id, payload, provider, model):
        run_id = uid()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute(
                "SELECT 1 FROM runs WHERE project_id=? AND status IN ('queued','running','awaiting_review')",
                (project_id,),
            ).fetchone():
                raise ValueError("Complete the active revision before starting another.")
            version = db.execute(
                "SELECT coalesce(max(version),0)+1 FROM runs WHERE project_id=?", (project_id,)
            ).fetchone()[0]
            db.execute(
                "INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    project_id,
                    version,
                    payload.brief,
                    payload.constraints,
                    payload.review_required,
                    provider,
                    model,
                    "queued",
                    now(),
                    now(),
                    None,
                ),
            )
        return self.run(run_id)

    def run(self, run_id):
        with self.db() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["artifacts"] = {
                r["stage"]: json.loads(r["content"])
                for r in db.execute("SELECT * FROM artifacts WHERE run_id=?", (run_id,))
            }
            result["events"] = [
                dict(r) | {"detail": json.loads(r["detail"])}
                for r in db.execute("SELECT * FROM events WHERE run_id=? ORDER BY id", (run_id,))
            ]
            return result

    def status(self, run_id, status, error=None):
        with self.db() as db:
            db.execute("UPDATE runs SET status=?,updated_at=?,error=? WHERE id=?", (status, now(), error, run_id))

    def claim(self, run_id, allowed):
        with self.db() as db:
            marks = ",".join("?" for _ in allowed)
            return (
                db.execute(
                    f"UPDATE runs SET status=?,error=NULL,updated_at=? WHERE id=? AND status IN ({marks})",
                    ("queued", now(), run_id, *allowed),
                ).rowcount
                == 1
            )

    def artifact(self, run_id, stage, content):
        with self.db() as db:
            db.execute("INSERT OR REPLACE INTO artifacts VALUES (?,?,?)", (run_id, stage, json.dumps(content)))

    def event(self, run_id, stage, status, detail=None):
        with self.db() as db:
            db.execute(
                "INSERT INTO events(run_id,stage,status,detail,created_at) VALUES (?,?,?,?,?)",
                (run_id, stage, status, json.dumps(detail or {}), now()),
            )

    def recover(self):
        with self.db() as db:
            db.execute("UPDATE runs SET status='interrupted' WHERE status IN ('running','queued')")

    def add_knowledge(self, project_id, title, content, doc_id):
        with self.db() as db:
            db.execute("INSERT INTO knowledge VALUES (?,?,?,?,?)", (doc_id, project_id, title, content, now()))

    def knowledge(self, project_id):
        with self.db() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM knowledge WHERE project_id=? ORDER BY created_at DESC", (project_id,)
                )
            ]
