import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_industrial_profile(days=30, site_id="Site_1"):
    """
    Generates synthetic industrial energy data.
    - Load: Base load + Periodic spikes + Random noise
    - Solar: Bell curve based on daylight hours
    """
    np.random.seed(42)
    intervals = days * 24 * 4 # 15-min intervals
    timestamps = [datetime(2026, 1, 1) + timedelta(minutes=15*i) for i in range(intervals)]
    
    # 1. Load Profile (kW)
    base_load = 200 
    daily_cycle = 100 * np.sin(np.linspace(0, 2 * np.pi * days, intervals))
    random_spikes = np.random.choice([0, 150, 300], size=intervals, p=[0.9, 0.07, 0.03])
    load = base_load + daily_cycle + random_spikes + np.random.normal(0, 10, intervals)
    load = np.maximum(load, 50) # Min load 50kW

    # 2. Solar Generation (kW)
    solar_gen = []
    for ts in timestamps:
        hour = ts.hour + ts.minute/60
        if 6 <= hour <= 18:
            val = 300 * np.sin(np.pi * (hour - 6) / 12) 
            solar_gen.append(val + np.random.normal(0, 5))
        else:
            solar_gen.append(0)
    solar_gen = np.maximum(solar_gen, 0)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'load_kw': load,
        'solar_kw': solar_gen,
        'site_id': site_id
    })
    return df
