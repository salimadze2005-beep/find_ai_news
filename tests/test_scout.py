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


def test_results_budget_is_shared_between_queries():
    from app.models import NewsSource
    from app.search.base import SearchProvider
    class Search(SearchProvider):
        def search(self, query, start_date, end_date, limit):
            return [NewsSource(title=query, url=f"https://example.com/{query}/{i}") for i in range(3)]
    class LLM:
        def generate_structured(self, agent, prompt, data, schema):
            if agent == "queries":
                return schema(queries=["one", "two", "three"])
            assert [s["title"] for s in data["results"]] == ["one", "two", "three"]
            return schema(events=[])
    now = datetime(2026, 9, 21, tzinfo=timezone.utc)
    assert scout(LLM(), Search(), Settings(_env_file=None, search_queries_count=3, max_scout_results=3),
                 now-timedelta(hours=48), now, lambda *args: None) == []


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
