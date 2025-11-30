# src/spotify_api.py
'''Fetches data from the Spotify API using spotipy.'''

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from src.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

'''
def get_spotify_client():
    """Authenticate and return a Spotify API client."""
    auth_manager = SpotifyClientCredentials(
        client_id = SPOTIFY_CLIENT_ID,
        client_secret = SPOTIFY_CLIENT_SECRET
    )
    return spotipy.Spotify(auth_manager=auth_manager)
'''    
def fetch_tracks_by_artist(artist_name, limit=50):
    """Fetch metadata and audio features for
     tracks by a given artist."""
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:8501",
        scope="user-read-private"
    ))
    results = sp.search(q=f'artist:{artist_name}', type='track', 
        limit=limit)
    tracks = results['tracks']['items']
    
    track_data = []
    for track in tracks:
        audio_features = sp.audio_features(track['id'])[0]
        if audio_features:
            track_data.append({
                'artist': track['artists'][0]['name'],
                'track_name': track['name'],
                'popularity': track['popularity'],
                'release_date': track['album']['release_date'],
                **audio_features
            })
    return pd.DataFrame(track_data)
    
    
