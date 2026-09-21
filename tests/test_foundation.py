from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.config import Settings
from app.models import NewsSource, Scores
from app.storage import Database


def test_settings_weights():
    with pytest.raises(ValidationError):
        Settings(scoring_weights={"importance": 1}, _env_file=None)


def test_scores_bounds():
    with pytest.raises(ValidationError):
        Scores(importance=11, novelty=1, practicality=2, impact=3, confidence=4)


def test_timezone_required():
    with pytest.raises(ValidationError):
        NewsSource(title="x", url="https://example.com", published_at=datetime(2026, 1, 1))


def test_database(tmp_path):
    db = Database(tmp_path / "test.sqlite")
    db.start("run")
    db.trace("run", "scout", {"count": 2})
    db.finish("run", error="test failure")
    assert db.history()[0]["status"] == "failed"
    assert db.traces("run")[0]["data"]["count"] == 2
