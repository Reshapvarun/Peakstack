import pulp
import numpy as np

class DispatchOptimizer:
    """
    Enterprise-Grade Energy Operating System Dispatch Engine.
    Supports: Multi-day horizon, Degradation modeling, Hybrid DG, and Dynamic IEX pricing.
    """
    def __init__(self, load_forecast, solar_forecast, tariff_profile, battery_capacity_kwh, battery_power_kw, 
                 chemistry="lfp", efficiency=0.90, dg_cost=20.0, dg_running_profile=None, 
                 initial_soc_percent=50.0, dg_hours_per_day=2.0):
        self.load = load_forecast
        self.solar = solar_forecast
        self.tariff = tariff_profile
        self.capacity = battery_capacity_kwh
        self.power = battery_power_kw
        self.chemistry = chemistry
        self.efficiency = efficiency
        self.dg_cost = dg_cost
        self.dg_running = dg_running_profile if dg_running_profile else [False] * len(load_forecast)
        self.initial_soc = (initial_soc_percent / 100.0) * battery_capacity_kwh
        self.intervals = len(load_forecast)
        self.dg_hours_per_day = dg_hours_per_day
        
        # Chemistry Defaults
        if self.chemistry == "na_ion":
            self.degradation_factor = 0.60 # ₹/kWh (Na-ion is cheaper/more cycles)
            self.efficiency = 0.90
        else: # LFP
            self.degradation_factor = 0.85 # ₹/kWh
            self.efficiency = 0.92

    def solve(self):
        """
        Solves the MILP dispatch problem.
        Objective: Minimize Total Cost (Grid + DG + Degradation)
        """
        # Create LP problem - Minimize Cost
        prob = pulp.LpProblem("MultiDay_Hybrid_Dispatch", pulp.LpMinimize)
        
        # Variables
        charge = pulp.LpVariable.dicts("charge", range(self.intervals), lowBound=0, upBound=self.power)
        discharge = pulp.LpVariable.dicts("discharge", range(self.intervals), lowBound=0, upBound=self.power)
        
        # Real-World SOC Limits: 10% to 90%
        soc_min = self.capacity * 0.10
        soc_max = self.capacity * 0.90
        soc = pulp.LpVariable.dicts("soc", range(self.intervals + 1), lowBound=soc_min, upBound=soc_max)
        
        # Initial SOC
        prob += soc[0] == self.initial_soc
        
        total_cost = 0
        peak_load = max(self.load) if self.load else 0
        
        for t in range(self.intervals):
            charge_kwh = charge[t] * 0.25
            discharge_kwh = discharge[t] * 0.25
            dt = 0.25 # 15 min = 0.25 hours
            
            # v3 DG Logic
            # dg_energy(t) = (dg_hours_per_day / 24) × peak_load × dt
            dg_energy_limit = (self.dg_hours_per_day / 24) * peak_load * dt
            dg_available = peak_load if self.dg_running[t] else 0
            
            # dg_offset(t) = min(discharge(t), dg_energy(t), dg_available)
            # Since discharge is a variable, we represent dg_offset as a variable bounded by these
            dg_offset_kwh = pulp.LpVariable(f"dg_offset_{t}", lowBound=0)
            prob += dg_offset_kwh <= discharge_kwh
            prob += dg_offset_kwh <= dg_energy_limit
            prob += dg_offset_kwh <= dg_available * dt
            
            # Net grid import calculation
            # grid_import = load - solar + charge - discharge + dg_offset?
            # Wait, BESS discharge REDUCES load. DG offset is the portion of discharge that replaces DG.
            # Grid import is whatever is left after solar and BESS.
            net_load = self.load[t] - self.solar[t]
            grid_import_kwh = (net_load * dt) + charge_kwh - discharge_kwh
            
            # Objective Function Components:
            # 1. Grid Cost: (Grid Import) * Tariff
            # 2. DG Cost Avoided: (DG Offset) * (DG Cost - Tariff)
            # 3. Degradation: (Charge + Discharge) * Degradation Factor
            
            # We want to MINIMIZE: Grid Cost + DG Cost + Degradation
            # If we offset DG, we pay grid tariff instead of DG cost?
            # Actually, total cost = (Grid Import) * Tariff + (Remaining DG Load) * DG Cost
            # Remaining DG Load = (Original DG Load) - (DG Offset)
            # Original DG Load is roughly the 'dg_energy_limit' if DG is available.
            
            total_cost += (grid_import_kwh * self.tariff[t]) \
                       + (dg_offset_kwh * (self.tariff[t] - self.dg_cost)) \
                       + ((charge_kwh + discharge_kwh) * self.degradation_factor)
            
            # Constraints
            # 1. SOC transition with Efficiency
            prob += soc[t+1] == soc[t] + (charge_kwh * self.efficiency) - (discharge_kwh / self.efficiency)
            
            # 2. Behind-The-Meter constraint: No negative import
            prob += grid_import_kwh >= 0
            
        prob += total_cost
        
        # Solve
        status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if status != pulp.LpStatusOptimal:
            return None
            
        # Extract schedule and granular savings
        schedule = []
        total_discharge_kwh = 0.0
        dg_savings_val = 0.0
        
        for t in range(self.intervals):
            c_val = pulp.value(charge[t])
            d_val = pulp.value(discharge[t])
            s_val = pulp.value(soc[t+1])
            o_val = pulp.value(prob.variablesDict()[f"dg_offset_{t}"])
            d_kwh = d_val * 0.25
            
            # DG Savings: (DG Offset * (DG Cost - Tariff))
            dg_savings_val += o_val * (self.dg_cost - self.tariff[t])

            # Time calculation for multi-day
            day = t // 96
            interval_in_day = t % 96
            hour = (interval_in_day // 4) % 24
            minute = (interval_in_day % 4) * 15
            time_str = f"D{day+1} {hour:02d}:{minute:02d}"
            
            total_discharge_kwh += d_kwh
            
            schedule.append({
                "time": time_str,
                "charge_kw": float(c_val),
                "discharge_kw": float(d_val),
                "soc_percent": float((s_val / self.capacity) * 100),
                "tariff": float(self.tariff[t]),
                "is_dg_offset": bool(o_val > 0.01),
                "dg_offset_kw": float(o_val / 0.25)
            })
            
        return {
            "schedule": schedule,
            "total_cost": float(pulp.value(prob.objective)),
            "total_discharge_kwh": total_discharge_kwh,
            "dg_savings": float(dg_savings_val),
            "status": "Optimal"
        }

