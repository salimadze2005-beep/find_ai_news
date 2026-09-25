import re
from app.models import Evidence, Verification, VerifiedEvent
from app.agents.common import ask, source_data
from app.search.pages import canonical_url, domain, in_window, valid_url


def normalized_quote(text):
    return re.sub(r"\s+", " ", text).strip().casefold()


def quote_in_content(quote, content):
    haystack = normalized_quote(content)
    needle = normalized_quote(quote)
    if needle in haystack:
        return True
    # Preserve character/word order but tolerate typography and terminal punctuation.
    compact_needle = "".join(char for char in needle if char.isalnum())
    compact_haystack = "".join(char for char in haystack if char.isalnum())
    if len(compact_needle) >= 24 and compact_needle in compact_haystack:
        return True
    segments = [part.strip() for part in re.split(r"(?:\.\.\.|…)", needle) if len(part.strip()) >= 12]
    if len(segments) < 2:
        return False
    position = 0
    for segment in segments:
        found = haystack.find(segment, position)
        if found < 0:
            return False
        position = found + len(segment)
    return True


def numeric_tokens(text):
    # Hyphenated product versions (Qwen-Image-2.1) are entity names, not numeric claims.
    dates = set()
    cleaned = text
    for match in list(re.finditer(r"(?<!\d)(20\d{2})[-./](0?[1-9]|1[0-2])[-./](0?[1-9]|[12]\d|3[01])(?!\d)", cleaned)):
        year, month, day = (int(value) for value in match.groups())
        dates.add(f"date:{year:04d}-{month:02d}-{day:02d}")
        cleaned = cleaned.replace(match.group(0), " ")
    months = {"января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5,
              "июня": 6, "июля": 7, "августа": 8, "сентября": 9, "октября": 10,
              "ноября": 11, "декабря": 12}
    pattern = r"(?<!\d)([0-3]?\d)\s+(" + "|".join(months) + r")\s+(20\d{2})(?!\d)"
    for match in list(re.finditer(pattern, cleaned.casefold())):
        day, month_name, year = match.groups()
        dates.add(f"date:{int(year):04d}-{months[month_name]:02d}-{int(day):02d}")
        cleaned = re.sub(re.escape(match.group(0)), " ", cleaned, count=1, flags=re.IGNORECASE)
    english_months = {name: month for month, names in enumerate([
        ("January", "Jan"), ("February", "Feb"), ("March", "Mar"), ("April", "Apr"),
        ("May",), ("June", "Jun"), ("July", "Jul"), ("August", "Aug"),
        ("September", "Sept", "Sep"), ("October", "Oct"), ("November", "Nov"),
        ("December", "Dec")], 1) for name in names}
    month_pattern = "|".join(english_months)
    pattern = rf"\b({month_pattern})\.?\s+([0-3]?\d)(?:,\s*|\s+)(20\d{{2}})\b"
    for match in list(re.finditer(pattern, cleaned, re.IGNORECASE)):
        name, day, year = match.groups()
        month = next(value for key, value in english_months.items() if key.casefold() == name.casefold())
        dates.add(f"date:{int(year):04d}-{month:02d}-{int(day):02d}")
        cleaned = cleaned.replace(match.group(0), " ")
    values = set(re.findall(r"(?<![\w-])\d+(?:[.,]\d+)*(?:[KMB])?(?![\w-])", cleaned, re.IGNORECASE))
    return dates | {value.casefold().replace(",", ".") for value in values}


def numeric_errors(texts, evidence_text):
    allowed = numeric_tokens(evidence_text)
    return [text for text in texts if not numeric_tokens(text) <= allowed]


def unsupported_numbers(texts, evidence_text):
    """Safe feedback contains only numeric/date tokens, never source or response prose."""
    return ", ".join(sorted(set().union(*(numeric_tokens(t) for t in texts)) - numeric_tokens(evidence_text))[:12])


def quoted_event_date(quote):
    match = re.search(r"(?<!\d)(20\d{2})[-./](0[1-9]|1[0-2])[-./](0[1-9]|[12]\d|3[01])(?!\d)", quote)
    if not match:
        # Full textual dates carry the same calendar evidence as ISO dates; no time is inferred.
        dates = [token[5:] for token in numeric_tokens(quote) if token.startswith("date:")]
        if len(dates) != 1:
            return None
        try:
            from datetime import date
            return date.fromisoformat(dates[0])
        except ValueError:
            return None
    try:
        from datetime import date
        return date(*(int(value) for value in match.groups()))
    except ValueError:
        return None


def evidence_errors(items, sources):
    by_url = {s.url: s for s in sources if s.fetched}
    errors = []
    for item in items:
        if numeric_errors([item.text], item.quote):
            errors.append("Evidence introduces a number absent from its quote")
        if any(u not in by_url or not valid_url(u) for u in item.source_urls):
            errors.append("Evidence cites an unavailable or invented URL")
        elif not all(quote_in_content(item.quote, by_url[u].content) for u in item.source_urls):
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
    quote_date = quoted_event_date(v.date_quote)
    quoted_date_valid = bool(date_source and v.date_quote and quote_date and
        (quote_in_content(v.date_quote, date_source.content) or
         normalized_quote(v.date_quote) == normalized_quote(date_source.date_evidence)))
    if not date_source or not (in_window(date_source, start, end) or quoted_date_valid):
        errors.append("Event date lacks fresh metadata or an exact dated page quote")
    if primary and not (in_window(primary, start, end) or
                        (primary.url == v.date_source_url and quoted_date_valid)):
        errors.append("Primary source is stale or lacks exact event-date evidence")
    if not any(in_window(source, start, end) for source in independent):
        errors.append("No fresh independent publication inside the window")
    if v.occurred_at is None or not start <= v.occurred_at <= end:
        errors.append("Event date outside analysis window or unknown")
    elif quote_date and v.occurred_at.date() != quote_date:
        errors.append("Event date does not match the exact dated quote")
    elif date_source and date_source.published_at and v.occurred_at > date_source.published_at:
        errors.append("Event date is after its publication evidence")
    return list(dict.fromkeys(errors))


def normalize_evidence(v, sources):
    by_url = {source.url: source for source in sources if source.fetched}
    def clean(items):
        kept = []
        for item in items:
            matching = [url for url in item.source_urls if url in by_url and
                        quote_in_content(item.quote, by_url[url].content)]
            if matching and not numeric_errors([item.text], item.quote):
                item.source_urls = matching
                kept.append(item)
        return kept
    v.confirmed_facts = clean(v.confirmed_facts)
    v.company_claims = clean(v.company_claims)
    v.unverified_claims = clean(v.unverified_claims)
    v.key_numbers = clean(v.key_numbers)
    if v.occurred_at:
        formats = {v.occurred_at.strftime("%Y-%m-%d"), v.occurred_at.strftime("%Y.%m.%d"),
                   v.occurred_at.strftime("%Y/%m/%d")}
        preferred = [by_url.get(v.primary_source_url)] + list(by_url.values())
        for source in preferred:
            if not source:
                continue
            token = next((value for value in formats if value in source.content), None)
            if token:
                v.date_source_url = source.url
                v.date_quote = token
                break
    return v


def core_event_quote(content, entities):
    """Return a verbatim, bounded excerpt that explicitly describes the core event."""
    entity = next((value for value in sorted(entities, key=len, reverse=True)
                   if len(value.strip()) >= 4 and value.casefold() in content.casefold()), "")
    if not entity:
        return ""
    chunks = re.split(r"(?<=[.!?。])\s+|[\r\n]+", content)
    actions = ("release", "released", "launch", "announc", "publish", "open-source",
               "price", "cost", "effective", "change", "cut", "公開", "発表",
               "выпущ", "релиз", "анонс", "опублик", "цен", "стоимост")
    candidates = [chunk.strip() for chunk in chunks if entity.casefold() in chunk.casefold()]
    selected = next((chunk for chunk in candidates if any(word in chunk.casefold() for word in actions)), "")
    if not selected:
        return ""
    if len(selected) <= 240:
        return selected
    position = selected.casefold().find(entity.casefold())
    start = max(0, position - 70)
    end = min(len(selected), position + len(entity) + 150)
    return selected[start:end].strip()


def ensure_core_evidence(v, sources, entities):
    """Recover exact core-event citations from URLs the verifier already selected."""
    if not v.verified:
        return v
    by_url = {source.url: source for source in sources if source.fetched}
    cited = {url for fact in v.confirmed_facts for url in fact.source_urls}
    targets = []
    if v.primary_source_url not in cited:
        targets.append(v.primary_source_url)
    if not any(url in cited for url in v.independent_source_urls):
        targets.extend(v.independent_source_urls)
    for url in targets:
        source = by_url.get(url)
        quote = core_event_quote(source.content, entities) if source else ""
        if quote:
            v.confirmed_facts.append(Evidence(text=quote, source_urls=[url], quote=quote))
            cited.add(url)
            if url in v.independent_source_urls:
                break
    return v


def verify(candidate, llm, search, pages, settings, start, end, trace):
    subject = candidate.search_subject or candidate.entities[0]
    queries = [
        f'{subject} official {candidate.event_kind}',
        f'{subject} {candidate.event_kind} news',
    ]
    found = []
    for query in queries:
        # Primary docs/repositories are often undated; discovery dates must not hide evidence.
        # All fetched event and independent-publication dates are still checked below.
        batch = search.search(query, None, end, settings.verify_sources_target * 2)
        trace("verification_search", {"query": query, "results": source_data(batch, False)})
        found.extend(batch)
    sources = {}
    # Candidate sources first, then additional research, within a bounded evidence budget.
    for s in candidate.sources + found:
        key = canonical_url(s.url)
        if key not in sources and len(sources) < settings.verify_sources_target * 3:
            sources[key] = pages.fetch(s.model_copy(update={"url": key}))
    fetched = list(sources.values())
    request = {"candidate": candidate.model_dump(mode="json"), "sources": source_data(fetched),
               "window_start": start.isoformat(), "window_end": end.isoformat()}
    v, errors = None, []
    for attempt in range(settings.verifier_attempts):
        raw_v = ask(llm, "verifier", request, Verification)
        v = ensure_core_evidence(normalize_evidence(raw_v.model_copy(deep=True), fetched),
                                 fetched, candidate.entities)
        errors = verification_errors(v, fetched, start, end, settings.verify_sources_min)
        if not errors or not v.verified:
            break
        if attempt + 1 < settings.verifier_attempts:
            trace("verification_retry", {"id": candidate.id, "errors": errors})
            # Let the model repair the evidence it actually emitted. The normalized copy may
            # have pruned invalid citations, which removes the very material a retry must fix.
            request["previous_output"] = raw_v.model_dump(mode="json")
            request["validation_feedback"] = {
                "errors": errors,
                "instruction": "Revise previous_output instead of starting over. Preserve its valid evidence and source choices. confirmed_facts must collectively include a primary-source Evidence item and a separate independent-source Evidence item that confirms the core event. Quotes must be short verbatim text in the original source language, from exactly one source per Evidence item. Do not combine translations or snippets. date_quote must contain the occurred_at calendar date exactly."
            }
    if errors:
        v = v.model_copy(update={"verified": False, "confidence": min(v.confidence, 4),
                                "reason": v.reason + "; " + "; ".join(errors)})
    event = VerifiedEvent(candidate=candidate, verification=v, sources=fetched)
    trace("verification", event.model_dump(mode="json"))
    return event
