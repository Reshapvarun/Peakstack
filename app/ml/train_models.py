import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
import os
from datetime import datetime

def train_and_save_models():
    """
    Standalone training script to build the ML models.
    Updated for Phase 1: Incorporating short-term lags, rolling means, and weather.
    """
    print("Starting ML Model Training Pipeline (Phase 1 Upgrades)...")

    # 1. Generate / Load Training Data
    from app.simulation.data_gen import generate_industrial_profile
    df = generate_industrial_profile(days=90) # Increased to 90 days for better pattern recognition

    # 2. Feature Engineering
    print("Engineering features...")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    
    # Lags (assuming 15-min intervals)
    df['load_lag_15m'] = df['load_kw'].shift(1)
    df['load_lag_1h'] = df['load_kw'].shift(4)
    df['load_lag_24h'] = df['load_kw'].shift(96)
    
    df['solar_lag_15m'] = df['solar_kw'].shift(1)
    df['solar_lag_1h'] = df['solar_kw'].shift(4)
    df['solar_lag_24h'] = df['solar_kw'].shift(96)

    # Rolling Means
    df['load_rolling_3h'] = df['load_kw'].shift(1).rolling(window=12).mean()
    df['solar_rolling_3h'] = df['solar_kw'].shift(1).rolling(window=12).mean()

    # Drop NaNs created by shifts
    df = df.dropna().reset_index(drop=True)

    # Define Feature Sets
    load_features = [
        'hour', 'day_of_week', 'month', 
        'load_lag_15m', 'load_lag_1h', 'load_lag_24h', 'load_rolling_3h',
        'temperature_c'
    ]
    
    solar_features = [
        'hour', 'month',
        'solar_lag_15m', 'solar_lag_1h', 'solar_lag_24h', 'solar_rolling_3h',
        'temperature_c', 'ghi'
    ]

    model_dir = "models/ml"
    os.makedirs(model_dir, exist_ok=True)

    # 3. Train Load Model
    print("Training Load Model...")
    X_load = df[load_features]
    y_load = df['load_kw']
    
    load_model = xgb.XGBRegressor(
        objective='reg:absoluteerror', 
        n_estimators=300, 
        learning_rate=0.05, 
        max_depth=6, 
        random_state=42
    )
    load_model.fit(X_load, y_load)
    joblib.dump(load_model, os.path.join(model_dir, "load_model.joblib"))
    print("Load Model Trained & Saved.")

    # 4. Train Solar Model
    print("Training Solar Model...")
    X_solar = df[solar_features]
    y_solar = df['solar_kw']
    
    solar_model = xgb.XGBRegressor(
        objective='reg:absoluteerror', 
        n_estimators=300, 
        learning_rate=0.05, 
        max_depth=6, 
        random_state=42
    )
    solar_model.fit(X_solar, y_solar)
    joblib.dump(solar_model, os.path.join(model_dir, "solar_model.joblib"))
    print("Solar Model Trained & Saved.")

if __name__ == "__main__":
    train_and_save_models()
