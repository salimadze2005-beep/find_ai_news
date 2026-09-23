# Project status

## Retest checkpoint — 2026-09-23

Recovered from clean ed2a91e; inspected structure, status/checklist/README, history and both
diffs. All 51 tests pass (14.12 seconds). No application/configuration changes this checkpoint.
All roles still use openrouter/free, live mode and json_schema.

Bounded current-news run (data/free-retest-2026-09-23.json/.sqlite3): queries succeeded,
actual routed model nvidia/nemotron-3-ultra-550b-a55b:free, finish_reason=stop. All three
Tavily searches returned no results. No candidates or downstream LLM calls; zero warnings.
One LLM call, 845 tokens, provider-reported cost zero. This is not end-to-end acceptance.

Curated real-source run e484515e-a8ce-4657-ba92-40f5ab5e7a16
(data/free-retest-curated-2026-09-23.json/.sqlite3): Scout produced two candidates.
Qwen Verifier failed schema validation; xAI was rejected for insufficient independent
evidence/date support. Zero confirmed events, one warning, five calls, 30,541 tokens,
configured LLM cost zero. Old corpus uses current run time; it is not a historical replay.
Total retest usage: 31,386 tokens. Tavily cost is separate.

Still unfinished: reliable real run through Context/Impact/Editor. Next concrete step remains
safe diagnosis of Verifier schema errors and bounded response repair; do not relax evidence
gates or silently use paid models. Updated only this status file and TODO.md.

## Latest checkpoint — free OpenRouter routing, 2026-09-22

User requested free models for every role. Public OpenRouter `/api/v1/models` lists
`openrouter/free` at zero input/output prices; `z-ai/glm-5.3-flash:free` is absent.
Updated ignored local `.env`: LLM_MODEL and all five role overrides are `openrouter/free`,
OpenRouter base URL, MOCK_MODE=false, LLM_RESPONSE_FORMAT=json_schema, zero model prices.
Queries and deduplication inherit Scout's free model. Keys were preserved and never printed.
Tracked changes: README.md, PROJECT_STATUS.md, TODO.md only; application code unchanged.

Recovery: clean starting tree at b9020c0; read status/checklist/README, git history/diffs;
51 tests passed before configuration and all 51 passed afterwards (11.61 seconds).
`.env` remains ignored and untracked; git diff --check passes.

Live results (not a successful nonempty digest):
- json_object attempt failed schema validation at query generation.
- json_schema curated public-source run 8ae8e862-4047-4df7-8956-40c69a61a87f:
  5 calls, 32,926 tokens, $0 configured LLM cost; 0 events, one ValidationError warning.
  Reports/traces: ignored data/free-router-schema-check.json and .sqlite3.
- Tavily access recovered: one probe returned two results, then three real discovery searches worked.
- Ordinary bounded live run: 3 LLM calls, 21,280 tokens, $0 configured LLM cost; Scout
  extracted one candidate, Verifier returned incomplete/refused output. No event reached
  Context/Impact or an actual Editor LLM call. Data: data/free-router-discovery.json/.sqlite3.

Remaining limitation: free routing is callable but output reliability is insufficient for
confirmed end-to-end acceptance. Do not call empty warning-bearing runs a successful digest.
Next step: inspect bounded output/reasoning allocation or evaluate another available free
model, then rerun all roles. Keep free-only selection unless the user requests paid models.
Search usage is separate from free LLM pricing. Previous checkpoint reports below are historical.

## Current snapshot — implementation complete; real-source hardening added
All nine implementation stages are complete. The repository contains five research roles,
seven editable prompts plus shared rules, typed evidence, bounded Tavily/AgentRouter-compatible
adapters, strict date/source gates, semantic deduplication, configurable scoring, SQLite history,
analysis reuse, CLI, Streamlit dashboard, usage/cost reporting and offline synthetic mode.
Final stage changed README.md and added recovery instructions/CI in the preceding checkpoint.

Verified before the current checkpoint: 41 tests pass (unit, HTTP contracts, adversarial integration, full mock pipeline,
cache reuse and Streamlit RUN ANALYSIS via AppTest); no failing tests. `pip check` and
compileall pass. README CLI writes Markdown/JSON; actual Streamlit root and health endpoint
return HTTP 200. Secret-pattern audit passes; .env is ignored and untracked, as are .venv
and data. Original repository license/history preserved, incremental commits on main.

Delivery before this checkpoint: implementation pushed to origin/main (3e2e271); final full
local suite at that point: 41 passed. No implementation stage remains unfinished. Live
credentials are now configured locally and remain ignored by Git. The current checkpoint below
records the real-source evaluation and remaining external quota limitation.

Known limitations to preserve in reporting: HTML only, conservative publication metadata/date-only
handling, snippets/page text caps, LLM-dependent semantic entailment and editorial independence,
no hidden retries, LLM cost excludes search and special cached-token tariffs, six-hour analysis
reuse may delay contextual refresh. Aborted process leaves a running row with preserved traces.
Numeric token checks are conservative and reject unsourced derived percentages/unit rewrites.

Decisions not to change casually: re-verify facts on each run; cache only expensive analysis;
keep mock explicit and never silently fall back from live; never fill a digest to meet a quota;
keep credentials and local databases outside Git; preserve FACT/CLAIM/INFERENCE separation.

## Real-source evaluation checkpoint — 2026-09-21

Tested the live adapters and pipeline against current public news. OpenRouter structured JSON
and usage reporting worked with `openai/gpt-4.1-mini`; the first Tavily discovery run worked,
then subsequent Tavily calls returned HTTP 403. The initial broad run consumed 65,077 tokens
across nine LLM calls and conservatively rejected stale, weakly sourced and malformed candidates.
Curated public-source runs then exercised the same Scout/Verifier/page pipeline without Tavily.
Persisted run summaries account for 306,896 OpenRouter tokens across the broad and curated
evaluations (excluding one small connectivity probe); reported provider cost remains unknown.

Qwen-Image-2.1 (official GitHub changelog dated 2026-09-20, independent PC Watch report and
fresh Pexo publication) now passes strict verification with primary plus independent verbatim
evidence. A fresh recap of Unity's September 9 release is rejected because the event itself is
outside the 48-hour window. MLPerf September 16 and a future-effective xAI pricing change are
also represented in the audit corpus as negative date cases.

Real runs exposed and fixed: missing date quotation in the Verification schema; insufficient
publication metadata selectors; overly literal punctuation/date numeric matching; combined
multi-page quotes; loss of the previous invalid JSON during Verifier retries; brittle rejection
when one evidence item or historical citation was invalid. Verifier now searches primary and
independent evidence separately, prunes invalid items, preserves the raw response for repair,
and can extract bounded verbatim core-event excerpts only from URLs already selected by the
Verifier. Context drops invalid historical citations and records the limitation instead of
discarding a verified current event.

Created `app/evaluate_sources.py`, `app/evaluate_pipeline.py` and
`evaluation/real_news_2026-09-21.json`. Substantially changed verifier/context agents, page date
parsing, schemas, prompts, settings and regression tests. Local databases and generated reports
remain ignored. No secret values were printed, committed or placed in command arguments.

Current validation: all 51 tests pass; no failing tests. The last paid run reached and passed
Verifier, then exposed the Context citation issue. After that fix, OpenRouter returned HTTP 402
at Scout because the account
quota/balance was exhausted; `openai/gpt-4.1` was also unavailable with HTTP 402. Therefore the
final Context → Impact → Editor rerun is pending external quota. Estimated cost is unavailable
because `MODEL_PRICES` is not configured; provider usage is persisted per call.

Next concrete step: restore OpenRouter quota and Tavily access, set stronger role-specific model
IDs if available, then rerun the curated command followed by the ordinary Tavily live command.
Do not weaken the date/source/evidence gates to force a non-empty digest.

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

## Delivery checkpoint
Ten incremental implementation commits pushed successfully using existing environment auth.
Working tree was clean after the implementation push; .env remains ignored/untracked.
GitHub Actions for 3e2e271 completed successfully (Python 3.11/3.12), run 35591163733.
Local verification is complete. A transient GitHub connection failure affected the first
attempt to push the final status-only commit; retrying delivery does not require code changes.
