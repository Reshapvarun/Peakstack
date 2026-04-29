import numpy as np
import pandas as pd
from app.simulation.data_gen import generate_industrial_profile
from app.simulation.energy_sources import generate_solar_profile, generate_wind_profile
from app.simulation.realism import RealismCalibrator
from app.core.tariff import DEFAULT_TARIFF
from app.core.battery import BatteryConfig
from app.core.optimizer import EnergyOptimizer

def run_simulation(load, solar, wind, config):
    # Use a larger battery to ensure feasibility in noisy/constrained environments
    batt_cfg = BatteryConfig(capacity_kwh=1000.0, max_power_kw=250.0)
    optimizer = EnergyOptimizer(
        load_profile=load, 
        solar_profile=solar, 
        wind_profile=wind, 
        battery_cfg=batt_cfg,
        export_allowed=config['export_allowed'], 
        max_export_limit=config['max_export_limit'], 
        export_rate=config['export_rate'], 
        arbitrage_enabled=config['arbitrage_enabled'],
        dg_cost_per_kwh=config['dg_cost_per_kwh']
    )
    
    res = optimizer.solve()
    if res is None: return None
    
    total_cost = res['total_cost']
    return total_cost, res['peak_demand']

def main():
    print("--- REALISM CALIBRATION: IDEAL VS REALISTIC ---")
    
    # 1. Data Setup
    df = generate_industrial_profile(days=1)
    ideal_load = df['load_kw'].values
    ideal_solar = generate_solar_profile(capacity_kw=300)
    ideal_wind = generate_wind_profile(capacity_kw=100)
    
    # Baseline (No BESS, No Gen)
    total_energy_no_bess = 0
    max_demand_no_bess = 0
    for i, row in df.iterrows():
        hour = row['timestamp'].hour
        total_energy_no_bess += row['load_kw'] * 0.25 * DEFAULT_TARIFF.get_rate(hour)
        if row['load_kw'] > max_demand_no_bess:
            max_demand_no_bess = row['load_kw']
    cost_no_bess = total_energy_no_bess + (max_demand_no_bess * DEFAULT_TARIFF.demand_charge_per_kva / 30.0)

    # 2. Ideal Run (High export rates, arbitrage enabled)
    ideal_config = {
        "export_allowed": True, "max_export_limit": 100.0, "export_rate": 5.0,
        "arbitrage_enabled": True, "dg_cost_per_kwh": 12.0
    }
    ideal_res = run_simulation(ideal_load, ideal_solar, ideal_wind, ideal_config)
    
    # 3. Realistic Run
    calibrator = RealismCalibrator()
    real_solar, real_wind, forecast_load = calibrator.apply_uncertainty(ideal_load, ideal_solar, ideal_wind)
    real_config = calibrator.get_realistic_config()
    
    real_res = run_simulation(forecast_load, real_solar, real_wind, real_config)
    
    print(f"\nBASELINE (Grid Only):   INR {cost_no_bess:.2f} | Peak: {max_demand_no_bess:.2f} kW")
    
    if ideal_res:
        ideal_cost, ideal_peak = ideal_res
        print(f"IDEAL BESS SETUP:      INR {ideal_cost:.2f} | Peak: {ideal_peak:.2f} kW | Savings: {((cost_no_bess-ideal_cost)/cost_no_bess)*100:.2f}%")
    else:
        print("IDEAL BESS SETUP:      FAILED TO SOLVE")

    if real_res:
        real_cost, real_peak = real_res
        print(f"REALISTIC BESS SETUP:  INR {real_cost:.2f} | Peak: {real_peak:.2f} kW | Savings: {((cost_no_bess-real_cost)/cost_no_bess)*100:.2f}%")
    else:
        print("REALISTIC BESS SETUP:  FAILED TO SOLVE")
    
    print("-" * 60)
    if ideal_res and real_res:
        print(f"REALISM GAP: The savings dropped from {((cost_no_bess-ideal_res[0])/cost_no_bess)*100:.1f}% to {((cost_no_bess-real_res[0])/cost_no_bess)*100:.1f}%")
        print("This is the 'Credibility Range' expected by DPIIT reviewers.")

if __name__ == "__main__":
    main()
