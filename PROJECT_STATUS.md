# Project status

## Russian reader report — 2026-09-25

Implemented the user's confirmed presentation choices: report only, concise news cards with
expandable details, plain Russian, immediately visible significance and reliability scores,
and calm minimal styling. Every confirmed news item has the five requested sections:
what happened, why it matters, practical use, limitations and sources. Company claims and
supported facts remain distinguishable using Russian wording. Removed reader-facing
INFERENCE/FACT/COMPANY CLAIM headings and replaced inference labels with natural language.
Detailed evidence, historical comparisons and usage stay available in expandable blocks.
Unknown cost is explicitly unknown rather than a misleading zero price.

Added app/report.py and app/report.css: shared content structure produces Markdown and a
self-contained HTML file using native details/summary (no JavaScript, CDN or API required).
Added CLI --html and --from-json so saved runs can be reformatted without any paid calls.
app/ui.py only adds the HTML download action; dashboard news cards/layout are unchanged.
Updated app/render.py, app/run.py, prompts/common.md, prompts/impact_analyst.md and README.
Original JSON, quotes, evidence, scores, source URLs and verification gates are unchanged.
The report cleans legacy status labels when displaying historical runs; prompts request
short, natural Russian for future analyses. Established technical/product names remain.

Verified: regenerated the actual accepted live report into ignored
data/current-news-readable.html and .md, opened it in a browser, inspected both collapsed
and expanded cards and working source links. This formatting work made no paid LLM calls.
All 80 tests pass, including HTML/script/link escaping, visible ratings, five-section layout,
unchanged evidence, unknown-cost wording and offline saved-JSON export; no failing tests.
Markdown details depend on the viewer, so standalone HTML is the recommended reading format.
Old stored wording is preserved apart from display-label cleanup; future prose follows the
new style prompts. Presentation stage complete. Next optional step: user review of the HTML
report; broader research-quality follow-ups remain below. Preserve source/evidence separation.

## Current-news acceptance passed — 2026-09-25

Ordinary live discovery using 9Router cx/gpt-5.6-sol and Tavily completed for the real UTC
window 2026-09-23T07:57:40Z through 2026-09-25T07:57:40Z: 59 raw hits, 30 unique retained,
8 candidates, 6 evaluated under the diagnostic cap, 1 confirmed event and 2 unconfirmed,
zero final warnings. All five roles ran on real data. Amazon's Selling Partner plugin for
Quick/Claude passed primary plus independent evidence, Context, Impact and Editor; score 6.7.
Amazon's dated primary announcement is 2026-09-23T13:00:08.829Z, with fresh GeekWire reporting.
Old Nvidia/GPN-Star events, uncertain Google coverage and unestablished event dates were
rejected rather than silently included. One malformed Verifier response recovered via the
existing bounded structured-output retry.

This acceptance run used 15 LLM calls and 162,187 reported tokens. All calls have usage;
prices are unconfigured, so cost is unknown. Reports/traces remain in ignored
data/current-news-acceptance.{md,json,sqlite3}. Appended this genuine live run and its traces
to the normal application database so it is visible in run history; previous runs preserved.
Added non-secret evaluation/current_news_acceptance_2026-09-25.json with counts, times,
source URLs and usage. Default application settings remain 48 hours, 8 queries, 30 results,
12 analysis candidates and the user's cx/gpt-5.6-sol model. Diagnostic caps did not alter .env.

Final refinements: Scout search_subject includes the distinguishing platform/update, not
just the old product name; verifier treats it as search keywords instead of an exact quoted
phrase. Full English calendar dates with explicit years now normalize consistently with
Russian/ISO evidence, avoiding false numeric/date rejection; absent years remain unknown.
Analytical repair feedback identifies the exact unsupported numeric/date tokens without
logging source prose. Changes: scout/verifier/context/impact/editor, prompts/scout.md,
prompts/verifier.md, tests/test_providers.py, this file, TODO.md and acceptance artifact.

Validation: all 76 tests pass; meaningful tests cover retrieval fallback/budget, fair allocation,
unfiltered primary lookup, unrelated timestamps, multilingual full dates and bounded
Context/Impact/Editor repair. Mock README CLI succeeds; pip check succeeds; actual Streamlit
health responds HTTP 200. No known failing tests. .env remains ignored/untracked.
Current implementation stage is complete. Next concrete optional step: measure recall and
editorial independence against a labelled multi-day corpus; do not infer exhaustive market
coverage from one successful run. External publisher blocking and LLM quality remain
limitations. Preserve strict evidence/date gates and the selected gateway/model.

## Search and evidence recovery fixes — 2026-09-25 (live acceptance in progress)

Recovered clean b0ecb84; all original 68 tests passed. Diagnosed actual stored queries:
Russian date-prefixed multi-topic keyword lists returned one broad Reddit result. Short
English news-topic queries produced relevant current stories. Changed query prompt to one
topic/vendor, English, no inline dates. Scout now uses SearchProvider.discover (default
delegates to search); Tavily uses news first and a bounded seven-day general fallback only
when sparse. Final confirmation still uses the exact requested window. Round-robin result
selection prevents early queries exhausting the global result cap. Discovery summary is
persisted; empty discovery gets an explicit insufficient-evidence warning.

First current-data trial: 54 search hits, 30 unique retained, 7 candidates; top 3 evaluated,
0 confirmed and 2 unconfirmed. This exposed further concrete retrieval bugs: verifier used
the broad vendor entity, and date filters hid undated primary documentation. Added optional
search_subject to discovery/candidate models, used for targeted verification/context. Primary
lookups no longer apply search-index date filters; fetched evidence is still date-checked.
Real A/B lookup recovered GPN-Star Nature/GitHub and UiPath's primary Cartographer announcement.

Page parser included related-card time tags in publication metadata, making TechCrunch dates
unknown. Prefer publication metadata, use article-scoped time tags only as fallback; conflicting
publication metadata still fails closed. Real TechCrunch page now resolves to
2026-09-24T19:00:42Z. Context, Impact and Editor now have one bounded domain-validation repair
with concrete feedback, preserving numeric/evidence gates and provider call budgets.

Changed app/search/{base,provider,pages}.py, scout/verifier/context/impact/editor/common agents,
models.py, orchestrator.py, query/scout prompts, provider/scout tests and new analysis-repair
tests. All 75 tests pass; no failing tests. Next concrete step: repeat ordinary current-data
pipeline with the combined fixes and examine every accepted event and trace. Full live
acceptance remains unfinished; do not claim a nonempty verified digest yet. Artifacts under
ignored data/ include search-diagnosis.json, current-news-fix.*, techcrunch-diagnosis.html.
Keep the existing five-role architecture, chosen cx/gpt-5.6-sol model, secrets in ignored .env,
strict dates, independent evidence, numerical gates and paid-call bounds.

## Authenticated 9Router test — 2026-09-25

The user provided a local 9Router API key in ignored `.env`. Validated without printing or
committing it: a direct `cx/gpt-5.6-sol` chat request returned HTTP 200 and `OK` (provider
reported 2,495 tokens); a strict `json_schema` call through `AgentRouterProvider` returned
valid Pydantic output with 77 tokens. Updated only ignored `.env` to use
`http://127.0.0.1:20128/v1`, `cx/gpt-5.6-sol` for `LLM_MODEL` and all five role overrides,
`MOCK_MODE=false` and `LLM_RESPONSE_FORMAT=json_schema`. Existing Tavily key was preserved.
The gateway reports actual model `gpt-5.6-sol` and usage for every completed call. Individual
structured probes succeeded for Impact Analyst and Editor (77 tokens each).

Bounded fresh-news run (8 LLM calls / 6 searches / 12 pages maximum): Tavily was reachable
when the process had network access; three searches returned one broad Reddit timeline and
no qualifying candidates. Queries and Scout succeeded through 9Router (1,534 tokens total),
zero events, zero warnings. Files are ignored under `data/9router-live.*`. An earlier run in
the restricted network sandbox failed on Tavily connection; a direct Tavily probe with
network access returned HTTP 200. These are environment-access differences, not an
application auth failure.

Bounded historical real-source replay of the 2026-09-21 Qwen corpus: Queries, Scout,
Verifier and Context Analyst made four successful 9Router calls, 22,453 tokens total.
Verifier accepted the candidate; Context added a number absent from its cited evidence,
so the deterministic evidence guard rejected it. Final digest has zero confirmed events
and one warning. The guarded rejection is correct; Context answer quality is a remaining
limitation. Impact and Editor were separately confirmed callable, but the complete real-news
chain did not reach them on a verified event. Search/page/LLM usage is persisted in ignored
SQLite/JSON artifacts. Price is unknown because `MODEL_PRICES` is not configured; do not
interpret zero known cost as a free run.

Files materially changed in this checkpoint: ignored `.env` (local only), PROJECT_STATUS.md,
TODO.md. Prior checkpoint committed the adapter, URL tests and README. All 68 tests pass;
no failing tests. Next concrete step: improve fresh-news retrieval and Context evidence
grounding using the labelled corpus, then rerun a capped full pipeline. Preserve the
source/date/numeric gates, local-only HTTP exception and bounded call budget. Remaining
quality tasks are tracked in TODO.md.

## Local 9Router integration checkpoint — 2026-09-25

User selected local 9Router with `cx/gpt-5.6-sol` for the AI roles. The running gateway at
`http://127.0.0.1:20128` returned HTTP 200 for `/api/health` and `/v1/models`; its current
catalog contains `cx/gpt-5.6-sol` but no `gpt-6-sol`. An unauthenticated bounded
`/v1/chat/completions` probe returned HTTP 401, so model inference has not been confirmed.
The ignored local `.env` still points to OpenRouter and holds an OpenRouter-format key; it was
not sent to 9Router or changed. Codex account integration is not an application API key.

Architecture decision: retain the existing OpenAI-compatible `AgentRouterProvider`; permit
HTTP only for `localhost`, `127.0.0.1`, and `::1` so it can reach a local 9Router instance.
Remote gateways still require HTTPS and credentials/query in the base URL remain forbidden.
No agent architecture or evidence rules were changed. Substantially changed
`app/llm/provider.py`, `tests/test_providers.py`, `README.md`, `.env.example`, and both status
files. Tests now cover allowed loopback endpoints and rejected remote HTTP/credentialed URLs.

Verification: local gateway health/catalog and explicit missing-key 401 confirmed. All 68
tests pass, including the seven new provider URL tests; no failing tests. Known limitation:
9Router API key is not configured, so authenticated agent, bounded pipeline, token usage,
model quality and costs remain untested. The current unfinished stage is local credential
configuration. Next concrete step: create a 9Router API key in its dashboard, save it only in
ignored `.env` as `LLM_API_KEY`, set `LLM_BASE_URL=http://127.0.0.1:20128/v1`, set
`LLM_MODEL` and five role overrides to `cx/gpt-5.6-sol`, then run one short structured
Scout probe before a capped live pipeline. Do not reuse the existing OpenRouter key.
Remaining quality work: fresh-news discovery and independent evidence evaluation in TODO.md.
Preserve strict source/date/numeric gates, bounded calls and secret-free git history.

## Latest implementation checkpoint — bounded response repair, 2026-09-23

Fixed root cause: Verifier's evidence retry only ran after Pydantic parsing succeeded;
schema/JSON errors escaped before that loop. AgentRouterProvider now retries malformed
JSON/schema responses within LLM_RESPONSE_ATTEMPTS (default 2, max 3), supplying the original
input, bounded previous output and sanitized field/type diagnostics. All attempts count
toward MAX_LLM_CALLS and are persisted separately. Whole fenced JSON is unwrapped locally;
missing facts are never synthesized. HTTP failures/refusals are not retried.

Truncation now reports finish_reason=length and can retry with at most double output tokens,
capped at 16000; OpenRouter receives reasoning.enabled=false on that retry. Usage adds actual
routed model, finish reason, reasoning tokens, attempt and safe validation codes. Raw outputs
and API error bodies are not logged. Keepalive responses have an elapsed-time check after
each chunk (LLM_RESPONSE_DEADLINE_SECONDS=120), socket timeout and 2 MB response cap.

Files changed: app/llm/provider.py, app/config.py, app/models.py, .env.example,
app/evaluate_pipeline.py, tests/test_response_repair.py, README.md and both status files.
Evaluation supports explicit timezone-aware --as-of for historical runs and preserves role
overrides from .env unless --analysis-model is supplied. No secrets/config keys changed.

Live validation with openrouter/free:
- Real-source historical run recovered an invalid JSON query response from a routed content
  safety model on its second attempt. A subsequent evidence retry stalled on keepalives;
  that diagnostic process was stopped and its database run marked failed (not left running).
- Targeted replay of previously fetched real Qwen sources at 2026-09-21T11:00:27Z reproduced
  Verifier length truncation: nex-n2.5-mini returned 6000 completion tokens and finish=length.
  Automatic retry via nex-n2.5-pro returned valid JSON, and unchanged evidence gates passed.
- Context and Impact then passed real API/schema/evidence checks. The first Editor response
  was rejected for an unsupported number; an explicit Editor-only replay using the same
  analyzed event passed and selected one event. This was a cached-source historical evaluation,
  not a claim of successful fresh Tavily discovery. Trace data stays in ignored data/:
  free-repair-validation.sqlite3, repair-replay-results.json, editor-replay-response.json.
  Targeted replay plus Editor rerun used 52,608 LLM tokens at configured zero cost; the earlier
  stopped diagnostic has partial usage and unknown usage for the interrupted request.

Validation: response-repair regression tests cover field errors, fences, truncation, refusal,
HTTP failure, budgets, sanitized logs, keepalive deadline, aggregate retry input and complete
pipeline recovery through Editor. Mock CLI writes Markdown/JSON. All 61 tests pass (10.54s),
including Streamlit AppTest; compileall and pip check pass. No failing tests. Diff check passes;
.env is ignored/untracked. This checkpoint is ready for commit and delivery.
Preserve all source/date/numeric gates and free-only routing. Remaining limitation: free-router
semantic quality and latency vary; valid JSON can still contain unsupported claims. Next step:
evaluate fresh news coverage and evidence quality separately from transport/schema reliability.

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
