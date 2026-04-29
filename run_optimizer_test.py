import numpy as np
import pandas as pd
from app.simulation.data_gen import generate_industrial_profile
from app.core.tariff import DEFAULT_TARIFF
from app.core.battery import BatteryConfig
from app.core.optimizer import EnergyOptimizer

def run_test():
    print("--- Testing PRODUCTION-GRADE Optimizer ---")
    
    # 1. Data Setup
    df = generate_industrial_profile(days=1)
    load = df['load_kw'].values
    solar = df['solar_kw'].values
    
    # Baseline Calculation (No Battery)
    total_energy_no_bess = 0
    max_demand_no_bess = 0
    for i, row in df.iterrows():
        hour = row['timestamp'].hour
        net = max(0, row['load_kw'] - row['solar_kw'])
        total_energy_no_bess += net * 0.25 * DEFAULT_TARIFF.get_rate(hour)
        if net > max_demand_no_bess:
            max_demand_no_bess = net
            
    demand_charge_no_bess = max_demand_no_bess * DEFAULT_TARIFF.demand_charge_per_kva / 30.0 # Daily pro-rata
    cost_no_bess = total_energy_no_bess + demand_charge_no_bess
    
    # 2. Optimizer Setup
    batt_cfg = BatteryConfig(capacity_kwh=500.0, max_power_kw=200.0) 
    optimizer = EnergyOptimizer(load, solar, batt_cfg)
    
    # Solve
    result = optimizer.solve()
    
    if result is None:
        print("Optimizer failed to find solution!")
        return

    # 3. Results Breakdown
    cost_with_bess = result['total_cost']
    peak_with_bess = result['peak_demand']
    
    savings = cost_no_bess - cost_with_bess
    savings_pct = (savings / cost_no_bess) * 100
    
    print(f"\nCOST BREAKDOWN (24H):")
    print(f"--------------------------------------------------")
    print(f"BASELINE (No BESS):")
    print(f"  Energy Cost:    INR {total_energy_no_bess:.2f}")
    print(f"  Demand Charge:  INR {demand_charge_no_bess:.2f}")
    print(f"  Total Cost:     INR {cost_no_bess:.2f}")
    print(f"  Peak Demand:    {max_demand_no_bess:.2f} kW")
    print(f"--------------------------------------------------")
    print(f"OPTIMIZED (With BESS):")
    print(f"  Energy Cost:    INR {result['energy_cost']:.2f}")
    print(f"  Demand Charge:  INR {result['demand_cost']:.2f}")
    print(f"  Battery Cost:    INR {result['degradation_cost']:.2f}")
    print(f"  Total Cost:     INR {cost_with_bess:.2f}")
    print(f"  Peak Demand:    {peak_with_bess:.2f} kW")
    print(f"--------------------------------------------------")
    print(f"FINAL METRICS:")
    print(f"  Total Savings:  INR {savings:.2f} ({savings_pct:.2f}%)")
    print(f"  Peak Reduction: {max_demand_no_bess - peak_with_bess:.2f} kW")
    print(f"  Reduction %:     {((max_demand_no_bess - peak_with_bess)/max_demand_no_bess)*100:.2f}%")
    print(f"--------------------------------------------------")

if __name__ == "__main__":
    run_test()
