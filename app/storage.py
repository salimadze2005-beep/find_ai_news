import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from app.models import utcnow


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, started_at TEXT NOT NULL, status TEXT NOT NULL,
                    digest TEXT, error TEXT);
                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, stage TEXT NOT NULL,
                    payload TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sources (
                    url TEXT PRIMARY KEY, payload TEXT NOT NULL, last_seen TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS analyses (
                    cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def start(self, run_id):
        with self.connect() as db:
            db.execute("INSERT INTO runs VALUES (?, ?, 'running', NULL, NULL)", (run_id, utcnow().isoformat()))

    def trace(self, run_id, stage, payload):
        with self.connect() as db:
            db.execute("INSERT INTO traces(run_id,stage,payload,created_at) VALUES(?,?,?,?)",
                       (run_id, stage, json.dumps(payload, ensure_ascii=False, default=str), utcnow().isoformat()))

    def source(self, source):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO sources VALUES(?,?,?)", (source.url, source.model_dump_json(), utcnow().isoformat()))

    def cached(self, key):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM analyses WHERE cache_key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else None

    def cache(self, key, event):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO analyses VALUES(?,?,?)", (key, event.model_dump_json(), utcnow().isoformat()))

    def finish(self, run_id, digest=None, error=None):
        with self.connect() as db:
            db.execute("UPDATE runs SET status=?,digest=?,error=? WHERE id=?",
                       ("failed" if error else "completed", digest.model_dump_json() if digest else None, error, run_id))

    def history(self):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute("SELECT id,started_at,status,error FROM runs ORDER BY started_at DESC LIMIT 50")]

    def load(self, run_id):
        with self.connect() as db:
            row = db.execute("SELECT digest FROM runs WHERE id=?", (run_id,)).fetchone()
            return json.loads(row[0]) if row and row[0] else None

    def traces(self, run_id):
        with self.connect() as db:
            return [{"stage": r[0], "data": json.loads(r[1])} for r in db.execute(
                "SELECT stage,payload FROM traces WHERE run_id=? ORDER BY id", (run_id,))]
