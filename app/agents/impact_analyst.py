from app.models import ImpactAnalysis, AnalyzedEvent
from app.agents.common import ask_validated
from app.pipeline.scoring import significance
from app.agents.verifier import numeric_errors
from app.llm.base import ProviderError


def analyze_impact(event, context, context_sources, llm, settings, trace):
    baseline = " ".join(x.text for x in context.previous_state + event.verification.confirmed_facts + event.verification.company_claims + event.verification.key_numbers)
    def validate(impact):
        if numeric_errors([impact.what_happened, impact.why_it_matters, impact.product_impact, impact.what_to_try,
                           impact.alfa_bank_relevance] + impact.practical_opportunities + impact.inference_limitations, baseline):
            raise ProviderError("Impact introduces a number absent from cited evidence")
    impact = ask_validated(llm, "impact_analyst", {"event": event.model_dump(mode="json", exclude={"sources"}),
        "context": context.model_dump(mode="json"), "enable_alfa": settings.enable_alfa_relevance},
        ImpactAnalysis, validate, trace)
    impact.scores.confidence = min(impact.scores.confidence, event.verification.confidence)
    if not settings.enable_alfa_relevance:
        impact.alfa_bank_relevance = ""
    result = AnalyzedEvent(event=event, context=context, context_sources=context_sources, impact=impact,
        significance_score=significance(impact.scores, settings.scoring_weights))
    trace("impact", result.model_dump(mode="json"))
    return result
