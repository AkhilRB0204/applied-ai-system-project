"""Offline tests for the agentic workflow. Claude is replaced by a scripted fake client."""

import json
from types import SimpleNamespace

from src.agent import MAX_STEPS, AgentState, ToolInputError, ask_agent, run_tool
from src.rag import load_knowledge_base
from src.recommender import load_songs

SONGS = load_songs("data/songs.csv")
KB = load_knowledge_base("data/knowledge_base.json")


def tool_call(name, tool_input, call_id="call_1"):
    block = SimpleNamespace(type="tool_use", id=call_id, name=name, input=tool_input)
    return SimpleNamespace(stop_reason="tool_use", content=[block])


def final(text):
    return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)])


class ScriptedClient:
    """Returns scripted responses in order and records every request."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        # Copy messages: the agent keeps appending to the same list after this call.
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.responses.pop(0)


GOOD_ANSWER = (
    '- "Library Rain" by Paper Lanterns: calm lofi with acoustic warmth.\n'
    '- "Midnight Coding" by LoRoom: steady low energy for focus.\n'
    '- "Focus Flow" by LoRoom: made for concentrating.'
)

PLAN_ACT_CHECK = [
    tool_call("search_notes", {"query": "studying", "reason": "Learn what suits studying."}, "c1"),
    tool_call("find_songs", {"genre": "lofi", "mood": "chill", "energy": 0.4, "reason": "Use study targets."}, "c2"),
    tool_call("check_picks", {"titles": ["Library Rain", "Midnight Coding", "Focus Flow"],
                              "reason": "Verify before answering."}, "c3"),
]


def test_agent_plans_acts_and_checks():
    client = ScriptedClient(PLAN_ACT_CHECK + [final(GOOD_ANSWER)])
    result = ask_agent("lofi for studying", SONGS, KB, client=client)

    assert result.source == "agent"
    assert result.answer == GOOD_ANSWER
    log = "\n".join(result.log)
    for expected in ("search_notes", "find_songs", "check_picks", "plan: Use study targets.", '"ok": true'):
        assert expected in log
    assert result.notes and result.candidates
    # Tool results were sent back to Claude, matched to each call.
    tool_result = client.calls[1]["messages"][-1]["content"][0]
    assert tool_result["tool_use_id"] == "c1" and not tool_result["is_error"]


def test_bad_final_answer_gets_one_correction():
    bad = '- "Iron Tempest" by Graveforge: great for studying.'
    client = ScriptedClient(PLAN_ACT_CHECK[1:2] + [final(bad), final(GOOD_ANSWER)])
    result = ask_agent("lofi for studying", SONGS, KB, client=client)

    assert result.source == "agent"
    assert "failed these checks" in client.calls[-1]["messages"][-1]["content"]


def test_agent_falls_back_when_answer_keeps_failing():
    bad = '- "Made Up Song" by Nobody: nope.'
    client = ScriptedClient([final(bad), final(bad)])
    result = ask_agent("lofi for studying", SONGS, KB, client=client)

    assert result.source == "fallback"
    assert any("template answer" in line for line in result.log)


def test_step_limit_stops_endless_tool_calls():
    looping = [tool_call("search_notes", {"query": "music", "reason": "again"}, f"c{i}") for i in range(MAX_STEPS)]
    client = ScriptedClient(looping)
    result = ask_agent("anything", SONGS, KB, client=client)

    assert len(client.calls) == MAX_STEPS
    assert result.source == "fallback"
    assert any("step limit" in line for line in result.log)


def test_invalid_tool_input_is_returned_as_error():
    client = ScriptedClient([
        tool_call("find_songs", {"energy": 5, "reason": "oops"}, "c1"),
        tool_call("find_songs", {"genre": "lofi", "energy": 0.4, "reason": "fixed"}, "c2"),
        final(GOOD_ANSWER),
    ])
    result = ask_agent("lofi for studying", SONGS, KB, client=client)

    error_result = client.calls[1]["messages"][-1]["content"][0]
    assert error_result["is_error"] and "energy" in error_result["content"]
    assert result.source == "agent"


def test_check_picks_flags_songs_never_found():
    state = AgentState(SONGS, KB)
    run_tool("find_songs", {"genre": "lofi", "reason": "r"}, state)
    report = json.loads(run_tool("check_picks", {"titles": ["Library Rain", "Iron Tempest"], "reason": "r"}, state))
    assert report["ok"] is False
    assert report["problems"] == ['"Iron Tempest" was never returned by find_songs']


def test_unknown_tool_is_rejected():
    import pytest
    with pytest.raises(ToolInputError):
        run_tool("delete_catalog", {}, AgentState(SONGS, KB))


def test_agent_without_api_key_uses_offline_pipeline():
    result = ask_agent("music for the gym", SONGS, KB, client=None)
    assert result.source == "offline"
    assert "needs an API key" in result.log[0]


def test_main_agent_flag_runs_offline(capsys):
    from src.main import main
    assert main(["--agent", "--offline", "sad", "rainy", "day"]) == 0
    assert "Ashes in Winter" in capsys.readouterr().out
