import hashlib
import json
from datetime import timedelta
from uuid import uuid4
from app.config import Settings
from app.models import FinalDigest, AnalyzedEvent, utcnow
from app.storage import Database
from app.agents.common import PROMPTS
from app.agents.scout import scout
from app.agents.verifier import verify, evidence_errors
from app.agents.context_analyst import analyze_context
from app.agents.impact_analyst import analyze_impact
from app.agents.editor import edit
from app.pipeline.deduplication import deduplicate
from app.llm.base import ProviderError
from app.search.pages import in_window


def providers(settings, now):
    if settings.mock_mode:
        from app.mock import MockLLM, MockSearch, MockPages
        return MockLLM(), MockSearch(now), MockPages(now)
    if not settings.llm_api_key.get_secret_value() or not settings.tavily_api_key.get_secret_value():
        raise ProviderError("Live mode requires LLM_API_KEY and TAVILY_API_KEY in .env")
    if settings.llm_model == "configure-model-id":
        raise ProviderError("Set LLM_MODEL to an available model ID")
    from app.llm.provider import AgentRouterProvider
    from app.search.provider import TavilyProvider
    from app.search.pages import WebPages
    return AgentRouterProvider(settings), TavilyProvider(settings), WebPages(settings.max_page_fetches)


def analysis_key(event, settings, now):
    # Re-verify every run; only expensive context/impact can be reused within a six-hour bucket.
    policy = {"version": 1, "mock": settings.mock_mode, "models": [settings.model_for(r) for r in ["context_analyst", "impact_analyst"]],
        "weights": settings.scoring_weights, "alfa": settings.enable_alfa_relevance,
        "time_bucket": int(now.timestamp()) // (6 * 3600),
        "prompts": [(p.name, p.read_text(encoding="utf-8")) for p in sorted(PROMPTS.glob("*.md"))]}
    payload = json.dumps({"event": event.model_dump(mode="json"), "policy": policy}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def run_pipeline(settings=None, now=None, injected=None, progress=lambda message: None):
    settings = settings or Settings()
    now = now or utcnow()
    if now.tzinfo is None:
        raise ValueError("Pipeline now must be timezone-aware")
    start = now - timedelta(hours=settings.lookback_hours)
    run_id = str(uuid4())
    db = Database(settings.database_path)
    db.start(run_id)
    llm = search = pages = None
    warnings, unconfirmed, analyzed = [], [], []
    def trace(stage, data):
        db.trace(run_id, stage, data)
    try:
        llm, search, pages = injected or providers(settings, now)
        llm.on_usage = lambda usage: trace("usage", usage.model_dump(mode="json"))
        progress("Scout: поиск и извлечение кандидатов")
        events = deduplicate(scout(llm, search, settings, start, now, trace), llm, trace)
        if not events and not settings.mock_mode:
            warnings.append("Discovery found no candidates. This is insufficient search evidence, not proof that no AI news occurred.")
        events.sort(key=lambda e: e.potential_significance_score, reverse=True)
        for deferred in events[settings.max_analysis_events:]:
            trace("rejected", {"id": deferred.id, "reason": "Deferred: analysis event budget"})
        for i, candidate in enumerate(events[:settings.max_analysis_events], 1):
            progress(f"Verifier / Analysts: {i}/{min(len(events), settings.max_analysis_events)} — {candidate.title}")
            try:
                event = verify(candidate, llm, search, pages, settings, start, now, trace)
                for source in event.sources:
                    db.source(source)
                if not event.verification.verified:
                    trace("rejected", {"id": candidate.id, "reason": event.verification.reason})
                    v = event.verification
                    # Display only attributable, fresh, potentially material unconfirmed information.
                    if (candidate.potential_significance_score >= settings.min_significance_score
                        and v.unverified_claims and not evidence_errors(v.unverified_claims, event.sources)
                        and any(s.fetched and in_window(s, start, now) and s.url in {u for c in v.unverified_claims for u in c.source_urls}
                                for s in event.sources)):
                        unconfirmed.append(event)
                    continue
                key = analysis_key(event, settings, now)
                cached = db.cached(key)
                if cached:
                    analysis = AnalyzedEvent.model_validate(cached)
                    trace("cache_hit", {"id": candidate.id, "key": key})
                else:
                    context, sources = analyze_context(event, llm, search, pages, now, trace)
                    for source in sources:
                        db.source(source)
                    analysis = analyze_impact(event, context, sources, llm, settings, trace)
                    db.cache(key, analysis)
                analyzed.append(analysis)
            except ProviderError as exc:
                warnings.append(f"{candidate.id}: {exc}")
                trace("rejected", {"id": candidate.id, "reason": str(exc)})
        progress("Editor: отбор и финальный дайджест")
        selected, summary, trend = edit(analyzed, llm, settings, trace)
        digest = FinalDigest(run_id=run_id, started_at=now, window_start=start, window_end=now,
            mock=settings.mock_mode, summary=summary, market_trend=trend, events=selected,
            unconfirmed=unconfirmed, usage=llm.usage, warnings=warnings)
        db.finish(run_id, digest=digest)
        return digest
    except Exception as exc:
        # Never persist raw HTTP bodies, headers or exceptions containing credentials.
        message = str(exc) if isinstance(exc, ProviderError) else f"Pipeline failed ({type(exc).__name__})"
        db.finish(run_id, error=message)
        raise ProviderError(message) from None
    finally:
        for provider in (llm, search, pages):
            client = getattr(provider, "client", None)
            if client:
                client.close()
