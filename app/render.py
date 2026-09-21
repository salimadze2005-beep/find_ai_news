import re


def safe(text):
    return re.sub(r"([\\`*_{}\[\]<>()#!|])", r"\\\1", str(text))


def evidence_lines(items, label):
    lines = []
    if items:
        lines.append(f"### {label}")
        for item in items:
            refs = " ".join(f"[источник {i+1}](<{u}>)" for i, u in enumerate(item.source_urls))
            lines.append(f"- {safe(item.text)} {refs}")
    return lines


def usage_totals(usage):
    return {"input_tokens": sum(u.input_tokens or 0 for u in usage),
        "output_tokens": sum(u.output_tokens or 0 for u in usage),
        "total_tokens": sum(u.total_tokens or 0 for u in usage),
        "known_cost": sum(u.estimated_cost or 0 for u in usage),
        "calls": len(usage), "unknown_usage_calls": sum(u.total_tokens is None for u in usage),
        "unknown_cost_calls": sum(u.estimated_cost is None for u in usage),
        "duration": round(sum(u.duration for u in usage), 2)}


def render_digest(digest):
    hours = (digest.window_end - digest.window_start).total_seconds() / 3600
    lines = [f"# AI Intelligence — последние {hours:g} часов",
        f"{digest.window_start.isoformat()} — {digest.window_end.isoformat()} (UTC)"]
    if digest.mock:
        lines.append("**DEMO / MOCK: искусственные события. Это не реальные новости.**")
    lines += [safe(digest.summary)]
    for index, event in enumerate(digest.events, 1):
        v, context, impact = event.event.verification, event.context, event.impact
        lines += [f"## {index}. {safe(event.event.candidate.title)}", "### Что произошло", safe(impact.what_happened)]
        lines += evidence_lines(v.confirmed_facts, "FACT — подтверждённые факты")
        lines += evidence_lines(v.company_claims, "COMPANY CLAIM — заявления компании")
        lines += ["### Почему это важно — INFERENCE", safe(impact.why_it_matters), "### Что реально изменилось", safe(context.what_changed)]
        lines += evidence_lines(context.previous_state, "Предыдущее состояние")
        lines += ["### Практические возможности — INFERENCE"] + ["- " + safe(s) for s in impact.practical_opportunities]
        lines += ["### Влияние на AI-продукты — INFERENCE", safe(impact.product_impact)]
        if impact.what_to_try:
            lines += ["### Что попробовать", safe(impact.what_to_try)]
        if impact.alfa_bank_relevance:
            lines += ["### Возможная польза для Альфа-Банка — гипотеза", safe(impact.alfa_bank_relevance)]
        lines += evidence_lines(v.key_numbers, "Ключевые цифры (статус — в FACT / COMPANY CLAIM выше)")
        if v.conflicts:
            lines += ["### Конфликты источников"] + ["- " + safe(s) for s in v.conflicts]
        lines += ["### Оценка", " | ".join(f"{k.title()}: {value:g}/10" for k, value in impact.scores.model_dump().items()),
            f"**Significance: {event.significance_score:g}/10 · Hype: {context.hype}**", safe(context.hype_reason),
            "### Ограничения"] + ["- " + safe(s) for s in context.limitations + impact.inference_limitations]
        lines += ["### Источники", f"Primary: [первоисточник](<{v.primary_source_url}>)"]
        lines += [f"Independent: [источник {i+1}](<{url}>)" for i, url in enumerate(v.independent_source_urls)]
    lines += ["## Что изменилось в AI за анализируемый период", safe(digest.market_trend)]
    if digest.unconfirmed:
        lines += ["## UNCONFIRMED — не подтверждено"]
        for event in digest.unconfirmed:
            v = event.verification
            lines += [f"### {safe(event.candidate.title)}", "Потенциальная важность: " + safe(event.candidate.potential_significance)]
            lines += evidence_lines(v.unverified_claims, "Что утверждается (не подтверждено)")
            lines += ["Что подтверждено: найдена публикация с указанным утверждением; само событие не установлено.",
                "Что не подтверждено: " + safe(v.reason), f"Confidence: {v.confidence:g}/10"]
    if digest.warnings:
        lines += ["## Ограничения запуска"] + ["- " + safe(s) for s in digest.warnings]
    totals = usage_totals(digest.usage)
    lines += ["## Usage", f"LLM calls: {totals['calls']}; reported tokens: {totals['total_tokens']}; "
        f"known estimated LLM cost: ${totals['known_cost']:.6f}.",
        f"Calls without usage: {totals['unknown_usage_calls']}; without price: {totals['unknown_cost_calls']}. Search charges excluded."]
    return "\n\n".join(lines) + "\n"
