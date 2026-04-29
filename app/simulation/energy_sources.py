import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_solar_profile(days=1, capacity_kw=300, site_id="Site_1"):
    """Generates a solar generation profile based on a bell curve."""
    intervals = days * 24 * 4
    timestamps = [datetime(2026, 1, 1) + timedelta(minutes=15*i) for i in range(intervals)]
    
    solar_gen = []
    for ts in timestamps:
        hour = ts.hour + ts.minute/60
        if 6 <= hour <= 18:
            # Bell curve for solar: max at 12pm
            val = capacity_kw * np.sin(np.pi * (hour - 6) / 12)
            solar_gen.append(max(0, val + np.random.normal(0, 5)))
        else:
            solar_gen.append(0)
            
    return np.array(solar_gen)

def generate_wind_profile(days=1, capacity_kw=100, site_id="Site_1"):
    """Generates a wind generation profile (more random than solar)."""
    intervals = days * 24 * 4
    # Wind is more stochastic. We use a combination of a slow trend and random noise.
    base = capacity_kw * 0.3
    trend = 0.2 * capacity_kw * np.sin(np.linspace(0, 2 * np.pi * days, intervals))
    noise = np.random.normal(0, 0.1 * capacity_kw, intervals)
    
    wind_gen = base + trend + noise
    return np.maximum(wind_gen, 0)

def generate_dynamic_prices(days=1):
    """Generates synthetic dynamic electricity prices for arbitrage."""
    intervals = days * 24 * 4
    prices = []
    for i in range(intervals):
        hour = (i // 4) % 24
        # Base ToD price
        base = 8.0 if (10 <= hour < 14 or 18 <= hour < 22) else 4.5
        # Add random market volatility (+/- 2.0)
        price = base + np.random.uniform(-2.0, 2.0)
        prices.append(max(0.5, price))
    return np.array(prices)
