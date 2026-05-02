import pandas as pd
import numpy as np
from app.simulation.data_gen import generate_industrial_profile
import os

class DataIngestor:
    """
    Handles the 'Demo' vs 'Real' data modes for the EMS.
    Ensures that regardless of the source, the data is cleaned,
    resampled, and formatted for the ML and Optimization layers.
    """
    def __init__(self, target_freq="15min"):
        self.target_freq = target_freq

    def get_data(self, mode: str, file_path: str = None):
        """
        Routes data acquisition based on mode.
        """
        if mode.lower() == "demo":
            return self._get_demo_data()
        elif mode.lower() == "real":
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"CSV file not found at path: {file_path}")
            return self._ingest_csv(file_path)
        else:
            raise ValueError("Invalid mode. Use 'demo' or 'real'.")

    def _get_demo_data(self):
        """
        Generates synthetic data for the demo experience.
        Returns a dataframe with 30 days of history to allow ML warm-up.
        """
        return generate_industrial_profile(days=30)

    def _ingest_csv(self, file_path: str):
        """
        Loads and validates a real-world industrial energy CSV.
        Expected columns: ['timestamp', 'load_kw', 'solar_kw']
        """
        df = pd.read_csv(file_path)

        # 1. Timestamp Validation & Conversion
        if 'timestamp' not in df.columns:
            raise ValueError("CSV must contain a 'timestamp' column.")

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()

        # 2. Column Validation
        required_cols = ['load_kw', 'solar_kw']
        for col in required_cols:
            if col not in df.columns:
                # Fallback: if solar is missing, assume 0
                if col == 'solar_kw':
                    df['solar_kw'] = 0.0
                else:
                    raise ValueError(f"CSV must contain '{col}' column.")

        # 3. Resampling to 15-minute intervals (Standard EMS Resolution)
        df = df.resample(self.target_freq).mean().ffill().fillna(0)

        # 4. Basic Outlier Detection (Z-Score)
        # Industrial load can have spikes, but we clip extreme errors (e.g., > 5 sigma)
        for col in required_cols:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                df[col] = df[col].clip(lower=0, upper=mean + 5 * std)

        return df.reset_index()
