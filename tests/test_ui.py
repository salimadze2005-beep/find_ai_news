from streamlit.testing.v1 import AppTest
from pathlib import Path


def test_mock_dashboard(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "ui.sqlite"))
    monkeypatch.setenv("MOCK_MODE", "true")
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=20).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "2"
    assert any("UNCONFIRMED" in title.value for title in app.subheader)
    assert any("DEMO" in warning.value for warning in app.warning)
