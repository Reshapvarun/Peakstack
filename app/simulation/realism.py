import numpy as np
from typing import Tuple

class RealismCalibrator:
    """
    Introduces real-world imperfections into ideal simulations.
    Used to ensure DPIIT results are credible and not 'too good to be true'.
    """
    def __init__(self, solar_variability=0.20, wind_variability=0.30, load_error=0.08):
        self.solar_variability = solar_variability
        self.wind_variability = wind_variability
        self.load_error = load_error

    def apply_uncertainty(self, load, solar, wind):
        """Adds stochastic noise to generation and load."""
        # Solar: Normal distribution around the ideal curve
        real_solar = solar * (1 + np.random.normal(0, self.solar_variability, len(solar)))
        # Wind: High variability
        real_wind = wind * (1 + np.random.normal(0, self.wind_variability, len(wind)))
        # Load: Simulation of forecast error (what the optimizer 'sees' vs reality)
        forecast_load = load * (1 + np.random.normal(0, self.load_error, len(load)))
        
        return np.maximum(real_solar, 0), np.maximum(real_wind, 0), forecast_load

    def get_realistic_config(self):
        """Returns a conservative, real-world BESS/Grid configuration."""
        return {
            "export_allowed": False, # Most Indian industries can't export easily
            "export_rate": 1.5,      # Low feed-in tariff
            "max_export_limit": 20.0,
            "arbitrage_enabled": False, # Pure arbitrage usually forbidden/unprofitable
            "dg_cost_per_kwh": 18.0    # Higher diesel cost for realism
        }
