import numpy as np
import pandas as pd
from app.simulation.data_gen import generate_industrial_profile
from app.simulation.energy_sources import generate_solar_profile, generate_wind_profile
from app.core.tariff import DEFAULT_TARIFF
from app.core.battery import BatteryConfig
from app.core.optimizer import EnergyOptimizer
from app.core.policy_manager import PolicyManager

def main():
    print("--- TESTING POLICY-AWARE ENERGY PLATFORM ---")
    
    # 1. Setup
    df = generate_industrial_profile(days=1)
    load = df['load_kw'].values
    solar = generate_solar_profile(capacity_kw=500)
    wind = generate_wind_profile(capacity_kw=200)
    
    # Load Policy
    policy_mgr = PolicyManager()
    
    batt_cfg = BatteryConfig(capacity_kwh=800.0, max_power_kw=250.0)
    optimizer = EnergyOptimizer(load, solar, wind, batt_cfg, policy_manager=policy_mgr)
    
    res = optimizer.solve()
    
    if res is None:
        print("Optimizer failed!")
        return

    # 2. Output Results
    print(f"\nPOLICY MODE: {res['policy_mode']}")
    print(f"State: {policy_mgr.policy.state}")
    print(f"--------------------------------------------------")
    print(f"Total Cost:      INR {res['total_cost']:.2f}")
    print(f"Energy Cost:     INR {res['energy_cost']:.2f}")
    print(f"Demand Charge:   INR {res['demand_cost']:.2f}")
    print(f"DG Cost:         INR {res['dg_cost']:.2f}")
    print(f"Export Revenue:  INR {res['export_revenue']:.2f}")
    print(f"Curtailed Energy: {res['curtailment']:.2f} kWh")
    print(f"Peak Demand:     {res['peak_demand']:.2f} kW")
    print(f"--------------------------------------------------")
    
    # 3. Policy Warnings
    warnings = policy_mgr.get_policy_warnings(res)
    print("\nREGULATORY NOTICES:")
    for w in warnings:
        print(f"NOTICE: {w}")

if __name__ == "__main__":
    main()
