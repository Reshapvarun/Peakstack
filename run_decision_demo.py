import numpy as np
from app.simulation.data_gen import generate_industrial_profile
from app.core.tariff import DEFAULT_TARIFF
from app.core.battery import BatteryConfig
from app.core.finance import FinanceConfig
from app.core.decision_engine import InvestmentAdvisor

def main():
    print("--- RUNNING BESS INVESTMENT DECISION ENGINE ---")
    
    # 1. Setup
    df = generate_industrial_profile(days=1)
    load = df['load_kw'].values
    solar = df['solar_kw'].values
    
    fin_cfg = FinanceConfig(capex_per_kwh=12000.0) # Reduced CAPEX to be more realistic
    advisor = InvestmentAdvisor(load, solar, fin_cfg)
    
    # 2. Optimal Sizing
    print("\nSearching for optimal battery size...")
    sizes = [100, 200, 300, 400, 500, 600, 700, 800, 1000]
    best_size, best_res = advisor.find_optimal_sizing(sizes, power_fixed=150.0)
    
    print(f"Recommended Size: {best_size} kWh")
    print(f"Min Payback Period: {best_res['payback']:.2f} years")
    print(f"Estimated Annual Savings: INR {best_res['annual_savings']:,.2f}")

    # 3. Business Model Comparison
    print("\nComparing Business Models for Recommended Size...")
    model_comp = advisor.compare_business_models(best_res['daily_savings'], best_size)
    
    print(f"{'Model':<25} | {'Client Upfront':<15} | {'Client Payback':<15} | {'Provider Payback':<15}")
    print("-" * 75)
    for m in model_comp:
        print(f"{m['model']:<25} | {m['client_upfront']:<15.0f} | {m['client_payback_yrs']:<15.2f} | {m['provider_payback_yrs']:<15.2f}")

    # 4. DG Replacement Scenario
    # Assume 100kWh of DG usage per day with a ₹5 premium over grid cost
    total_savings, dg_extra = advisor.analyze_dg_replacement(best_res['daily_savings'], 100.0, 5.0)
    
    # Recalculate ROI with DG replacement
    roi_dg = advisor.fin_engine.calculate_roi(total_savings, best_size)
    
    print(f"\nDG REPLACEMENT IMPACT:")
    print(f"Extra Daily Savings from DG: INR {dg_extra:.2f}")
    print(f"Updated Payback Period:     {roi_dg['payback_period_years']:.2f} years")
    print(f"ROI improvement:           {best_res['payback'] - roi_dg['payback_period_years']:.2f} years faster")

if __name__ == "__main__":
    main()
