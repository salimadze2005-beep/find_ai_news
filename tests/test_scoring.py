import pytest
from app.models import Scores
from app.config import Settings
from app.pipeline.scoring import significance
from app.agents.impact_analyst import analyze_impact
from app.agents.context_analyst import analyze_context
from app.mock import MockLLM, MockSearch, MockPages
from test_verifier import verified_fixture, NOW


def test_weighted_score():
    scores = Scores(importance=10, impact=8, practicality=6, novelty=4, confidence=2)
    assert significance(scores, Settings(_env_file=None).scoring_weights) == 7
    with pytest.raises(ValueError):
        significance(scores, {"importance": 1})


def test_impact_confidence_and_optional_relevance():
    event = verified_fixture()
    event.verification.confidence = 7
    llm = MockLLM()
    context, sources = analyze_context(event, llm, MockSearch(NOW), MockPages(NOW), NOW, lambda *a: None)
    result = analyze_impact(event, context, sources, llm, Settings(_env_file=None), lambda *a: None)
    assert result.impact.scores.confidence == 7
    assert result.impact.alfa_bank_relevance == ""
    assert result.significance_score > 6
