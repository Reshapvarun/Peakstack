import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.simulation.data_gen import generate_industrial_profile
from app.core.tariff import TariffManager
from app.core.optimizer import EnergyOptimizer
from app.core.battery import BatteryConfig

def run_validation():
    print("==================================================")
    print("PEAKSTACK EMS NUMERICAL VALIDATION")
    print("==================================================")
    
    # 1. Load Hardened Tariff
    tm = TariffManager()
    tariff = tm.get_tariff("maharashtra") # MSEDCL HT-I
    if not tariff:
        from app.core.tariff import DEFAULT_TARIFF, load_tariff
        tariff = load_tariff("maharashtra")
        print("Using default/fallback tariff.")
    else:
        print(f"Loaded {tariff.state_name} ({tariff.utility}) Tariff")

    # 2. Generate 1 day of realistic industrial data
    df = generate_industrial_profile(days=1)
    load = df['load_kw'].values
    solar = df['solar_kw'].values
    
    # 3. Setup Hardened Optimization Engine
    batt = BatteryConfig(
        capacity_kwh=500.0,
        max_power_kw=125.0
    )
    
    optimizer = EnergyOptimizer(load, solar, batt, tariff)
    result = optimizer.solve()
    
    if not result:
        print("Optimization failed!")
        return

    # 4. Numerical Audit
    daily_savings = result['baseline_cost'] - result['optimized_cost']
    savings_pct = (daily_savings / result['baseline_cost']) * 100
    peak_red_kw = result['peak_demand_baseline'] - result['peak_demand']
    
    print(f"\nRESULTS FOR 24-HOUR SIMULATION:")
    print("-" * 50)
    print(f"Baseline Peak Demand:      {result['peak_demand_baseline']:.1f} kW")
    print(f"Post-EMS Peak Demand:      {result['peak_demand']:.1f} kW")
    print(f"Peak Reduction:            {peak_red_kw:.1f} kW")
    print("-" * 50)
    print(f"Baseline Daily Cost:       INR {result['baseline_cost']:,.0f}")
    print(f"Post-EMS Daily Cost:       INR {result['optimized_cost']:,.0f}")
    print(f"Estimated Daily Savings:   INR {daily_savings:,.0f} ({savings_pct:.1f}%)")
    print("-" * 50)
    print(f"Battery Utilization:       {result['battery_util']*100:.1f}%")
    
    # VALIDATION TESTS
    print("\nVALIDATION TESTS:")
    
    # 1. Cost check
    print(f"Test 1: Savings > 0 | {'PASS' if daily_savings > 0 else 'FAIL'}")
    
    # 2. Savings range
    print(f"Test 2: Savings (10-40%) | {'PASS' if 10 <= savings_pct <= 40 else 'CAUTION'}")

    # 3. Peak reduction
    print(f"Test 3: Peak Reduction > 0 | {'PASS' if peak_red_kw > 0 else 'FAIL'}")

    print("==================================================")

    # 4. Savings Realistic (8% - 35%)
    print(f"Test 4: Savings Range Check | {'PASS' if 8 <= savings_pct <= 35 else 'CAUTION'}")

    print("==================================================")

if __name__ == "__main__":
    run_validation()
