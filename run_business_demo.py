import numpy as np
import pandas as pd
from app.simulation.data_gen import generate_industrial_profile
from app.core.tariff import DEFAULT_TARIFF
from app.core.battery import BatteryConfig
from app.core.optimizer import EnergyOptimizer
from app.core.finance import FinancialEngine, FinanceConfig
from app.core.what_if import WhatIfEngine

def run_site_simulation(site_id, days=1):
    df = generate_industrial_profile(days=days, site_id=site_id)
    load = df['load_kw'].values
    solar = df['solar_kw'].values
    
    # Baseline
    total_energy_no_bess = 0
    max_demand_no_bess = 0
    for i, row in df.iterrows():
        hour = row['timestamp'].hour
        net = max(0, row['load_kw'] - row['solar_kw'])
        total_energy_no_bess += net * 0.25 * DEFAULT_TARIFF.get_rate(hour)
        if net > max_demand_no_bess:
            max_demand_no_bess = net
    demand_charge_no_bess = max_demand_no_bess * DEFAULT_TARIFF.demand_charge_per_kva / 30.0
    cost_no_bess = total_energy_no_bess + demand_charge_no_bess

    # Optimized
    batt_cfg = BatteryConfig(capacity_kwh=500.0, max_power_kw=200.0)
    optimizer = EnergyOptimizer(load, solar, batt_cfg)
    res = optimizer.solve()
    
    cost_with_bess = res['total_cost'] + (res['peak_demand'] * DEFAULT_TARIFF.demand_charge_per_kva / 30.0)
    daily_savings = cost_no_bess - cost_with_bess
    
    return {
        "site_id": site_id,
        "baseline_cost": cost_no_bess,
        "optimized_cost": cost_with_bess,
        "daily_savings": daily_savings,
        "peak_reduction": max_demand_no_bess - res['peak_demand'],
        "battery_capacity": batt_cfg.capacity_kwh
    }

def main():
    print("--- RUNNING ENTERPRISE BUSINESS DEMO ---")
    
    # 1. Multi-Site Simulation
    sites = ["Factory_Ahmedabad", "Plant_Pune", "Warehouse_Bangalore", "Unit_Chennai"]
    all_site_results = []
    
    print(f"\nSimulating {len(sites)} sites...")
    for site in sites:
        res = run_site_simulation(site)
        all_site_results.append(res)
    
    # Aggregate Metrics
    total_daily_savings = sum(s['daily_savings'] for s in all_site_results)
    avg_peak_reduction = np.mean([s['peak_reduction'] for s in all_site_results])
    
    print(f"\nAGGREGATE PERFORMANCE:")
    print(f"--------------------------------------------------")
    print(f"Total Daily Savings:  INR {total_daily_savings:.2f}")
    print(f"Annualized Savings:   INR {total_daily_savings * 365:.2f}")
    print(f"Avg Peak Reduction:   {avg_peak_reduction:.2f} kW")
    print(f"--------------------------------------------------")

    # 2. Financial Analysis (For one typical site)
    fin_engine = FinancialEngine(FinanceConfig())
    typical_site = all_site_results[0]
    roi_res = fin_engine.calculate_roi(typical_site['daily_savings'], typical_site['battery_capacity'])
    
    print(f"\nFINANCIAL FEASIBILITY (Typical Site):")
    print(f"--------------------------------------------------")
    print(f"Estimated CAPEX:      INR {roi_res['total_capex']:,.2f}")
    print(f"Annual Net Savings:    INR {roi_res['annual_savings']:,.2f}")
    print(f"Payback Period:        {roi_res['payback_period_years']:.2f} years")
    print(f"Annual ROI:           {roi_res['annual_roi_pct']:.2f}%")
    print(f"10-Year NPV:          INR {roi_res['net_present_value_10yr']:,.2f}")
    print(f"--------------------------------------------------")

    # 3. What-If Analysis
    print("\nRUNNING WHAT-IF ANALYSIS (Optimizing Battery Size)...")
    df_sample = generate_industrial_profile(days=1)
    wi_engine = WhatIfEngine(df_sample['load_kw'].values, df_sample['solar_kw'].values)
    
    sizes = [200, 400, 600, 800, 1000]
    wi_results = wi_engine.analyze_battery_sizes(sizes, power_kw_fixed=200.0)
    
    print(f"Capacity (kWh) | Peak Demand (kW) | Total Cost")
    print(f"--------------------------------------------------")
    for r in wi_results:
        print(f"{r['capacity_kwh']:^14} | {r['peak_demand']:^16.2f} | {r['total_cost']:^12.2f}")
    print(f"--------------------------------------------------")

if __name__ == "__main__":
    main()
