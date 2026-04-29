from app.core.battery import BatteryConfig
from app.core.optimizer import EnergyOptimizer
from app.core.tariff import DEFAULT_TARIFF

class WhatIfEngine:
    def __init__(self, load, solar):
        self.load = load
        self.solar = solar

    def analyze_battery_sizes(self, sizes_kwh: list, power_kw_fixed: float):
        results = []
        
        # Calculate baseline for comparison
        baseline_peak = max(self.load - self.solar)
        
        for size in sizes_kwh:
            cfg = BatteryConfig(capacity_kwh=size, max_power_kw=power_kw_fixed)
            opt = EnergyOptimizer(self.load, self.solar, cfg)
            res = opt.solve()
            
            if res:
                results.append({
                    "capacity_kwh": size,
                    "total_cost": res['total_cost'],
                    "peak_demand": res['peak_demand'],
                    "savings": 0 # Calculated in wrapper
                })
        return results
