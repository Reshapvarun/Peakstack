import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_industrial_profile(days=30, site_id="Site_1"):
    """
    Generates synthetic industrial energy data with weather context.
    - Load: Base load + Periodic spikes + Random noise + Temp correlation
    - Solar: Derived from GHI (Global Horizontal Irradiance) and Temp
    - Weather: Temperature (C) and GHI (W/m^2)
    """
    np.random.seed(42)
    intervals = days * 24 * 4 # 15-min intervals
    timestamps = [datetime(2026, 1, 1) + timedelta(minutes=15*i) for i in range(intervals)]
    
    # Generate Weather First
    temperature_c = []
    ghi = []
    
    for ts in timestamps:
        hour = ts.hour + ts.minute/60
        
        # Temperature: Cool at night, peaks around 14:00 (2pm)
        base_temp = 22 # baseline 22C
        daily_temp_swing = 10 * np.sin(np.pi * (hour - 8) / 12) if 8 <= hour <= 20 else 10 * np.sin(np.pi * (hour + 16) / 24) * 0.5
        temp = base_temp + daily_temp_swing + np.random.normal(0, 1)
        temperature_c.append(np.clip(temp, 15, 45))
        
        # GHI: Parabola during daylight (6am to 6pm)
        if 6 <= hour <= 18:
            val = 800 * np.sin(np.pi * (hour - 6) / 12) 
            # Add some cloud cover randomness
            cloud_factor = np.random.choice([1.0, 0.8, 0.4], p=[0.7, 0.2, 0.1])
            ghi.append(max(0, val * cloud_factor + np.random.normal(0, 20)))
        else:
            ghi.append(0)
            
    temperature_c = np.array(temperature_c)
    ghi = np.array(ghi)

    # 1. Load Profile (kW)
    base_load = 200 
    daily_cycle = 100 * np.sin(np.linspace(0, 2 * np.pi * days, intervals))
    random_spikes = np.random.choice([0, 150, 300], size=intervals, p=[0.9, 0.07, 0.03])
    
    # Add cooling load penalty when temperature > 28C
    cooling_load = np.where(temperature_c > 28, (temperature_c - 28) * 15, 0)
    
    load = base_load + daily_cycle + random_spikes + cooling_load + np.random.normal(0, 10, intervals)
    load = np.maximum(load, 50) # Min load 50kW

    # 2. Solar Generation (kW)
    # Correlate solar with GHI directly. Efficiency drops slightly at high temps.
    # Base capacity roughly 300kW
    temp_derating = 1 - ((temperature_c - 25) * 0.004) # 0.4% loss per degree above 25C
    solar_gen = (ghi / 1000) * 350 * temp_derating
    solar_gen = np.maximum(solar_gen, 0)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'load_kw': load,
        'solar_kw': solar_gen,
        'temperature_c': temperature_c,
        'ghi': ghi,
        'site_id': site_id
    })
    return df
