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
from src.rag import ask, load_knowledge_base, make_client  # noqa: E402
from src.recommender import load_songs, recommend_songs  # noqa: E402

SOURCE_LABELS = {
    "claude": "Written by Claude from retrieved data (RAG)",
    "agent": "Written by the Claude agent after planning, tool use and checks",
    "offline": "Offline template (no API key, or offline mode)",
    "fallback": "Fallback template (Claude's answer failed the checks or the API failed)",
}

st.set_page_config(page_title="VibeMatch", page_icon="🎵", layout="wide")
setup_logging(verbose=False)


@st.cache_data
def load_data():
    return load_songs("data/songs.csv"), load_knowledge_base("data/knowledge_base.json")


def get_client(api_key: str, offline: bool):
    """Client from the sidebar key, else from ANTHROPIC_API_KEY, else None (offline)."""
    if offline:
        return None
    if api_key:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    return make_client()


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
             "Agent: Claude plans its own steps, calls retrieval tools and checks its picks.",
    )
    api_key = st.text_input(
        "Anthropic API key (optional)", type="password",
        help="Used only for this session and never saved. Leave empty to use ANTHROPIC_API_KEY, if set.",
    )
    offline = st.toggle("Offline mode (don't call Claude)", value=False)
    client = get_client(api_key.strip(), offline)
    if client is None:
        st.info("Running offline: answers are templates built from retrieved data.")
    else:
        st.success("Claude is connected.")

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
            with st.spinner("Claude is planning and checking..." if mode == "Agent" else "Retrieving and generating..."):
                result = answer_fn(query, songs, knowledge_base, client)
        except ValueError as error:
            st.warning(str(error))
        except Exception as error:  # never show a raw traceback to the user
            st.error(f"Something went wrong: {error}. Details are in logs/vibematch.log.")
        else:
            label = SOURCE_LABELS.get(result.source, result.source)
            (st.success if result.source in ("claude", "agent") else st.info)(label)
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
