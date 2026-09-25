# Implementation checklist
- [x] Configuration, Pydantic models and SQLite foundation
- [x] Foundation tests and checkpoint
- [x] LLMProvider and AgentRouter-compatible integration
- [x] SearchProvider and Tavily integration
- [x] Safe page retrieval and publication-date evidence
- [x] Mock providers and synthetic fixtures
- [x] Scout, dynamic queries and candidate extraction
- [x] Normalization, semantic deduplication, date filtering
- [x] Verifier and source/fact/claim validation
- [x] Context Analyst and hype detection
- [x] Impact Analyst and weighted scoring
- [x] Editor, digest and unconfirmed section
- [x] Pipeline persistence, reuse, logs and usage totals
- [x] Streamlit UI, debug views and history
- [x] Integration and adversarial regression tests
- [x] README and final CLI/UI smoke tests
- [x] Secrets audit, clean git status and GitHub push
- [x] Russian reader report with expandable news cards and visible significance/reliability
- [x] Standalone HTML download and offline reformatting of saved JSON reports
- [x] Reader-report browser review and escaping/evidence-preservation tests

## Optional quality follow-ups (not unimplemented MVP components)
- [x] Diagnose and fix overloaded queries, news retrieval, fair result allocation and primary lookup
- [x] Fix publication dates polluted by related article timestamps
- [x] Add bounded evidence repair for Context, Impact and Editor
- [x] Accept search/evidence fixes on an ordinary current-news run and inspect its confirmed event
- [x] Verify local 9Router availability and model catalog; support loopback HTTP safely
- [x] Configure 9Router API key locally and run authenticated agent plus bounded live pipeline
- [x] Confirm all five roles can call the selected 9Router model
- [x] Obtain a fully confirmed real-news event through Context, Impact and Editor on 9Router
- [x] Configure live APIs and evaluate discovery, real pages and strict verification on current news
- [x] Configure all roles on openrouter/free and verify real API/search calls
- [x] Retest on 2026-09-23: 51 tests pass; live search empty; curated Verifier schema failure reproduced
- [x] Bounded schema/truncation repair, diagnostics, deadline and pipeline regression test
- [x] Real free-API Verifier recovery and downstream historical replay through Editor (Editor rerun required)
- [ ] Confirm reliable fresh-news discovery and digest quality; free models can still emit unsupported claims
- [ ] Build a labelled corpus to compare source independence, recall and factual accuracy
- [ ] Expand date extraction and non-HTML support using that evaluation

## Reader follow-up — 2026-09-25
- [x] Open every news section independently; verify in tests and browser
- [ ] Complete and inspect a real 72-hour news report
