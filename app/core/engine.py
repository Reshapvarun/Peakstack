import numpy as np
from typing import Dict, Any, List
from app.core.tariff import StateTariff

class BillingEngine:
    """
    Industrial HT Billing Engine for Indian utilities.
    Hardened for dimensional correctness and realistic Indian HT tariff structures.
    """
    def __init__(self, tariff: StateTariff):
        self.tariff = tariff

    def calculate_bill(self, load_profile_kw: List[float], pf: float = 0.95) -> Dict[str, Any]:
        """
        Calculates the monthly bill with dimensional correctness.
        energy_kwh = power_kw * 0.25 (for 15-min intervals)
        """
        energy_charge = 0.0
        peak_demand_kw = max(load_profile_kw)
        
        # Indian HT billing uses kVA (Phase 1)
        peak_demand_kva = peak_demand_kw / pf
        
        # 1. Energy Charges (15-min intervals)
        for i, load_kw in enumerate(load_profile_kw):
            hour = (i // 4) % 24
            # Dimensional Correctness: 15-min interval to kWh
            energy_kwh = load_kw * 0.25 
            rate = self.tariff.get_rate(hour)
            energy_charge += energy_kwh * rate

        # 2. Daily Simulation Scaling (Phase 1)
        # Scale 1-day energy cost to 30 days
        monthly_energy_charge = energy_charge * 30
        
        # 3. Demand Charges (Phase 1)
        # Based on peak kVA of the month
        monthly_demand_charge = peak_demand_kva * self.tariff.demand_charge_inr_per_kva
        
        # 4. Fixed Charges
        fixed_charge = self.tariff.fixed_charge_inr_per_month
        
        # 5. Taxes
        subtotal = monthly_energy_charge + monthly_demand_charge + fixed_charge
        tax = subtotal * (self.tariff.tax_percent / 100.0)
        total_bill = subtotal + tax

        # Assertions for sanity (Phase 1)
        assert total_bill >= 0, "Total bill cannot be negative"
        assert peak_demand_kva >= 0, "Peak demand cannot be negative"

        return {
            "energy_charge": round(monthly_energy_charge, 2),
            "demand_charge": round(monthly_demand_charge, 2),
            "fixed_charge": round(fixed_charge, 2),
            "tax": round(tax, 2),
            "total_bill": round(total_bill, 2),
            "peak_demand_kva": round(peak_demand_kva, 2)
        }

if __name__ == "__main__":
    # Internal Test
    from app.core.tariff import DEFAULT_TARIFF
    engine = BillingEngine(DEFAULT_TARIFF)
    flat_load = [200.0] * 96 # 200kW constant
    bill = engine.calculate_bill(flat_load)
    print(f"Test Bill: INR {bill['total_bill']:,.2f} | Peak: {bill['peak_demand_kva']:.1f} kVA")
