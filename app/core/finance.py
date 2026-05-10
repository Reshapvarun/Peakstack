"""
Peakstack EMS — finance.py
Indigenously developed by Peakstack Technologies
India-specific BESS optimization for HT industrial consumers
DPIIT Startup India | VGF EMS Domestic Content Compliant
github.com/Reshapvarun/Peakstack
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class FinanceConfig:
    capex_per_kwh: float = 18000.0   # ₹18,000 per kWh (Installed)
    om_cost_annual_pct: float = 0.015 # 1.5% of CAPEX per year (Maintenance)
    discount_rate: float = 0.10      # 10% for NPV
    elec_inflation_pct: float = 0.05 # 5% annual increase in electricity cost
    degradation_annual_pct: float = 0.02 # 2% annual capacity loss
    inverter_replacement_pct: float = 0.10 # 10% of CAPEX for inverter
    project_life_years: int = 10

class FinancialEngine:
    """
    Hardened Financial Engine for Investor-Grade BESS Feasibility.
    Includes degradation, inflation, O&M, and NPV/IRR calculations.
    """
    def __init__(self, config: FinanceConfig = None):
        self.config = config if config else FinanceConfig()

    def run_analysis(self, monthly_savings: float, battery_capacity_kwh: float) -> Dict[str, Any]:
        """
        Runs a 10-year financial analysis.
        """
        total_capex = battery_capacity_kwh * self.config.capex_per_kwh
        annual_savings_base = monthly_savings * 12
        
        cashflows = [-total_capex]
        cumulative_cashflow = [-total_capex]
        
        annual_maintenance_base = total_capex * self.config.om_cost_annual_pct
        
        for year in range(1, self.config.project_life_years + 1):
            # 1. Savings with Inflation and Degradation
            # Savings scale with electricity price inflation
            inflation_factor = (1 + self.config.elec_inflation_pct) ** (year - 1)
            # Savings decrease as battery capacity degrades (2% per year)
            degradation_factor = (1 - self.config.degradation_annual_pct) ** (year - 1)
            
            yearly_savings = annual_savings_base * inflation_factor * degradation_factor
            
            # 2. Costs (Maintenance)
            yearly_maintenance = annual_maintenance_base * ((1 + 0.03) ** (year - 1)) # 3% maintenance inflation
            
            # 3. Special Reserves
            inverter_reserve = 0
            if year == 7:
                inverter_reserve = total_capex * self.config.inverter_replacement_pct
            
            net_cashflow = yearly_savings - yearly_maintenance - inverter_reserve
            cashflows.append(net_cashflow)
            cumulative_cashflow.append(cumulative_cashflow[-1] + net_cashflow)

        # Metrics
        npv = self._calculate_npv(cashflows)
        irr = self._calculate_irr(cashflows)
        payback = self._calculate_payback(cumulative_cashflow)
        
        return {
            "estimated_capex": round(total_capex, 0),
            "annual_savings_year1": round(cashflows[1], 0),
            "simple_payback_years": round(payback, 2),
            "npv_10yr": round(npv, 0),
            "irr_pct": round(irr * 100, 2),
            "total_10yr_savings": round(sum(cashflows[1:]), 0),
            "cashflows": [round(c, 0) for c in cashflows],
            "cumulative_cashflow": [round(c, 0) for c in cumulative_cashflow]
        }

    def calculate_roi(self, daily_savings: float, battery_capacity_kwh: float) -> Dict[str, Any]:
        """
        Special wrapper for the FastAPI wiring that takes daily savings.
        """
        results = self.run_analysis(daily_savings * 30, battery_capacity_kwh)
        return {
            "payback_period_years": results["simple_payback_years"],
            "annual_roi_pct": results["irr_pct"], # Using IRR as annual ROI
            "net_present_value_10yr": results["npv_10yr"],
            "irr_pct": results["irr_pct"]
        }

    def _calculate_npv(self, cashflows: List[float]) -> float:
        return sum(cf / (1 + self.config.discount_rate)**t for t, cf in enumerate(cashflows))

    def _calculate_irr(self, cashflows: List[float]) -> float:
        try:
            return np.irr(cashflows)
        except:
            # Fallback for newer numpy or failed convergence
            try:
                import numpy_financial as npf
                return npf.irr(cashflows)
            except:
                return 0.0 # Failed to converge

    def _calculate_payback(self, cumulative_cashflow: List[float]) -> float:
        for i in range(1, len(cumulative_cashflow)):
            if cumulative_cashflow[i] >= 0:
                # Linear interpolation for more accuracy
                prev = cumulative_cashflow[i-1]
                curr = cumulative_cashflow[i]
                fraction = abs(prev) / (curr - prev)
                return i - 1 + fraction
        return float('inf')
