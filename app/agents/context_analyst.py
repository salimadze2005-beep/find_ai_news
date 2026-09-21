from app.models import ContextAnalysis
from app.agents.common import ask, source_data
from app.agents.verifier import evidence_errors, numeric_errors
from app.llm.base import ProviderError
from app.search.pages import canonical_url


def analyze_context(event, llm, search, pages, end, trace):
    query = f"{' '.join(event.candidate.entities)} previous version competitors pricing capabilities comparison"
    found = search.search(query, None, end, 5)
    trace("context_search", {"query": query, "results": source_data(found, False)})
    sources = list({canonical_url(s.url): pages.fetch(s.model_copy(update={"url": canonical_url(s.url)})) for s in found}.values())
    sources = [s for s in sources if s.fetched and (s.published_at is None or s.published_at <= end)]
    context = ask(llm, "context_analyst", {"event": event.model_dump(mode="json", exclude={"sources"}),
        "sources": source_data(sources), "as_of": end.isoformat()}, ContextAnalysis)
    errors = evidence_errors(context.previous_state, sources)
    if errors:
        raise ProviderError("Historical context evidence failed validation")
    baseline = " ".join(x.text for x in context.previous_state + event.verification.confirmed_facts + event.verification.company_claims + event.verification.key_numbers)
    if numeric_errors([context.what_changed, context.hype_reason] + context.limitations, baseline):
        raise ProviderError("Context introduces a number absent from cited evidence")
    trace("context", context.model_dump(mode="json"))
    return context, sources
