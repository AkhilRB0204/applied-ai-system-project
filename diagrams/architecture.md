# System Diagram

How VibeMatch 2.0 is organized: a request flows from **input** through **retrieval, generation and evaluation** to an **output**, with tests and humans checking the AI's results. The Mermaid source is also kept as [`architecture.mmd`](architecture.mmd).

```mermaid
flowchart LR
    subgraph Input
        Req(["User request<br/>e.g. chill music for studying"])
        KB[("Knowledge base<br/>data/knowledge_base.json")]
        CSV[("Song catalog<br/>data/songs.csv")]
    end

    subgraph Process["Process: src/rag.py"]
        Guard["Input guardrail<br/>clean_query()"]
        Retriever["Retriever<br/>retrieve_notes() + recommend_songs()<br/>top 5 candidate songs"]
        Generator["Generator: Claude<br/>writes 3 picks from<br/>retrieved data only"]
        Evaluator{"Evaluator<br/>check_answer():<br/>all picks retrieved?"}
        Fallback["Fallback<br/>template answer"]
    end

    subgraph Output
        Answer["Answer + the notes and songs<br/>it was based on"]
        Log[("logs/vibematch.log<br/>every step + check result")]
    end

    subgraph Checks["Checking AI results"]
        Tests["Tester: pytest<br/>14 offline tests, fake Claude"]
        Human["Human review<br/>user compares answer to sources;<br/>developer reads the log and<br/>--profiles adversarial demo"]
    end

    Req --> Guard --> Retriever
    KB --> Retriever
    CSV --> Retriever
    Retriever --> Generator --> Evaluator
    Evaluator -->|"pass"| Answer
    Evaluator -->|"fail: retry once"| Generator
    Evaluator -->|"fail again / API error / no key"| Fallback --> Answer
    Process -.-> Log

    Tests -.->|"verify retriever, evaluator,<br/>retry, fallback, guardrails"| Process
    Answer -.-> Human
    Log -.-> Human
```

## Components

| Component | Where | Role |
|---|---|---|
| Input guardrail | `clean_query()` in `src/rag.py` | Rejects empty requests, cuts ones over 300 characters |
| Retriever | `retrieve_notes()`, `build_prefs()`, `recommend_songs()` | Finds matching knowledge-base notes, turns them into targets, retrieves the top 5 songs |
| Generator | Claude `claude-opus-5-5` via `ask()` | Writes 3 picks using only the retrieved notes and songs |
| Evaluator | `check_answer()` | Rejects picks that were not retrieved; triggers one retry, then the fallback |
| Fallback | `fallback_answer()` | Template answer from retrieved data when Claude fails, errors or there is no API key |
| Logger | `logs/vibematch.log` | Records every step and check result |
| CLI | `src/main.py` | Runs requests, interactive mode, and the `--profiles` demo |

## Where results are checked

- **Automatically, every request:** the evaluator checks Claude's answer before it is shown.
- **Tests:** `pytest` runs 14 offline tests (fake Claude client) covering the retriever, evaluator, retry, fallbacks and guardrails.
- **Humans:** the user sees the answer next to the notes and songs it came from, so unsupported claims are easy to spot; the developer reviews `logs/vibematch.log` and the adversarial profiles in `python -m src.main --profiles` (findings in `model_card.md`).
