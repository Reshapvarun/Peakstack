import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime
try:
    import shap
except ImportError:
    shap = None

class EnergyForecaster:
    """
    Predictive AI layer for the EMS.
    Upgraded for Phase 3: Caching SHAP explainers for high-performance Enterprise XAI.
    """
    def __init__(self, model_dir="models/ml"):
        self.model_dir = model_dir
        self.load_model = self._load_model("load_model.joblib")
        self.solar_model = self._load_model("solar_model.joblib")
        
        self.load_features = [
            'hour', 'day_of_week', 'month', 
            'load_lag_15m', 'load_lag_1h', 'load_lag_24h', 'load_rolling_3h',
            'temperature_c'
        ]
        
        self.solar_features = [
            'hour', 'month',
            'solar_lag_15m', 'solar_lag_1h', 'solar_lag_24h', 'solar_rolling_3h',
            'temperature_c', 'ghi'
        ]
        
        # Cache explainers for performance optimization
        self.load_explainer = None
        self.solar_explainer = None
        if shap is not None:
            if self.load_model is not None:
                self.load_explainer = shap.TreeExplainer(self.load_model)
            if self.solar_model is not None:
                self.solar_explainer = shap.TreeExplainer(self.solar_model)

    def _load_model(self, filename):
        path = os.path.join(self.model_dir, filename)
        if os.path.exists(path):
            return joblib.load(path)
        print(f"Warning: Model {filename} not found at {path}. Please run train_models.py")
        return None

    def _create_features(self, df):
        """
        Extracts identical features used during training.
        Requires at least 24h + 3h of historical context in df to calculate shifts.
        """
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        
        # Load lags
        df['load_lag_15m'] = df['load_kw'].shift(1)
        df['load_lag_1h'] = df['load_kw'].shift(4)
        df['load_lag_24h'] = df['load_kw'].shift(96)
        
        # Solar lags
        df['solar_lag_15m'] = df['solar_kw'].shift(1)
        df['solar_lag_1h'] = df['solar_kw'].shift(4)
        df['solar_lag_24h'] = df['solar_kw'].shift(96)

        # Rolling means
        df['load_rolling_3h'] = df['load_kw'].shift(1).rolling(window=12).mean()
        df['solar_rolling_3h'] = df['solar_kw'].shift(1).rolling(window=12).mean()

        # If weather data is missing from inference payload, inject safe defaults
        if 'temperature_c' not in df.columns:
            df['temperature_c'] = 25.0
        if 'ghi' not in df.columns:
            # Very basic day/night GHI approximation if totally missing
            df['ghi'] = np.where((df['hour'] >= 6) & (df['hour'] <= 18), 500.0, 0.0)

        return df.fillna(method='bfill').fillna(0) # Forward/backward fill safely

    def forecast(self, current_df):
        """
        Generates forecasts for the next 24 hours (96 intervals).
        Expects current_df to contain historical data (ideally >= 24h).
        """
        if self.load_model is None or self.solar_model is None:
            # Improved fallback: Use time-of-day averages instead of flat line
            current_df['hour'] = pd.to_datetime(current_df['timestamp']).dt.hour
            hourly_load = current_df.groupby('hour')['load_kw'].mean().to_dict()
            hourly_solar = current_df.groupby('hour')['solar_kw'].mean().to_dict()
            
            # Predict next 96 steps based on fallback hourly dict
            last_ts = pd.to_datetime(current_df['timestamp'].iloc[-1])
            future_hours = [(last_ts + pd.Timedelta(minutes=15*(i+1))).hour for i in range(96)]
            
            load_preds = np.array([hourly_load.get(h, 200) for h in future_hours])
            solar_preds = np.array([hourly_solar.get(h, 0) for h in future_hours])
            
            return load_preds, solar_preds

        # We assume the dataframe passed contains enough history.
        feat_df = self._create_features(current_df)
        
        # Take the last 96 rows for inference
        forecast_df = feat_df.tail(96)

        load_preds = self.load_model.predict(forecast_df[self.load_features])
        solar_preds = self.solar_model.predict(forecast_df[self.solar_features])

        return np.maximum(load_preds, 0), np.maximum(solar_preds, 0)
