# Project status

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

## Current stage / next action
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
