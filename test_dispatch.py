import sys
from app.core.dispatch import DispatchOptimizer

def run_test():
    load = [100.0] * 96
    solar = [0.0] * 96
    for t in range(40, 60):  # 10am to 3pm approx
        solar[t] = 150.0
        
    tariff = [8.0] * 96
    for t in range(40, 56): # 10am to 2pm peak
        tariff[t] = 11.0
    for t in range(72, 88): # 6pm to 10pm peak
        tariff[t] = 11.0
        
    opt = DispatchOptimizer(
        load_forecast=load,
        solar_forecast=solar,
        tariff_profile=tariff,
        battery_capacity_kwh=600.0,
        battery_power_kw=200.0,
        efficiency=0.9
    )
    
    res = opt.solve()
    if res:
        print("SUCCESS!")
        print(f"Total Savings: {res['total_savings']:.2f}")
        for s in res['schedule']:
            if s['action'] != 'IDLE':
                print(f"{s['time']} | {s['action']} | {s['power']:.1f}kW | SOC: {s['soc_percent']:.1f}%")
    else:
        print("FAILED to solve")

if __name__ == "__main__":
    run_test()
