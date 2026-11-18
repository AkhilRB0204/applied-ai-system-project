"""Tests for API key loading (.env) and the startup key check."""

from types import SimpleNamespace

import anthropic
import httpx2

from src import rag


def fake_client(error=None):
    def list_models(**kwargs):
        if error:
            raise error
        return []
    return SimpleNamespace(models=SimpleNamespace(list=list_models))


def api_error(cls, status):
    request = httpx2.Request("GET", "https://api.anthropic.com/v1/models")
    return cls("error", response=httpx2.Response(status, request=request), body=None)


def test_env_file_supplies_the_key(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-ant-from-file\n")
    monkeypatch.setattr(rag, "ENV_PATH", str(env))
    assert rag.find_api_key() == "sk-ant-from-file"


def test_editing_env_file_takes_effect_without_restart(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    monkeypatch.setattr(rag, "ENV_PATH", str(env))
    env.write_text("ANTHROPIC_API_KEY=\n")
    assert rag.find_api_key() == ""
    env.write_text("ANTHROPIC_API_KEY=sk-ant-new\n")
    assert rag.find_api_key() == "sk-ant-new"


def test_shell_key_wins_over_env_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-ant-from-file\n")
    monkeypatch.setattr(rag, "ENV_PATH", str(env))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-shell")
    assert rag.find_api_key() == "sk-ant-from-shell"


def test_no_key_uses_free_local_model():
    from src.llm import OllamaClient
    assert isinstance(rag.make_client(), OllamaClient)


def test_provider_setting_can_force_offline(monkeypatch):
    monkeypatch.setenv("VIBEMATCH_PROVIDER", "offline")
    assert rag.make_client() is None


def test_claude_key_selects_claude(monkeypatch):
    import anthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert isinstance(rag.make_client(), anthropic.Anthropic)


def test_ollama_not_running_gives_clear_message():
    ok, message = rag.check_api_key(rag.make_client())
    assert not ok and "Ollama is not running" in message


def test_check_api_key_accepts_working_key():
    assert rag.check_api_key(fake_client())[0] is True


def test_check_api_key_explains_rejected_key():
    ok, message = rag.check_api_key(fake_client(api_error(anthropic.AuthenticationError, 401)))
    assert not ok and "401" in message and ".env" in message


def test_check_api_key_explains_connection_problem():
    error = anthropic.APIConnectionError(request=httpx2.Request("GET", "https://api.anthropic.com"))
    ok, message = rag.check_api_key(fake_client(error))
    assert not ok and "internet" in message


def test_cli_stops_with_clear_message_on_bad_key(monkeypatch, capsys):
    from src import main as main_module
    bad = fake_client(api_error(anthropic.AuthenticationError, 401))
    monkeypatch.setattr(main_module, "make_client", lambda: bad)
    assert main_module.main(["music for the gym"]) == 1
    assert "rejected the API key" in capsys.readouterr().out
