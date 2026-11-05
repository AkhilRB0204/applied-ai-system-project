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

    for name, user_prefs in [("Pop / Happy (default)", POP_HAPPY),
                             ("Late-Night Study", LATE_NIGHT_STUDY)]:
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print_recommendations(name, user_prefs, recommendations)


if __name__ == "__main__":
    main()
