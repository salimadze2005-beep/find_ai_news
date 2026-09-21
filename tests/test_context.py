from datetime import datetime, timezone
from app.mock import MockLLM, MockSearch, MockPages
from app.agents.context_analyst import analyze_context
from test_verifier import verified_fixture


def test_historical_sources_allowed_for_context():
    now = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)
    result, sources = analyze_context(verified_fixture(), MockLLM(), MockSearch(now), MockPages(now), now, lambda *a: None)
    assert result.previous_state
    assert "atlas-old" in result.previous_state[0].source_urls[0]
    assert result.hype == "LOW"
