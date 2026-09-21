# AI Intelligence

Короткий аналитический дайджест значимых изменений AI-индустрии за последние 48 часов.
Открытый web search → Scout → дедупликация → Verifier → Context Analyst → Impact Analyst → Editor.
Две полезные новости лучше десяти слабых. Нет фиксированной квоты карточек.

**По умолчанию включён offline mock mode:** синтетические события, домены `.example`,
весь pipeline и UI работают без API. Это не обзор реального рынка.

## Запуск

Python 3.11+, локально проверено на Python 3.12 / Windows. Команды из корня проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Если активация запрещена PowerShell, используйте `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
и `.\.venv\Scripts\python.exe -m streamlit run app.py`.

Linux/macOS:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Откройте [локальный интерфейс](http://localhost:8501), нажмите **RUN ANALYSIS**.
Не перезаписывайте существующий `.env`, если уже добавили ключи.

CLI и тесты:

```sh
python -m app.run
python -m app.run --mock --output data/digest.md --json data/digest.json
python -m pytest -q
```

`--mock` принудительно включает бесплатную демонстрацию. Иначе режим задаёт `MOCK_MODE`.
Ошибка live API не включает mock автоматически.

## Реальные API

В `.env` установите `MOCK_MODE=false`, заполните `TAVILY_API_KEY`, `LLM_API_KEY`,
`LLM_MODEL` и при необходимости `LLM_BASE_URL`. Ключи нужны только для live mode.
Адаптер использует HTTPS и добавляет `/chat/completions` к base URL.
Значение по умолчанию — `https://agentrouter.org/v1`; подтвердите адрес и model IDs
в кабинете своего gateway. Сервисы с названием AgentRouter могут иметь разные endpoints.
Поддерживается совместимый JSON chat-completions контракт, не нестандартные agentic APIs.

`LLM_RESPONSE_FORMAT=json_object` совместим с большинством таких gateway: схема передаётся
в prompt, ответ валидируется Pydantic. `json_schema` включает strict structured output,
если его поддерживает провайдер. Ошибки HTTP, отказ, неполный JSON и неверная схема
отображаются явно. Verifier может сделать до `VERIFIER_ATTEMPTS` ограниченных попыток;
usage каждой попытки сохраняется.

Live-проверка 21 сентября 2026 подтвердила OpenRouter structured output, Tavily search,
загрузку публичных страниц и строгий Verifier на реальном релизе Qwen-Image-2.1. После
первого поиска Tavily начал отвечать HTTP 403, а дальнейшие прогоны исчерпали доступный
лимит OpenRouter (HTTP 402), поэтому повтор всего pipeline до Editor после последних
исправлений требует доступной квоты. HTTP-контракты также проверены подставными ответами.
Контракты: [Tavily](https://github.com/tavily-ai/tavily-python/blob/master/tavily/tavily.py),
[пример совместимого Agent Router API](https://github.com/theagentrouter/agent-router/blob/main/site/docs/capabilities/llm-integrations/supported-endpoints.md).

## Структура

```text
app.py                 Streamlit entry point
app/
  config.py            настройки из .env, проверка весов/границ
  models.py            Pydantic: sources, events, evidence, scores, digest, usage
  run.py               CLI
  mock.py              синтетические LLM/search/page providers
  agents/              отдельные модули пяти ролей
  llm/                 LLMProvider + AgentRouterProvider
  search/              SearchProvider + Tavily + загрузка HTML
  pipeline/            orchestration, deduplication, scoring
  storage.py           SQLite repository
  render.py            Markdown и суммарный usage
  ui.py                карточки, debug, история, экспорт
prompts/               отдельные Markdown prompts всех ролей
tests/                 unit, HTTP contracts, integration, Streamlit AppTest
.github/workflows/     CI: Python 3.11 и 3.12
SPEC.md                исходное ТЗ
AGENTS.md              правила восстановления и checkpoints
PROJECT_STATUS.md      фактический статус и проверки
TODO.md                актуальный checklist
```

## Проверка событий

Scout генерирует разные запросы и работает с короткими snippets. Дедупликация использует
заголовки, сущности, тип действия, время и отдельный семантический вызов. Релиз,
benchmark и pricing не склеиваются только по компании.

Verifier дополнительно ищет источники и получает страницы. Нужны первоисточник,
независимый издатель, подтверждающие цитаты и свежая дата события/публикации.
FACT, COMPANY CLAIM и INFERENCE разделены. Цифры имеют цитаты, ссылки и статус.
Слухи допускаются лишь в отдельный UNCONFIRMED, если есть свежая атрибутируемая
публикация и потенциальная значимость. Причины отказов видны в debug.

Context Analyst ищет прошлое состояние и конкурентов; исторические источники разрешены
только для контекста. Impact Analyst даёт условные продуктовые выводы и конкретные
эксперименты. Код считает significance по весам; confidence ограничен оценкой Verifier.
Editor получает компактные проверенные результаты, выбирает IDs и пишет summary/trend.
Он не делает research и не меняет доказательства или оценки.

## Сравнение качества и расхода

| Параметр | По умолчанию | Назначение |
|---|---:|---|
| LOOKBACK_HOURS | 48 | Строгий UTC-интервал |
| MIN_SIGNIFICANCE_SCORE | 6.5 | Порог полезности |
| MAX_SCOUT_RESULTS | 30 | Лимит результатов и кандидатов |
| SEARCH_QUERIES_COUNT | 8 | Разнообразие поисковых направлений |
| MAX_ANALYSIS_EVENTS | 12 | Максимум анализируемых кандидатов |
| VERIFY_SOURCES_MIN / TARGET | 2 / 3 | Минимум издателей / цель research |
| VERIFIER_ATTEMPTS | 2 | Ограниченные исправления невалидного evidence JSON |
| SCORING_WEIGHTS | .30/.25/.20/.15/.10 | Importance / Impact / Practicality / Novelty / Confidence |
| MAX_LLM_CALLS / MAX_SEARCH_CALLS | 80 / 80 | Жёсткие лимиты вызовов |
| MAX_PAGE_FETCHES | 80 | Лимит загрузок страниц |
| MAX_INPUT_CHARS | 70000 | Предельный JSON input одного вызова |
| LLM_MAX_OUTPUT_TOKENS | 6000 | Предельная длина ответа |
| ENABLE_ALFA_RELEVANCE | false | Только естественные продуктовые гипотезы |

Для экономии задайте дешёвые `SCOUT_MODEL` и `VERIFIER_MODEL`, более сильные
`CONTEXT_MODEL` и `IMPACT_MODEL`, качественный `EDITOR_MODEL`. Пустые значения
используют `LLM_MODEL`. Конкретные model IDs зависят от вашего провайдера.

`MODEL_PRICES` — JSON вида `{"your-model":{"input":0.1,"output":0.4}}`, USD за миллион
токенов. Это пример формата, не текущий прайс. Сохраняются роль, модель, timestamp,
duration, input/output/total tokens, успех и estimated cost. Цена вычисляется только
при наличии usage и настроенных тарифов; неизвестная стоимость отмечается отдельно.
Специальные тарифы cached tokens не выделяются. **Стоимость поиска не входит в LLM cost.**
Ограничения числа вызовов не являются точным денежным бюджетом.

Для воспроизводимого аудита реальных страниц без поискового API:

```sh
python -m app.evaluate_sources evaluation/real_news_2026-09-21.json --output data/real-source-audit.json
```

Для полного pipeline с реальным LLM и зафиксированным публичным набором URL (без Tavily):

```sh
python -m app.evaluate_pipeline evaluation/real_news_2026-09-21.json --output-prefix data/curated-live
```

Опция `--analysis-model MODEL_ID` направляет Verifier, Context, Impact и Editor в более
сильную модель, оставляя Scout на дешёвой модели из `.env`.

## Хранение и восстановление

SQLite: `data/intelligence.sqlite3`. Хранит URL, evidence, результаты этапов, отказы,
usage, историю и кэш анализа. Ключи и сырые HTTP error bodies не записываются.
`data/`, базы, `.env`, `.venv` и caches исключены из Git.

Проверка фактов выполняется каждый запуск. Неизменившийся context/impact переиспользуется
внутри шестичасового интервала; prompts, модели, evidence, веса и Alfa-настройка входят
в ключ кэша. Частичный сбой сохраняет другие результаты с предупреждением. Ошибка
Scout/Editor завершает run с ошибкой; промежуточные данные доступны в истории.
При жёстком завершении процесса run может остаться `running`: новый запуск использует
готовый кэш, но не продолжает отдельный оборванный HTTP-запрос.

После прерывания **разработки** следуйте AGENTS.md: структура, PROJECT_STATUS.md,
TODO.md, README.md, git status/log/diff, тесты, затем первый незавершённый шаг.
Не переписывайте работающие части без зафиксированной причины.

## Ограничения и дальнейшее улучшение качества

- Публичный HTML: нет авторизации, обхода paywall, JS rendering или PDF extraction.
  Таймауты, блокировки и недоступные страницы снижают recall.
- Дата — publication metadata, не snippet/dateModified. Неизвестная timezone не угадывается.
  Date-only без timezone обычно не проходит строгую проверку 48 часов из-за неопределённости.
- Независимость редакций, точность даты события и соответствие цитаты смыслу зависят
  от LLM. Проверки URL, цитат и numeric tokens не доказывают все выводы. Пересчитанный
  процент или иное написание числа может быть консервативно отклонено.
- Текст страницы ограничен 6000 символами. Семантическая дедупликация может ошибаться;
  debug позволяет исследовать пропуски и объединения.
- Mock-тесты не измеряют качество реальных новостей. CI не требует ключей.
- Локальный MVP без многопользовательской авторизации; debug-база не предназначена
  для публичного общего доступа.

Приоритеты развития: размеченный evaluation corpus реальных событий, factual entailment,
независимость издателей, извлечение дат из большего числа форматов, поисковое покрытие
и измеряемое сравнение моделей/prompts. Усложнение инфраструктуры вторично.
