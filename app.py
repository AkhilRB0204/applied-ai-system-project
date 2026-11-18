"""
VibeMatch web app (Streamlit).

    streamlit run app.py      -> opens http://localhost:8501

Uses the same RAG pipeline (src/rag.py) and agent (src/agent.py) as the CLI.
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # data/ and logs/ paths are relative to the project folder

from src.agent import ask_agent  # noqa: E402
from src.main import PROFILES, setup_logging  # noqa: E402
from src.rag import ask, check_api_key, find_api_key, load_knowledge_base, make_client  # noqa: E402
from src.recommender import load_songs, recommend_songs  # noqa: E402

SOURCE_LABELS = {
    "claude": "Written by {model} from retrieved data (RAG)",
    "agent": "Written by the {model} agent after planning, tool use and checks",
    "offline": "Offline template (no AI model selected or available)",
    "fallback": "Fallback template (the model's answer failed the checks, or the model call failed)",
}

PROVIDERS = {
    "Free local model (Ollama)": "ollama",
    "Claude (paid API key)": "claude",
    "Offline (no AI)": "offline",
}

st.set_page_config(page_title="VibeMatch", page_icon="🎵", layout="wide")
setup_logging(verbose=False)


@st.cache_data
def load_data():
    return load_songs("data/songs.csv"), load_knowledge_base("data/knowledge_base.json")


@st.cache_data(ttl=30, show_spinner="Checking the AI model...")
def model_status(provider: str, key: str):
    """(ok, message) for a provider; ok is None in offline mode. Cached 30 s."""
    client = make_client(key or None, provider=provider)
    if client is None:
        return None, "No AI model"
    return check_api_key(client)


def songs_table(candidates):
    return pd.DataFrame([
        {
            "Title": song["title"], "Artist": song["artist"], "Genre": song["genre"], "Mood": song["mood"],
            "Energy": song["energy"], "Score": round(score, 2), "Why it matched": reasons or "nothing",
        }
        for song, score, reasons in candidates
    ])


try:
    songs, knowledge_base = load_data()
except (OSError, ValueError, KeyError) as error:
    st.error(f"Could not load data files: {error}")
    st.stop()

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Settings")
    mode = st.radio(
        "Mode",
        ["RAG", "Agent"],
        help="RAG: fixed retrieve → generate → check pipeline. "
             "Agent: the model plans its own steps, calls retrieval tools and checks its picks.",
    )
    provider = PROVIDERS[st.radio(
        "AI model", list(PROVIDERS),
        help="Ollama runs a free model on your computer (no key, no cost). "
             "Claude needs a paid API key. Offline uses template answers only.",
    )]
    api_key = ""
    if provider == "claude":
        api_key = st.text_input(
            "Anthropic API key (optional)", type="password",
            help="Overrides ANTHROPIC_API_KEY from .env for this session only; never saved.",
        ).strip()
        if not find_api_key(api_key):
            st.warning("No API key: add ANTHROPIC_API_KEY to .env or paste one above.")
    ok, message = model_status(provider, find_api_key(api_key) if provider == "claude" else "")
    if ok is None:
        client = None
        st.info("Offline: answers are templates built from retrieved data.")
    elif not ok:
        client = None
        st.error(message)
        st.caption("Using template answers until this is fixed. Click Rerun after fixing it.")
    else:
        client = make_client(api_key or None, provider=provider)
        st.success(message)

st.title("🎵 VibeMatch")
st.caption("Describe what you want to listen to. Answers come only from songs and notes retrieved from this project's data.")

tab_ask, tab_profiles, tab_catalog = st.tabs(["Ask", "Profile demo", "Catalog"])

# ---------------------------------------------------------------- ask
with tab_ask:
    with st.form("ask"):
        query = st.text_input("Your request", placeholder="e.g. chill lo-fi music for studying late at night")
        submitted = st.form_submit_button("Recommend")

    if submitted:
        answer_fn = ask_agent if mode == "Agent" else ask
        try:
            with st.spinner("The agent is planning and checking..." if mode == "Agent" else "Retrieving and generating..."):
                result = answer_fn(query, songs, knowledge_base, client)
        except ValueError as error:
            st.warning(str(error))
        except Exception as error:  # never show a raw traceback to the user
            st.error(f"Something went wrong: {error}. Details are in logs/vibematch.log.")
        else:
            label = SOURCE_LABELS.get(result.source, result.source).format(model=result.model or "AI model")
            (st.success if result.source in ("claude", "agent") else st.info)(label)
            log_text = " ".join(result.log)
            if "AuthenticationError" in log_text:
                st.error("Claude rejected the API key (401). Check that you pasted a complete, active key "
                         "from platform.claude.com → API Keys. Showing the template answer instead.")
            elif "PermissionDeniedError" in log_text or "credit balance" in log_text.lower():
                st.error("The API key works but the account can't make requests. Check Billing / credits "
                         "on platform.claude.com.")
            elif "API error" in log_text:
                st.error("The AI model call failed; see the pipeline log below for details.")
            st.subheader("Recommendation")
            st.text(result.answer)

            left, right = st.columns(2)
            with left:
                st.subheader("Retrieved notes")
                if result.notes:
                    for note in result.notes:
                        with st.expander(note["title"]):
                            st.write(note["text"])
                else:
                    st.write("No notes matched.")
            with right:
                st.subheader("Targets used")
                st.json(result.prefs or {})

            st.subheader("Retrieved songs")
            st.dataframe(songs_table(result.candidates), hide_index=True, use_container_width=True)

            with st.expander("Pipeline log (also saved to logs/vibematch.log)", expanded=mode == "Agent"):
                for line in result.log:
                    st.markdown(f"- {line}")

# ---------------------------------------------------------------- profiles
with tab_profiles:
    st.write("The original VibeMatch 1.0 scorer on hand-written profiles, including adversarial ones. No AI involved.")
    names = [name for name, _ in PROFILES]
    choice = st.selectbox("Profile", names)
    prefs = dict(PROFILES)[choice]
    st.json(prefs)
    st.dataframe(
        songs_table([(s, score, reasons) for s, score, reasons in recommend_songs(prefs, songs, k=5)]),
        hide_index=True, use_container_width=True,
    )

# ---------------------------------------------------------------- catalog
with tab_catalog:
    st.write(f"{len(songs)} songs in `data/songs.csv`.")
    st.dataframe(pd.DataFrame(songs), hide_index=True, use_container_width=True)
