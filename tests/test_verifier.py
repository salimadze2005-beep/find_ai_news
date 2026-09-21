from datetime import datetime, timezone, timedelta
from app.config import Settings
from app.mock import MockLLM, MockSearch, MockPages
from app.agents.scout import scout
from app.agents.verifier import (verify, verification_errors, normalize_evidence,
                                 ensure_core_evidence, quote_in_content)

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


def test_official_changelog_date_quote_is_accepted():
    event = verified_fixture()
    primary = next(s for s in event.sources if s.url == event.verification.primary_source_url)
    primary.published_at = None
    primary.date_precision = "unknown"
    primary.date_evidence = ""
    primary.content += " 2026.09.21: We released Atlas."
    event.verification.date_quote = "2026.09.21: We released Atlas."
    event.verification.occurred_at = NOW.replace(hour=0)
    assert not verification_errors(event.verification, event.sources, START, NOW, 2)


def test_date_quote_must_be_exact_and_match_event_date():
    event = verified_fixture()
    event.verification.date_quote = "2026.09.20 invented"
    assert verification_errors(event.verification, event.sources, START, NOW, 2)


def test_quote_ellipsis_and_source_pruning():
    event = verified_fixture()
    fact = event.verification.confirmed_facts[0]
    fact.text = "Atlas pricing changed."
    fact.quote = "Atlas input price falls ... effective today."
    fact.source_urls.append(event.sources[-1].url)
    assert quote_in_content(fact.quote, event.sources[0].content)
    normalize_evidence(event.verification, event.sources)
    assert fact.source_urls == [event.sources[0].url]


def test_normalization_drops_only_invalid_evidence():
    event = verified_fixture()
    good = event.verification.confirmed_facts[0]
    bad = good.model_copy(update={"text": "invented 999", "quote": "invented quote"})
    event.verification.confirmed_facts.append(bad)
    normalize_evidence(event.verification, event.sources)
    assert good in event.verification.confirmed_facts
    assert bad not in event.verification.confirmed_facts


def test_terminal_punctuation_does_not_break_quote():
    assert quote_in_content("2026.09.20: We released Product.",
                            "News 2026.09.20: We released Product! More details")


def test_numeric_dates_match_across_russian_and_iso_formats():
    from app.agents.verifier import numeric_errors
    assert not numeric_errors(["Выпущено 20 сентября 2026 года"], "2026.09.20: released")


def test_retry_receives_previous_invalid_output():
    class RepairingLLM(MockLLM):
        calls = 0

        def respond(self, agent, data):
            result = super().respond(agent, data)
            if agent != "verifier":
                return result
            self.calls += 1
            if self.calls == 1:
                result["occurred_at"] = "2020-01-01T00:00:00Z"
            else:
                assert data["previous_output"]["confirmed_facts"]
                assert "outside analysis window" in " ".join(data["validation_feedback"]["errors"])
            return result

    settings, llm, search = Settings(_env_file=None), RepairingLLM(), MockSearch(NOW)
    candidate = scout(llm, search, settings, START, NOW, lambda *a: None)[0]
    event = verify(candidate, llm, search, MockPages(NOW), settings, START, NOW, lambda *a: None)
    assert llm.calls == 2
    assert event.verification.verified


def test_core_evidence_recovered_only_from_selected_pages():
    event = verified_fixture()
    event.verification.confirmed_facts = []
    ensure_core_evidence(event.verification, event.sources, event.candidate.entities)
    cited = {url for fact in event.verification.confirmed_facts for url in fact.source_urls}
    assert event.verification.primary_source_url in cited
    assert cited.intersection(event.verification.independent_source_urls)
    assert all(quote_in_content(fact.quote, next(
        source.content for source in event.sources if source.url == fact.source_urls[0]))
        for fact in event.verification.confirmed_facts)
