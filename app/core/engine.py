import numpy as np
from typing import Dict, Any, List

class BillingEngine:
    """
    Industrial HT Billing Engine for Indian utilities.
    Calculates charges based on 96-point load profiles and state-specific tariffs.
    """
    def __init__(self, tariff: Dict[str, Any]):
        self.tariff = tariff

    def calculate_bill(self, load_profile_kw: List[float], with_bess: bool = False) -> Dict[str, Any]:
        """
        Calculates the monthly bill (simulated by multiplying 1-day costs by 30).
        """
        energy_charge = 0.0
        peak_demand_kw = max(load_profile_kw)
        
        # Indian HT billing typically uses kVA. 
        # Assuming Power Factor (PF) of 0.95 if not provided.
        pf = 0.95
        peak_demand_kva = peak_demand_kw / pf
        
        for i, load in enumerate(load_profile_kw):
            hour = (i // 4) % 24
            energy_kwh = load * 0.25
            
            # Determine rate based on ToD
            rate = self.tariff['energy_charge_normal_inr_per_kwh']
            
            # Check if peak
            is_peak = False
            for start, end in self.tariff['peak_hours']:
                if start <= end:
                    if start <= hour < end:
                        is_peak = True
                        break
                else: # Overnight
                    if hour >= start or hour < end:
                        is_peak = True
                        break
            
            if is_peak:
                rate = self.tariff['energy_charge_peak_inr_per_kwh']
            else:
                # Check if off-peak
                is_offpeak = False
                for start, end in self.tariff['offpeak_hours']:
                    if start <= end:
                        if start <= hour < end:
                            is_offpeak = True
                            break
                    else: # Overnight
                        if hour >= start or hour < end:
                            is_offpeak = True
                            break
                if is_offpeak:
                    rate = self.tariff['energy_charge_offpeak_inr_per_kwh']
            
            energy_charge += energy_kwh * rate

        # Monthly Scaling (Simplified for MVP: 1 day * 30)
        monthly_energy_charge = energy_charge * 30
        
        # Demand Charge: actual_peak_kva * rate
        # (Assuming sanctioned demand is higher than actual peak for simplicity, 
        # or that we pay for actual peak as per many HT tariffs)
        monthly_demand_charge = peak_demand_kva * self.tariff['demand_charge_inr_per_kva']
        
        fixed_charge = self.tariff.get('fixed_charge_inr_per_month', 0)
        
        # Apply Tax
        subtotal = monthly_energy_charge + monthly_demand_charge + fixed_charge
        tax = subtotal * (self.tariff.get('tax_percent', 0) / 100.0)
        total_bill = subtotal + tax

        return {
            "energy_charge": round(monthly_energy_charge, 2),
            "demand_charge": round(monthly_demand_charge, 2),
            "fixed_charge": round(fixed_charge, 2),
            "total_bill": round(total_bill, 2),
            "peak_demand_kva": round(peak_demand_kva, 2)
        }

if __name__ == "__main__":
    # Test with Tamil Nadu Tariff
    tn_tariff = {
        "energy_charge_peak_inr_per_kwh": 9.00,
        "energy_charge_offpeak_inr_per_kwh": 7.10,
        "energy_charge_normal_inr_per_kwh": 7.50,
        "demand_charge_inr_per_kva": 562.0,
        "peak_hours": [[6, 9], [18, 21]],
        "offpeak_hours": [[22, 6]],
        "tax_percent": 5.0
    }
    
    # Generate 500 kWh/day industrial load profile
    # 500 kWh / 24 hrs = 20.83 kW avg.
    # Let's make it a flat 20.83 kW for testing.
    flat_load = [20.83] * 96
    
    engine = BillingEngine(tn_tariff)
    bill = engine.calculate_bill(flat_load)
    
    print("--- BILLING TEST (500 kWh/day flat load) ---")
    print(f"Monthly Energy Charge: INR {bill['energy_charge']:,.2f}")
    print(f"Monthly Demand Charge: INR {bill['demand_charge']:,.2f}")
    print(f"Total Monthly Bill:    INR {bill['total_bill']:,.2f}")
    print(f"Peak Demand:           {bill['peak_demand_kva']:.2f} kVA")
