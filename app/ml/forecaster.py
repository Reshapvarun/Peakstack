import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import joblib
import os
from datetime import datetime

class EnergyForecaster:
    """
    Predictive AI layer for the EMS.
    Now refactored for production inference: loads pre-trained models.
    """
    def __init__(self, model_dir="models/ml"):
        self.model_dir = model_dir
        self.load_model = self._load_model("load_model.joblib")
        self.solar_model = self._load_model("solar_model.joblib")

    def _load_model(self, filename):
        path = os.path.join(self.model_dir, filename)
        if os.path.exists(path):
            return joblib.load(path)
        print(f"Warning: Model {filename} not found at {path}. Please run train_models.py")
        return None

    def _create_features(self, df):
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['load_lag_24h'] = df['load_kw'].shift(96)
        df['solar_lag_24h'] = df['solar_kw'].shift(96)
        return df.fillna(0)

    def forecast(self, current_df):
        """
        Generates forecasts for the next 24 hours (96 intervals).
        """
        if self.load_model is None or self.solar_model is None:
            # Fallback to naive average if models are missing
            load_avg = current_df['load_kw'].mean()
            solar_avg = current_df['solar_kw'].mean()
            return np.full(96, load_avg), np.full(96, solar_avg)

        feat_df = self._create_features(current_df)
        features = ['hour', 'day_of_week', 'month', 'load_lag_24h', 'solar_lag_24h']
        forecast_df = feat_df.tail(96)[features]

        load_preds = self.load_model.predict(forecast_df)
        solar_preds = self.solar_model.predict(forecast_df)

        return np.maximum(load_preds, 0), np.maximum(solar_preds, 0)
