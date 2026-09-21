from datetime import datetime, timezone, timedelta
from app.config import Settings
from app.agents.scout import scout
from app.mock import MockLLM, MockSearch
from app.pipeline.deduplication import deduplicate


def candidates():
    now = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)
    return scout(MockLLM(), MockSearch(now), Settings(_env_file=None), now-timedelta(hours=48), now, lambda *args: None)


def test_scout_synthetic_events():
    events = candidates()
    assert len(events) == 4
    assert all(e.title.startswith("DEMO") for e in events)


def test_duplicate_articles_merged():
    e = candidates()[0]
    assert len(deduplicate([e, e.model_copy(update={"id": "duplicate"})])) == 1


def test_distinct_actions_preserved():
    e = candidates()[0]
    other = e.model_copy(update={"id": "other", "event_kind": "release"})
    assert len(deduplicate([e, other])) == 2


def test_semantic_dedup_with_guard():
    e = candidates()[0]
    translated = e.model_copy(update={"id": "translation", "title": "Atlas снижает цену"})
    class Semantic:
        def generate_structured(self, agent, prompt, data, schema):
            return schema(groups=[[e.id, translated.id]])
    assert len(deduplicate([e, translated], Semantic())) == 1
    translated.event_kind = "benchmark"
    assert len(deduplicate([e, translated], Semantic())) == 2
