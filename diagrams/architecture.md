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
        Generator["Generator: AI model<br/>(Claude or local Ollama)<br/>writes 3 picks from<br/>retrieved data only"]
        Evaluator{"Evaluator<br/>check_answer():<br/>all picks retrieved?"}
        Fallback["Fallback<br/>template answer"]
    end

    subgraph Agent["Agent mode --agent: src/agent.py"]
        Plan["Plan<br/>reason on every tool call"]
        Tools["Act: model calls tools<br/>search_notes / find_songs<br/>(retries with new targets)"]
        SelfCheck["Check: check_picks<br/>then fix picks"]
    end

    subgraph Output
        Answer["Answer + the notes and songs<br/>it was based on"]
        Log[("logs/vibematch.log<br/>every step + check result")]
    end

    subgraph Checks["Checking AI results"]
        Tests["Tester: pytest<br/>37 offline tests, fake model"]
        Human["Human review<br/>user compares answer to sources;<br/>developer reads the log and<br/>--profiles adversarial demo"]
    end

    Req --> Guard --> Retriever
    Guard -->|"--agent"| Plan --> Tools --> SelfCheck
    Tools <-.->|"same retrieval code"| Retriever
    SelfCheck -->|"final answer"| Evaluator
    KB --> Retriever
    CSV --> Retriever
    Retriever --> Generator --> Evaluator
    Evaluator -->|"pass"| Answer
    Evaluator -->|"fail: retry once"| Generator
    Evaluator -->|"fail again / API error / no key"| Fallback --> Answer
    Process -.-> Log
    Agent -.->|"steps + plans"| Log

    Tests -.->|"verify retriever, evaluator,<br/>retry, fallback, guardrails"| Process
    Tests -.->|"verify loop, step limit,<br/>tool input checks"| Agent
    Answer -.-> Human
    Log -.-> Human
```

## Components

| Component | Where | Role |
|---|---|---|
| Input guardrail | `clean_query()` in `src/rag.py` | Rejects empty requests, cuts ones over 300 characters |
| Retriever | `retrieve_notes()`, `build_prefs()`, `recommend_songs()` | Finds matching knowledge-base notes, turns them into targets, retrieves the top 5 songs |
| Generator | Claude `claude-opus-5-5`, or the free local `qwen3:4b-instruct` via Ollama, through `ask()` | Writes 3 picks using only the retrieved notes and songs |
| Agent | `ask_agent()` in `src/agent.py`, with `--agent` | The model plans each step, calls `search_notes` / `find_songs` / `check_picks`, and fixes its picks before answering |
| Evaluator | `check_answer()` | Rejects picks that were not retrieved; triggers one retry, then the fallback |
| Fallback | `fallback_answer()` | Template answer from retrieved data when the model fails, errors or no model is available |
| Logger | `logs/vibematch.log` | Records every step and check result |
| CLI | `src/main.py` | Runs requests, interactive mode, and the `--profiles` demo |

## Where results are checked

- **Automatically, every request:** the evaluator checks the model's answer before it is shown. In agent mode the model also checks its own picks with `check_picks` first.
- **Tests:** `pytest` runs 37 offline tests (scripted fake model client) covering the retriever, evaluator, retry, fallbacks, guardrails, and the agent's loop, step limit and tool-input validation.
- **Humans:** the user sees the answer next to the notes and songs it came from, so unsupported claims are easy to spot; the developer reviews `logs/vibematch.log` and the adversarial profiles in `python -m src.main --profiles` (findings in `model_card.md`).
