"""Deterministic synthetic fixtures; all sources are reserved example domains."""
from datetime import timedelta
from app.llm.base import LLMProvider
from app.models import NewsSource, Usage
from app.search.base import SearchProvider, PageProvider


def fixture_sources(now):
    date = (now - timedelta(hours=12)).replace(microsecond=0)
    entries = [
        ("https://vendor.example/atlas-price", "DEMO: Atlas inference pricing cut", "Atlas input price falls from $2 to $1 per million tokens. The pricing change is effective today.", date),
        ("https://lab.example/atlas-review", "DEMO: Independent Atlas price check", "We independently checked Atlas billing: input costs $1 per million tokens instead of $2. Quality was not evaluated.", date + timedelta(hours=1)),
        ("https://vendor.example/atlas-old", "DEMO: Previous Atlas price", "Atlas input costs $2 per million tokens.", date - timedelta(days=30)),
        ("https://tools.example/evalkit", "DEMO: EvalKit regression runner released", "EvalKit releases a runnable regression suite for tool-calling agents, with reproducible fixtures and a command line runner.", date),
        ("https://review.example/evalkit", "DEMO: EvalKit hands-on", "We ran EvalKit's regression suite on a local agent and reproduced the documented fixture results.", date),
        ("https://rumor.example/atlas-next", "DEMO: Unconfirmed Atlas Next", "An anonymous source claims Atlas Next may launch soon. No official announcement exists.", date),
        ("https://archive.example/old-model", "DEMO: Old model launch", "OldModel was released years ago.", date - timedelta(days=100)),
    ]
    return [NewsSource(title=t, url=u, snippet=c, content=c, source=u.split('/')[2],
        published_at=d, date_precision="exact", date_evidence="Synthetic fixture publication: " + d.isoformat(), fetched=True)
        for u, t, c, d in entries]


class MockSearch(SearchProvider):
    def __init__(self, now):
        self.sources = fixture_sources(now)

    def search(self, query, start_date, end_date, limit):
        return self.sources[:limit]


class MockPages(PageProvider):
    def __init__(self, now):
        self.sources = {s.url: s for s in fixture_sources(now)}

    def fetch(self, source):
        return self.sources.get(source.url, source.model_copy(update={"fetched": False, "fetch_error": "Unknown fixture"}))


def evidence(source, text=None):
    return {"text": text or source["content"], "source_urls": [source["url"]], "quote": source["content"]}


class MockLLM(LLMProvider):
    def generate_structured(self, agent, system_prompt, input_data, response_schema):
        data = self.respond(agent, input_data)
        result = response_schema.model_validate(data)
        self.record(Usage(agent=agent, model="synthetic-mock", input_tokens=0, output_tokens=0, total_tokens=0, estimated_cost=0))
        return result

    def respond(self, agent, data):
        if agent == "queries":
            topics = ["AI model release", "AI API pricing", "AI agent tools", "AI open source", "AI practical research", "AI multimodal", "AI benchmarks", "AI coding tools"]
            return {"queries": [f"{topics[i % len(topics)]} {data['start']} {i}" for i in range(data["count"])]}
        if agent == "scout":
            events = []
            specs = [("Atlas price change", "pricing", "pricing", "Atlas", "atlas-price"),
                     ("EvalKit release", "tool", "release", "EvalKit", "tools.example/evalkit"),
                     ("Atlas Next rumor", "model", "release", "Atlas Next", "atlas-next"),
                     ("OldModel launch", "model", "release", "OldModel", "old-model")]
            for title, category, kind, entity, match in specs:
                sources = [s for s in data["results"] if match in s["url"]]
                if sources:
                    events.append({"title": "DEMO: " + title, "short_description": sources[0]["snippet"],
                        "category": category, "event_kind": kind, "entities": [entity],
                        "source_urls": [s["url"] for s in sources],
                        "potential_significance": "Синтетический пример потенциально полезного изменения."})
            return {"events": events}
        if agent == "deduplication":
            return {"groups": []}
        if agent == "verifier":
            event, sources = data["candidate"], data["sources"]
            primary_url = event["sources"][0]["url"]
            primary = next(s for s in sources if s["url"] == primary_url)
            independent = [s for s in sources if ("lab.example" in s["url"] if event["category"] == "pricing" else "review.example" in s["url"])]
            rumor = "rumor" in primary_url
            if rumor:
                independent = []
            return {"verified": not rumor, "occurred_at": primary["published_at"], "date_source_url": primary_url,
                "primary_source_url": "" if rumor else primary_url,
                "independent_source_urls": [s["url"] for s in independent],
                "confirmed_facts": [] if rumor else [evidence(primary)] + [evidence(s) for s in independent],
                "company_claims": [], "unverified_claims": [evidence(primary)] if rumor else [],
                "key_numbers": [evidence(primary)] if event["category"] == "pricing" else [],
                "conflicts": [], "confidence": 3 if rumor else 9,
                "reason": "Нет официального подтверждения" if rumor else "Подтверждено синтетическими источниками"}
        if agent == "context_analyst":
            pricing = data["event"]["candidate"]["category"] == "pricing"
            previous = [s for s in data["sources"] if "atlas-old" in s["url"]] if pricing else []
            return {"previous_state": [evidence(s) for s in previous],
                "what_changed": "Снизилась опубликованная стоимость входных токенов; качество требует отдельной проверки." if pricing else "Появился исполняемый набор регрессионных проверок; преимущество над другими инструментами не установлено.",
                "hype": "LOW" if pricing else "MODERATE", "hype_reason": "Есть проверяемый артефакт; обобщения ограничены.",
                "limitations": ["Демонстрационные данные, не реальные новости."]}
        if agent == "impact_analyst":
            return {"scores": {"importance": 8, "impact": 8, "practicality": 9, "novelty": 6, "confidence": 9},
                "what_happened": data["event"]["candidate"]["short_description"],
                "why_it_matters": "INFERENCE: изменение можно проверить на существующей продуктовой задаче.",
                "practical_opportunities": ["Сравнить стоимость и качество на фиксированном наборе задач."],
                "product_impact": "INFERENCE: возможно снижение затрат или улучшение контроля регрессий.",
                "what_to_try": "Запустить парное сравнение текущей конфигурации и нового варианта на одном наборе примеров; измерить стоимость успешного результата.",
                "alfa_bank_relevance": "Гипотеза: оценить применимость к обработке документов; внутренняя инфраструктура неизвестна." if data["enable_alfa"] else "",
                "inference_limitations": ["Эффект зависит от результатов собственного эксперимента."]}
        if agent == "editor":
            ids = [e["id"] for e in data["events"]]
            return {"selected_ids": ids, "summary": "Демонстрационный дайджест: синтетические изменения стоимости и инструментов проверки.",
                "market_trend": "На этих искусственных примерах показано, как отделять проверяемые изменения от продуктовых гипотез. Вывод о реальном рынке делать нельзя.",
                "trend_event_ids": ids, "excluded": {}}
        raise ValueError(f"Unsupported mock role: {agent}")
