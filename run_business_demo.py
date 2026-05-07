import asyncio
import json
from app.pipeline import PipelineOrchestrator

async def run_business_demo():
    """
    Simulates a multi-site enterprise EMS rollout.
    """
    orchestrator = PipelineOrchestrator()
    
    sites = [
        {
            "site_name": "Chennai Manufacturing Unit",
            "state": "tamil_nadu",
            "battery_kwh": 500,
            "battery_power_kw": 125,
            "annual_kwh": 1200000,
            "solar_kw": 0
        },
        {
            "site_name": "Pune Automotive Parts",
            "state": "maharashtra",
            "battery_kwh": 1000,
            "battery_power_kw": 250,
            "annual_kwh": 2400000,
            "solar_kw": 200
        },
        {
            "site_name": "Bengaluru Data Center",
            "state": "karnataka",
            "battery_kwh": 250,
            "battery_power_kw": 100,
            "annual_kwh": 800000,
            "solar_kw": 50
        }
    ]
    
    results = []
    print("Starting Peakstack Enterprise Analysis...")
    
    for site in sites:
        res = await orchestrator.run(site)
        results.append(res)
        print(res['investor_summary'])

    # Aggregate Metrics (Phase 5)
    total_capex = sum(r['financials']['estimated_capex'] for r in results)
    total_savings_y1 = sum(r['financials']['annual_savings_year1'] for r in results)
    total_peak_reduction_kw = sum(r['dispatch']['peak_reduction_kw'] for r in results)
    total_capacity_kwh = sum(s['battery_kwh'] for s in sites)
    
    # Sort by IRR (Phase 5 Site Ranking)
    ranked_sites = sorted(results, key=lambda x: x['financials']['irr_pct'], reverse=True)
    
    print("\n" + "="*50)
    print("ENTERPRISE FLEET SUMMARY")
    print("="*50)
    print(f"Total Sites Analyzed:      {len(sites)}")
    print(f"Total Battery Capacity:    {total_capacity_kwh} kWh")
    print(f"Total Fleet Peak Shaving:  {total_peak_reduction_kw:.1f} kW")
    print(f"Total Fleet CAPEX:         INR {total_capex:,.0f}")
    print(f"Total Annual Savings (Y1): INR {total_savings_y1:,.0f}")
    print(f"Aggregate Simple Payback:  {total_capex / total_savings_y1:.1f} years")
    
    print("\nSITE RANKING (By IRR)")
    print("-" * 30)
    for i, r in enumerate(ranked_sites):
        justified = "YES" if r['is_economically_justified'] else "NO"
        print(f"{i+1}. {r['site_name']} | IRR: {r['financials']['irr_pct']}% | {justified}")
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(run_business_demo())
