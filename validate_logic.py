import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.simulation.data_gen import generate_industrial_profile
from app.core.tariff import DEFAULT_TARIFF

def run_validation():
    print("--- Validating EMS Simulation & Tariff Logic ---")
    
    # 1. Generate 1 day of sample data
    df = generate_industrial_profile(days=1)
    
    # Battery Specs
    CAPACITY = 200.0 # kWh
    MAX_POWER = 100.0 # kW
    EFFICIENCY = 0.90
    SOC = 0.5 * CAPACITY # Start at 50%
    
    # --- BASELINE: NO BATTERY ---
    total_energy_cost_no_bess = 0
    max_demand_no_bess = 0
    
    for i, row in df.iterrows():
        hour = row['timestamp'].hour
        # Net load = Load - Solar
        net_load = max(0, row['load_kw'] - row['solar_kw'])
        
        # Energy cost for 15 mins (0.25 hours)
        rate = DEFAULT_TARIFF.get_rate(hour)
        total_energy_cost_no_bess += net_load * 0.25 * rate
        
        if net_load > max_demand_no_bess:
            max_demand_no_bess = net_load
            
    demand_charge_no_bess = max_demand_no_bess * DEFAULT_TARIFF.demand_charge_per_kva / 1000 
    total_cost_no_bess = total_energy_cost_no_bess + demand_charge_no_bess

    # --- RULE-BASED BESS ---
    total_energy_cost_with_bess = 0
    max_demand_with_bess = 0
    current_soc = SOC
    
    for i, row in df.iterrows():
        hour = row['timestamp'].hour
        net_load = max(0, row['load_kw'] - row['solar_kw'])
        
        # Rule-based logic
        battery_power = 0 # Positive = discharge, Negative = charge
        
        # Charge during off-peak (0-6)
        if 0 <= hour < 6:
            charge_amount = min(MAX_POWER, (CAPACITY - current_soc) / (0.25 * EFFICIENCY))
            battery_power = -charge_amount
        
        # Discharge during peak (18-22)
        elif 18 <= hour < 22:
            discharge_amount = min(MAX_POWER, (current_soc * EFFICIENCY) / 0.25)
            battery_power = discharge_amount
            
        # Update SOC
        if battery_power < 0: # Charging
            current_soc += abs(battery_power) * 0.25 * EFFICIENCY
        else: # Discharging
            current_soc -= (battery_power * 0.25) / EFFICIENCY
            
        current_soc = max(0, min(CAPACITY, current_soc))
        
        # New net load from grid
        grid_load = max(0, net_load - battery_power)
        
        rate = DEFAULT_TARIFF.get_rate(hour)
        total_energy_cost_with_bess += grid_load * 0.25 * rate
        
        if grid_load > max_demand_with_bess:
            max_demand_with_bess = grid_load

    demand_charge_with_bess = max_demand_with_bess * DEFAULT_TARIFF.demand_charge_per_kva / 1000
    total_cost_with_bess = total_energy_cost_with_bess + demand_charge_with_bess
    
    # Results
    savings = total_cost_no_bess - total_cost_with_bess
    savings_pct = (savings / total_cost_no_bess) * 100
    peak_reduction = max_demand_no_bess - max_demand_with_bess
    
    print(f"\nRESULTS FOR 24 HOURS:")
    print(f"--------------------------------------------------")
    print(f"Cost without BESS:   INR {total_cost_no_bess:.2f}")
    print(f"Cost with BESS:     INR {total_cost_with_bess:.2f}")
    print(f"Total Savings:      INR {savings:.2f} ({savings_pct:.2f}%)")
    print(f"--------------------------------------------------")
    print(f"Peak Demand (No BESS):   {max_demand_no_bess:.2f} kW")
    print(f"Peak Demand (With BESS): {max_demand_with_bess:.2f} kW")
    print(f"Peak Reduction:          {peak_reduction:.2f} kW")
    print(f"--------------------------------------------------")

if __name__ == "__main__":
    run_validation()
