import re
from app.models import Verification, VerifiedEvent
from app.agents.common import ask, source_data
from app.search.pages import canonical_url, domain, in_window, valid_url


def normalized_quote(text):
    return re.sub(r"\s+", " ", text).strip().casefold()


def numeric_tokens(text):
    return set(re.findall(r"\d+(?:[.,]\d+)*", text))


def numeric_errors(texts, evidence_text):
    allowed = numeric_tokens(evidence_text)
    return [text for text in texts if not numeric_tokens(text) <= allowed]


def evidence_errors(items, sources):
    by_url = {s.url: s for s in sources if s.fetched}
    errors = []
    for item in items:
        if numeric_errors([item.text], item.quote):
            errors.append("Evidence introduces a number absent from its quote")
        if any(u not in by_url or not valid_url(u) for u in item.source_urls):
            errors.append("Evidence cites an unavailable or invented URL")
        elif not all(normalized_quote(item.quote) in normalized_quote(by_url[u].content) for u in item.source_urls):
            errors.append("Evidence quote absent from fetched page text")
    return errors


def verification_errors(v, sources, start, end, minimum):
    errors = evidence_errors(v.confirmed_facts + v.company_claims + v.unverified_claims + v.key_numbers, sources)
    available = {s.url: s for s in sources if s.fetched}
    primary = available.get(v.primary_source_url)
    date_source = available.get(v.date_source_url)
    if not primary:
        errors.append("No fetched primary source")
    independent = [available[u] for u in set(v.independent_source_urls) if u in available]
    if len(independent) != len(set(v.independent_source_urls)):
        errors.append("Independent source unavailable")
    publishers = {domain('https://' + s.source) if s.source else domain(s.url) for s in independent}
    primary_domain = (domain('https://' + primary.source) if primary.source else domain(primary.url)) if primary else ""
    if primary_domain in publishers:
        errors.append("Primary and independent publishers are not distinct")
    publishers.discard(primary_domain)
    if len(publishers) + bool(primary) < minimum:
        errors.append("Insufficient distinct publishers")
    cited = {u for fact in v.confirmed_facts for u in fact.source_urls}
    if not v.confirmed_facts or not any(s.url in cited for s in independent) or v.primary_source_url not in cited:
        errors.append("Facts lack primary and independent supporting evidence")
    if not date_source or not in_window(date_source, start, end):
        errors.append("Publication date not independently extracted inside the window")
    if not primary or not in_window(primary, start, end):
        errors.append("Primary publication is stale or undated")
    if v.occurred_at is None or not start <= v.occurred_at <= end:
        errors.append("Event date outside analysis window or unknown")
    elif date_source and date_source.published_at and v.occurred_at > date_source.published_at:
        errors.append("Event date is after its publication evidence")
    return list(dict.fromkeys(errors))


def verify(candidate, llm, search, pages, settings, start, end, trace):
    query = f"{' '.join(candidate.entities)} {candidate.event_kind} official announcement independent analysis"
    found = search.search(query, start, end, settings.verify_sources_target * 2)
    trace("verification_search", {"query": query, "results": source_data(found, False)})
    sources = {}
    # Candidate sources first, then additional research, within a bounded evidence budget.
    for s in candidate.sources + found:
        key = canonical_url(s.url)
        if key not in sources and len(sources) < settings.verify_sources_target * 2:
            sources[key] = pages.fetch(s.model_copy(update={"url": key}))
    fetched = list(sources.values())
    v = ask(llm, "verifier", {"candidate": candidate.model_dump(mode="json"), "sources": source_data(fetched),
        "window_start": start.isoformat(), "window_end": end.isoformat()}, Verification)
    errors = verification_errors(v, fetched, start, end, settings.verify_sources_min)
    if errors:
        v = v.model_copy(update={"verified": False, "confidence": min(v.confidence, 4),
                                "reason": v.reason + "; " + "; ".join(errors)})
    event = VerifiedEvent(candidate=candidate, verification=v, sources=fetched)
    trace("verification", event.model_dump(mode="json"))
    return event
