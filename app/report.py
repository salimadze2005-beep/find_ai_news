"""Reader-facing Russian reports; raw evidence and stored analysis remain untouched."""
import html as html_lib
import re
from pathlib import Path
from urllib.parse import urlsplit
from app.render import safe, usage_totals
from app.search.pages import valid_url


LABELS = r"(?:FACT|ФАКТ|INFERENCE|ИНФЕРЕНЦИЯ|COMPANY CLAIM|ЗАЯВЛЕНИЕ КОМПАНИИ|ГИПОТЕЗА)"
DIAGNOSTICS = {
    "No fetched primary source": "Не удалось получить первоисточник",
    "Insufficient distinct publishers": "Недостаточно независимых источников",
    "Facts lack primary and independent supporting evidence": "Для фактов не хватает подтверждения первоисточником и независимой публикацией",
    "Event date lacks fresh metadata or an exact dated page quote": "Дата события не подтверждена метаданными или точной цитатой",
    "Event date outside analysis window or unknown": "Дата события неизвестна или выходит за выбранный период",
    "Primary source is stale or lacks exact event-date evidence": "Первоисточник не подтверждает событие в выбранном периоде",
    "No fresh independent publication inside the window": "Нет независимой публикации за выбранный период",
    "Historical comparison omitted where its citations could not be validated.": "Часть исторического сравнения исключена: цитаты не удалось подтвердить.",
    "Discovery found no candidates. This is insufficient search evidence, not proof that no AI news occurred.": "Поиск не нашёл подходящих событий. Данных недостаточно, чтобы утверждать, что новостей не было.",
}


def reader_text(value, labelled=False):
    text = str(value).strip()
    if labelled:
        text = re.sub(rf"^{LABELS}\s*:\s*", "", text, flags=re.I)
        if text and re.match("[а-яё]", text[0]):
            text = text[0].upper() + text[1:]
    text = re.sub(r"\b(?:INFERENCE|ИНФЕРЕНЦИЯ)\s*:\s*", "Наш вывод: ", text, flags=re.I)
    text = re.sub(r"\b(?:COMPANY CLAIM|ЗАЯВЛЕНИЕ КОМПАНИИ)\s*:\s*", "По заявлению компании: ", text, flags=re.I)
    text = re.sub(r"\b(?:FACT|ФАКТ)\s*:\s*", "", text, flags=re.I)
    for old, new in DIAGNOSTICS.items():
        text = text.replace(old, new)
    text = text.replace("fetched первичного", "загруженного первичного")
    text = text.replace("occurred_at оставлено null", "дата события не указана")
    text = text.replace("verified=false", "событие не подтверждено")
    text = text.replace("Page HTTP", "код ответа страницы")
    text = text.replace("hundreds of thousands", "сотни тысяч")
    text = re.sub(r"\b(\d+)-month\b", r"\1 месяцев", text)
    text = re.sub(r"\b(\d+) seconds\b", r"\1 секунд", text)
    return text


def number(value):
    return f"{value:g}".replace(".", ",")


class Writer:
    def __init__(self, html):
        self.html = html
        self.lines = []

    def text(self, value, labelled=False):
        value = reader_text(value, labelled)
        return html_lib.escape(value) if self.html else safe(value)

    def heading(self, value, level=3):
        text = self.text(value)
        self.lines.append(f"<h{level}>{text}</h{level}>" if self.html else "#" * level + " " + text)

    def paragraph(self, value, labelled=False):
        # Short paragraphs, without summarizing or discarding factual qualifiers.
        sentences = re.split(r"(?<=[.!?])\s+(?=[А-ЯЁA-Z])", reader_text(value, labelled))
        for offset in range(0, len(sentences), 2):
            text = self.text(" ".join(sentences[offset:offset + 2]))
            if text:
                self.lines.append(f"<p>{text}</p>" if self.html else text)

    def bullets(self, values, labelled=False):
        values = list(dict.fromkeys(v for v in values if v))
        if not values:
            return
        items = [self.text(v, labelled) for v in values]
        self.lines.append("<ul>" + "".join(f"<li>{v}</li>" for v in items) + "</ul>" if self.html
                          else "\n".join("- " + v for v in items))

    def link(self, url):
        if not valid_url(url):
            return self.text("Ссылка недоступна")
        label = self.text((urlsplit(url).hostname or "Источник").removeprefix("www."))
        return f'<a href="{html_lib.escape(url, quote=True)}" rel="noreferrer">{label}</a>' if self.html else f"[{label}](<{url}>)"

    def evidence(self, items):
        lines = []
        for item in items:
            refs = " · ".join(self.link(url) for url in dict.fromkeys(item.source_urls))
            lines.append(self.text(item.text, labelled=True) + " — " + refs)
        if lines:
            self.lines.append("<ul>" + "".join(f"<li>{v}</li>" for v in lines) + "</ul>" if self.html
                              else "\n".join("- " + v for v in lines))

    def details(self, title):
        # summary is HTML in both formats; escape as HTML even in Markdown.
        self.lines.append("<details>\n<summary>" + html_lib.escape(title) + "</summary>\n")

    def end_details(self):
        self.lines.append("\n</details>")

    def card(self):
        self.lines.append('<article class="news-card">' if self.html else "---")

    def end_card(self):
        if self.html:
            self.lines.append("</article>")

    def ratings(self, significance, confidence, confirmed=True):
        status = "Подтверждено" if confirmed else "Пока не подтверждено"
        importance = "Значимость" if confirmed else "Предварительная значимость"
        text = f"{importance}: {number(significance)}/10 · Достоверность: {number(confidence)}/10 · {status}"
        self.lines.append(f'<p class="ratings">{self.text(text)}</p>' if self.html else f"**{self.text(text)}**")

    def source(self, label, url):
        text = self.text(label) + ": " + self.link(url)
        self.lines.append(f"<p>{text}</p>" if self.html else "- " + text)


def render_report(digest, html=False):
    w = Writer(html)
    hours = (digest.window_end - digest.window_start).total_seconds() / 3600
    w.heading(f"Новости ИИ · последние {number(hours)} часов", 1)
    w.paragraph(f"{digest.window_start:%d.%m.%Y, %H:%M} — {digest.window_end:%d.%m.%Y, %H:%M} (UTC)")
    if digest.mock:
        w.paragraph("Демонстрационный отчёт. События вымышлены; это не реальные новости.")
    w.paragraph(f"Подтверждённых новостей: {len(digest.events)}. Требуют проверки: {len(digest.unconfirmed)}.")
    introduction = re.split(r"(?<=[.!?])\s+(?=[А-ЯЁA-Z])", digest.summary, maxsplit=1)
    w.paragraph(introduction[0])
    if len(introduction) > 1:
        w.details("Контекст выпуска")
        w.paragraph(introduction[1])
        w.end_details()
    for index, event in enumerate(digest.events, 1):
        v, c, i = event.event.verification, event.context, event.impact
        w.card()
        w.heading(f"{index}. {event.event.candidate.title}", 2)
        w.ratings(event.significance_score, i.scores.confidence)
        w.paragraph(v.confirmed_facts[0].text if v.confirmed_facts else i.what_happened, labelled=True)
        w.details("Что произошло")
        w.paragraph(i.what_happened, labelled=True)
        for title, items in [("Подтверждено источниками", v.confirmed_facts),
                             ("По заявлению компании", v.company_claims),
                             ("Подтверждённые цифры", [x for x in v.key_numbers if x.status == "FACT"]),
                             ("Цифры со слов компании", [x for x in v.key_numbers if x.status == "COMPANY CLAIM"])]:
            if items:
                w.heading(title, 4)
                w.evidence(items)
        w.end_details()
        w.details("Почему важно")
        w.paragraph(i.why_it_matters, labelled=True)
        w.heading("Что изменилось", 4)
        w.paragraph(c.what_changed)
        if c.previous_state:
            w.heading("Что было раньше", 4)
            w.evidence(c.previous_state)
        w.paragraph(c.hype_reason)
        names = {"importance": "Важность", "novelty": "Новизна", "practicality": "Применимость", "impact": "Влияние", "confidence": "Достоверность"}
        w.bullets([f"{names[k]}: {number(value)}/10" for k, value in i.scores.model_dump().items()])
        w.end_details()
        w.details("Как применить")
        w.bullets(i.practical_opportunities, labelled=True)
        if i.what_to_try:
            w.heading("С чего начать", 4)
            w.paragraph(i.what_to_try, labelled=True)
        w.heading("Для продуктовой команды", 4)
        w.paragraph(i.product_impact, labelled=True)
        if i.alfa_bank_relevance:
            w.heading("Возможная польза для Альфа-Банка", 4)
            w.paragraph(i.alfa_bank_relevance, labelled=True)
        w.end_details()
        w.details("Ограничения")
        w.bullets(i.inference_limitations + c.limitations + v.conflicts, labelled=True)
        w.end_details()
        w.details("Источники")
        w.source("Первоисточник", v.primary_source_url)
        for url in dict.fromkeys(v.independent_source_urls):
            w.source("Независимая публикация", url)
        w.end_details()
        w.end_card()
    w.heading("Общая картина", 2)
    w.paragraph(digest.market_trend)
    if digest.unconfirmed:
        w.heading("Требует проверки", 2)
        w.paragraph("Об этих событиях пишут, но подтверждений пока недостаточно. Они не входят в список подтверждённых новостей.")
        for event in digest.unconfirmed:
            v = event.verification
            w.card()
            w.heading(event.candidate.title)
            w.ratings(event.candidate.potential_significance_score, v.confidence, confirmed=False)
            w.details("Что известно и чего не хватает")
            w.evidence(v.unverified_claims)
            w.heading("Почему пока не подтверждено", 4)
            w.paragraph(v.reason)
            w.heading("Почему следим за темой", 4)
            w.paragraph(event.candidate.potential_significance, labelled=True)
            w.end_details()
            w.end_card()
    if digest.warnings:
        w.heading("Ограничения этого отчёта", 2)
        for warning in digest.warnings:
            text = reader_text(warning)
            w.paragraph(text if re.search("[А-Яа-я]", text) else
                "Часть данных не удалось полностью обработать или проверить. Подробная диагностика сохранена в истории запуска.")
    totals = usage_totals(digest.usage)
    w.details("О подготовке отчёта")
    w.paragraph("Значимость показывает возможное влияние события, достоверность — насколько хорошо оно подтверждено. Обе оценки выставлены по шкале от 0 до 10; это редакционные оценки, а не вероятность в процентах.")
    w.bullets([f"Вызовов модели: {totals['calls']}",
               f"Учтено токенов: {totals['total_tokens']:,}".replace(",", " ")])
    if totals["unknown_cost_calls"]:
        w.paragraph("Полная стоимость неизвестна: для части вызовов не задана цена.")
    else:
        w.paragraph(f"Расчётная стоимость вызовов модели: {totals['known_cost']:.6f} USD.")
    if totals["unknown_usage_calls"]:
        w.paragraph(f"Вызовов без сведений о токенах: {totals['unknown_usage_calls']}. Общий расход может быть выше указанного.")
    w.paragraph("Расходы на поиск оплачиваются отдельно и здесь не учтены.")
    w.end_details()
    body = "\n\n".join(w.lines) + "\n"
    if not html:
        return body
    css = Path(__file__).with_name("report.css").read_text(encoding="utf-8")
    return ('<!doctype html>\n<html lang="ru"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Новости ИИ — отчёт</title><style>' + css + '</style></head><body><main>'
            + body + '</main><footer>Новости ИИ · обзор источников и практических выводов</footer></body></html>')
