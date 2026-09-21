# Project status

## Current snapshot — implementation complete, delivery in progress
All nine implementation stages are complete. The repository contains five research roles,
seven editable prompts plus shared rules, typed evidence, bounded Tavily/AgentRouter-compatible
adapters, strict date/source gates, semantic deduplication, configurable scoring, SQLite history,
analysis reuse, CLI, Streamlit dashboard, usage/cost reporting and offline synthetic mode.
Final stage changed README.md and added recovery instructions/CI in the preceding checkpoint.

Verified: 41 tests pass (unit, HTTP contracts, adversarial integration, full mock pipeline,
cache reuse and Streamlit RUN ANALYSIS via AppTest); no failing tests. `pip check` and
compileall pass. README CLI writes Markdown/JSON; actual Streamlit root and health endpoint
return HTTP 200. Secret-pattern audit passes; .env is ignored and untracked, as are .venv
and data. Original repository license/history preserved, incremental commits on main.

Next concrete step: final diff review/commit and push main to existing origin; confirm remote SHA.
Remaining required work: GitHub delivery only. Live API evaluation is a follow-up requiring keys,
not claimed as tested. Current environment has no configured live API keys.

Known limitations to preserve in reporting: HTML only, conservative publication metadata/date-only
handling, snippets/page text caps, LLM-dependent semantic entailment and editorial independence,
no hidden retries, LLM cost excludes search and special cached-token tariffs, six-hour analysis
reuse may delay contextual refresh. Aborted process leaves a running row with preserved traces.
Numeric token checks are conservative and reject unsourced derived percentages/unit rewrites.

Decisions not to change casually: re-verify facts on each run; cache only expensive analysis;
keep mock explicit and never silently fall back from live; never fill a digest to meet a quota;
keep credentials and local databases outside Git; preserve FACT/CLAIM/INFERENCE separation.

## Checkpoint history (earlier states below are historical)

## Requirements and recovery
See SPEC.md for the complete original brief. Before continuing: inspect files, this file,
TODO.md, README.md, git status/log/diff, then run `.venv/Scripts/python -m pytest`.
Never replace working architecture without recording why.

## Architecture decisions
- Python, Pydantic v2, synchronous bounded pipeline with five independent AI roles.
- Replaceable SearchProvider and LLMProvider; Tavily and configurable AgentRouter-compatible HTTP adapter.
- SQLite stores runs, intermediate evidence, URLs and reusable analyses; no sensitive DB in git.
- Strict UTC time window; unknown dates cannot enter confirmed digest. Historical research is separate.
- FACT / COMPANY CLAIM / INFERENCE separation; source-backed numbers; deterministic scoring and rendering.
- Mock mode must exercise the same orchestration without network or API charges.
- Model IDs and prices are configuration, never assumed current.

## Implemented
Foundation: configuration with validated weights/bounds, typed domain models, SQLite storage, CLI bootstrap.
Created app/config.py, app/models.py, app/storage.py, app/run.py, tests/test_foundation.py,
requirements.txt, pyproject.toml and .gitignore. Remote origin points to the requested repository;
existing Apache license/history preserved.

## Verification
Foundation: 4 tests passed; CLI bootstrap successfully initializes SQLite. Dependencies installed in .venv. No failing tests.

## Foundation stage / next action at that checkpoint
Stage 1 completed and checked. Stage 2 in progress: providers exist in working tree; next add HTTP contract tests and mock fixtures.

## Known limitations
Agents and UI are not implemented yet; bootstrap CLI only initializes storage.
Live API end-to-end testing requires user-supplied credentials and available models.

## Remaining
See TODO.md. Each major checkpoint must include tests, status updates, diff review and a commit.


## Checkpoint 2 — providers
Implemented LLMProvider/AgentRouterProvider, Tavily SearchProvider, public HTML retrieval, publication metadata and UTC filtering. Files: app/llm/*, app/search/*, tests/test_providers.py. Eleven tests pass, including mocked HTTP contracts, usage/cost, error sanitization, old/unknown dates and URL checks. No live paid calls made. Next: Scout, deduplication and mock providers. JSON object mode is default for gateway compatibility; schema mode is opt-in. Page text is capped at 6000 characters; HTML only. Date-only boundary cases are conservatively rejected.

## Checkpoint 3 — discovery
Scout dynamically generates queries, validates source URLs and extracts structured candidates. Hybrid title/entity/time and LLM semantic dedup preserves action types. Synthetic providers cover pricing, tools, rumor and stale articles; no mock network access. Added app/agents/common.py, scout.py, app/pipeline/deduplication.py, app/mock.py, prompts and tests/test_scout.py. All 15 tests pass. Next: verification gates, context and impact analysis.

## Checkpoint 4 — verification
Implemented separate Verifier prompt/module, supplementary research, fetched quotation checks, distinct-publisher gates, primary and independent factual evidence, event/publication date checks, explicit claims and conflicts. Added tests/test_verifier.py. All 19 tests pass; no failing tests. Next: historical context, hype and impact scoring. Editorial independence/semantic entailment still depend on the LLM; deterministic checks cannot prove those.

## Checkpoint 5 — context
Context Analyst performs separate historical research, validates baseline quotations and reports relative change, hype and limitations. Files: app/agents/context_analyst.py, prompts/context_analyst.md, tests/test_context.py. Next: configurable scoring and practical impact. Live comparative quality remains unmeasured without credentials.
Checkpoint 5 validation: all 20 tests passed; no failing tests.

## Checkpoint 6 — impact
Impact Analyst now produces practical opportunities, product hypotheses, concrete experiments and optional Alfa relevance. Deterministic weighted score and confidence capped by verification. Added app/agents/impact_analyst.py, app/pipeline/scoring.py, impact prompt and tests/test_scoring.py. Fixed a Pydantic deprecated model_fields access. Next: Editor, full orchestration and CLI.
Checkpoint 6: 22 tests passed without warnings; no known failing tests.

## Checkpoint 7 — complete pipeline
Editor selects IDs only and cannot alter evidence or scores. Deterministic Russian Markdown renderer includes facts/claims/inferences, figures, sources, limitations, optional unconfirmed and usage totals. Orchestrator persists traces, failures, sources and analyses; bounded per-event failures produce warnings. Rechecks verification every run, reuses context/impact for identical evidence/settings/prompts in a six-hour bucket. CLI supports --mock, --output and --json. Changed app/models.py, app/mock.py, scout prompt/schema; added editor, orchestrator, render and pipeline tests. All 24 tests pass. CLI generated data/demo.md and data/demo.json (ignored). Next: Streamlit dashboard and final robustness review. Analysis cache is deliberately conservative; live search costs are not included in LLM cost totals.

## Checkpoint 8 — UI
Streamlit dashboard has run control, mock/live choice, threshold/time settings, event cards, evidence, scores, unconfirmed, downloads, history, debug traces and per-call usage. Files: app.py, app/ui.py, .streamlit/config.toml, tests/test_ui.py. All 25 tests pass, including clicking RUN ANALYSIS with AppTest. Fixed AppTest path handling for installed Streamlit. Next: adversarial integration tests, documentation, security/secret audit and push.

## Hardening checkpoint
Added adversarial regression coverage for unknown/future/conflicting dates, each citation quotation, fabricated numbers, private redirects, DNS pinning, cache invalidation, missing keys, partial failures, invented editor IDs, token budgets and offline mock. Numeric evidence has FACT/COMPANY CLAIM status; downstream prose cannot introduce numeric tokens absent from cited evidence. Changed evidence/schema/prompts and page fetcher. Editorial exclusions changed from open dict to typed list so strict JSON Schema mode is supported. Added AGENTS.md recovery instructions and GitHub Actions. pip check passes; no live API credentials configured. Next: README, final CLI/server smoke, audit and push.
Hardening validation: all 41 tests pass; no failing tests.

Final page transport detail: validated public IP is pinned with original TLS SNI/Host; keepalive disabled to prevent certificate reuse across hostnames sharing an IP. Targeted provider/regression suite: 23 tests pass after this change.
Real public HTTPS page fetch via pinned transport succeeded (python.org); no paid API involved.
