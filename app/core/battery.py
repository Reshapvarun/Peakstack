from dataclasses import dataclass

@dataclass
class BatteryConfig:
    capacity_kwh: float = 200.0
    max_power_kw: float = 100.0
    efficiency: float = 0.90
    min_soc_pct: float = 0.20
    cycle_cost_per_kwh: float = 0.05  # Cost of degradation per kWh throughput

class BatteryModel:
    def __init__(self, config: BatteryConfig):
        self.config = config
        self.soc_kwh = config.capacity_kwh * 0.5  # Start at 50%

    def get_limits(self):
        return {
            "max_charge": self.config.max_power_kw,
            "max_discharge": self.config.max_power_kw,
            "min_soc": self.config.capacity_kwh * self.config.min_soc_pct,
            "max_soc": self.config.capacity_kwh
        }
