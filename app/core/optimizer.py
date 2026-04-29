import pulp
import numpy as np
from app.core.tariff import DEFAULT_TARIFF
from app.core.battery import BatteryConfig

class EnergyOptimizer:
    def __init__(self, load_profile, solar_profile, wind_profile, battery_cfg: BatteryConfig,
                 policy, dg_cost_per_kwh=18.0):
        self.load = load_profile
        self.solar = solar_profile
        self.wind = wind_profile
        self.battery = battery_cfg
        self.intervals = len(load_profile)
        self.dg_cost_per_kwh = dg_cost_per_kwh
        self.policy = policy

    def solve(self):
        prob = pulp.LpProblem("StateAware_BTM_Optimization", pulp.LpMinimize)

        # Variables
        grid_import = pulp.LpVariable.dicts("grid_imp", range(self.intervals), lowBound=0)
        bess_dis = pulp.LpVariable.dicts("bess_dis", range(self.intervals), lowBound=0, upBound=self.battery.max_power_kw)
        bess_char = pulp.LpVariable.dicts("bess_char", range(self.intervals), lowBound=0, upBound=self.battery.max_power_kw)
        dg_gen = pulp.LpVariable.dicts("dg_gen", range(self.intervals), lowBound=0)
        soc = pulp.LpVariable.dicts("soc", range(self.intervals + 1),
                                   lowBound=self.battery.capacity_kwh * self.battery.min_soc_pct,
                                   upBound=self.battery.capacity_kwh)
        peak_demand = pulp.LpVariable("peak_demand", lowBound=0)
        curtailment = pulp.LpVariable.dicts("curtail", range(self.intervals), lowBound=0)

        energy_cost = 0
        degradation_cost = 0
        dg_cost = 0

        for t in range(self.intervals):
            hour = (t // 4) % 24
            rate_imp = self.policy.peak_rate if (10 <= hour < 14 or 18 <= hour < 22) else self.policy.off_peak_rate

            energy_cost += (grid_import[t] * 0.25 * rate_imp)
            dg_cost += (dg_gen[t] * 0.25 * self.dg_cost_per_kwh)
            degradation_cost += (bess_dis[t] + bess_char[t]) * 0.25 * self.battery.cycle_cost_per_kwh

        # Correct Demand Charge using State Policy
        demand_charge_cost = peak_demand * (self.policy.demand_charge_per_kva / 30.0)

        # Objective: Minimize Total cost (Strict BTM - No export revenue)
        prob += energy_cost + demand_charge_cost + degradation_cost + dg_cost

        prob += soc[0] == self.battery.capacity_kwh * 0.5

        for t in range(self.intervals):
            net_gen = self.solar[t] + self.wind[t]

            # Power Balance logic (Strict Behind-the-Meter)
            # Load + BatteryCharge = Gen + GridImport + BatteryDischarge + DG - Curtailment
            prob += self.load[t] + bess_char[t] == net_gen + grid_import[t] + bess_dis[t] + dg_gen[t] - curtailment[t]

            prob += soc[t+1] == soc[t] + (bess_char[t] * self.battery.efficiency - bess_dis[t] / self.battery.efficiency) * 0.25
            prob += grid_import[t] <= peak_demand

        status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
        if status != pulp.LpStatusOptimal: return None

        return {
            "grid_import": [grid_import[t].varValue for t in range(self.intervals)],
            "grid_export": [0]*self.intervals,
            "bess_dis": [bess_dis[t].varValue for t in range(self.intervals)],
            "bess_char": [bess_char[t].varValue for t in range(self.intervals)],
            "curtailment": sum([curtailment[t].varValue for t in range(self.intervals)]) * 0.25,
            "peak_demand": pulp.value(peak_demand),
            "energy_cost": pulp.value(energy_cost),
            "demand_cost": pulp.value(demand_charge_cost),
            "degradation_cost": pulp.value(degradation_cost),
            "dg_cost": pulp.value(dg_cost),
            "export_revenue": 0,
            "total_cost": pulp.value(prob.objective),
            "battery_util": (sum(bess_dis[t].varValue for t in range(self.intervals)) * 0.25) / self.battery.capacity_kwh,
            "policy_mode": getattr(self.policy, "mode", "BTM_STRICT")
        }
