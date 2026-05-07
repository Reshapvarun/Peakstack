import numpy as np
from typing import List, Dict, Any

class RuleBasedDispatchEngine:
    """
    Operationally Realistic Rule-Based Dispatch Engine.
    Hardened for industrial peak shaving, solar priority, and battery health.
    """
    def __init__(
        self, 
        battery_kwh: float, 
        battery_power_kw: float, 
        min_soc: float = 0.20, 
        max_soc: float = 0.90,
        efficiency: float = 0.95
    ):
        self.battery_kwh = battery_kwh
        self.battery_power_kw = battery_power_kw
        self.min_soc = min_soc
        self.max_soc = max_soc
        self.efficiency = efficiency
        self.cumulative_throughput_kwh = 0.0

    def run_dispatch(
        self, 
        load_profile: List[float], 
        solar_profile: List[float] = None, 
        peak_hours: List[List[int]] = None,
        offpeak_hours: List[List[int]] = None,
        target_grid_limit_kw: float = None
    ) -> Dict[str, Any]:
        """
        Runs hardened dispatch logic for 96 intervals (15-min).
        """
        n = len(load_profile)
        if solar_profile is None:
            solar_profile = [0.0] * n
        
        # 1. Initialize State
        soc_kwh = [self.min_soc * self.battery_kwh] * (n + 1)
        charge_kw = [0.0] * n
        discharge_kw = [0.0] * n
        grid_import_with_bess = [0.0] * n
        grid_import_without_bess = [0.0] * n
        
        dt = 0.25 # 15-minute intervals (Dimensional Correctness)
        max_daily_discharge_kwh = self.battery_kwh # 1 full cycle discharge limit
        daily_discharge_kwh = 0.0

        # 2. Demand Charge Awareness: Identify top peak intervals dynamically
        load_threshold = np.percentile(load_profile, 85)
        # We also need the global baseline peak to ensure charging stays below it
        baseline_peak_kw = max(grid_import_without_bess)
        
        # Target limit for shaving (Phase 2.2)
        target = target_grid_limit_kw if target_grid_limit_kw else load_threshold

        def is_in_hours(hour, hour_ranges):
            if not hour_ranges: return False
            for start, end in hour_ranges:
                if start <= end:
                    if start <= hour < end: return True
                else:
                    if hour >= start or hour < end: return True
            return False

        # 3. Execution Loop
        for i in range(n):
            hour = (i // 4) % 24
            current_load = load_profile[i]
            current_solar = solar_profile[i]
            
            # Baseline (Without BESS)
            # Solar serves load first (Phase 2.3)
            net_load_no_bess = max(0, current_load - current_solar)
            grid_import_without_bess[i] = net_load_no_bess

            # BESS Logic
            current_soc = soc_kwh[i]
            can_charge_kwh = (self.max_soc * self.battery_kwh) - current_soc
            can_discharge_kwh = current_soc - (self.min_soc * self.battery_kwh)
            
            # Step 1: Solar Priority (Phase 2.3)
            # Use solar for load first
            load_after_solar = max(0, current_load - current_solar)
            excess_solar = max(0, current_solar - current_load)
            
            # Step 2: Charge with excess solar
            solar_charge_kwh = min(excess_solar * dt * self.efficiency, can_charge_kwh)
            solar_charge_kw = solar_charge_kwh / dt / self.efficiency if dt > 0 else 0
            
            # Update state after solar charging
            current_soc += solar_charge_kwh
            can_charge_kwh -= solar_charge_kwh

            # Step 3: Rule-based Grid Interaction
            final_charge_kw = solar_charge_kw
            final_discharge_kw = 0.0

            # Charging during off-peak (Phase 2.1)
            if is_in_hours(hour, offpeak_hours) and can_charge_kwh > 0:
                # Ensure charging does not create a new peak (Phase 1)
                # Max allowed import is the baseline peak or target
                available_charge_margin_kw = max(0, target - load_after_solar)
                
                grid_charge_kw = min(self.battery_power_kw - solar_charge_kw, 
                                     can_charge_kwh / dt / self.efficiency,
                                     available_charge_margin_kw)
                
                final_charge_kw += grid_charge_kw
                current_soc += (grid_charge_kw * dt * self.efficiency)
            
            # Discharging during peaks (Phase 2.2 & 2.4)
            elif (is_in_hours(hour, peak_hours) or current_load >= load_threshold) and can_discharge_kwh > 0:
                # Cycle limit check (Phase 2.5)
                remaining_cycle_kwh = max(0, max_daily_discharge_kwh - daily_discharge_kwh)
                
                if load_after_solar > target and remaining_cycle_kwh > 0:
                    required_shave = load_after_solar - target
                    possible_discharge_kw = min(required_shave, self.battery_power_kw, 
                                                (can_discharge_kwh * self.efficiency) / dt,
                                                remaining_cycle_kwh / dt)
                    
                    final_discharge_kw = possible_discharge_kw
                    daily_discharge_kwh += (final_discharge_kw * dt)
                    current_soc -= (final_discharge_kw * dt / self.efficiency)

            # Final check to prevent simultaneous charge/discharge (Phase 8 Test 4)
            if final_charge_kw > 0 and final_discharge_kw > 0:
                if final_charge_kw > final_discharge_kw:
                    final_charge_kw -= final_discharge_kw
                    final_discharge_kw = 0
                else:
                    final_discharge_kw -= final_charge_kw
                    final_charge_kw = 0

            # 4. Update State & Results
            charge_kw[i] = final_charge_kw
            discharge_kw[i] = final_discharge_kw
            soc_kwh[i+1] = current_soc
            
            # Grid Import with BESS
            # Grid Import = (Load - Solar + Charge) - Discharge
            grid_import_with_bess[i] = max(0, load_after_solar + final_charge_kw - final_discharge_kw)
            
            # Phase 1 Assertions
            assert soc_kwh[i+1] >= (self.min_soc * self.battery_kwh) - 1e-6, f"SOC underflow at {i}"
            assert soc_kwh[i+1] <= (self.max_soc * self.battery_kwh) + 1e-6, f"SOC overflow at {i}"
            assert grid_import_with_bess[i] >= -1e-6, f"Negative grid import at {i}"

        self.cumulative_throughput_kwh += daily_discharge_kwh

        return {
            "battery_soc": [s / self.battery_kwh for s in soc_kwh[:-1]],
            "battery_charge_kw": charge_kw,
            "battery_discharge_kw": discharge_kw,
            "grid_import_with_bess": grid_import_with_bess,
            "grid_import_without_bess": grid_import_without_bess,
            "daily_discharge_kwh": daily_discharge_kwh,
            "peak_reduction_kw": max(grid_import_without_bess) - max(grid_import_with_bess)
        }
