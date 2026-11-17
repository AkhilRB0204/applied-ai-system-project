import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

# Columns in songs.csv that need converting from text so we can do math with them.
INT_FIELDS = ["id"]
FLOAT_FIELDS = ["energy", "tempo_bpm", "valence", "danceability", "acousticness"]

# Algorithm Recipe weights (see README "How The System Works").
GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.5
NUMERIC_WEIGHTS = {"energy": 1.5, "valence": 1.0, "acousticness": 0.5}

# Moods in the same family earn half the mood points.
MOOD_FAMILIES = {
    "calm": {"chill", "relaxed", "peaceful", "dreamy", "focused"},
    "upbeat": {"happy", "joyful", "euphoric", "energetic", "confident"},
    "intense": {"intense", "angry", "moody"},
    "tender": {"sad", "nostalgic", "romantic"},
}

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        """Store the catalog of Song objects to recommend from."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for this user, highest score first."""
        prefs = _profile_to_prefs(user)
        by_id = {song.id: song for song in self.songs}
        ranked = recommend_songs(prefs, [asdict(song) for song in self.songs], k)
        return [by_id[song_dict["id"]] for song_dict, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable explanation of why this song scored the way it did."""
        score, reasons = score_song(_profile_to_prefs(user), asdict(song))
        return f"Score {score:.2f}: " + ", ".join(reasons)


def _profile_to_prefs(user: UserProfile) -> Dict:
    """Convert a UserProfile into the user_prefs dict used by score_song."""
    return {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "energy": user.target_energy,
        # likes_acoustic is a yes/no flag, so map it to a target value.
        "acousticness": 0.8 if user.likes_acoustic else 0.2,
    }

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv into a list of dicts, converting numeric columns to int/float."""
    print(f"Loading songs from {csv_path}...")
    songs = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            for field in INT_FIELDS:
                row[field] = int(row[field])
            for field in FLOAT_FIELDS:
                row[field] = float(row[field])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against the user's prefs; return (score, list of reasons)."""
    score = 0.0
    reasons = []

    # Genre: full points for an exact match, half for a partial one ("pop" / "indie pop").
    # An empty genre or mood (e.g. a free-text request that never named one) earns nothing,
    # instead of partially matching every song because "" is a substring of everything.
    genre, song_genre = user_prefs.get("genre", "").lower(), song["genre"].lower()
    if not genre:
        pass
    elif genre == song_genre:
        score += GENRE_WEIGHT
        reasons.append(f"genre match (+{GENRE_WEIGHT:.2f})")
    elif genre in song_genre or song_genre in genre:
        score += GENRE_WEIGHT / 2
        reasons.append(f"similar genre: {song['genre']} (+{GENRE_WEIGHT / 2:.2f})")

    # Mood: full points for an exact match, half for the same mood family.
    mood, song_mood = user_prefs.get("mood", "").lower(), song["mood"].lower()
    if not mood:
        pass
    elif mood == song_mood:
        score += MOOD_WEIGHT
        reasons.append(f"mood match (+{MOOD_WEIGHT:.2f})")
    elif _mood_family(mood) and _mood_family(mood) == _mood_family(song_mood):
        score += MOOD_WEIGHT / 2
        reasons.append(f"similar mood: {song['mood']} (+{MOOD_WEIGHT / 2:.2f})")

    # Numeric features: points for being close to the target, not for being high or low.
    for feature, weight in NUMERIC_WEIGHTS.items():
        if feature not in user_prefs:
            continue
        points = weight * _closeness(song[feature], user_prefs[feature])
        score += points
        if points > 0:
            reasons.append(f"{feature} {song[feature]:.2f} near target {user_prefs[feature]:.2f} (+{points:.2f})")

    return score, reasons


def _closeness(value: float, target: float) -> float:
    """Return 1.0 for an exact match, dropping to 0 at a distance of 0.5 or more."""
    return max(0.0, 1 - 2 * abs(value - target))


def _mood_family(mood: str) -> Optional[str]:
    """Return the name of the family a mood belongs to, or None if it has none."""
    for family, moods in MOOD_FAMILIES.items():
        if mood in moods:
            return family
    return None


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, rank highest first (ties: closer energy), and return the top k."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, "; ".join(reasons)))

    ranked = sorted(
        scored,
        key=lambda item: (-item[1], abs(item[0]["energy"] - user_prefs.get("energy", 0.5))),
    )
    return ranked[:k]
