# src/data_cleaning.py
'''Performs preprocessing and feature engineering.'''

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def clean_data(df):
    """Clean and normalize raw Spotify data."""
    df = df.drop_duplicates(subset=['track_name', 'artist'])
    df = df.dropna(subset=['popularity'])
    
    # Normalize numerical features
    num_cols = ['danceability', 'energy', 'loudness', 'tempo', 'valence']
    scaler = MinMaxScaler()
    df[num_cols] = scaler.fit_transform(df[num_cols])
    
    return df
    
    
