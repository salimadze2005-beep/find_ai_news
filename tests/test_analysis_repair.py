import pytest
from app.agents.common import ask_validated
from app.config import Settings
from app.llm.base import ProviderError
from app.mock import MockLLM, MockSearch, MockPages
from app.pipeline.orchestrator import run_pipeline
from test_verifier import NOW


def test_pipeline_repairs_unsupported_analytical_numbers(tmp_path):
    class RepairLLM(MockLLM):
        def __init__(self):
            super().__init__()
            self.failed = set()

        def respond(self, agent, data):
            result = super().respond(agent, data)
            field = {"context_analyst": "what_changed", "impact_analyst": "what_to_try", "editor": "summary"}.get(agent)
            if field and agent not in self.failed:
                self.failed.add(agent)
                result[field] = "Unsupported improvement: 987654 percent."
            if field and "validation_feedback" in data:
                assert "987654" in str(data["previous_output"])
            return result
    llm = RepairLLM()
    digest = run_pipeline(Settings(_env_file=None, database_path=tmp_path / "repair.db"), now=NOW,
        injected=(llm, MockSearch(NOW), MockPages(NOW)))
    assert len(digest.events) == 2
    assert not digest.warnings
    assert llm.failed == {"context_analyst", "impact_analyst", "editor"}
    assert "987654" not in digest.model_dump_json()


def test_persistent_evidence_error_is_never_accepted():
    from pydantic import BaseModel
    class Answer(BaseModel):
        text: str
    class LLM:
        calls = 0
        def generate_structured(self, agent, prompt, data, schema):
            self.calls += 1
            return schema(text="unsupported")
    def reject(answer):
        raise ProviderError("Unsupported evidence")
    llm = LLM()
    with pytest.raises(ProviderError, match="Unsupported evidence"):
        ask_validated(llm, "editor", {}, Answer, reject, lambda *args: None)
    assert llm.calls == 2
