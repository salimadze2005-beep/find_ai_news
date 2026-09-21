from app.models import ContextAnalysis
from app.agents.common import ask, source_data
from app.agents.verifier import evidence_errors
from app.llm.base import ProviderError
from app.search.pages import canonical_url


def analyze_context(event, llm, search, pages, end, trace):
    query = f"{' '.join(event.candidate.entities)} previous version competitors pricing capabilities comparison"
    found = search.search(query, None, end, 5)
    trace("context_search", {"query": query, "results": source_data(found, False)})
    sources = list({canonical_url(s.url): pages.fetch(s) for s in found}.values())
    context = ask(llm, "context_analyst", {"event": event.model_dump(mode="json", exclude={"sources"}),
        "sources": source_data(sources), "as_of": end.isoformat()}, ContextAnalysis)
    errors = evidence_errors(context.previous_state, sources)
    if errors:
        raise ProviderError("Historical context evidence failed validation")
    trace("context", context.model_dump(mode="json"))
    return context, sources
