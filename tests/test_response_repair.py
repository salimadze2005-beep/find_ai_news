import json
import httpx
import pytest
from pydantic import BaseModel, ConfigDict
from app.config import Settings
from app.llm.provider import AgentRouterProvider
from app.llm.base import ProviderError


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str


def provider(responses, **settings):
    requests = []
    def handle(request):
        requests.append(json.loads(request.content))
        return responses.pop(0)
    return AgentRouterProvider(Settings(_env_file=None, **settings),
        httpx.Client(transport=httpx.MockTransport(handle))), requests


def response(content, finish="stop"):
    return httpx.Response(200, json={"model": "actual/free", "choices": [
        {"finish_reason": finish, "message": {"content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                  "completion_tokens_details": {"reasoning_tokens": 2}}})


def test_schema_repair_retains_original_input_and_logs_each_attempt():
    llm, requests = provider([response('{"answer":null}'), response('{"answer":"ok"}')])
    assert llm.generate_structured("verifier", "Evidence only", {"source": "original"}, Answer).answer == "ok"
    assert requests[0]["messages"][:2] == requests[1]["messages"][:2]
    assert "answer:string_type" in requests[1]["messages"][2]["content"]
    assert len(llm.usage) == 2
    assert [u.success for u in llm.usage] == [False, True]
    assert [u.attempt for u in llm.usage] == [1, 2]
    assert llm.usage[0].actual_model == "actual/free"
    assert llm.usage[0].reasoning_tokens == 2


def test_fenced_json_is_unwrapped_without_network_retry():
    llm, requests = provider([response('```json\n{"answer":"ok"}\n```')])
    assert llm.generate_structured("verifier", "JSON", {}, Answer).answer == "ok"
    assert len(requests) == 1


def test_truncation_retries_with_bounded_output_and_no_openrouter_reasoning():
    llm, requests = provider([response('{"answer":', "length"), response('{"answer":"ok"}')],
                             llm_base_url="https://openrouter.ai/api/v1", llm_max_output_tokens=10000)
    assert llm.generate_structured("verifier", "JSON", {}, Answer).answer == "ok"
    assert requests[1]["max_tokens"] == 16000
    assert requests[1]["reasoning"] == {"enabled": False}
    assert llm.usage[0].finish_reason == "length"


def test_persistent_schema_failure_is_bounded_and_sanitized():
    llm, requests = provider([response('{"SECRET_KEY":"private"}')] * 2)
    with pytest.raises(ProviderError) as exc:
        llm.generate_structured("verifier", "JSON", {}, Answer)
    assert "SECRET_KEY" not in str(exc.value)
    assert "private" not in str(exc.value)
    assert "answer:missing" in str(exc.value)
    assert len(requests) == 2
    assert "SECRET_KEY" not in json.dumps([u.model_dump(mode="json") for u in llm.usage])


@pytest.mark.parametrize("failure", [httpx.Response(429), response("refused", "content_filter")])
def test_http_and_refusal_are_not_retried(failure):
    llm, requests = provider([failure])
    with pytest.raises(ProviderError):
        llm.generate_structured("verifier", "JSON", {}, Answer)
    assert len(requests) == 1


def test_repair_respects_total_call_budget():
    llm, requests = provider([response('{}')], max_llm_calls=1)
    with pytest.raises(ProviderError, match="schema"):
        llm.generate_structured("verifier", "JSON", {}, Answer)
    assert len(requests) == 1


def test_keepalive_response_cannot_wait_forever(monkeypatch):
    from types import SimpleNamespace
    clock = iter([0, 121, 121])
    monkeypatch.setattr("app.llm.provider.time", SimpleNamespace(monotonic=lambda: next(clock)))
    llm, requests = provider([response('{"answer":"ok"}')])
    with pytest.raises(ProviderError, match="deadline"):
        llm.generate_structured("verifier", "JSON", {}, Answer)
    assert len(requests) == 1
    assert not llm.usage[0].success


def test_repair_input_remains_bounded():
    llm, requests = provider([response('{}'), response('{"answer":"ok"}')], max_input_chars=4000)
    with pytest.raises(ProviderError, match="repair input"):
        llm.generate_structured("verifier", "JSON", {"source": "x" * 3900}, Answer)
    assert len(requests) == 1


def test_pipeline_reaches_editor_after_verifier_schema_repair(tmp_path):
    from app.mock import MockLLM, MockSearch, MockPages
    from app.pipeline.orchestrator import run_pipeline
    from test_verifier import NOW
    roles = {"Queries": "queries", "Discoveries": "scout", "Verification": "verifier",
             "ContextAnalysis": "context_analyst", "ImpactAnalysis": "impact_analyst",
             "Editorial": "editor", "Groups": "deduplication"}
    fixture = MockLLM()
    broken = False
    def handle(request):
        nonlocal broken
        data = json.loads(request.content)
        role = roles[data["response_format"]["json_schema"]["name"]]
        payload = json.loads(data["messages"][1]["content"])
        output = fixture.respond(role, payload)
        if role == "verifier" and not broken:
            broken = True
            output["confidence"] = "invalid"
        return response(json.dumps(output))
    settings = Settings(_env_file=None, llm_response_format="json_schema",
                        database_path=tmp_path / "repair.db")
    llm = AgentRouterProvider(settings, httpx.Client(transport=httpx.MockTransport(handle)))
    digest = run_pipeline(settings, now=NOW, injected=(llm, MockSearch(NOW), MockPages(NOW)))
    assert len(digest.events) == 2
    assert not digest.warnings
    assert any(u.agent == "verifier" and u.attempt == 2 and u.success for u in digest.usage)
    assert any(u.agent == "editor" and u.success for u in digest.usage)
