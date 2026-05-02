import pulp
import numpy as np

class DispatchOptimizer:
    """
    Enterprise-Grade Energy Operating System Dispatch Engine.
    Supports: Multi-day horizon, Degradation modeling, Hybrid DG, and Dynamic IEX pricing.
    """
    def __init__(self, load_forecast, solar_forecast, tariff_profile, battery_capacity_kwh, battery_power_kw, 
                 efficiency=0.90, dg_cost=20.0, dg_running_profile=None, initial_soc_percent=50.0):
        self.load = load_forecast
        self.solar = solar_forecast
        self.tariff = tariff_profile
        self.capacity = battery_capacity_kwh
        self.power = battery_power_kw
        self.efficiency = efficiency
        self.dg_cost = dg_cost
        self.dg_running = dg_running_profile if dg_running_profile else [False] * len(load_forecast)
        self.initial_soc = (initial_soc_percent / 100.0) * battery_capacity_kwh
        self.intervals = len(load_forecast)
        
    def solve(self):
        """
        Solves the MILP dispatch problem.
        Objective: Maximize Savings - Degradation Cost
        """
        # Create LP problem
        prob = pulp.LpProblem("MultiDay_Hybrid_Dispatch", pulp.LpMaximize)
        
        # Variables
        charge = pulp.LpVariable.dicts("charge", range(self.intervals), lowBound=0, upBound=self.power)
        discharge = pulp.LpVariable.dicts("discharge", range(self.intervals), lowBound=0, upBound=self.power)
        
        # Real-World SOC Limits: 10% to 90%
        soc_min = self.capacity * 0.10
        soc_max = self.capacity * 0.90
        soc = pulp.LpVariable.dicts("soc", range(self.intervals + 1), lowBound=soc_min, upBound=soc_max)
        
        # Initial SOC
        prob += soc[0] == self.initial_soc
        
        # Parameters
        # degradation_factor = Cost per kWh of throughput (approx ₹0.80 based on lifecycle)
        degradation_factor = 0.80 
        
        savings_objective = 0
        for t in range(self.intervals):
            charge_kwh = charge[t] * 0.25
            discharge_kwh = discharge[t] * 0.25
            
            # Dynamic Tariff Integration (Grid vs DG vs IEX)
            # Logic: If DG is running, alternative cost is DG. Else, use the provided tariff (which should include IEX)
            effective_tariff = self.dg_cost if self.dg_running[t] else self.tariff[t]
            
            # Objective Function:
            # 1. Arbitrage: (Discharge * Effective Tariff) - (Charge * Grid Tariff)
            # 2. Degradation: (Charge + Discharge) * Degradation Factor
            savings_objective += (discharge_kwh * effective_tariff) - (charge_kwh * self.tariff[t]) - ((charge_kwh + discharge_kwh) * degradation_factor)
            
            # Constraints
            # 1. SOC transition with Efficiency
            prob += soc[t+1] == soc[t] + (charge_kwh * self.efficiency) - (discharge_kwh / self.efficiency)
            
            # 2. Behind-The-Meter constraint: Cannot discharge more than net load (no grid export allowed in C&I usually)
            # We use "Safe Forecasts" here (passed into constructor)
            net_load = max(0, self.load[t] - self.solar[t])
            prob += discharge[t] <= net_load
            
        prob += savings_objective
        
        # Solve
        status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if status != pulp.LpStatusOptimal:
            return None
            
        # Extract schedule
        schedule = []
        total_discharge_kwh = 0.0
        
        for t in range(self.intervals):
            c_val = pulp.value(charge[t])
            d_val = pulp.value(discharge[t])
            s_val = pulp.value(soc[t+1])
            
            # Time calculation for multi-day
            day = t // 96
            interval_in_day = t % 96
            hour = (interval_in_day // 4) % 24
            minute = (interval_in_day % 4) * 15
            time_str = f"D{day+1} {hour:02d}:{minute:02d}"
            
            total_discharge_kwh += d_val * 0.25
            
            schedule.append({
                "time": time_str,
                "charge_kw": float(c_val),
                "discharge_kw": float(d_val),
                "soc_percent": float((s_val / self.capacity) * 100),
                "tariff": float(self.tariff[t]),
                "is_dg_offset": bool(self.dg_running[t] and d_val > 0.1)
            })
            
        return {
            "schedule": schedule,
            "total_savings": float(pulp.value(prob.objective)),
            "total_discharge_kwh": total_discharge_kwh,
            "status": "Optimal"
        }
