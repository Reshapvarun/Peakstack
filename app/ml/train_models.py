import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import joblib
import os
from datetime import datetime

def train_and_save_models():
    """
    Standalone training script to build the ML models.
    In a production SaaS, this would run as a scheduled job or triggered by new data.
    """
    print("Starting ML Model Training Pipeline...")

    # 1. Generate / Load Training Data
    from app.simulation.data_gen import generate_industrial_profile
    df = generate_industrial_profile(days=60) # 60 days for better generalization

    # 2. Feature Engineering
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['load_lag_24h'] = df['load_kw'].shift(96)
    df['solar_lag_24h'] = df['solar_kw'].shift(96)
    df = df.fillna(0)

    features = ['hour', 'day_of_week', 'month', 'load_lag_24h', 'solar_lag_24h']
    model_dir = "models/ml"
    os.makedirs(model_dir, exist_ok=True)

    # 3. Train Load Model
    X = df[features]
    y_load = df['load_kw']
    load_model = xgb.XGBRegressor(objective='reg:absoluteerror', n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42)
    load_model.fit(X, y_load)
    joblib.dump(load_model, os.path.join(model_dir, "load_model.joblib"))
    print("Load Model Trained & Saved")

    # 4. Train Solar Model
    y_solar = df['solar_kw']
    solar_model = xgb.XGBRegressor(objective='reg:absoluteerror', n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42)
    solar_model.fit(X, y_solar)
    joblib.dump(solar_model, os.path.join(model_dir, "solar_model.joblib"))
    print("Solar Model Trained & Saved")

if __name__ == "__main__":
    train_and_save_models()
