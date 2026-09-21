import json
from datetime import datetime, timezone, timedelta
import httpx
import pytest
from pydantic import BaseModel
from app.config import Settings
from app.llm.provider import AgentRouterProvider
from app.llm.base import ProviderError
from app.search.provider import TavilyProvider
from app.search.pages import article_data, in_window, valid_url, canonical_url, public_url
from app.models import NewsSource


class Answer(BaseModel):
    answer: str


def test_llm_contract_usage_and_model():
    def handle(req):
        data = json.loads(req.content)
        assert data["model"] == "cheap"
        assert data["response_format"]["type"] == "json_object"
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"answer":"ok"}'}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}})
    settings = Settings(_env_file=None, scout_model="cheap", model_prices={"cheap": {"input": 1, "output": 2}})
    llm = AgentRouterProvider(settings, httpx.Client(transport=httpx.MockTransport(handle)))
    assert llm.generate_structured("scout", "JSON", {}, Answer).answer == "ok"
    assert llm.usage[0].total_tokens == 120
    assert llm.usage[0].estimated_cost == pytest.approx(.00014)


@pytest.mark.parametrize("response", [httpx.Response(429, text="secret"), httpx.Response(200, json={"choices": []})])
def test_llm_sanitized_failure(response):
    llm = AgentRouterProvider(Settings(_env_file=None), httpx.Client(transport=httpx.MockTransport(lambda r: response)))
    with pytest.raises(ProviderError) as error:
        llm.generate_structured("scout", "JSON", {}, Answer)
    assert "secret" not in str(error.value)
    assert not llm.usage[0].success


def test_tavily_discards_search_date():
    def handle(req):
        assert json.loads(req.content)["start_date"] == "2026-09-19"
        return httpx.Response(200, json={"results": [{"title": "Release", "url": "https://example.com/a",
            "content": "News", "published_date": "2026-09-20"}]})
    search = TavilyProvider(Settings(_env_file=None), httpx.Client(transport=httpx.MockTransport(handle)))
    assert search.search("release", datetime(2026, 9, 19, tzinfo=timezone.utc), datetime(2026, 9, 21, tzinfo=timezone.utc), 2)[0].published_at is None


def test_page_dates_and_window():
    content, date, precision, evidence = article_data('<meta property="article:published_time" content="2026-09-20T10:00:00Z"><article>New release</article>')
    source = NewsSource(title="a", url="https://example.com/a", content=content, published_at=date, date_precision=precision, date_evidence=evidence)
    assert in_window(source, date - timedelta(hours=1), date + timedelta(hours=1))
    assert not in_window(source, date + timedelta(seconds=1), date + timedelta(hours=2))
    assert article_data('<meta property="article:modified_time" content="2026-09-20T10:00:00Z">')[1] is None
    assert article_data('<meta name="date" content="2026-09-20T10:00:00">')[1] is None


def test_conflicting_dates_unknown():
    assert article_data('<meta name="date" content="2026-09-20"><script type="application/ld+json">{"datePublished":"2020-01-01"}</script>')[1] is None


def test_source_urls():
    assert not valid_url("file:///etc/passwd")
    assert not valid_url("https://user:pass@example.com")
    assert not valid_url("https://t.me/test")
    assert not public_url("http://127.0.0.1/test")
    assert canonical_url("https://example.com/a/?utm_source=x#heading") == "https://example.com/a"
