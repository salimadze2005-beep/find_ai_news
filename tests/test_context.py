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


def test_invalid_historical_item_is_omitted_without_rejecting_event():
    class InvalidHistoryLLM(MockLLM):
        def respond(self, agent, data):
            result = super().respond(agent, data)
            if agent == "context_analyst":
                result["previous_state"][0]["quote"] = "invented historical quote"
                result["what_changed"] = "INFERENCE: the verified event changes the available option."
            return result

    now = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)
    result, _ = analyze_context(verified_fixture(), InvalidHistoryLLM(), MockSearch(now),
                                MockPages(now), now, lambda *a: None)
    assert result.previous_state == []
    assert any("could not be validated" in item for item in result.limitations)
