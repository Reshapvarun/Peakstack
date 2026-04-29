from dataclasses import dataclass
from typing import Dict

@dataclass
class FinanceConfig:
    capex_per_kwh: float = 15000.0  # ₹15,000 per kWh
    om_cost_annual_pct: float = 0.02 # 2% of CAPEX per year
    discount_rate: float = 0.10     # 10% for IRR/NPV

    def update_capex(self, new_value: float):
        self.capex_per_kwh = new_value

class FinancialEngine:
    def __init__(self, config: FinanceConfig):
        self.config = config

    def calculate_roi(self, daily_savings: float, battery_capacity_kwh: float):
        # 1. CAPEX Calculation
        total_capex = battery_capacity_kwh * self.config.capex_per_kwh
        
        # 2. Annual Savings
        annual_energy_savings = daily_savings * 365
        annual_om_cost = total_capex * self.config.om_cost_annual_pct
        net_annual_savings = annual_energy_savings - annual_om_cost
        
        # 3. Payback Period
        payback_years = total_capex / net_annual_savings if net_annual_savings > 0 else float('inf')
        
        # 4. Simple IRR (Approximate)
        # For a simple annuity: IRR is the rate where NPV = 0
        # We'll provide a simplified ROI percentage for the MVP
        roi_pct = (net_annual_savings / total_capex) * 100
        
        return {
            "total_capex": total_capex,
            "annual_savings": net_annual_savings,
            "payback_period_years": payback_years,
            "annual_roi_pct": roi_pct,
            "net_present_value_10yr": self._calculate_npv(net_annual_savings, total_capex, 10)
        }

    def _calculate_npv(self, annual_cashflow, initial_investment, years=10):
        npv = -initial_investment
        for t in range(1, years + 1):
            npv += annual_cashflow / ((1 + self.config.discount_rate) ** t)
        return npv
