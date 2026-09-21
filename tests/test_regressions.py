import json
from datetime import timedelta
from pathlib import Path
import httpx
import pytest
from app.models import NewsSource, Editorial, Usage
from app.config import Settings
from app.llm.base import ProviderError
from app.llm.provider import AgentRouterProvider, strict_schema
from app.mock import MockLLM, MockSearch, MockPages
from app.pipeline.orchestrator import run_pipeline, analysis_key
from app.agents.editor import edit
from app.agents.verifier import evidence_errors, verification_errors
from app.search.pages import WebPages, article_data, in_window, valid_url
from app.storage import Database
from app.render import usage_totals
from test_verifier import verified_fixture, NOW, START


def test_every_citation_must_contain_quote():
    event = verified_fixture()
    fact = event.verification.confirmed_facts[0]
    fact.source_urls.append("https://lab.example/atlas-review")
    assert evidence_errors([fact], event.sources)


def test_fabricated_number_rejected():
    event = verified_fixture()
    fact = event.verification.confirmed_facts[0]
    fact.text = "Inference costs $999"
    assert "number absent" in str(evidence_errors([fact], event.sources))


def test_undated_and_future_cannot_verify():
    event = verified_fixture()
    primary = next(s for s in event.sources if s.url == event.verification.primary_source_url)
    primary.published_at = NOW + timedelta(hours=1)
    assert verification_errors(event.verification, event.sources, START, NOW, 2)
    primary.published_at = None
    assert verification_errors(event.verification, event.sources, START, NOW, 2)


def test_day_precision_near_boundary_is_rejected():
    source = NewsSource(title="x", url="https://example.com/x", published_at=NOW.replace(hour=0),
                        date_precision="day", date_evidence="2026-09-21")
    assert not in_window(source, START, NOW)


def test_conflicting_exact_timestamps_rejected():
    html = '<meta name="date" content="2026-09-20T10:00:00Z"><meta property="article:published_time" content="2026-09-20T15:00:00Z">'
    assert article_data(html)[1] is None


def test_redirect_to_private_network_blocked(monkeypatch):
    monkeypatch.setattr("app.search.pages.public_addresses", lambda url: [] if "127.0.0.1" in url else ["93.184.216.34"])
    requests = []
    def handle(request):
        requests.append(request)
        assert request.url.host == "93.184.216.34"
        assert request.headers["host"] == "example.com"
        assert request.extensions["sni_hostname"] == "example.com"
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private"})
    page = WebPages(client=httpx.Client(transport=httpx.MockTransport(handle)))
    result = page.fetch(NewsSource(title="x", url="https://example.com/x"))
    assert not result.fetched
    assert "Non-public" in result.fetch_error
    assert len(requests) == 1


def test_page_parsing_and_fetch_cache(monkeypatch):
    monkeypatch.setattr("app.search.pages.public_addresses", lambda url: ["93.184.216.34"])
    html = '<meta property="article:published_time" content="2026-09-20T10:00:00Z"><article>Release confirmed</article>'
    page = WebPages(client=httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, text=html, headers={"content-type": "text/html"}))))
    source = NewsSource(title="x", url="https://example.com/x")
    assert page.fetch(source).fetched
    assert page.fetch(source).content == "Release confirmed"
    assert page.calls == 1


def test_injected_url_rejected():
    assert not valid_url('https://example.com/>\n<script>')


def test_live_missing_credentials_persisted_failure(tmp_path):
    settings = Settings(_env_file=None, mock_mode=False, llm_api_key="", tavily_api_key="", database_path=tmp_path / "failure.db")
    with pytest.raises(ProviderError, match="requires"):
        run_pipeline(settings, now=NOW)
    assert Database(settings.database_path).history()[0]["status"] == "failed"


def test_partial_failure_keeps_other_events(tmp_path):
    class PartialLLM(MockLLM):
        def respond(self, agent, data):
            if agent == "verifier" and data["candidate"]["category"] == "pricing":
                raise ProviderError("Synthetic provider outage")
            return super().respond(agent, data)
    result = run_pipeline(Settings(_env_file=None, database_path=tmp_path / "partial.db"), now=NOW,
                          injected=(PartialLLM(), MockSearch(NOW), MockPages(NOW)))
    assert len(result.events) == 1
    assert result.warnings


def test_editor_cannot_invent_event(tmp_path):
    result = run_pipeline(Settings(_env_file=None, database_path=tmp_path / "editor.db"), now=NOW)
    class BadEditor(MockLLM):
        def respond(self, agent, data):
            value = super().respond(agent, data)
            value["selected_ids"] = ["fabricated"]
            return value
    with pytest.raises(ProviderError, match="unknown"):
        edit(result.events, BadEditor(), Settings(_env_file=None), lambda *a: None)


def test_strict_editor_schema_has_no_open_objects():
    def check(schema):
        if isinstance(schema, dict):
            if schema.get("type") == "object":
                assert schema["additionalProperties"] is False
                assert set(schema["required"]) == set(schema["properties"])
            for v in schema.values():
                check(v)
        elif isinstance(schema, list):
            for v in schema:
                check(v)
    check(strict_schema(Editorial.model_json_schema()))


def test_cache_invalidates_when_policy_changes():
    event = verified_fixture()
    a = Settings(_env_file=None)
    b = Settings(_env_file=None, enable_alfa_relevance=True)
    assert analysis_key(event, a, NOW) != analysis_key(event, b, NOW)


def test_unknown_usage_is_not_reported_as_free():
    total = usage_totals([Usage(agent="scout", model="unknown")])
    assert total["unknown_cost_calls"] == 1
    assert total["unknown_usage_calls"] == 1


def test_no_network_in_mock(tmp_path, monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("Mock attempted HTTP access")
    monkeypatch.setattr(httpx.Client, "send", forbidden)
    assert run_pipeline(Settings(_env_file=None, database_path=tmp_path / "offline.db"), now=NOW).events


def test_truncated_output_records_usage_and_budget():
    response = httpx.Response(200, json={"choices": [{"finish_reason": "length", "message": {"content": "{}"}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 2}})
    llm = AgentRouterProvider(Settings(_env_file=None, max_llm_calls=1), httpx.Client(transport=httpx.MockTransport(lambda r: response)))
    with pytest.raises(ProviderError, match="incomplete"):
        llm.generate_structured("editor", "JSON", {}, Editorial)
    assert llm.usage[0].total_tokens == 6
    with pytest.raises(ProviderError, match="budget"):
        llm.generate_structured("editor", "JSON", {}, Editorial)
