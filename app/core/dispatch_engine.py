import numpy as np
from typing import List, Dict, Any

class RuleBasedDispatchEngine:
    """
    Deterministic rule-based battery dispatch engine.
    Charge during off-peak, discharge during peak, respect SOC limits.
    """
    def __init__(
        self, 
        battery_kwh: float, 
        battery_power_kw: float, 
        min_soc: float = 0.2, 
        max_soc: float = 0.9,
        efficiency: float = 0.95
    ):
        self.battery_kwh = battery_kwh
        self.battery_power_kw = battery_power_kw
        self.min_soc = min_soc
        self.max_soc = max_soc
        self.efficiency = efficiency

    def run_dispatch(
        self, 
        load_profile: List[float], 
        solar_profile: List[float] = None, 
        peak_hours: List[List[int]] = None,
        offpeak_hours: List[List[int]] = None
    ) -> Dict[str, List[float]]:
        """
        Runs the dispatch logic for 96 intervals (15-min each).
        """
        n = len(load_profile)
        if solar_profile is None:
            solar_profile = [0.0] * n
        
        soc = [self.min_soc * self.battery_kwh] * (n + 1)
        charge_kw = [0.0] * n
        discharge_kw = [0.0] * n
        grid_import_with_bess = [0.0] * n
        grid_import_without_bess = [0.0] * n

        def is_in_hours(hour, hour_ranges):
            if not hour_ranges:
                return False
            for start, end in hour_ranges:
                if start <= end:
                    if start <= hour < end:
                        return True
                else: # Overnight range like 22:00 to 06:00
                    if hour >= start or hour < end:
                        return True
            return False

        for i in range(n):
            hour = (i // 4) % 24
            dt = 0.25 # 15 minutes
            
            current_load = load_profile[i]
            current_solar = solar_profile[i]
            
            # Without BESS
            grid_import_without_bess[i] = max(0, current_load - current_solar)
            
            # BESS Logic
            net_load = current_load - current_solar
            
            if is_in_hours(hour, offpeak_hours):
                # CHARGE
                # Priority 1: Use excess solar
                excess_solar = max(0, current_solar - current_load)
                solar_charge_kw = min(excess_solar, self.battery_power_kw)
                
                # Priority 2: Charge from grid if not full
                remaining_power_cap = self.battery_power_kw - solar_charge_kw
                can_take_kwh = (self.max_soc * self.battery_kwh) - soc[i]
                grid_charge_kw = min(remaining_power_cap, can_take_kwh / (dt * self.efficiency))
                
                charge_kw[i] = solar_charge_kw + grid_charge_kw
                discharge_kw[i] = 0.0
                
            elif is_in_hours(hour, peak_hours):
                # DISCHARGE
                # Smarter discharge: only discharge if load > 200 kW
                # Calculate total peak intervals remaining today to split energy
                
                remaining_peak_intervals = 0
                for j in range(i, n):
                    h_j = (j // 4) % 24
                    if is_in_hours(h_j, peak_hours):
                        remaining_peak_intervals += 1
                
                available_kwh = soc[i] - (self.min_soc * self.battery_kwh)
                
                if net_load > 200 and remaining_peak_intervals > 0:
                    # Allow using available_kwh / remaining_peak_intervals per interval
                    limit_kwh_this_interval = available_kwh / remaining_peak_intervals
                    
                    requested_discharge_kw = min(net_load - 200, self.battery_power_kw)
                    actual_discharge_kw = min(requested_discharge_kw, (limit_kwh_this_interval * self.efficiency) / dt)
                    discharge_kw[i] = actual_discharge_kw
                else:
                    discharge_kw[i] = 0.0
                charge_kw[i] = 0.0
            else:
                # Normal hours: Use solar for load, charge with excess solar if any
                excess_solar = max(0, current_solar - current_load)
                can_take_kwh = (self.max_soc * self.battery_kwh) - soc[i]
                solar_charge_kw = min(excess_solar, self.battery_power_kw, can_take_kwh / (dt * self.efficiency))
                
                charge_kw[i] = solar_charge_kw
                discharge_kw[i] = 0.0

            # Update SOC
            # soc[t+1] = soc[t] + (charge * eff) - (discharge / eff)
            soc[i+1] = soc[i] + (charge_kw[i] * dt * self.efficiency) - (discharge_kw[i] * dt / self.efficiency)
            
            # Grid Import with BESS
            # If net_load > 0, we might discharge to reduce it.
            # If net_load < 0, we might charge with excess solar.
            # If we charge from grid, grid import increases.
            
            if net_load >= 0:
                # Load exceeds solar
                grid_import_with_bess[i] = net_load - discharge_kw[i] + (charge_kw[i] if is_in_hours(hour, offpeak_hours) else 0)
            else:
                # Solar exceeds load
                # charge_kw[i] is already taken from excess solar if possible
                remaining_excess = abs(net_load) - charge_kw[i]
                grid_import_with_bess[i] = 0.0 # BTM - no export assumed

        return {
            "battery_soc": [s / self.battery_kwh for s in soc[:-1]],
            "battery_charge_kw": charge_kw,
            "battery_discharge_kw": discharge_kw,
            "grid_import_with_bess": grid_import_with_bess,
            "grid_import_without_bess": grid_import_without_bess
        }
