import pytest


@pytest.fixture(autouse=True)
def offline_settings(monkeypatch, tmp_path):
    """Keep tests offline and independent of the developer's machine:
    no Claude key, .env lookups point at a missing file, and Ollama points at a closed port."""
    for name in ("ANTHROPIC_API_KEY", "VIBEMATCH_PROVIDER", "OLLAMA_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:9")
    monkeypatch.setattr("src.rag.ENV_PATH", str(tmp_path / "missing.env"))
