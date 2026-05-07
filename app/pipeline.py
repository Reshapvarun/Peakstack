import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np

from app.core.dispatch_engine import RuleBasedDispatchEngine
from app.core.engine import BillingEngine
from app.schemas import AnalysisResponse

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    Orchestrates the 6-stage analysis pipeline.
    """
    def __init__(self, config_path: str = "config/state_tariffs.json"):
        self.config_path = config_path
        with open(self.config_path, 'r') as f:
            self.tariffs = json.load(f)

    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the pipeline and returns a valid AnalysisResponse structure.
        """
        state_key = request.get('state', 'tamil_nadu').lower().replace(' ', '_')
        if state_key not in self.tariffs:
            logger.warning(f"State {state_key} not found, falling back to tamil_nadu")
            state_key = 'tamil_nadu'
        
        tariff = self.tariffs[state_key]
        
        # 1. Data Ingestion (Synthetic for now as per requirements)
        annual_kwh = request.get('annual_kwh', 600000)
        load_profile = self._generate_synthetic_load(annual_kwh)
        solar_kw = request.get('solar_kw', 0)
        solar_profile = self._generate_solar_profile(solar_kw)
        
        # 2. Forecasting (Stub)
        # In this MVP, forecast = synthetic profile
        
        # 3. Optimization (Dispatch Engine)
        dispatch_engine = RuleBasedDispatchEngine(
            battery_kwh=request.get('battery_kwh', 500),
            battery_power_kw=request.get('battery_power_kw', 125)
        )
        dispatch_results = dispatch_engine.run_dispatch(
            load_profile=load_profile,
            solar_profile=solar_profile,
            peak_hours=tariff['peak_hours'],
            offpeak_hours=tariff['offpeak_hours']
        )
        
        # 4. Billing Engine
        billing_engine = BillingEngine(tariff)
        
        bill_without_bess = billing_engine.calculate_bill(dispatch_results['grid_import_without_bess'])
        bill_with_bess = billing_engine.calculate_bill(dispatch_results['grid_import_with_bess'])
        
        monthly_savings = bill_without_bess['total_bill'] - bill_with_bess['total_bill']
        annual_savings = monthly_savings * 12
        
        # 5. Financial Analysis (Payback)
        # Battery Cost estimate: ₹15,000 / kWh
        battery_cost = request.get('battery_kwh', 500) * 15000
        payback_years = battery_cost / annual_savings if annual_savings > 0 else 99
        
        # 6. Recommendation
        recommendation = "INSTALL" if payback_years < 6 else "INVESTIGATE"
        
        # Construct AnalysisResponse
        response = {
            "analysis_id": "anlyz-" + os.urandom(4).hex(),
            "summary": {
                "monthly_savings": round(monthly_savings, 2),
                "annual_savings": round(annual_savings, 2),
                "payback_years": round(payback_years, 2),
                "peak_reduction_kw": round(bill_without_bess['actual_peak'] * 0.95 - bill_with_bess['actual_peak'] * 0.95, 2)
            },
            "recommendation": {
                "decision": recommendation,
                "optimal_size": request.get('battery_kwh', 500),
                "confidence": "HIGH"
            },
            "charts": {
                "load_profile": load_profile,
                "bess_soc": dispatch_results['battery_soc'],
                "grid_with_bess": dispatch_results['grid_import_with_bess'],
                "grid_without_bess": dispatch_results['grid_import_without_bess']
            },
            "bill_breakdown": {
                "without_bess": bill_without_bess,
                "with_bess": bill_with_bess
            }
        }
        
        return response

    def _generate_synthetic_load(self, annual_kwh: float) -> List[float]:
        # Industrial profile: base 200 kW, peak 400 kW
        # For annual_kwh 600,000 -> daily 1643 kWh. 
        # If peak is 400 kW, that's a very high peak for 1643 kWh daily.
        # Let's scale a representative profile to match annual_kwh.
        
        base_load = 200.0
        peak_load = 400.0
        
        profile = []
        for i in range(96):
            hour = (i // 4) % 24
            # Peak hours: 09:00-12:00 and 18:00-21:00
            if (9 <= hour < 12) or (18 <= hour < 21):
                profile.append(peak_load + np.random.uniform(-20, 20))
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
            if 6 <= hour < 18:
                # Sine wave for solar
                val = capacity_kw * np.sin(np.pi * (hour - 6) / 12)
                profile.append(max(0, val + np.random.uniform(-0.1 * capacity_kw, 0.1 * capacity_kw)))
            else:
                profile.append(0.0)
        return profile
