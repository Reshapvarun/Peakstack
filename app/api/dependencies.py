import joblib
import os
from app.ml.forecaster import EnergyForecaster

def get_forecaster():
    """
    Dependency to provide a pre-initialized forecaster.
    In a real SaaS, this might be a singleton or managed by a model registry.
    """
    forecaster = EnergyForecaster()
    # The forecaster's __init__ already handles loading joblib models if they exist
    return forecaster
