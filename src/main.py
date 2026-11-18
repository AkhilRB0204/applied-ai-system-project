"""
VibeMatch command-line app.

    python -m src.main "chill music for studying"   # ask in plain English (RAG)
    python -m src.main                              # interactive: keep asking
    python -m src.main --profiles                   # original 8-profile demo
    python -m src.main --agent "..."                # agentic workflow: model plans + uses tools
    python -m src.main --offline "..."              # no AI model, template answer

Free-text requests go through the RAG pipeline in src/rag.py: retrieve notes
and candidate songs, have the AI model write the answer from them, then check
it. The model is a free local one via Ollama by default, or Claude if an
Anthropic API key is set (see VIBEMATCH_PROVIDER in .env.example).
With --agent, the model instead plans its own steps, calls retrieval tools
(src/agent.py) and checks its picks before answering.
Every run is logged to logs/vibematch.log.
"""

import argparse
import logging
import sys
from pathlib import Path

# Works both as `python -m src.main` and `python src/main.py`.
try:
    from src.agent import ask_agent
    from src.rag import ask, check_api_key, load_knowledge_base, make_client
    from src.recommender import load_songs, recommend_songs
except ImportError:
    from agent import ask_agent
    from rag import ask, check_api_key, load_knowledge_base, make_client
    from recommender import load_songs, recommend_songs

SOURCE_LABELS = {
    "claude": "written by {model} from retrieved data",
    "agent": "written by the {model} agent after planning, tool use and checks",
    "offline": "offline template",
    "fallback": "fallback template",
}

SONGS_PATH = "data/songs.csv"
KNOWLEDGE_BASE_PATH = "data/knowledge_base.json"
LOG_PATH = Path("logs/vibematch.log")

logger = logging.getLogger("vibematch")


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


def print_rag_result(result) -> None:
    """Show the answer, the data it was built from, and the pipeline log."""
    print("=" * 64)
    print(f"Request: {result.query}")
    print("=" * 64)
    label = SOURCE_LABELS.get(result.source, result.source).format(model=result.model or "AI model")
    print(f"Answer ({label}):")
    print(result.answer)
    print("\nBased on retrieved notes:")
    for note in result.notes or [{"title": "(none)"}]:
        print(f"  - {note['title']}")
    print("Based on retrieved songs:")
    for song, score, _ in result.candidates:
        print(f"  - {song['title']} by {song['artist']}  [{song['genre']} / {song['mood']}]  score {score:.2f}")
    print("\nPipeline log:")
    for line in result.log:
        print(f"  * {line}")
    print()


def setup_logging(verbose: bool) -> None:
    """Log everything to logs/vibematch.log; show warnings (or all with -v) on screen."""
    LOG_PATH.parent.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    console = logging.StreamHandler()
    console.setLevel(logging.INFO if verbose else logging.WARNING)
    console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    root = logging.getLogger("vibematch")
    root.setLevel(logging.INFO)
    root.handlers = [file_handler, console]


def run_profiles(songs: list) -> None:
    """Original demo: top-5 recommendations for each hand-written profile."""
    for name, user_prefs in PROFILES:
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print_recommendations(name, user_prefs, recommendations)


def run_request(query: str, songs: list, knowledge_base: list, client, agent: bool = False) -> None:
    """Answer one free-text request; report bad input instead of crashing."""
    answer_fn = ask_agent if agent else ask
    try:
        print_rag_result(answer_fn(query, songs, knowledge_base, client))
    except ValueError as error:
        print(f"Sorry: {error}\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="VibeMatch music recommender")
    parser.add_argument("request", nargs="*", help="what you want to listen to, in plain English")
    parser.add_argument("--profiles", action="store_true", help="run the original 8-profile demo")
    parser.add_argument("--agent", action="store_true", help="agentic mode: the model plans, calls tools, checks picks")
    parser.add_argument("--offline", action="store_true", help="do not call an AI model; use template answers")
    parser.add_argument("-v", "--verbose", action="store_true", help="print log messages to the screen")
    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    try:
        songs = load_songs(SONGS_PATH)
        knowledge_base = load_knowledge_base(KNOWLEDGE_BASE_PATH)
    except (OSError, ValueError, KeyError) as error:
        logger.error("Could not load data: %s", error)
        print(f"Could not load data files: {error}\nRun the app from the project folder.")
        return 1
    print(f"Loaded songs: {len(songs)}\n")
    logger.info("Started: %s", " ".join(sys.argv[1:]) or "(interactive)")

    if args.profiles:
        run_profiles(songs)
        return 0

    client = None if args.offline else make_client()
    if client is None:
        print("Running offline: answers are templates built from retrieved data.\n")
    else:
        ok, message = check_api_key(client)
        if not ok:
            logger.error("Model check failed: %s", message)
            print(f"{message}\nOr run with --offline to use template answers.")
            return 1
        logger.info("Model check passed: %s", message)
        print(f"{message}\n")

    if args.request:
        run_request(" ".join(args.request), songs, knowledge_base, client, args.agent)
        return 0

    while True:
        try:
            query = input("What do you want to listen to? (blank to quit) ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            break
        run_request(query, songs, knowledge_base, client, args.agent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
