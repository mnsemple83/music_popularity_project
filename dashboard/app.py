# dashboard/app.py
'''Interactive dashboard with Streamlit.'''

import streamlit as st
import os
from dotenv import load_dotenv
from src.spotify_client import get_spotify_client_interactive, safe_audio_features, AuthorizationRequired
from src.spotify_client import _build_oauth  # only for handling redirect flow in Streamlit

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

st.set_page_config(page_title="Music Popularity Predictor", layout="wide")
st.title("🎵 Music Popularity Predictor — Streamlit + Spotify OAuth")

# Step 0: show status
st.sidebar.header("Spotify Auth")
sp, auth_url = get_spotify_client_interactive()

if sp is None:
    st.sidebar.write("Not authenticated with Spotify.")
    st.sidebar.markdown(f"[Click here to login to Spotify]({auth_url})")
    st.sidebar.info("After logging in, Spotify will redirect you back to this app (http://localhost:8501).")
    st.info("Please click 'Login to Spotify' in the sidebar, log in, then return to the app.")
    # Early return so the rest of the app doesn't run until user authorizes
    st.stop()

st.sidebar.success("Authenticated ✅")

# Simple input to fetch tracks by artist name
artist_name = st.text_input("Enter artist name (e.g., The Weeknd):", "The Weeknd")
num_tracks = st.slider("Max tracks to fetch (approx)", 1, 50, 20)

if st.button("Fetch & Analyze"):
    with st.spinner("Searching Spotify..."):
        # Search the artist and fetch tracks (simple example)
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

                # Get audio features using safe wrapper
                features_list = safe_audio_features(sp, track_ids)
                # Build a dataframe
                import pandas as pd
                df = pd.DataFrame(features_list)
                df["track_name"] = track_names
                st.subheader("Audio features")
                st.dataframe(df.head())
        except AuthorizationRequired as auth_exc:
            st.error("Authorization required. Please login again.")
            st.sidebar.markdown(f"[Login to Spotify]({auth_exc.auth_url})")
        except Exception as e:
            st.error(f"Error fetching tracks: {e}")
