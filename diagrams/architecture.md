# System Architecture

How VibeMatch 2.0 turns a plain-English request into recommendations grounded in retrieved data. The Mermaid source is also kept as [`architecture.mmd`](architecture.mmd).

```mermaid
flowchart TD
    User(["User request<br/>python -m src.main &quot;chill music for studying&quot;"])

    subgraph Data["Data sources"]
        CSV[("data/songs.csv<br/>20-song catalog")]
        KB[("data/knowledge_base.json<br/>13 activity / mood / genre notes")]
    end

    subgraph App["src/main.py: CLI, logging setup, error handling"]
        Print["print answer + retrieved data<br/>+ pipeline log"]
    end

    subgraph RAG["RAG pipeline: src/rag.py ask()"]
        Guard["clean_query()<br/>reject empty, cut > 300 chars"]
        Notes["1. retrieve_notes()<br/>keyword match on note tags"]
        Prefs["build_prefs()<br/>note targets + genre / mood<br/>named in the request"]
        Songs["2. recommend_songs()<br/>top 5 candidates"]
        Gen["3. Claude claude-opus-5-5<br/>writes 3 picks using only<br/>retrieved notes + candidates"]
        Check{"4. check_answer()<br/>every pick a candidate?"}
        Retry["send problems back<br/>retry once"]
        Fallback["fallback_answer()<br/>template from retrieved data"]
    end

    subgraph Scorer["src/recommender.py (VibeMatch 1.0 scorer)"]
        Score["score_song()<br/>genre +2.0 / mood +1.5 /<br/>energy, valence, acousticness closeness"]
    end

    Log[("logs/vibematch.log")]
    Profiles["--profiles demo<br/>8 hand-written profiles"]
    Tests["pytest: tests/<br/>fake Claude client, offline"]

    User --> Guard --> Notes
    KB --> Notes
    Notes --> Prefs --> Songs
    CSV --> Songs
    Songs <--> Score
    Notes -->|"note text"| Gen
    Songs -->|"candidates + scores + reasons"| Gen
    Gen --> Check
    Check -->|"pass"| Print
    Check -->|"fail, 1st try"| Retry --> Gen
    Check -->|"fail again"| Fallback
    Gen -.->|"API error, refusal or no key"| Fallback
    Fallback --> Print
    RAG -.->|"every step"| Log
    Profiles --> Score
    Tests -.-> RAG
```

## Components

- **Data sources:** `data/songs.csv` (20-song catalog) and `data/knowledge_base.json` (notes about activities, moods and genres, each with text and suggested targets).
- **CLI (`src/main.py`):** parses arguments, sets up logging to `logs/vibematch.log`, loads data with clear errors, and prints the answer next to the data it came from. `--profiles` runs the original 8-profile demo.
- **RAG pipeline (`src/rag.py`):**
  1. `retrieve_notes()` finds notes whose tags match the request.
  2. `build_prefs()` turns the notes and any genre/mood named in the request into `user_prefs`; `recommend_songs()` retrieves the top 5 candidates.
  3. Claude writes 3 picks using only the retrieved notes and candidates.
  4. `check_answer()` rejects picks outside the candidates; Claude gets one retry with the problems listed, then `fallback_answer()` takes over. API errors, refusals and a missing key also use the fallback.
- **Scorer (`src/recommender.py`):** the VibeMatch 1.0 scoring rules, reused as the song retriever.
- **Tests:** `tests/` run offline with a fake Claude client.
