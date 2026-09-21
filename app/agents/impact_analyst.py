from app.models import ImpactAnalysis, AnalyzedEvent
from app.agents.common import ask
from app.pipeline.scoring import significance


def analyze_impact(event, context, context_sources, llm, settings, trace):
    impact = ask(llm, "impact_analyst", {"event": event.model_dump(mode="json", exclude={"sources"}),
        "context": context.model_dump(mode="json"), "enable_alfa": settings.enable_alfa_relevance}, ImpactAnalysis)
    impact.scores.confidence = min(impact.scores.confidence, event.verification.confidence)
    if not settings.enable_alfa_relevance:
        impact.alfa_bank_relevance = ""
    result = AnalyzedEvent(event=event, context=context, context_sources=context_sources, impact=impact,
        significance_score=significance(impact.scores, settings.scoring_weights))
    trace("impact", result.model_dump(mode="json"))
    return result
