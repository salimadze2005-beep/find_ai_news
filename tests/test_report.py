import copy
from bs4 import BeautifulSoup
from app.config import Settings
from app.pipeline.orchestrator import run_pipeline
from app.render import render_digest, render_html


def fixture(tmp_path):
    return run_pipeline(Settings(_env_file=None, database_path=tmp_path / "report.sqlite3"))


def test_reports_are_russian_structured_and_leave_evidence_unchanged(tmp_path):
    digest = fixture(tmp_path)
    before = copy.deepcopy(digest.model_dump())
    html, md = render_html(digest), render_digest(digest)
    soup = BeautifulSoup(html, "html.parser")
    assert soup.html["lang"] == "ru"
    for card in soup.select("article.news-card")[:len(digest.events)]:
        assert card.find("p", class_="ratings").find_parent("details") is None
        details = card.find("details")
        assert "open" not in details.attrs
        assert [h.get_text() for h in details.find_all("h3", recursive=False)] == [
            "Что произошло", "Почему важно", "Как применить", "Ограничения", "Источники"]
    for obsolete in ["INFERENCE", "ИНФЕРЕНЦИЯ", "FACT", "COMPANY CLAIM", "Significance:", "Confidence:", "статус — в"]:
        assert obsolete not in soup.get_text()
        assert obsolete not in md
    assert digest.model_dump() == before
    assert "<details>" in md


def test_html_and_markdown_reject_active_content_and_bad_links(tmp_path):
    digest = fixture(tmp_path)
    digest.summary = '<script>alert("unsafe")</script>'
    event = digest.events[0]
    event.event.candidate.title = '<img src=x onerror="alert(1)">'
    event.event.verification.primary_source_url = "javascript:alert(1)"
    event.event.verification.confirmed_facts[0].source_urls = ['https://example.com/\"><script>bad</script>']
    soup = BeautifulSoup(render_html(digest), "html.parser")
    assert not soup.find_all(["script", "img", "iframe"])
    assert all(a["href"].startswith(("https://", "http://")) for a in soup.find_all("a"))
    assert "javascript:" not in render_digest(digest)
    assert digest.summary in soup.get_text()


def test_unknown_cost_is_not_displayed_as_free(tmp_path):
    digest = fixture(tmp_path)
    digest.usage[0].estimated_cost = None
    for output in (render_html(digest), render_digest(digest)):
        assert "Полная стоимость неизвестна" in output
        assert "0.000000" not in output


def test_saved_report_cli_needs_no_api(tmp_path, monkeypatch):
    from app.run import main
    import sys
    digest = fixture(tmp_path)
    source, target = tmp_path / "run.json", tmp_path / "run.html"
    source.write_text(digest.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["app.run", "--from-json", str(source), "--html", str(target)])
    monkeypatch.setattr("app.run.run_pipeline", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("No new run")))
    main()
    assert "<html lang=\"ru\">" in target.read_text(encoding="utf-8")
