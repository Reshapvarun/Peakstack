import numpy as np
import pandas as pd
from app.core.optimizer import EnergyOptimizer
from app.core.battery import BatteryConfig
from app.core.finance import FinancialEngine, FinanceConfig
from app.core.tariff import DEFAULT_TARIFF

class ScenarioEngine:
    def __init__(self, load, solar, wind, prices):
        self.load = load
        self.solar = solar
        self.wind = wind
        self.prices = prices
        self.fin_engine = FinancialEngine(FinanceConfig())

    def run_scenario(self, name, config):
        gen_solar = self.solar if config['has_solar'] else np.zeros_like(self.solar)
        gen_wind = self.wind if config['has_wind'] else np.zeros_like(self.wind)
        total_gen = gen_solar + gen_wind
        
        if config['has_bess']:
            batt_cfg = BatteryConfig(capacity_kwh=config['bess_capacity'], max_power_kw=config['bess_power'])
            opt = EnergyOptimizer(self.load, total_gen, batt_cfg)
            
            prices_to_use = self.prices if config['arbitrage_enabled'] else None
            res = opt.solve(dynamic_prices=prices_to_use)
            
            if res is None: return None
            
            peak = res['peak_demand']
            total_cost = res['total_cost']
        else:
            total_energy_cost = 0
            max_demand = 0
            for t in range(len(self.load)):
                hour = (t // 4) % 24
                net = max(0, self.load[t] - total_gen[t])
                total_energy_cost += net * 0.25 * DEFAULT_TARIFF.get_rate(hour)
                if net > max_demand:
                    max_demand = net
            
            demand_cost = max_demand * DEFAULT_TARIFF.demand_charge_per_kva / 30.0
            total_cost = total_energy_cost + demand_cost
            peak = max_demand

        baseline = self._get_baseline()
        savings = baseline - total_cost
        
        roi_res = self.fin_engine.calculate_roi(savings, config['bess_capacity'] if config['has_bess'] else 1)
        
        return {
            "scenario": name,
            "total_cost": total_cost,
            "savings": savings,
            "peak": peak,
            "payback": roi_res['payback_period_years'],
            "roi_pct": roi_res['annual_roi_pct']
        }

    def _get_baseline(self):
        total_energy = 0
        max_demand = 0
        for t in range(len(self.load)):
            hour = (t // 4) % 24
            net = max(0, self.load[t])
            total_energy += net * 0.25 * DEFAULT_TARIFF.get_rate(hour)
            if net > max_demand:
                max_demand = net
        return total_energy + (max_demand * DEFAULT_TARIFF.demand_charge_per_kva / 30.0)
