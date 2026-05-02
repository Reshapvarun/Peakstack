import requests, json

payload = {
    "state": "tamil_nadu",
    "industry": "manufacturing",
    "battery_kwh": 600,
    "battery_power_kw": 200,
    "solar_kw": 400,
    "annual_kwh": 1200000,
    "tariff_energy": 8.0,
    "demand_charge": 300.0,
    "peak_tariff_difference": 3.0,
    "battery_cost_per_kwh": 18000.0,
    "solar_cost_per_kwh": 3.0,
    "utilization_factor": 0.8
}

r = requests.post("http://localhost:8000/api/v1/analyze", json=payload, timeout=30)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    d = r.json()
    kpis = d.get("kpis", {})
    realism = d.get("realism", {})
    print("=== BESS Analysis Results ===")
    print(f"Monthly Savings : Rs {kpis.get('monthly_savings_inr', 0):,.0f}")
    print(f"Annual  Savings : Rs {kpis.get('annual_savings_inr', 0):,.0f}")
    print(f"Payback Period  : {kpis.get('payback_years', 0):.1f} years")
    print(f"ROI             : {kpis.get('roi_percent', 0):.1f}%")
    print(f"Peak Reduction  : {kpis.get('peak_demand_reduction_kw', 0):.1f} kW")
    print(f"Recommendation  : {d.get('recommendation', 'N/A')}")
    print(f"Confidence      : {realism.get('confidence_score', 0)*100:.0f}%")
    print(f"Risk Flags      : {realism.get('risk_factors', [])}")
    print("\nFull keys available:", list(d.keys()))
else:
    print("ERROR:", r.text[:800])
