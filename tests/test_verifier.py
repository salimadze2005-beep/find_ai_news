from datetime import datetime, timezone, timedelta
from app.config import Settings
from app.mock import MockLLM, MockSearch, MockPages
from app.agents.scout import scout
from app.agents.verifier import verify, verification_errors

NOW = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)
START = NOW - timedelta(hours=48)


def verified_fixture(index=0):
    settings, llm, search = Settings(_env_file=None), MockLLM(), MockSearch(NOW)
    event = scout(llm, search, settings, START, NOW, lambda *a: None)[index]
    return verify(event, llm, search, MockPages(NOW), settings, START, NOW, lambda *a: None)


def test_verified_price():
    assert verified_fixture().verification.verified


def test_rumor_and_old_release_fail():
    assert not verified_fixture(2).verification.verified
    assert not verified_fixture(3).verification.verified


def test_fabricated_quote_rejected():
    event = verified_fixture()
    event.verification.confirmed_facts[0].quote = "invented evidence"
    assert "Evidence quote absent" in str(verification_errors(event.verification, event.sources, START, NOW, 2))


def test_same_publisher_not_independent():
    event = verified_fixture()
    event.verification.independent_source_urls = [event.verification.primary_source_url]
    assert "publishers are not distinct" in str(verification_errors(event.verification, event.sources, START, NOW, 2))
