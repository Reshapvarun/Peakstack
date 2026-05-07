import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.simulation.data_gen import generate_industrial_profile
from app.core.tariff import TariffManager
from app.core.dispatch_engine import RuleBasedDispatchEngine
from app.core.engine import BillingEngine

def run_validation():
    print("==================================================")
    print("PEAKSTACK EMS NUMERICAL VALIDATION")
    print("==================================================")
    
    # 1. Load Hardened Tariff
    tm = TariffManager()
    tariff = tm.get_tariff("maharashtra") # MSEDCL HT-I
    if not tariff:
        from app.core.tariff import DEFAULT_TARIFF
        tariff = DEFAULT_TARIFF
        print("Using default fallback tariff.")
    else:
        print(f"Loaded {tariff.state_name} ({tariff.utility}) Tariff")

    # 2. Generate 1 day of realistic industrial data
    df = generate_industrial_profile(days=1)
    load_profile = df['load_kw'].tolist()
    solar_profile = df['solar_kw'].tolist()
    
    # 3. Setup Hardened Dispatch Engine
    # 500 kWh / 125 kW (4-hour battery)
    battery_kwh = 500.0
    battery_power_kw = 125.0
    
    dispatch_engine = RuleBasedDispatchEngine(
        battery_kwh=battery_kwh,
        battery_power_kw=battery_power_kw
    )
    
    # Run Dispatch with 85th percentile target shaving
    target_limit = np.percentile(load_profile, 85)
    
    results = dispatch_engine.run_dispatch(
        load_profile=load_profile,
        solar_profile=solar_profile,
        peak_hours=tariff.peak_hours,
        offpeak_hours=tariff.offpeak_hours,
        target_grid_limit_kw=target_limit
    )
    
    # 4. Setup Billing Engine
    billing_engine = BillingEngine(tariff)
    
    bill_no_bess = billing_engine.calculate_bill(results['grid_import_without_bess'])
    bill_with_bess = billing_engine.calculate_bill(results['grid_import_with_bess'])
    
    # 5. Numerical Audit (Phase 1)
    savings = bill_no_bess['total_bill'] - bill_with_bess['total_bill']
    savings_pct = (savings / bill_no_bess['total_bill']) * 100
    peak_red_kva = bill_no_bess['peak_demand_kva'] - bill_with_bess['peak_demand_kva']
    
    print(f"\nRESULTS FOR 24-HOUR SIMULATION:")
    print("-" * 50)
    print(f"Baseline Peak Demand:      {bill_no_bess['peak_demand_kva']:.1f} kVA")
    print(f"Post-EMS Peak Demand:      {bill_with_bess['peak_demand_kva']:.1f} kVA")
    print(f"Peak Reduction:            {peak_red_kva:.1f} kVA")
    print("-" * 50)
    print(f"Baseline Monthly Cost:     INR {bill_no_bess['total_bill']:,.0f}")
    print(f"Post-EMS Monthly Cost:     INR {bill_with_bess['total_bill']:,.0f}")
    print(f"Estimated Monthly Savings: INR {savings:,.0f} ({savings_pct:.1f}%)")
    print("-" * 50)
    print(f"Daily Discharge Cycle:     {results['daily_discharge_kwh']/battery_kwh:.2f}")
    
    # VALIDATION TESTS (Phase 8)
    print("\nVALIDATION TESTS:")
    
    # 1. SOC Limits
    soc_min = min(results['battery_soc'])
    soc_max = max(results['battery_soc'])
    print(f"Test 1: SOC Window [{soc_min*100:.1f}%, {soc_max*100:.1f}%] | {'PASS' if 0.19 <= soc_min and soc_max <= 0.91 else 'FAIL'}")
    
    # 2. No Negative Grid Import
    min_import = min(results['grid_import_with_bess'])
    print(f"Test 2: Min Grid Import: {min_import:.1f} kW | {'PASS' if min_import >= -1e-6 else 'FAIL'}")
    
    # 3. Impossible Behavior (Simultaneous charge/discharge)
    simultaneous = sum(1 for c, d in zip(results['battery_charge_kw'], results['battery_discharge_kw']) if c > 0.1 and d > 0.1)
    print(f"Test 3: Simultaneous Chg/Dchg Intervals: {simultaneous} | {'PASS' if simultaneous == 0 else 'FAIL'}")

    # 4. Savings Realistic (8% - 35%)
    print(f"Test 4: Savings Range Check | {'PASS' if 8 <= savings_pct <= 35 else 'CAUTION'}")

    print("==================================================")

if __name__ == "__main__":
    run_validation()
