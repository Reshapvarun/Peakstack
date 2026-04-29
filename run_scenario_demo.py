import numpy as np
import pandas as pd
from app.simulation.data_gen import generate_industrial_profile
from app.simulation.energy_sources import generate_solar_profile, generate_wind_profile, generate_dynamic_prices
from app.core.scenario_engine import ScenarioEngine

def main():
    print("--- RUNNING MULTI-SCENARIO ENERGY INTELLIGENCE PLATFORM ---")
    
    df = generate_industrial_profile(days=1)
    load = df['load_kw'].values
    solar = generate_solar_profile(capacity_kw=400)
    wind = generate_wind_profile(capacity_kw=200)
    prices = generate_dynamic_prices()
    
    engine = ScenarioEngine(load, solar, wind, prices)
    
    scenarios = [
        ("Grid Only", {'has_bess': False, 'has_solar': False, 'has_wind': False, 'arbitrage_enabled': False, 'bess_capacity': 0, 'bess_power': 0, 'export_allowed': False}),
        ("Grid + BESS", {'has_bess': True, 'has_solar': False, 'has_wind': False, 'arbitrage_enabled': False, 'bess_capacity': 500, 'bess_power': 200, 'export_allowed': False}),
        ("Solar + Grid", {'has_bess': False, 'has_solar': True, 'has_wind': False, 'arbitrage_enabled': False, 'bess_capacity': 0, 'bess_power': 0, 'export_allowed': False}),
        ("Solar + BESS", {'has_bess': True, 'has_solar': True, 'has_wind': False, 'arbitrage_enabled': False, 'bess_capacity': 500, 'bess_power': 200, 'export_allowed': False}),
        ("Solar + Wind + BESS", {'has_bess': True, 'has_solar': True, 'has_wind': True, 'arbitrage_enabled': False, 'bess_capacity': 500, 'bess_power': 200, 'export_allowed': False}),
        ("Solar + Wind + BESS (Arbitrage)", {'has_bess': True, 'has_solar': True, 'has_wind': True, 'arbitrage_enabled': True, 'bess_capacity': 500, 'bess_power': 200, 'export_allowed': True}),
    ]
    
    results = []
    for name, cfg in scenarios:
        res = engine.run_scenario(name, cfg)
        if res: results.append(res)
        
    df_res = pd.DataFrame(results)
    print("\nSCENARIO COMPARISON TABLE:")
    print("---------------------------------------------------------------------------------------")
    print(df_res[['scenario', 'total_cost', 'savings', 'peak', 'payback', 'roi_pct']].to_string(index=False))
    print("---------------------------------------------------------------------------------------")
    
    best_scenario = df_res.loc[df_res['total_cost'].idxmin()]
    print(f"\nBEST CONFIGURATION: {best_scenario['scenario']}")
    print(f"Lowest Daily Cost: INR {best_scenario['total_cost']:.2f}")
    
    print("\nDECISION INSIGHTS:")
    grid_only_peak = df_res[df_res['scenario'] == "Grid Only"]['peak'].values[0]
    print(f"- Best mix reduces peak demand by {((grid_only_peak - best_scenario['peak'])/grid_only_peak)*100:.2f}%")
    
    # Safe check for solar vs solar+bess
    try:
        solar_only = df_res[df_res['scenario'] == "Solar + Grid"]['savings'].values[0]
        solar_bess = df_res[df_res['scenario'] == "Solar + BESS"]['savings'].values[0]
        print(f"- Adding BESS to Solar increases daily savings from INR {solar_only:.2f} to INR {solar_bess:.2f}")
    except IndexError:
        print("- Solar comparison data unavailable.")

if __name__ == "__main__":
    main()
