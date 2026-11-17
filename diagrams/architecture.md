# System Architecture

How VibeMatch turns a song catalog and a user taste profile into ranked, explained recommendations. The Mermaid source is also kept as [`architecture.mmd`](architecture.mmd).

```mermaid
flowchart TD
    subgraph Inputs["Inputs"]
        CSV[("data/songs.csv<br/>20-song catalog")]
        Profiles["User taste profiles<br/>src/main.py PROFILES<br/>genre, mood, energy,<br/>valence, acousticness"]
    end

    subgraph Engine["Recommendation engine: src/recommender.py"]
        Load["load_songs()<br/>parse CSV rows,<br/>convert numeric columns"]
        Score["score_song()<br/>returns score + reasons"]
        Genre["Genre rule<br/>exact +2.0 / partial +1.0"]
        Mood["Mood rule<br/>exact +1.5 / same family +0.75<br/>MOOD_FAMILIES"]
        Numeric["Numeric closeness<br/>energy x1.5, valence x1.0,<br/>acousticness x0.5"]
        Rank["recommend_songs()<br/>sort by score desc,<br/>tie-break on energy closeness,<br/>keep top k"]
    end

    subgraph OOP["OOP wrapper: Recommender class"]
        UP["UserProfile + Song<br/>dataclasses"]
        Adapter["_profile_to_prefs()<br/>likes_acoustic to target 0.8 / 0.2"]
        RecAPI["Recommender.recommend()<br/>Recommender.explain_recommendation()"]
    end

    subgraph Outputs["Outputs"]
        CLI["CLI report<br/>python -m src.main<br/>ranked top 5 with reasons"]
        Tests["pytest<br/>tests/test_recommender.py"]
    end

    CSV --> Load
    Load -->|"list of song dicts"| Rank
    Profiles -->|"user_prefs dict"| Rank
    Rank -->|"each song"| Score
    Score --> Genre
    Score --> Mood
    Score --> Numeric
    Genre & Mood & Numeric -->|"points + reasons"| Score
    Score -->|"(score, reasons)"| Rank
    Rank -->|"top k: song, score, explanation"| CLI

    Tests --> UP
    UP --> RecAPI
    RecAPI --> Adapter
    Adapter -->|"user_prefs dict"| Rank
    RecAPI -.->|"explain"| Score
    RecAPI -->|"ranked Song objects"| Tests
```

## Components

- **Inputs:** `data/songs.csv` (20-song catalog) and the taste profiles in `src/main.py`.
- **Recommendation engine (`src/recommender.py`):** `load_songs()` parses the catalog; `recommend_songs()` sends each song to `score_song()`, which adds genre, mood-family and numeric-closeness points and records a reason for each; results are sorted by score (ties broken by energy closeness) and the top k are kept.
- **OOP wrapper:** the `Recommender` class with `Song` and `UserProfile` dataclasses; `_profile_to_prefs()` converts a profile into the same `user_prefs` dict the engine uses.
- **Outputs:** the CLI report (`python -m src.main`) and the pytest suite (`tests/test_recommender.py`).
