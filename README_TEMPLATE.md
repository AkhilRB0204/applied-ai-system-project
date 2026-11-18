# [Project Title]

> [One-line tagline: what the project does]

## Original Project 

**Original project:** The original name of the project is VibeMatch, it's a small, CLI-first, content-based music recommender. It loads a 20-song catalog from `data/songs.csv`, scores every song against a user's taste profile (genre, mood, energy, and optionally valence and acousticness), and prints the top 5 with a short reason for every point a song earned.

## Summary

Now, it adds Retrieval-Augmented Generation: you can describe what you want in plain English, and Claude writes recommendations grounded in songs and notes retrieved from the project's own data and Agentic workflows which turns vague, plain-English requests into good search settings and checks the result, instead of relying on fixed keyword rules.

## Architecture Overview

![System diagram](assets/[diagram-image].png)

Mermaid source: [`diagrams/architecture.mmd`](diagrams/architecture.mmd)

[Short explanation of the diagram:]

- **Input:** Takes User request in Plain English e.g. chill music for studying 
- **Process:** Input is processed but there is a guardrail that rejects empty requests and cuts anything over 300 characters. The retriever finds knowledge based notes from the knowledge base json file and retrieves the songs based on the the context of the json file, the user requests in the songs.csv file and claude writes 3 picks from the retrieved data only and the evaluator rejects picks that are not retrieved so it basically checks the answer. Then the agent plans each step, calls to search notes and find songs and fixes pick before answering. The fallback is the answer from retrieved data should claude fail, there are errors or there is no API key.
- **Output:** Up to 3 recommendations in the format "Song Title" by Artist: reason, sometimes followed by a one-sentence note when the catalog is a weak fit. The app also shows which path produced the answer (Claude, agent, fallback or offline), the retrieved notes, the target features it used, the retrieved songs with scores, and a step-by-step pipeline log, which is also saved to logs/vibematch.log.
- **Where humans / testing check the AI:** Automated: check_answer checks every answer, and check_picks checks the agent's picks before the final answer.
Tests: 37 pytest tests cover retrieval, the guardrails, self-correction, the fallback, the agent's step limit, rejection of bad tool input, and API key setup. They run offline with a fake model.
Human: A person can compare each answer against the retrieved notes and songs shown on the page, and review the pipeline log or logs/vibematch.log to see every step, rejection and fallback.

## Setup Instructions

### Requirements


- Python 3.11 or newer (tested on 3.13.7)
- Optional: [Ollama](https://ollama.com) for a free local AI model, or an Anthropic API key to use Claude. Without either, the app still runs and gives template answers built from retrieved data.

### Steps

1. [Clone the repo]

   ```bash
   git clone https://github.com/AkhilRB0204/applied-ai-system-project.git

   cd applied-ai-system-project
   ```

2. [Create and activate a virtual environment]

   ```bash
   python3 -m venv .venv

   source .venv/bin/activate # Windows: .venv\Scripts\activate
   ```

3. [Install dependencies]

   ```bash
   pip install -r requirements.txt
   ```

4. [Set up the AI model / configuration]

   ```bash
   cp .env.example .env # then paste your key after ANTHROPIC_API_KEY= to use Claude

   or, for the free local model instead:
   ollama pull qwen3:4b-instruct
   ```

5. [Run the app]

   ```bash
   streamlit run app.py # web page

   python -m src.main "chill music for studying" # command line (RAG)

   python -m src.main --agent "something sad for a rainy day" # agent mode
   ```

6. [Run the tests]

   ```bash
   python -m pytest


   ```

## Sample Interactions

### Example 1: RAG answer for a study request

**Input:**

```
RAG answer for a study request
```

**AI output:**

```
Focus Flow	LoRoom	lofi	focused	0.4	4.46	mood match (+1.50); energy 0.40 near target 0.40 (+1.50); valence 0.59 near target 0.60 (+0.98); acousticness 0.78 near target 0.80 (+0.48)
Library Rain	Paper Lanterns	lofi	chill	0.35	3.54	similar mood: chill (+0.75); energy 0.35 near target 0.40 (+1.35); valence 0.60 near target 0.60 (+1.00); acousticness 0.86 near target 0.80 (+0.44)
Midnight Coding	LoRoom	lofi	chill	0.42	3.52	similar mood: chill (+0.75); energy 0.42 near target 0.40 (+1.44); valence 0.56 near target 0.60 (+0.92); acousticness 0.71 near target 0.80 (+0.41)
Coffee Shop Stories	Slow Stereo	jazz	relaxed	0.37	3.35	similar mood: relaxed (+0.75); energy 0.37 near target 0.40 (+1.41); valence 0.71 near target 0.60 (+0.78); acousticness 0.89 near target 0.80 (+0.41)
Spacewalk Thoughts	Orbit Bloom	ambient	chill	0.28	3.17	similar mood: chill (+0.75); energy 0.28 near target 0.40 (+1.14); valence 0.65 near target 0.60 (+0.90); acousticness 0.92 near target 0.80 (+0.38)
```
Pipeline log (also saved to logs/vibematch.log)

    Agent running on qwen3:4b-instruct (free local model via Ollama)

    Step 1: search_notes(query='studying late night lofi') | plan: Find mood and genre targets for a study session with a calm, focused vibe.

    Step 2: find_songs(genre='lofi', mood='focused', energy=0.4, valence=0.6, acousticness=0.8, k=5) | plan: Find lofi, focused music with low energy and high valence, matching study notes.

    Step 3: check_picks(titles=['Focus Flow', 'Library Rain', 'Midnight Coding']) | plan: Verify these top-ranked lofi, focused songs match the study request criteria.

    Step 3: check_picks → {"ok": true, "problems": []}

    Step 4: final answer passed check_answer()

This shows the output for the request of study music which is music that is chill, relaxed, focused

### Example 2: something sad for a rainy day

**Input:** something sad for a rainy day

```
something sad for a rainy day
```

**AI output:**

```
Ashes in Winter	Hollow Pines	folk	sad	0.3	3.94	mood match (+1.50); energy 0.30 near target 0.30 (+1.50); valence 0.22 near target 0.25 (+0.94)
Glass Cathedral	Mira Static	trip hop	dreamy	0.38	1.96	energy 0.38 near target 0.30 (+1.26); valence 0.40 near target 0.25 (+0.70)
Moonlit Sonata No. 2	Elise Hartmann	classical	peaceful	0.18	1.74	energy 0.18 near target 0.30 (+1.14); valence 0.45 near target 0.25 (+0.60)
Velvet Hours	Amara Lane	r&b	romantic	0.52	1.73	similar mood: romantic (+0.75); energy 0.52 near target 0.30 (+0.84); valence 0.68 near target 0.25 (+0.14)
Library Rain	Paper Lanterns	lofi	chill	0.35	1.65	energy 0.35 near target 0.30 (+1.35); valence 0.60 near target 0.25 (+0.30)


    Agent running on qwen3:4b-instruct (free local model via Ollama)

    Step 1: search_notes(query='sad rainy day mood') | plan: Find notes on how to interpret a sad rainy day mood and suggested genre or targets for song matching.

    Step 2: find_songs(mood='sad', energy=0.3, valence=0.25, acousticness=0.8, k=5) | plan: Find songs with sad mood, low energy, and low valence to match a rainy day feeling.

    Step 3: check_picks(titles=['Ashes in Winter', 'Library Rain', 'Moonlit Sonata No. 2']) | plan: Verify these top picks match the sad rainy day request and were found in the initial search results.

    Step 3: check_picks → {"ok": true, "problems": []}

    Step 4: final answer passed check_answer()


```

## Design Decisions

| Decision | Why | Trade-off |
| Keyword retrieval over a small hand-written knowledge base (`knowledge_base.json`) instead of embeddings | Easy to read and test, needs no extra libraries, and you can see exactly why a note was retrieved | Misses synonyms and unfamiliar words. "Polka" matched nothing. |
| Code checks every answer (`check_answer`), allows one correction round, then falls back to a template | The model can't recommend a song that wasn't retrieved, and the user always gets an answer | It checks titles and format, not whether the reasons are true. A correction round costs an extra model call. |
| Model choice: Claude if an API key is set, otherwise a free local model (Ollama), otherwise an offline template | Anyone can run the project for free, and tests run offline with no key | A small local model writes looser reasons, and answer quality depends on which model is used. |
| Agent mode with an 8-step limit and validated tool inputs | Lets the model plan its own search while keeping it from looping or passing bad values | Slower than a single call: about 4 model calls per request instead of 1. |

## Testing Summary

**What worked:**

All 37 pytest tests pass offline, using a fake model. They cover retrieval, the guardrails, self-correction, the fallback, the agent's step limit, rejection of bad tool input, and API key setup.
- The checker caught made-up songs (e.g. "Made Up Song" is not one of the CANDIDATE SONGS), and the correction round fixed them. When the model kept failing, the template answer took over.
- API errors (e.g. `APIConnectionError`) fell back to the template instead of crashing.
- In agent mode, even the small local model followed the plan, called the tools, checked its picks, and passed `check_answer`.

**What didn't:**

- The checker verifies song titles, not the reasons given. In Example 2, the model called "Moonlit Sonata No. 2" melancholic even though the catalog labels it peaceful, and nothing flagged it.
- Keyword retrieval can't handle words outside the knowledge base. Requests like "polka" get no notes and 0.00 scores.
- The genre bias from VibeMatch 1.0 is still in the scorer: a genre label can outweigh the mood a user asks for (see the "Sad Banger" case in `model_card.md`).

**What I learned:**

Checks written in code are more reliable than instructions in the prompt. The prompt asks the model to use only retrieved songs, but the code is what guarantees it.
A fallback path means the app always gives a useful answer, even with no key, no internet or a failing model.
- Logging every step (`logs/vibematch.log`) made it easy to see exactly where a run went wrong: which notes were retrieved, which check failed, and why it fell back.
## Reflection

[Optional: limitations, ethics, future improvements.]
