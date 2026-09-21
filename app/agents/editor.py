from app.models import Editorial
from app.agents.common import ask
from app.llm.base import ProviderError
from app.agents.verifier import numeric_errors


def edit(events, llm, settings, trace):
    eligible = sorted([e for e in events if e.significance_score >= settings.min_significance_score],
                      key=lambda e: e.significance_score, reverse=True)
    for event in events:
        if event not in eligible:
            trace("rejected", {"id": event.event.candidate.id, "reason": "Below significance threshold"})
    if not eligible:
        return [], "Достаточно значимых подтверждённых событий не найдено.", "Недостаточно данных для вывода о сдвиге рынка."
    compact = [{"id": e.event.candidate.id, "title": e.event.candidate.title,
        "facts": [f.model_dump() for f in e.event.verification.confirmed_facts],
        "claims": [f.model_dump() for f in e.event.verification.company_claims],
        "context": e.context.model_dump(), "impact": e.impact.model_dump(),
        "significance": e.significance_score} for e in eligible]
    decision = ask(llm, "editor", {"events": compact}, Editorial)
    allowed = {e.event.candidate.id for e in eligible}
    if len(set(decision.selected_ids)) != len(decision.selected_ids) or not set(decision.selected_ids) <= allowed:
        raise ProviderError("Editor returned duplicate or unknown event IDs")
    if not set(decision.trend_event_ids) <= set(decision.selected_ids):
        raise ProviderError("Market trend cites events not selected for digest")
    if decision.selected_ids and not decision.trend_event_ids and decision.market_trend:
        decision.market_trend = "Недостаточно данных для подтверждённого общего тренда."
    selected = [next(e for e in eligible if e.event.candidate.id == i) for i in decision.selected_ids]
    baseline = " ".join(x.text for e in selected for x in e.event.verification.confirmed_facts + e.event.verification.company_claims + e.event.verification.key_numbers + e.context.previous_state)
    if numeric_errors([decision.summary, decision.market_trend], baseline):
        raise ProviderError("Editor introduces a number absent from selected evidence")
    exclusions = {x.id: x.reason for x in decision.excluded}
    for e in eligible:
        if e.event.candidate.id not in decision.selected_ids:
            trace("rejected", {"id": e.event.candidate.id, "reason": exclusions.get(e.event.candidate.id, "Editor: insufficient signal")})
    trace("editor", decision.model_dump(mode="json"))
    if not selected:
        return [], "Редактор не нашёл достаточно полезных событий.", "Недостаточно данных для вывода о сдвиге рынка."
    return selected, decision.summary, decision.market_trend
