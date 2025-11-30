# src/modeling.py
'''Train a machine learning model to predict track popularity.'''

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

def train_model(df):
    """Train and evaluate a regression model to predict popularity."""
    features = ['danceability', 'energy', 'valence', 'tempo', 'acousticness']
    X = df[features]
    y = df['popularity']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegeressor(n_estimators=150, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    r2 = r2_score(y_test, y_pred)
    
    print(f"RMSE: {rmse:.2f}")
    print(f"R2 Score: {r2:.2f}")
    
    return model
