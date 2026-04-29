from dataclasses import dataclass
from typing import Dict

@dataclass
class IndianTariff:
    """
    Represents an industrial tariff structure in India.
    Typically includes Time-of-Day (ToD) rates and Fixed Demand Charges.
    """
    tod_rates: Dict[int, float]  # {hour: price_per_kWh}
    demand_charge_per_kva: float # ₹/kVA
    dg_cost_per_kwh: float       # Diesel cost equivalent
    contract_demand_kva: float   # Threshold before penalty

    def get_rate(self, hour: int) -> float:
        return self.tod_rates.get(hour, self.tod_rates.get(0, 5.0))

# Default Industrial Tariff Example (Approximate)
# Peak: 10am-2pm, 6pm-10pm
DEFAULT_TOD_RATES = {h: (8.0 if (10 <= h < 14 or 18 <= h < 22) else 4.5) for h in range(24)}

DEFAULT_TARIFF = IndianTariff(
    tod_rates=DEFAULT_TOD_RATES,
    demand_charge_per_kva=450.0,
    dg_cost_per_kwh=15.0,
    contract_demand_kva=500.0
)
