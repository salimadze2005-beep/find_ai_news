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

## Optional quality follow-ups (not unimplemented MVP components)
- [x] Configure live APIs and evaluate discovery, real pages and strict verification on current news
- [ ] Repeat the complete live run through Editor after OpenRouter quota and Tavily HTTP 403 are resolved
- [ ] Build a labelled corpus to compare source independence, recall and factual accuracy
- [ ] Expand date extraction and non-HTML support using that evaluation
