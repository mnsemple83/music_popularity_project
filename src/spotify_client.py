 # src/spotify_client.py
"""
Streamlit-friendly Spotify client using user OAuth (SpotifyOAuth).
Provides:
- get_spotify_client(streamlit_session=None): returns an authenticated spotipy.Spotify instance
- safe_audio_features(sp, track_ids): fetches audio features for up to 100 track ids and handles API errors
"""

import os
import time
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

load_dotenv()  # loads .env from project root

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
# Use the localhost base (no path) — must match exact Redirect URI in Spotify Dashboard
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8501")

# Minimal scope is fine for public data that still requires a user token.
# If you later want to access playlists or user libraries, add scopes like
# "user-top-read playlist-read-private"
SCOPE = os.getenv("SPOTIFY_SCOPE", "user-read-private")

OAUTH_CACHE_PATH = os.getenv("SPOTIFY_OAUTH_CACHE", ".cache-spotify")

def _build_oauth(cache_path: str = None):
    """Create a SpotifyOAuth object."""
    cache = cache_path or OAUTH_CACHE_PATH
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=cache,
        show_dialog=False  # set True to always force re-login
    )

def get_spotify_client(session_state=None):
    """
    Return an authenticated spotipy.Spotify client using SpotifyOAuth.

    If using Streamlit, pass st.session_state into this function so we can store
    temporary tokens there if desired. If not provided, token caching uses the local cache_path.
    """
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise RuntimeError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in environment (.env)")

    oauth = _build_oauth()

    # Try to get cached token
    token_info = oauth.get_cached_token()
    if token_info:
        access_token = token_info.get("access_token")
        expires_at = token_info.get("expires_at", 0)
        # Refresh if token expired (buffer 30s)
        if expires_at - int(time.time()) < 30:
            token_info = oauth.refresh_access_token(token_info["refresh_token"])
            access_token = token_info.get("access_token")
    else:
        # No cached token -> user must authorize via browser flow
        auth_url = oauth.get_authorize_url()
        # Return the auth_url for the UI to open; the app must handle the redirect
        # Note: in Streamlit, you can call st.experimental_set_query_params or open the URL in a link/button
        raise AuthorizationRequired(auth_url)

    sp = spotipy.Spotify(auth=access_token)
    return sp

def get_spotify_client_interactive(streamlit=None):
    """
    Streamlit-friendly wrapper that:
    - Returns (sp, auth_url) tuple.
      - If sp is not None: authenticated client ready to use.
      - If sp is None: auth_url is provided and the Streamlit UI should redirect/open it.
    """
    oauth = _build_oauth()

    # Try cached token
    token_info = oauth.get_cached_token()
    if token_info:
        access_token = token_info.get("access_token")
        expires_at = token_info.get("expires_at", 0)
        if expires_at - int(time.time()) < 30:
            try:
                token_info = oauth.refresh_access_token(token_info["refresh_token"])
                access_token = token_info.get("access_token")
            except Exception:
                # If refresh fails, clear cache and require auth
                try:
                    oauth.cache_handler.delete()
                except Exception:
                    pass
                token_info = None

    if token_info:
        return spotipy.Spotify(auth=token_info["access_token"]), None

    # No token: provide authorize URL so UI can open it
    auth_url = oauth.get_authorize_url()
    return None, auth_url

def safe_audio_features(sp, track_ids):
    """
    Fetch audio features for up to 100 track IDs (Spotify limits).
    Returns list of dicts (may contain None entries when a track is unavailable).
    Handles 403/429/500 and retries with backoff where reasonable.
    """
    if not sp:
        raise ValueError("Spotify client (sp) is None")

    if isinstance(track_ids, str):
        track_ids = [track_ids]
    # Spotify allows up to 100 ids per call
    result = []
    batch_size = 50
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        backoff = 1
        while True:
            try:
                features = sp.audio_features(batch)
                # features is a list with same length as batch (or None entries)
                result.extend(features or [None] * len(batch))
                break
            except SpotifyException as e:
                status = getattr(e, "http_status", None)
                # Rate limit
                if status == 429:
                    retry_after = int(e.headers.get("Retry-After", backoff)) if hasattr(e, "headers") else backoff
                    time.sleep(retry_after)
                    backoff = min(backoff * 2, 60)
                    continue
                # Forbidden/403: usually means token lacks permissions or token is invalid
                if status == 403:
                    raise AuthorizationRequired("403 Forbidden - audio-features requires user OAuth token.")
                # Server errors: retry a few times
                if status and 500 <= status < 600:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 30)
                    continue
                # Otherwise re-raise
                raise
            except Exception:
                # Generic safe retry
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
    return result

class AuthorizationRequired(Exception):
    """Raised when the user must authorize the application (contains the auth_url as message)."""
    def __init__(self, auth_url):
        self.auth_url = auth_url
        super().__init__(f"Authorization required: {auth_url}")


