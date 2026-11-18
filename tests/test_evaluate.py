"""The reliability evaluation runs offline and its template answers must pass every case."""

from src.evaluate import CASES, main, run_case, summarize
from src.rag import load_knowledge_base
from src.recommender import load_songs

SONGS = load_songs("data/songs.csv")
KB = load_knowledge_base("data/knowledge_base.json")


def test_offline_evaluation_passes_every_case():
    rows = [run_case(case, SONGS, KB, client=None, agent=False) for case in CASES]
    failed = [(r["id"], r["detail"]) for r in rows if not r["passed"]]
    assert failed == []
    assert all(r["grounded"] for r in rows if "grounded" in r)


def test_no_match_case_has_zero_confidence():
    case = next(c for c in CASES if c[0] == "no match")
    assert run_case(case, SONGS, KB, client=None, agent=False)["confidence"] == 0.0


def test_summary_counts_cases():
    rows = [run_case(case, SONGS, KB, client=None, agent=False) for case in CASES]
    assert summarize(rows, "test").startswith(f"test: {len(CASES)}/{len(CASES)} cases passed")


def test_cli_prints_table(capsys):
    assert main(["--offline"]) == 0
    assert "| Case | Request |" in capsys.readouterr().out
