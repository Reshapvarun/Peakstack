import logging
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np

from app.core.dispatch_engine import RuleBasedDispatchEngine
from app.core.engine import BillingEngine
from app.core.tariff import TariffManager, StateTariff
from app.core.finance import FinancialEngine, FinanceConfig

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Investor-Ready EMS Analysis Pipeline.
    Hardened for operational realism and multi-site aggregation.
    """
    def __init__(self, config_path: str = "config/state_tariffs.json"):
        self.tariff_manager = TariffManager(config_path)
        self.finance_engine = FinancialEngine()

    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the full analysis pipeline for a single site.
        """
        state_key = request.get('state', 'tamil_nadu').lower().replace(' ', '_')
        tariff = self.tariff_manager.get_tariff(state_key)
        if not tariff:
            logger.warning(f"Tariff for {state_key} not found, using default.")
            from app.core.tariff import DEFAULT_TARIFF
            tariff = DEFAULT_TARIFF

        # 1. Data Ingestion (Synthetic Industrial Profile)
        annual_kwh = request.get('annual_kwh', 600000)
        solar_kw = request.get('solar_kw', 0)
        
        load_profile = self._generate_synthetic_load(annual_kwh)
        solar_profile = self._generate_solar_profile(solar_kw)

        # 2. Hardened Optimization Simulation
        battery_kwh = request.get('battery_kwh', 500)
        battery_power_kw = request.get('battery_power_kw', 125)
        
        from app.core.optimizer import EnergyOptimizer
        from app.core.battery import BatteryConfig
        
        batt = BatteryConfig(
            capacity_kwh=battery_kwh,
            max_power_kw=battery_power_kw
        )
        
        optimizer = EnergyOptimizer(load_profile, solar_profile, batt, tariff)
        result = optimizer.solve()
        
        if not result:
            raise Exception(f"Optimization failed for site {request.get('site_name')}")

        # 3. Savings Analysis
        daily_savings = result['baseline_cost'] - result['optimized_cost']
        monthly_savings = daily_savings * 30
        
        # 4. Hardened Financial Analysis
        finance_results = self.finance_engine.run_analysis(monthly_savings, battery_kwh)
        
        # 5. Economic Justification Check
        is_justified = finance_results['irr_pct'] > 12.0 # 12% Hurdle Rate
        
        # 6. Investor-Grade Summary
        summary = self._generate_investor_summary(
            request.get('site_name', 'Industrial Site'),
            tariff,
            battery_kwh,
            battery_power_kw,
            result,
            finance_results,
            is_justified
        )

        return {
            "analysis_id": str(uuid.uuid4()),
            "site_name": request.get('site_name', 'Industrial Site'),
            "is_economically_justified": is_justified,
            "investor_summary": summary,
            "financials": finance_results,
            "dispatch": {
                "peak_reduction_kw": result['peak_demand_baseline'] - result['peak_demand'],
                "daily_throughput_kwh": result['battery_util'] * battery_kwh,
                "soc_profile": [] # Optional in this simplified summary
            },
            "bills": {
                "baseline": {"total_bill": result['baseline_cost'] * 30, "peak_demand_kva": result['peak_demand_baseline']},
                "with_bess": {"total_bill": result['optimized_cost'] * 30, "peak_demand_kva": result['peak_demand']}
            }
        }


    def _generate_investor_summary(self, site_name, tariff, kwh, kw, result, finance, justified) -> str:
        status = "RECOMMENDED" if justified else "NOT RECOMMENDED (Low ROI)"
        
        bill_old_total = result['baseline_cost'] * 30
        bill_new_total = result['optimized_cost'] * 30
        peak_old = result['peak_demand_baseline']
        peak_new = result['peak_demand']

        summary = f"""
================================================
PEAKSTACK EMS ANALYSIS
======================

SITE: {site_name}
STATE: {tariff.state_name} ({tariff.utility})
STATUS: {status}

## BASELINE
Peak Demand:              {peak_old:.1f} kW
Total Monthly Bill:       INR {bill_old_total:,.0f}

## WITH BATTERY EMS
Battery Size:             {kwh} kWh
Battery Power:            {kw} kW

Peak Demand:              {peak_new:.1f} kW
Monthly Bill:             INR {bill_new_total:,.0f}

## RESULTS
Monthly Savings:          INR {bill_old_total - bill_new_total:,.0f}
Annual Savings (Y1):      INR {finance['annual_savings_year1']:,.0f}
Peak Reduction:           {peak_old - peak_new:.1f} kW

## FINANCIALS
Estimated CAPEX:          INR {finance['estimated_capex']:,.0f}
Simple Payback:           {finance['simple_payback_years']:.1f} years
10Y NPV:                  INR {finance['npv_10yr']:,.0f}
IRR:                      {finance['irr_pct']:.1f}%

================================================
"""
        return summary


    def _generate_synthetic_load(self, annual_kwh: float) -> List[float]:
        # Industrial profile: base 200 kW, peak 600 kW
        base_load = 200.0
        peak_load = 600.0
        profile = []
        for i in range(96):
            hour = (i // 4) % 24
            if (9 <= hour < 12) or (18 <= hour < 21):
                profile.append(peak_load + np.random.uniform(-30, 30))
            else:
                profile.append(base_load + np.random.uniform(-10, 10))
        
        # Scale to match annual_kwh
        daily_kwh_target = annual_kwh / 365
        current_daily_kwh = sum(profile) * 0.25
        scale = daily_kwh_target / current_daily_kwh
        return [max(0, p * scale) for p in profile]

    def _generate_solar_profile(self, capacity_kw: float) -> List[float]:
        profile = []
        for i in range(96):
            hour = (i // 4) % 24
            if 7 <= hour < 17:
                val = capacity_kw * np.sin(np.pi * (hour - 7) / 10)
                profile.append(max(0, val + np.random.uniform(-2, 2)))
            else:
                profile.append(0.0)
        return profile
