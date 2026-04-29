import numpy as np
import pandas as pd
from app.simulation.data_gen import generate_industrial_profile
from app.simulation.energy_sources import generate_solar_profile, generate_wind_profile
from app.core.battery import BatteryConfig
from app.core.optimizer import EnergyOptimizer
from app.core.policy_manager import PolicyManager

def run_state_analysis(state_name, load, solar_base, wind_base):
    policy_mgr = PolicyManager()
    policy = policy_mgr.get_state_policy(state_name)
    
    solar = solar_base * policy.solar_mix_factor
    wind = wind_base * policy.wind_mix_factor
    
    # 1. Baseline (No BESS)
    total_energy_no_bess = 0
    max_demand_no_bess = 0
    for t in range(len(load)):
        hour = (t // 4) % 24
        rate = policy.peak_rate if (10 <= hour < 14 or 18 <= hour < 22) else policy.off_peak_rate
        net = max(0, load[t] - solar[t] - wind[t])
        total_energy_no_bess += net * 0.25 * rate
        if net > max_demand_no_bess: max_demand_no_bess = net
    
    cost_no_bess = total_energy_no_bess + (max_demand_no_bess * policy.demand_charge_per_kva / 30.0)
    
    # 2. Optimized BESS
    batt_cfg = BatteryConfig(capacity_kwh=600.0, max_power_kw=200.0)
    optimizer = EnergyOptimizer(load, solar, wind, batt_cfg, policy=policy)
    res = optimizer.solve()
    
    if not res: return None
    
    # Renewable Utilization
    total_gen = np.sum(solar + wind) * 0.25
    curtailed = res['curtailment']
    renew_util = ((total_gen - curtailed) / total_gen * 100) if total_gen > 0 else 100
    
    return {
        "State": state_name,
        "Cost": res['total_cost'],
        "Savings%": ((cost_no_bess - res['total_cost']) / cost_no_bess) * 100,
        "PeakRed%": ((max_demand_no_bess - res['peak_demand']) / max_demand_no_bess) * 100,
        "Curtailment": res['curtailment'],
        "BESS_Util%": res['battery_util'] * 100,
        "RenewUtil%": renew_util,
        "NetMetering": policy.net_metering_enabled
    }

def main():
    print("--- FINAL PRODUCTION READINESS VALIDATION ---")
    df = generate_industrial_profile(days=1)
    load = df['load_kw'].values
    solar_base = generate_solar_profile(capacity_kw=400)
    wind_base = generate_wind_profile(capacity_kw=100)
    
    states = ["Karnataka", "Tamil Nadu", "Maharashtra", "Gujarat", "Telangana", "Rajasthan", "Uttar Pradesh"]
    results = []
    for s in states:
        res = run_state_analysis(s, load, solar_base, wind_base)
        if res: results.append(res)
        
    df_res = pd.DataFrame(results)
    print("\nFINAL PRODUCTION COMPARISON TABLE:")
    print("-----------------------------------------------------------------------------------------------------------------------")
    print(df_res.to_string(index=False))
    print("-----------------------------------------------------------------------------------------------------------------------")
    
    best = df_res.loc[df_res['Cost'].idxmin()]
    print(f"\nHIGHEST FINANCIAL RETURN: {best['State']}")
    print(f"Reason: {'Net Metering Enabled' if best['NetMetering'] else 'High Efficiency Peak Shaving'} in {best['State']}")

if __name__ == "__main__":
    main()
