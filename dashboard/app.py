# dashboard/app.py
'''Interactive dashboard with Streamlit.'''

import streamlit as st
import sys
import os
from dotenv import load_dotenv
load_dotenv()

from src.spotify_client import spotify_login_flow, safe_audio_features

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



st.set_page_config(page_title="Music Popularity Predictor", layout="wide")
st.title("🎵 Music Popularity Predictor — Streamlit + Spotify OAuth")

# Authenticate with Spotify
st.sidebar.header("Spotify Auth")
sp = spotify_login_flow(st)

if sp is None:
    st.sidebar.warning("Not authenticated with Spotify.")
    st.info("Please log in using the link in the sidebar.")
    st.stop()

st.sidebar.success("Authenticated ✅")

# Main functionality
artist_name = st.text_input("Enter artist name (e.g., The Weeknd):", "The Weeknd")
num_tracks = st.slider("Max tracks to fetch (approx)", 1, 50, 20)

if st.button("Fetch & Analyze"):
    with st.spinner("Searching Spotify..."):
        try:
            results = sp.search(q=f"artist:{artist_name}", type="track", limit=num_tracks)
            items = results.get("tracks", {}).get("items", [])

            if not items:
                st.warning("No tracks found for that artist.")
            else:
                track_ids = [t["id"] for t in items]
                track_names = [f"{t['name']} — {t['artists'][0]['name']}" for t in items]

                st.write(f"Found {len(track_ids)} tracks.")
                st.dataframe({"track_name": track_names, "track_id": track_ids})

                # Get audio features
                features_list = safe_audio_features(sp, track_ids)

                import pandas as pd
                df = pd.DataFrame(features_list)
                df["track_name"] = track_names

                st.subheader("Audio features")
                st.dataframe(df)
        except Exception as e:
            st.error(f"Error fetching tracks: {e}")
