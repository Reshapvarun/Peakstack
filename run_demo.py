import json
import numpy as np
from app.core.dispatch_engine import RuleBasedDispatchEngine
from app.core.engine import BillingEngine

def run_demo():
    # 1. Load Maharashtra tariff (better arbitrage for demo)
    with open('config/state_tariffs.json', 'r') as f:
        tariffs = json.load(f)
    
    mh_tariff = tariffs['maharashtra']
    
    # 2. Generate synthetic 96-point industrial load profile
    # (base load 200 kW, peak 400 kW during tariff peak hours)
    load_profile = []
    for i in range(96):
        hour = (i // 4) % 24
        # Align with MH Peak hours: 09:00-12:00 and 18:00-21:00
        if (9 <= hour < 12) or (18 <= hour < 21):
            load_profile.append(400.0)
        else:
            load_profile.append(200.0)
            
    # 3. Runs dispatch engine with 500 kWh / 125 kW battery
    dispatch_engine = RuleBasedDispatchEngine(
        battery_kwh=500,
        battery_power_kw=125,
        min_soc=0.2,
        max_soc=0.9
    )
    
    # Use MH peak/off-peak for dispatch
    dispatch_results = dispatch_engine.run_dispatch(
        load_profile=load_profile,
        solar_profile=[0.0]*96, 
        peak_hours=mh_tariff['peak_hours'],
        offpeak_hours=mh_tariff['offpeak_hours']
    )
    
    # 4. Runs billing engine for WITH and WITHOUT BESS
    billing_engine = BillingEngine(mh_tariff)
    
    bill_without_bess = billing_engine.calculate_bill(dispatch_results['grid_import_without_bess'])
    bill_with_bess = billing_engine.calculate_bill(dispatch_results['grid_import_with_bess'])
    
    # 5. Prints a clean summary
    savings = bill_without_bess['total_bill'] - bill_with_bess['total_bill']
    annual_savings = savings * 12
    
    # Simple Payback calculation
    # Estimated CAPEX: INR 15,000 / kWh
    capex = 500 * 15000
    payback = capex / annual_savings if annual_savings > 0 else float('inf')
    
    print("=========================================")
    print("      PEAKSTACK EMS ANALYSIS DEMO        ")
    print("=========================================")
    print(f"State: {mh_tariff['state_name']} ({mh_tariff['utility']})")
    print(f"Battery: 500 kWh / 125 kW")
    print("-----------------------------------------")
    print(f"MONTHLY BILL WITHOUT BESS: INR {bill_without_bess['total_bill']:,.2f}")
    print(f"MONTHLY BILL WITH BESS:    INR {bill_with_bess['total_bill']:,.2f}")
    print(f"MONTHLY SAVINGS:           INR {savings:,.2f}")
    print(f"ANNUAL SAVINGS:            INR {annual_savings:,.2f}")
    print("-----------------------------------------")
    print(f"PEAK DEMAND REDUCTION:     {bill_without_bess['peak_demand_kva']:.1f} kVA -> {bill_with_bess['peak_demand_kva']:.1f} kVA")
    print(f"SIMPLE PAYBACK:            {payback:.2f} years")
    print("=========================================")

if __name__ == "__main__":
    run_demo()
