import json
import os
from dataclasses import dataclass
from typing import Dict

@dataclass
class StatePolicy:
    state_name: str
    net_metering_enabled: bool
    export_allowed: bool
    export_rate_ratio: float
    net_metering_limit_kw: float
    demand_charge_per_kva: float
    peak_rate: float
    off_peak_rate: float
    solar_mix_factor: float
    wind_mix_factor: float
    mode: str  # Added mode attribute to fix AttributeError

class PolicyManager:
    STATE_PROFILES = {
        "Gujarat": {"net_metering_enabled": True, "export_allowed": True, "export_rate_ratio": 0.5, 
            "net_metering_limit_kw": 1000, "demand_charge_per_kva": 400.0, 
            "peak_rate": 7.5, "off_peak_rate": 4.0, "solar_mix_factor": 1.2, "wind_mix_factor": 0.8},
        "Maharashtra": {"net_metering_enabled": False, "export_allowed": False, "export_rate_ratio": 0.3, 
            "net_metering_limit_kw": 500, "demand_charge_per_kva": 550.0, 
            "peak_rate": 9.0, "off_peak_rate": 5.0, "solar_mix_factor": 1.0, "wind_mix_factor": 0.6},
        "Karnataka": {"net_metering_enabled": True, "export_allowed": True, "export_rate_ratio": 0.4, 
            "net_metering_limit_kw": 500, "demand_charge_per_kva": 450.0, 
            "peak_rate": 8.0, "off_peak_rate": 4.5, "solar_mix_factor": 1.1, "wind_mix_factor": 1.1},
        "Tamil Nadu": {"net_metering_enabled": False, "export_allowed": False, "export_rate_ratio": 0.2, 
            "net_metering_limit_kw": 200, "demand_charge_per_kva": 500.0, 
            "peak_rate": 8.5, "off_peak_rate": 4.5, "solar_mix_factor": 1.0, "wind_mix_factor": 1.3},
        "Rajasthan": {"net_metering_enabled": True, "export_allowed": True, "export_rate_ratio": 0.4, 
            "net_metering_limit_kw": 1000, "demand_charge_per_kva": 400.0, 
            "peak_rate": 7.0, "off_peak_rate": 4.0, "solar_mix_factor": 1.4, "wind_mix_factor": 0.7},
        "Telangana": {"net_metering_enabled": True, "export_allowed": True, "export_rate_ratio": 0.3, 
            "net_metering_limit_kw": 500, "demand_charge_per_kva": 480.0, 
            "peak_rate": 8.0, "off_peak_rate": 4.5, "solar_mix_factor": 1.1, "wind_mix_factor": 0.5},
        "Uttar Pradesh": {"net_metering_enabled": False, "export_allowed": False, "export_rate_ratio": 0.2, 
            "net_metering_limit_kw": 500, "demand_charge_per_kva": 420.0, 
            "peak_rate": 7.5, "off_peak_rate": 4.0, "solar_mix_factor": 0.9, "wind_mix_factor": 0.4},
    }

    def __init__(self, config_path="config/policy.json"):
        self.config_path = config_path
        self.current_policy = self.load_policy()

    def load_policy(self) -> StatePolicy:
        if not os.path.exists(self.config_path):
            return self.get_state_policy("Maharashtra")
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            state = data.get("state", "Maharashtra")
            return self.get_state_policy(state, data)

    def get_state_policy(self, state: str, overrides: dict = None) -> StatePolicy:
        profile = self.STATE_PROFILES.get(state, self.STATE_PROFILES["Maharashtra"]).copy()
        net_metering = profile["net_metering_enabled"]
        if overrides:
            net_metering = overrides.get("net_metering_enabled", net_metering)
        
        export_allowed = profile["export_allowed"]
        if not net_metering:
            export_allowed = False
        elif overrides and "export_allowed" in overrides:
            export_allowed = overrides["export_allowed"]

        mode = "flexible" if net_metering else "strict_btm"

        return StatePolicy(
            state_name=state,
            net_metering_enabled=net_metering,
            export_allowed=export_allowed,
            export_rate_ratio=overrides.get("export_rate_ratio", profile["export_rate_ratio"]) if overrides else profile["export_rate_ratio"],
            net_metering_limit_kw=overrides.get("net_metering_limit_kw", profile["net_metering_limit_kw"]) if overrides else profile["net_metering_limit_kw"],
            demand_charge_per_kva=profile["demand_charge_per_kva"],
            peak_rate=profile["peak_rate"],
            off_peak_rate=profile["off_peak_rate"],
            solar_mix_factor=profile["solar_mix_factor"],
            wind_mix_factor=profile["wind_mix_factor"],
            mode=mode
        )

    def get_policy_warnings(self, results):
        warnings = []
        if not self.current_policy.net_metering_enabled:
            warnings.append("Net Metering disabled. Excess generation will be curtailed.")
        if not self.current_policy.export_allowed:
            warnings.append("Grid export disabled due to BTM policy.")
        if results.get('curtailment', 0) > 0:
            warnings.append(f"Excess energy curtailed: {results['curtailment']:.2f} kWh.")
        return warnings
