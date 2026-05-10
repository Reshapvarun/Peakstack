from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os

@dataclass
class StateTariff:
    """
    Hardened Tariff Model for Industrial HT consumers.
    """
    state_name: str
    utility: str
    category: str
    energy_charge_peak_inr_per_kwh: float
    energy_charge_offpeak_inr_per_kwh: float
    energy_charge_normal_inr_per_kwh: float
    demand_charge_inr_per_kva: float
    fixed_charge_inr_per_month: float
    peak_hours: List[List[int]]
    offpeak_hours: List[List[int]]
    tod_applicable: bool = True
    tax_percent: float = 0.0

    def get_rate(self, hour: int) -> float:
        """Returns the energy rate based on ToD window."""
        if not self.tod_applicable:
            return self.energy_charge_normal_inr_per_kwh
        
        # Check Peak
        for start, end in self.peak_hours:
            if start <= end:
                if start <= hour < end: return self.energy_charge_peak_inr_per_kwh
            else: # Overnight
                if hour >= start or hour < end: return self.energy_charge_peak_inr_per_kwh
        
        # Check Off-Peak
        for start, end in self.offpeak_hours:
            if start <= end:
                if start <= hour < end: return self.energy_charge_offpeak_inr_per_kwh
            else: # Overnight
                if hour >= start or hour < end: return self.energy_charge_offpeak_inr_per_kwh
                
        return self.energy_charge_normal_inr_per_kwh

class TariffManager:
    def __init__(self, config_path: str = "config/state_tariffs.json"):
        self.config_path = config_path
        self.tariffs: Dict[str, StateTariff] = {}
        self._load_tariffs()

    def _load_tariffs(self):
        if not os.path.exists(self.config_path):
            return
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            for key, val in data.items():
                self.tariffs[key] = StateTariff(**val)

    def get_tariff(self, state_code: str) -> Optional[StateTariff]:
        return self.tariffs.get(state_code.lower())

# Backward compatibility
DEFAULT_TARIFF = StateTariff(
    state_name="Generic",
    utility="Generic",
    category="Industrial",
    energy_charge_peak_inr_per_kwh=10.0,
    energy_charge_offpeak_inr_per_kwh=5.0,
    energy_charge_normal_inr_per_kwh=7.5,
    demand_charge_inr_per_kva=450.0,
    fixed_charge_inr_per_month=0,
    peak_hours=[[10, 14], [18, 22]],
    offpeak_hours=[[22, 6]],
    tod_applicable=True,
    tax_percent=5.0
)
def load_tariff(state_code: str) -> StateTariff:
    manager = TariffManager()
    tariff = manager.get_tariff(state_code)
    return tariff if tariff else DEFAULT_TARIFF
