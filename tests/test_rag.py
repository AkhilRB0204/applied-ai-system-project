"""Offline tests for the RAG pipeline. Claude is replaced by a fake client."""

from types import SimpleNamespace

from src.rag import ask, build_prefs, check_answer, load_knowledge_base, retrieve_notes
from src.recommender import load_songs

SONGS = load_songs("data/songs.csv")
KB = load_knowledge_base("data/knowledge_base.json")


class FakeClient:
    """Mimics client.beta.messages.create, returning scripted answers in order."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        text = self.answers.pop(0)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)])


def test_retrieve_notes_finds_study_note():
    notes = retrieve_notes("chill music for studying", KB)
    assert notes[0]["id"] == "activity-study"


def test_build_prefs_uses_notes_and_explicit_genre():
    query = "lofi for studying"
    prefs = build_prefs(query, retrieve_notes(query, KB), SONGS)
    assert prefs["genre"] == "lofi"
    assert prefs["energy"] == 0.40


def test_build_prefs_prefers_longest_genre_match():
    prefs = build_prefs("some indie pop please", [], SONGS)
    assert prefs["genre"] == "indie pop"


def test_offline_answer_only_uses_retrieved_songs():
    result = ask("music for the gym", SONGS, KB, client=None)
    assert result.source == "offline"
    assert check_answer(result.answer, result.candidates, SONGS) == []


def test_check_flags_song_that_was_not_retrieved():
    result = ask("calm music to sleep", SONGS, KB, client=None)
    bad = '- "Iron Tempest" by Graveforge: very calming.'
    problems = check_answer(bad, result.candidates, SONGS)
    assert any("Iron Tempest" in p for p in problems)


def test_claude_answer_passes_check():
    top = ask("music for studying", SONGS, KB, client=None).candidates[0][0]
    good = f'- "{top["title"]}" by {top["artist"]}: steady and calm.'
    result = ask("music for studying", SONGS, KB, client=FakeClient([good]))
    assert result.source == "claude"
    assert result.answer == good


def test_self_correction_retries_after_failed_check():
    top = ask("music for studying", SONGS, KB, client=None).candidates[0][0]
    bad = '- "Some Song Not In The Catalog" by Nobody: great vibes.'
    good = f'- "{top["title"]}" by {top["artist"]}: steady and calm.'
    client = FakeClient([bad, good])
    result = ask("music for studying", SONGS, KB, client=client)
    assert result.source == "claude"
    assert len(client.calls) == 2
    # The retry tells Claude what failed.
    assert "failed these checks" in client.calls[1]["messages"][-1]["content"]


def test_falls_back_when_claude_keeps_failing():
    bad = '- "Made Up Song" by Nobody: nope.'
    result = ask("music for studying", SONGS, KB, client=FakeClient([bad, bad]))
    assert result.source == "fallback"
    assert check_answer(result.answer, result.candidates, SONGS) == []


def test_empty_request_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        ask("   ", SONGS, KB, client=None)


def test_long_request_is_cut():
    result = ask("lofi " * 200, SONGS, KB, client=None)
    assert len(result.query) <= 300


def test_api_error_falls_back_safely():
    import anthropic, httpx2

    class BrokenClient(FakeClient):
        def _create(self, **kwargs):
            raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com"))

    result = ask("music for studying", SONGS, KB, client=BrokenClient([]))
    assert result.source == "fallback"
    assert any("API error" in line for line in result.log)


def test_main_runs_a_request_offline(capsys):
    from src.main import main
    assert main(["--offline", "happy", "pop", "for", "the", "morning"]) == 0
    out = capsys.readouterr().out
    assert "Sunrise City" in out
