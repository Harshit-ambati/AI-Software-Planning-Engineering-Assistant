import hashlib
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


def fingerprint(content):
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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
                CREATE TABLE IF NOT EXISTS requirement_reviews (
                  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT REFERENCES runs(id),
                  old_hash TEXT, new_hash TEXT, before_content TEXT, after_content TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS evaluations (
                  id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), kind TEXT,
                  payload TEXT, result TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS ratings (
                  id TEXT PRIMARY KEY, run_id TEXT REFERENCES runs(id), payload TEXT, created_at TEXT);
            """)
            existing = {row[1] for row in db.execute("PRAGMA table_info(runs)")}
            for column, definition in {
                "strategy": "TEXT NOT NULL DEFAULT 'staged'",
                "use_memory": "INTEGER NOT NULL DEFAULT 1",
                "parent_run_id": "TEXT",
            }.items():
                if column not in existing:
                    db.execute(f"ALTER TABLE runs ADD COLUMN {column} {definition}")

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                db.row_factory = sqlite3.Row
                db.execute("PRAGMA foreign_keys=ON")
                yield db
        finally:
            db.close()

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
                "INSERT INTO runs (id,project_id,version,brief,constraints_text,review_required,provider,model,status,created_at,updated_at,error,strategy,use_memory,parent_run_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
                    payload.strategy,
                    payload.use_memory,
                    payload.parent_run_id,
                ),
            )
            if payload.requirements_seed is not None:
                db.execute(
                    "INSERT INTO artifacts VALUES (?,?,?)",
                    (
                        run_id,
                        "seed_provenance",
                        json.dumps(
                            dict(
                                parent_run_id=payload.parent_run_id,
                                requirements_hash=fingerprint(payload.requirements_seed.model_dump()),
                            )
                        ),
                    ),
                )
                db.execute(
                    "INSERT INTO artifacts VALUES (?,?,?)",
                    (run_id, "requirements", payload.requirements_seed.model_dump_json()),
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
            result["requirements_etag"] = (
                fingerprint(result["artifacts"]["requirements"]) if "requirements" in result["artifacts"] else None
            )
            return result

    def edit_requirements(self, run_id, payload):
        content = payload.requirements.model_dump()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row or row["status"] != "awaiting_review":
                raise ValueError("Requirements can only be edited while awaiting review.")
            before = json.loads(
                db.execute(
                    "SELECT content FROM artifacts WHERE run_id=? AND stage='requirements'", (run_id,)
                ).fetchone()[0]
            )
            old_hash, new_hash = fingerprint(before), fingerprint(content)
            if payload.expected_etag != old_hash:
                raise ValueError("Requirements changed since you opened the editor. Reload before saving.")
            if old_hash == new_hash:
                return
            db.execute(
                "INSERT OR IGNORE INTO artifacts VALUES (?,?,?)", (run_id, "requirements_original", json.dumps(before))
            )
            db.execute(
                "UPDATE artifacts SET content=? WHERE run_id=? AND stage='requirements'", (json.dumps(content), run_id)
            )
            db.execute(
                "INSERT INTO requirement_reviews(run_id,old_hash,new_hash,before_content,after_content,created_at) VALUES (?,?,?,?,?,?)",
                (run_id, old_hash, new_hash, json.dumps(before), json.dumps(content), now()),
            )
            db.execute(
                "INSERT INTO events(run_id,stage,status,detail,created_at) VALUES (?,?,?,?,?)",
                (run_id, "review", "edited", json.dumps(dict(before_hash=old_hash, after_hash=new_hash)), now()),
            )

    def review_history(self, run_id):
        with self.db() as db:
            return [
                dict(row)
                | {
                    "before_content": json.loads(row["before_content"]),
                    "after_content": json.loads(row["after_content"]),
                }
                for row in db.execute("SELECT * FROM requirement_reviews WHERE run_id=? ORDER BY id", (run_id,))
            ]

    def save_evaluation(self, project_id, kind, payload, result):
        value = dict(id=uid(), project_id=project_id, kind=kind, payload=payload, result=result, created_at=now())
        with self.db() as db:
            db.execute(
                "INSERT INTO evaluations VALUES (?,?,?,?,?,?)",
                (value["id"], project_id, kind, json.dumps(payload), json.dumps(result), value["created_at"]),
            )
        return value

    def evaluations(self, project_id):
        with self.db() as db:
            return [
                dict(row) | {"payload": json.loads(row["payload"]), "result": json.loads(row["result"])}
                for row in db.execute(
                    "SELECT * FROM evaluations WHERE project_id=? ORDER BY created_at DESC", (project_id,)
                )
            ]

    def rate(self, run_id, payload):
        with self.db() as db:
            db.execute("INSERT INTO ratings VALUES (?,?,?,?)", (uid(), run_id, payload.model_dump_json(), now()))

    def ratings(self, run_id):
        with self.db() as db:
            return [
                dict(row) | {"payload": json.loads(row["payload"])}
                for row in db.execute("SELECT * FROM ratings WHERE run_id=? ORDER BY created_at", (run_id,))
            ]

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
