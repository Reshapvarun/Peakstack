import numpy as np
import pandas as pd
from app.simulation.data_gen import generate_industrial_profile
from app.simulation.energy_sources import generate_solar_profile, generate_wind_profile
from app.core.tariff import DEFAULT_TARIFF
from app.core.battery import BatteryConfig
from app.core.optimizer import EnergyOptimizer

def run_scenario(name, load, solar, wind, has_bess=False):
    if has_bess:
        batt_cfg = BatteryConfig(capacity_kwh=600.0, max_power_kw=200.0)
        optimizer = EnergyOptimizer(load, solar, wind, batt_cfg)
        res = optimizer.solve()
        if res:
            return res
    else:
        # Simple calculation for non-BESS
        total_energy = 0
        max_demand = 0
        curtail = 0
        for t in range(len(load)):
            hour = (t // 4) % 24
            net = load[t] - solar[t] - wind[t]
            if net < 0:
                curtail += abs(net)
                net = 0
            total_energy += net * 0.25 * DEFAULT_TARIFF.get_rate(hour)
            if net > max_demand:
                max_demand = net
        
        demand_cost = max_demand * DEFAULT_TARIFF.demand_charge_per_kva / 30.0
        return {
            "total_cost": total_energy + demand_cost,
            "energy_cost": total_energy,
            "demand_cost": demand_cost,
            "dg_cost": 0,
            "degradation_cost": 0,
            "peak_demand": max_demand,
            "curtailment": curtail
        }

def main():
    print("--- REAL-WORLD INDIAN BTM VALIDATION ---")
    df = generate_industrial_profile(days=1)
    load = df['load_kw'].values
    solar = generate_solar_profile(capacity_kw=400)
    wind = generate_wind_profile(capacity_kw=200)
    
    scenarios = [
        ("Grid Only", False, 0, 0),
        ("Solar + Grid", False, 400, 0),
        ("Solar + Wind + Grid", False, 400, 200),
        ("Solar + Wind + BESS", True, 400, 200),
    ]
    
    results = []
    for name, has_bess, s_cap, w_cap in scenarios:
        # Setup specific gen for this scenario
        s = generate_solar_profile(capacity_kw=s_cap) if s_cap > 0 else np.zeros_like(load)
        w = generate_wind_profile(capacity_kw=w_cap) if w_cap > 0 else np.zeros_like(load)
        
        res = run_scenario(name, load, s, w, has_bess)
        if res:
            res['scenario'] = name
            results.append(res)

    df_res = pd.DataFrame(results)
    print("\nBTM SCENARIO COMPARISON:")
    print("---------------------------------------------------------------------------------------")
    print(df_res[['scenario', 'total_cost', 'energy_cost', 'demand_cost', 'peak_demand']].to_string(index=False))
    print("---------------------------------------------------------------------------------------")
    
    best = df_res.loc[df_res['total_cost'].idxmin()]
    baseline = df_res[df_res['scenario'] == "Grid Only"]['total_cost'].values[0]
    
    print(f"\nBEST BTM CONFIG: {best['scenario']}")
    print(f"Daily Savings: INR {baseline - best['total_cost']:.2f} ({((baseline - best['total_cost'])/baseline)*100:.2f}%)")
    print(f"Peak Reduction: {df_res[df_res['scenario'] == 'Grid Only']['peak_demand'].values[0] - best['peak_demand']:.2f} kW")
    
    # Business Insights
    if 'curtailment' in df_res.columns:
        bess_curtail = df_res[df_res['scenario'] == "Solar + Wind + BESS"]['curtailment'].values[0] if "Solar + Wind + BESS" in df_res['scenario'].values else 0
        no_bess_curtail = df_res[df_res['scenario'] == "Solar + Wind + Grid"]['curtailment'].values[0] if "Solar + Wind + Grid" in df_res['scenario'].values else 0
        reduction = ((no_bess_curtail - bess_curtail) / no_bess_curtail * 100) if no_bess_curtail > 0 else 0
        print(f"BESS reduced curtailed energy by {reduction:.2f}%")

if __name__ == "__main__":
    main()
