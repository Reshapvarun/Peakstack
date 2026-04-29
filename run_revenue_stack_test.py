import numpy as np
import pandas as pd
from app.simulation.data_gen import generate_industrial_profile
from app.simulation.energy_sources import generate_solar_profile, generate_wind_profile, generate_dynamic_prices
from app.core.tariff import DEFAULT_TARIFF
from app.core.battery import BatteryConfig
from app.core.optimizer import EnergyOptimizer

def run_revenue_stacking_test():
    print("--- TESTING REAL-WORLD REVENUE STACKING OPTIMIZER ---")
    
    # 1. Setup
    df = generate_industrial_profile(days=1)
    load = df['load_kw'].values
    solar = generate_solar_profile(capacity_kw=400)
    wind = generate_wind_profile(capacity_kw=200)
    prices = generate_dynamic_prices()
    
    # Baseline: Grid Only (No Solar, No Wind, No BESS, No DG)
    total_energy_no_bess = 0
    max_demand_no_bess = 0
    for i, row in df.iterrows():
        hour = row['timestamp'].hour
        total_energy_no_bess += row['load_kw'] * 0.25 * DEFAULT_TARIFF.get_rate(hour)
        if row['load_kw'] > max_demand_no_bess:
            max_demand_no_bess = row['load_kw']
    demand_charge_no_bess = max_demand_no_bess * DEFAULT_TARIFF.demand_charge_per_kva / 30.0
    cost_no_bess = total_energy_no_bess + demand_charge_no_bess

    # 2. Production Optimizer Setup
    batt_cfg = BatteryConfig(capacity_kwh=600.0, max_power_kw=200.0)
    optimizer = EnergyOptimizer(
        load_profile=load, 
        solar_profile=solar, 
        wind_profile=wind, 
        battery_cfg=batt_cfg,
        export_allowed=True, 
        max_export_limit=100.0, 
        export_rate=2.0, 
        arbitrage_enabled=True,
        dg_cost_per_kwh=15.0
    )
    
    # Solve with dynamic prices for arbitrage
    res = optimizer.solve(dynamic_prices=prices)
    
    if res is None:
        print("Optimizer failed!")
        return

    # 3. Results Analysis
    total_cost_with_bess = res['total_cost']
    
    print(f"\nBASELINE (GRID ONLY):")
    print(f"  Total Cost:    INR {cost_no_bess:.2f}")
    print(f"  Peak Demand:   {max_demand_no_bess:.2f} kW")
    print(f"--------------------------------------------------")
    print(f"OPTIMIZED (REVENUE STACKING):")
    print(f"  Energy Cost:   INR {res['energy_cost']:.2f}")
    print(f"  Demand Charge:  INR {res['demand_cost']:.2f}")
    print(f"  DG Cost:       INR {res['dg_cost']:.2f}")
    print(f"  Battery Cost:  INR {res['degradation_cost']:.2f}")
    print(f"  Export Revenue:INR {res['export_revenue']:.2f}")
    print(f"  Total Cost:    INR {total_cost_with_bess:.2f}")
    print(f"  Peak Demand:    {res['peak_demand']:.2f} kW")
    print(f"--------------------------------------------------")
    
    savings = cost_no_bess - total_cost_with_bess
    print(f"TOTAL SAVINGS:  INR {savings:.2f} ({ (savings/cost_no_bess)*100:.2f}%)")
    print(f"PEAK REDUCTION: {max_demand_no_bess - res['peak_demand']:.2f} kW")

if __name__ == "__main__":
    run_revenue_stacking_test()
