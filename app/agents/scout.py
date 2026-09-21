import hashlib
from typing import Literal
from pydantic import Field
from app.models import Model, CandidateEvent
from app.agents.common import ask, source_data
from app.search.pages import canonical_url


class Queries(Model):
    queries: list[str] = Field(min_length=3, max_length=16)


class Discovery(Model):
    title: str
    short_description: str
    category: Literal["model", "update", "research", "tool", "pricing", "open_source"]
    event_kind: Literal["release", "update", "benchmark", "pricing", "research"]
    source_urls: list[str] = Field(min_length=1)
    potential_significance: str
    entities: list[str] = Field(min_length=1)


class Discoveries(Model):
    events: list[Discovery]


def scout(llm, search, settings, start, end, trace):
    queries = ask(llm, "queries", {"start": start.isoformat(), "end": end.isoformat(),
        "count": settings.search_queries_count}, Queries).queries
    results = {}
    for query in list(dict.fromkeys(queries))[:settings.search_queries_count]:
        found = search.search(query, start, end, min(10, settings.max_scout_results))
        trace("search", {"query": query, "results": source_data(found, False)})
        for source in found:
            key = canonical_url(source.url)
            if key in results or len(results) < settings.max_scout_results:
                results[key] = source.model_copy(update={"url": key})
    if not results:
        return []
    extracted = ask(llm, "scout", {"start": start.isoformat(), "end": end.isoformat(),
        "results": source_data(list(results.values()), False)}, Discoveries)
    events = []
    for item in extracted.events[:settings.max_scout_results]:
        urls = list(dict.fromkeys(canonical_url(u) for u in item.source_urls))
        if not urls or any(u not in results for u in urls):
            trace("rejected", {"title": item.title, "reason": "Scout invented or omitted source URL"})
            continue
        identity = "|".join(sorted(urls)) + "|" + item.event_kind + "|" + item.title.casefold()
        events.append(CandidateEvent(id=hashlib.sha256(identity.encode()).hexdigest()[:20],
            sources=[results[u] for u in urls], **item.model_dump(exclude={"source_urls"})))
    trace("scout", [e.model_dump(mode="json") for e in events])
    return events
