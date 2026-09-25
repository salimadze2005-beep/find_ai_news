import streamlit as st
from pydantic import ValidationError
from app.config import Settings
from app.models import FinalDigest
from app.storage import Database
from app.pipeline.orchestrator import run_pipeline
from app.llm.base import ProviderError
from app.render import render_digest, render_html, usage_totals, safe, evidence_lines


def show_digest(digest):
    if digest.mock:
        st.warning("DEMO / MOCK — искусственные события, не реальные новости. API-вызовов нет.")
    st.caption(f"UTC · {digest.window_start:%d.%m.%Y %H:%M} → {digest.window_end:%d.%m.%Y %H:%M}")
    st.write(digest.summary)
    totals = usage_totals(digest.usage)
    cols = st.columns(4)
    cols[0].metric("Подтверждённые события", len(digest.events))
    cols[1].metric("LLM-вызовы", totals["calls"])
    cols[2].metric("Reported tokens", totals["total_tokens"])
    cols[3].metric("Known LLM cost", f"${totals['known_cost']:.5f}")
    if not digest.events:
        st.info("Нет событий, прошедших проверку и порог значимости. Количество не дополняется искусственно.")
    for event in digest.events:
        impact, verification, context = event.impact, event.event.verification, event.context
        with st.container(border=True):
            st.subheader(event.event.candidate.title)
            st.caption(f"Significance {event.significance_score:g}/10 · Hype {context.hype} · {event.event.candidate.category}")
            st.markdown("**Что произошло**")
            st.write(impact.what_happened)
            st.markdown("\n\n".join(evidence_lines(verification.confirmed_facts, "FACT")))
            st.markdown("\n\n".join(evidence_lines(verification.company_claims, "COMPANY CLAIM")))
            st.markdown("**Что реально изменилось**")
            st.write(context.what_changed)
            st.markdown("**Почему это важно — INFERENCE**")
            st.write(impact.why_it_matters)
            st.markdown("**Практические возможности — INFERENCE**")
            for opportunity in impact.practical_opportunities:
                st.markdown("- " + safe(opportunity))
            st.markdown("**Влияние на AI-продукты — INFERENCE**")
            st.write(impact.product_impact)
            if impact.what_to_try:
                st.info("Что попробовать: " + impact.what_to_try)
            if impact.alfa_bank_relevance:
                st.markdown("**Возможная польза для Альфа-Банка — гипотеза**")
                st.write(impact.alfa_bank_relevance)
            with st.expander("Оценки, цифры, контекст и источники"):
                st.dataframe([impact.scores.model_dump()], hide_index=True)
                st.markdown("\n\n".join(evidence_lines(context.previous_state, "Предыдущее состояние")))
                st.markdown("\n\n".join(evidence_lines(verification.key_numbers, "Ключевые цифры")))
                st.write("Hype: " + context.hype_reason)
                for limitation in context.limitations + impact.inference_limitations + verification.conflicts:
                    st.caption(limitation)
                st.markdown(f"Primary: [первоисточник](<{verification.primary_source_url}>)")
                for i, url in enumerate(verification.independent_source_urls):
                    st.markdown(f"Independent: [источник {i+1}](<{url}>)")
    st.subheader("Что изменилось в AI за анализируемый период")
    st.write(digest.market_trend)
    if digest.unconfirmed:
        st.subheader("UNCONFIRMED")
        for event in digest.unconfirmed:
            with st.container(border=True):
                st.write(event.candidate.title)
                st.caption("Потенциальная важность: " + event.candidate.potential_significance)
                st.markdown("\n\n".join(evidence_lines(event.verification.unverified_claims, "Что утверждается — не подтверждено")))
                st.write("Подтверждено наличие публикации. Само событие не установлено.")
                st.warning(event.verification.reason)
                st.caption(f"Confidence {event.verification.confidence:g}/10")
    for warning in digest.warnings:
        st.warning(warning)
    st.download_button("Скачать Markdown", render_digest(digest), file_name="ai-intelligence.md", mime="text/markdown")
    st.download_button("Скачать отчёт с подробностями", render_html(digest), file_name="ai-intelligence.html", mime="text/html")
    st.download_button("Скачать JSON", digest.model_dump_json(indent=2), file_name="ai-intelligence.json", mime="application/json")


def main():
    st.set_page_config(page_title="AI Intelligence", page_icon="◈", layout="wide")
    st.title("AI Intelligence")
    st.caption("Last 48 hours · Проверенные события и практические выводы")
    try:
        settings = Settings()
    except ValidationError:
        st.error("Ошибка конфигурации .env: проверьте типы, границы параметров и сумму весов. Секреты не отображаются.")
        return
    with st.sidebar:
        st.header("Параметры анализа")
        settings.mock_mode = st.toggle("Mock mode — без API", value=settings.mock_mode)
        settings.lookback_hours = st.selectbox("Период, часов", sorted(set([24, 48, 72, settings.lookback_hours])),
            index=sorted(set([24, 48, 72, settings.lookback_hours])).index(settings.lookback_hours))
        settings.min_significance_score = st.slider("Минимальная значимость", 0.0, 10.0, settings.min_significance_score, .5)
        settings.enable_alfa_relevance = st.checkbox("Релевантность для Альфа-Банка", value=settings.enable_alfa_relevance)
        st.caption(f"Лимиты: {settings.max_analysis_events} кандидатов · {settings.max_llm_calls} LLM-вызовов · {settings.max_search_calls} поисков")
        if not settings.mock_mode:
            st.caption("Live mode использует оплачиваемые API из .env. Цена поиска не входит в LLM cost.")
    db = Database(settings.database_path)
    if st.button("RUN ANALYSIS", type="primary"):
        st.session_state.pop("digest", None)
        with st.status("Анализ выполняется…", expanded=True) as status:
            try:
                result = run_pipeline(settings, progress=lambda msg: status.update(label=msg))
                st.session_state["digest"] = result.model_dump(mode="json")
                status.update(label="Анализ завершён", state="complete", expanded=False)
            except ProviderError as exc:
                status.update(label="Ошибка анализа", state="error")
                st.error(str(exc))
    digest_tab, debug_tab, history_tab, usage_tab = st.tabs(["Дайджест", "Debug / Pipeline data", "История", "Usage / Cost"])
    raw = st.session_state.get("digest")
    digest = FinalDigest.model_validate(raw) if raw else None
    with digest_tab:
        if digest:
            show_digest(digest)
        else:
            st.info("Запустите анализ. Mock mode показывает весь pipeline на синтетических данных без ключей.")
    with debug_tab:
        if digest:
            for i, trace in enumerate(db.traces(digest.run_id)):
                with st.expander(f"{i+1}. {trace['stage']}"):
                    st.json(trace["data"])
        else:
            st.caption("Данные появятся после запуска; неуспешные запуски доступны в истории.")
    with history_tab:
        history = db.history()
        if history:
            st.dataframe(history, hide_index=True)
            run_id = st.selectbox("Сохранённый запуск", [r["id"] for r in history])
            if st.button("Открыть запуск"):
                stored = db.load(run_id)
                if stored:
                    st.session_state["digest"] = stored
                    st.rerun()
                else:
                    st.warning("Запуск не завершён. Промежуточные данные сохранены ниже.")
            with st.expander("Данные выбранного запуска, включая ошибки"):
                st.json(db.traces(run_id))
        else:
            st.caption("История пуста.")
    with usage_tab:
        if digest:
            st.json(usage_totals(digest.usage))
            st.dataframe([u.model_dump(mode="json") for u in digest.usage], hide_index=True)
        st.caption("Стоимость — оценка по MODEL_PRICES (USD за миллион токенов). Неизвестная цена не означает нулевую стоимость. Search API оплачивается отдельно.")
