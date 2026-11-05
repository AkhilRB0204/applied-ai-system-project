"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

# Works both as `python -m src.main` and `python src/main.py`.
try:
    from src.recommender import load_songs, recommend_songs
except ImportError:
    from recommender import load_songs, recommend_songs


# Default profile: upbeat pop listener.
POP_HAPPY = {"genre": "pop", "mood": "happy", "energy": 0.8}

# Taste profile: "late-night study session"
# Target values for each scored feature. Calm, mildly positive,
# acoustic-leaning background music.
LATE_NIGHT_STUDY = {
    "genre": "lofi",        # categorical: +2.0 exact, +1.0 partial
    "mood": "chill",        # categorical: +1.5 exact, +0.75 same mood family
    "energy": 0.40,         # target 0-1: low intensity, but not sleepy
    "valence": 0.60,        # target 0-1: slightly positive, not sad or hyper
    "acousticness": 0.80,   # target 0-1: warm, mostly acoustic sound
}

HIGH_ENERGY_POP = {"genre": "pop", "mood": "happy", "energy": 0.85, "valence": 0.85, "acousticness": 0.15}
DEEP_INTENSE_ROCK = {"genre": "rock", "mood": "intense", "energy": 0.92, "valence": 0.40, "acousticness": 0.10}

# Adversarial / edge-case profiles: designed to see if the scoring can be tricked.
# Conflicting: a "sad" mood but a very high energy target.
SAD_BANGER = {"genre": "pop", "mood": "sad", "energy": 0.90, "valence": 0.20}
# Unknown labels: no song is k-pop or "hype", but "k-pop" contains "pop".
UNKNOWN_KPOP = {"genre": "k-pop", "mood": "hype", "energy": 0.80}
# Spelling variant: "lo-fi" instead of "lofi" in the CSV.
LOFI_TYPO = {"genre": "lo-fi", "mood": "chill", "energy": 0.40}
# Contradictory labels: calm classical genre with an angry mood.
ANGRY_CLASSICAL = {"genre": "classical", "mood": "angry", "energy": 0.50, "valence": 0.50, "acousticness": 0.50}

PROFILES = [
    ("Pop / Happy (default)", POP_HAPPY),
    ("High-Energy Pop", HIGH_ENERGY_POP),
    ("Chill Lofi (late-night study)", LATE_NIGHT_STUDY),
    ("Deep Intense Rock", DEEP_INTENSE_ROCK),
    ("Adversarial: Sad Banger (sad mood, 0.9 energy)", SAD_BANGER),
    ("Adversarial: Unknown K-Pop / hype", UNKNOWN_KPOP),
    ("Adversarial: 'lo-fi' spelling", LOFI_TYPO),
    ("Adversarial: Angry Classical", ANGRY_CLASSICAL),
]


def print_recommendations(name: str, user_prefs: dict, recommendations: list) -> None:
    """Print a ranked, explained list of recommendations for one profile."""
    print("=" * 64)
    print(f"Profile: {name}")
    print("  " + ", ".join(f"{key}={value}" for key, value in user_prefs.items()))
    print("=" * 64)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} by {song['artist']}  [{song['genre']} / {song['mood']}]")
        print(f"   Score: {score:.2f}")
        for reason in explanation.split("; "):
            print(f"     - {reason}")
    print()


def main() -> None:
    """Load the catalog and print top-5 recommendations for each profile."""
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}\n")

    for name, user_prefs in PROFILES:
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print_recommendations(name, user_prefs, recommendations)


if __name__ == "__main__":
    main()
