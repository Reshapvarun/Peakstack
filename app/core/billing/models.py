from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class EnergyRates(BaseModel):
    off_peak: float
    normal: float
    peak: float

class ToDHours(BaseModel):
    peak: List[int]
    off_peak: List[int]

class HTTariffModel(BaseModel):
    version: str
    last_updated: str
    source_url: str
    demand_charge_per_kva: float
    fixed_charge_per_kva: float
    energy_rate: EnergyRates
    tod_hours: ToDHours
    pf_penalty_threshold: float
    pf_incentive_threshold: float
    tax_percent: float

class StateConfiguration(BaseModel):
    tariffs: Dict[str, HTTariffModel]
