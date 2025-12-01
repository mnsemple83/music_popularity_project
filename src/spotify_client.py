 # src/spotify_client.py
import os
from dotenv import load_dotenv

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = "user-read-private"
CACHE_PATH = ".spotify_cache"

import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import urlparse, parse_qs

def build_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_PATH
    )


def spotify_login_flow(st):
    """
    Handles the full Streamlit OAuth login flow:
    - If user has a valid cached token -> return Spotify client
    - If redirect contains ?code -> process and save token
    - Otherwise -> show login link
    """
    oauth = build_oauth()

    # 1. Check for cached token
    token_info = oauth.get_cached_token()
    if token_info:
        access_token = token_info["access_token"]
        expires_at = token_info["expires_at"]
        if expires_at - int(time.time()) < 30:
            token_info = oauth.refresh_access_token(token_info["refresh_token"])
            access_token = token_info["access_token"]
        return spotipy.Spotify(auth=access_token)

    # 2. Check for redirected ?code=xxx
    params = st.query_params
    if "code" in params:
        code = params["code"]
        token_info = oauth.get_access_token(code)
        access_token = token_info["access_token"]
        return spotipy.Spotify(auth=access_token)

    # 3. Otherwise show login URL
    auth_url = oauth.get_authorize_url()
    st.sidebar.markdown(f"[Login to Spotify]({auth_url})")
    return None


def safe_audio_features(sp, track_ids):
    """
    Safe wrapper fetching audio features with retry logic.
    """
    if not sp:
        raise ValueError("Spotify client is None")

    if isinstance(track_ids, str):
        track_ids = [track_ids]

    results = sp.audio_features(track_ids)
    return results
