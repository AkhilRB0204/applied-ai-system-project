# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does

## How The System Works

The recommender is user preference based: it compares each song's attributes to the user's taste profile, gives every song a score, and returns the highest-scoring songs based on the user preferences which is based on what they engage with, the songs they listen to the most given the artist, genre, album.

### Features used

- **Song:** `genre`, `mood`, `energy`, `valence`, `acousticness`
- **User profile:** favorite genre, favorite mood, target energy, and optionally a target valence and whether they like acoustic music

`tempo_bpm` and `danceability` are not scored. In this dataset they track energy very closely (correlation 0.96 and 0.86), so they would count the same signal again.

### Algorithm Recipe

Each song starts at 0 points and earns:

| Rule | Points | Max |
|---|---|---|
| **Genre match**: exact match | +2.0 | 2.0 |
| **Genre match**: partial match, where one genre name contains the other (e.g. "pop" vs. "indie pop") | +1.0 | |
| **Mood match**: exact match | +1.5 | 1.5 |
| **Energy closeness**: `1.5 × (1 − abs(song.energy − target_energy))` | 0–1.5 | 1.5 |
| **Valence closeness** (if the user gives a target): `1.0 × (1 − abs(song.valence − target_valence))` | 0–1.0 | 1.0 |
| **Acoustic fit** (if the user gives a preference): +0.5 when `likes_acoustic` matches whether `acousticness ≥ 0.6` | +0.5 | 0.5 |

**Maximum score: 6.5** (4.5 for a profile that only gives genre, mood and energy).

Why these weights:
- **Genre is weighted highest** because it's the user's most explicit preference.
- **Mood comes next** because it captures context (chill vs. focused) that the numeric features can't tell apart.
- **Energy and valence describe the vibe.** Energy measures intensity, and valence measures how positive the song sounds. Their closeness scores mean a song that's nearly right still earns partial credit, so a near miss isn't scored as a complete miss.
- **Acoustic fit is a small tiebreaker.** Acousticness is almost the inverse of energy here (−0.99), so a larger weight would double-count.

### Choosing recommendations

1. Score every song with the recipe above.
2. Sort the songs from highest to lowest score. If two songs tie, the one with the closer energy goes first.
3. Return the top `k` songs, each with a short explanation listing the rules it earned points from (e.g. "genre match (+2.0), mood match (+1.5), energy close to target (+1.47)").

### Example

For the profile `{genre: "pop", mood: "happy", energy: 0.8}`:

| Rank | Song | Score | Why |
|---|---|---|---|
| 1 | Sunrise City (pop/happy) | 4.97 | genre + mood + energy |
| 2 | Rooftop Lights (indie pop/happy) | 3.94 | partial genre + mood + energy |
| 3 | Gym Hero (pop/intense) | 3.30 | genre + energy |

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



