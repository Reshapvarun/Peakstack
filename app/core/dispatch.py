import pulp
import numpy as np

class DispatchOptimizer:
    """
    AI-Powered Battery Dispatch Optimizer (Real-time MILP engine).
    Generates optimal charge/discharge schedules based on forecasts and tariff structures.
    """
    def __init__(self, load_forecast, solar_forecast, tariff_profile, battery_capacity_kwh, battery_power_kw, efficiency=0.9):
        self.load = load_forecast
        self.solar = solar_forecast
        self.tariff = tariff_profile
        self.capacity = battery_capacity_kwh
        self.power = battery_power_kw
        self.efficiency = efficiency
        self.intervals = len(load_forecast) # Expected 96 for 24h 15-min intervals
        
    def solve(self):
        # Create LP problem: Maximize Savings
        prob = pulp.LpProblem("RealTime_Battery_Dispatch", pulp.LpMaximize)
        
        # Variables
        charge = pulp.LpVariable.dicts("charge", range(self.intervals), lowBound=0, upBound=self.power)
        discharge = pulp.LpVariable.dicts("discharge", range(self.intervals), lowBound=0, upBound=self.power)
        
        # Real-World SOC Limits: 10% to 90%
        soc_min = self.capacity * 0.10
        soc_max = self.capacity * 0.90
        soc = pulp.LpVariable.dicts("soc", range(self.intervals + 1), lowBound=soc_min, upBound=soc_max)
        
        # Initial SOC (assume 50% for day-ahead optimization, or pass it as param later)
        prob += soc[0] == self.capacity * 0.5
        
        # Objective: Maximize arbitrage savings minus degradation
        # Assuming intervals are 15-min (0.25 hr) for energy calculation
        # savings = discharge_energy * tariff - charge_energy * tariff - throughput * cycle_cost
        savings_objective = 0
        cycle_cost_per_kwh = 0.5
        
        for t in range(self.intervals):
            # Energy in kWh for this 15-min interval
            charge_kwh = charge[t] * 0.25
            discharge_kwh = discharge[t] * 0.25
            
            # Add to objective (Arbitrage - Degradation)
            savings_objective += (discharge_kwh * self.tariff[t]) - (charge_kwh * self.tariff[t]) - ((charge_kwh + discharge_kwh) * cycle_cost_per_kwh)
            
            # Constraints
            # 1. SOC transition
            prob += soc[t+1] == soc[t] + (charge_kwh * self.efficiency) - (discharge_kwh / self.efficiency)
            
            # 2. Behind-The-Meter limit: Cannot discharge more than (load - solar) to avoid grid export
            net_load = max(0, self.load[t] - self.solar[t])
            prob += discharge[t] <= net_load
            
            # 3. Cannot charge from grid at peak tariff if we only want solar charging, 
            # but the objective function naturally handles this (it will charge when tariff is lowest).
            
            # 4. Prevent simultaneous charge and discharge
            # In pure LP, efficiency < 1 prevents simultaneous charge/discharge automatically
            # because cycling energy loses money.
            
        prob += savings_objective
        
        # Solve
        status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if status != pulp.LpStatusOptimal:
            return None
            
        # Extract schedule
        schedule = []
        for t in range(self.intervals):
            c_val = pulp.value(charge[t])
            d_val = pulp.value(discharge[t])
            
            # Format time
            hour = (t // 4) % 24
            minute = (t % 4) * 15
            time_str = f"{hour:02d}:{minute:02d}"
            
            action = "IDLE"
            power = 0.0
            
            if c_val > 0.1:
                action = "CHARGE"
                power = c_val
            elif d_val > 0.1:
                action = "DISCHARGE"
                power = d_val
                
            schedule.append({
                "time": time_str,
                "action": action,
                "power": float(power),
                "soc_percent": float((pulp.value(soc[t+1]) / self.capacity) * 100)
            })
            
        return {
            "schedule": schedule,
            "total_savings": float(pulp.value(prob.objective)),
            "status": "Optimal"
        }
