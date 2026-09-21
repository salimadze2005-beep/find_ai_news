from datetime import datetime, timezone
from app.config import Settings
from app.pipeline.orchestrator import run_pipeline
from app.storage import Database
from app.render import render_digest, usage_totals


def test_end_to_end_and_reuse(tmp_path):
    settings = Settings(_env_file=None, database_path=tmp_path / "test.db")
    now = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)
    first = run_pipeline(settings, now=now)
    assert len(first.events) == 2
    assert len(first.unconfirmed) == 1
    assert not first.warnings
    assert "UNCONFIRMED" in render_digest(first)
    assert "DEMO / MOCK" in render_digest(first)
    second = run_pipeline(settings, now=now)
    assert len(second.events) == 2
    assert len(second.usage) < len(first.usage)
    assert usage_totals(first.usage)["known_cost"] == 0
    db = Database(settings.database_path)
    assert db.history()[0]["status"] == "completed"
    assert any(t["stage"] == "cache_hit" for t in db.traces(second.run_id))


def test_high_threshold_produces_empty_digest(tmp_path):
    result = run_pipeline(Settings(_env_file=None, database_path=tmp_path / "test.db", min_significance_score=10))
    assert not result.events
    assert not result.unconfirmed
    assert not any(u.agent == "editor" for u in result.usage)
