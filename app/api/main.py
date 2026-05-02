from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import Dict, Any
import logging

# New production-ready imports
from app.api.routes import router as analysis_router
from app.schemas import AnalysisRequest as NewAnalysisRequest, AnalysisResponse as NewAnalysisResponse

# Legacy imports (keep for backward compatibility)
try:
    from app.api.schemas import AnalysisRequest, AnalysisResponse, UploadResponse
    from app.api.dependencies import get_forecaster
    from app.core.data_ingestion import DataIngestor
    from app.core.optimizer import EnergyOptimizer
    from app.core.policy_manager import PolicyManager
    from app.core.finance import FinancialEngine, FinanceConfig
    from app.core.battery import BatteryConfig
    from app.core.decision_engine import DecisionEngine
    from app.ml.xai import ExplainableAI
    from app.core.billing.engine import TariffEngine
    from app.core.billing.refresher import TariffRefreshManager
    from app.core.report_generator import ReportGenerator
except ImportError as e:
    print(f"Warning: Could not import legacy modules: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI-Powered BESS Investment Advisor API", version="2.0.0-production")

# Include new production routes
app.include_router(analysis_router)

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0-saas"}

@app.post("/upload-data", response_model=UploadResponse)
async def upload_data(file: UploadFile = File(...)):
    """Upload a CSV for 'Real Mode' analysis."""
    try:
        save_path = f"data/uploads/{file.filename}"
        os.makedirs("data/uploads", exist_ok=True)
        with open(save_path, "wb") as buffer:
            buffer.write(await file.read())
        return {"filename": file.filename, "status": "success", "message": f"File saved to {save_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tariffs/check-update/{state}")
def check_tariff_update(state: str):
    """Check if the official source for a state's tariff has changed."""
    refresher = TariffRefreshManager()
    return refresher.check_for_update(state)

@app.post("/tariffs/update-manual")
def update_tariff_manual(data: Dict[str, Any]):
    """Manually update tariff values after review."""
    refresher = TariffRefreshManager()
    # Expects: {"state": "Karnataka", "new_data": {...}}
    state = data.get("state")
    new_val = data.get("new_data")
    if not state or not new_val:
        raise HTTPException(status_code=400, detail="Missing state or new_data")
    return refresher.update_tariff_manual(state, new_val)

@app.get("/analyze/report/{report_id}")
def get_report(report_id: str):
    """Download the generated PDF report."""
    report_path = f"reports/{report_id}"
    if os.path.exists(report_path):
        from fastapi.responses import FileResponse
        return FileResponse(report_path, media_type='application/pdf', filename=report_id)
    raise HTTPException(status_code=404, detail="Report not found")

@app.post("/analyze", response_model=AnalysisResponse)
def analyze(
    req: AnalysisRequest,
    forecaster=Depends(get_forecaster)
):
    """Main optimization endpoint with integrated HT Billing."""
    try:
        # 1. Data Ingestion
        ingestor = DataIngestor()
        df = ingestor.get_data(req.mode, req.csv_file_path)

        # 2. Predictive Forecasting
        load_preds, solar_preds = forecaster.forecast(df)

        # 3. HT Billing Engine Setup
        billing_engine = TariffEngine(req.state)

        # We provide the optimizer with the ToD rates as a simple policy object
        # to maintain compatibility with the existing optimizer structure.
        class PolicyProxy:
            def __init__(self, engine):
                self.engine = engine
                self.state = engine.state
                self.peak_rate = engine.tariff.energy_rate.peak
                self.off_peak_rate = engine.tariff.energy_rate.off_peak
                self.demand_charge_per_kva = engine.tariff.demand_charge_per_kva
                self.net_metering_enabled = req.net_metering_enabled

        policy_proxy = PolicyProxy(billing_engine)

        # 4. Optimizer
        batt_cfg = BatteryConfig(capacity_kwh=req.battery_capacity_kwh, max_power_kw=req.battery_power_kw)
        optimizer = EnergyOptimizer(load_preds, solar_preds, np.zeros_like(load_preds), batt_cfg, policy=policy_proxy)
        res = optimizer.solve()

        # 5. Comprehensive HT Billing (Post-Optimization)
        results_df = pd.DataFrame({
            'timestamp': pd.date_range(start='2026-04-23', periods=len(load_preds), freq='15min'),
            'net_load_kw': res['grid_import'] + res['dg_power']
        })

        sanctioned_demand = res['peak_demand'] * 1.2
        bill = billing_engine.calculate_monthly_bill(results_df, sanctioned_demand, pf=0.92)

        # 6. ROI & Savings
        baseline_df = pd.DataFrame({
            'timestamp': pd.date_range(start='2026-04-23', periods=len(load_preds), freq='15min'),
            'net_load_kw': load_preds - solar_preds
        })
        baseline_bill = billing_engine.calculate_monthly_bill(baseline_df, sanctioned_demand, pf=0.92)

        daily_savings = (baseline_bill['total_bill'] - bill['total_bill']) / 30.0

        fin_engine = FinancialEngine(FinanceConfig())
        roi = fin_engine.calculate_roi(daily_savings, req.battery_capacity_kwh)

        # 7. Recommendation Engine
        dec_engine = DecisionEngine()
        recommendation = dec_engine.get_optimal_sizing(df, policy_proxy, batt_cfg)

        # Calculate Business Model Comparisons
        biz_models = dec_engine.calculate_business_models(daily_savings, recommendation['size'])

        # 8. XAI Explanations
        if not req.fast_mode:
            xai = ExplainableAI()
            xai_results_df = pd.DataFrame({
                'timestamp': pd.date_range(start='2026-04-23', periods=len(load_preds), freq='15min'),
                'load_kw': load_preds,
                'solar_kw': solar_preds,
                'bess_charge_kw': res['bess_charge'],
                'bess_discharge_kw': res['bess_discharge'],
                'dg_kw': res['dg_power'],
                'curtailment': res.get('curtailment_series', [0]*len(load_preds))
            })
            explanations = xai.explain_decision(xai_results_df, {"demand_charge_rate": billing_engine.tariff.demand_charge_per_kva, "mode": "BTM_STRICT"})
        else:
            explanations = []

        # 9. PDF Report Generation
        if not req.fast_mode:
            report_gen = ReportGenerator()
            report_filename = f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            # Compute baseline bill for the report
            baseline_df = pd.DataFrame({
                'timestamp': pd.date_range(start='2026-04-23', periods=len(load_preds), freq='15min'),
                'net_load_kw': load_preds - solar_preds
            })
            baseline_bill = billing_engine.calculate_monthly_bill(baseline_df, sanctioned_demand, pf=0.92)

            report_path = report_gen.generate_pdf({
                "summary": {
                    "daily_savings": daily_savings,
                    "savings_pct": (daily_savings / (baseline_bill['total_bill']/30.0) * 100) if baseline_bill['total_bill'] > 0 else 0,
                    "peak_reduction_pct": ((baseline_df['net_load_kw'].max() - res['peak_demand']) / baseline_df['net_load_kw'].max() * 100) if baseline_df['net_load_kw'].max() > 0 else 0,
                    "payback_years": roi['payback_period_years']
                },
                "recommendation": {
                    "decision": "INSTALL" if roi['payback_period_years'] <= 10 else "DO_NOT_INSTALL",
                    "optimal_size": recommendation['size'],
                    "tech": recommendation['tech'],
                    "confidence": recommendation['confidence'],
                    "reasoning": recommendation['reasoning'],
                    "emerging_tech_option": "Sodium-ion (Future scenario)" if req.include_emerging_tech else None
                },
                "bill_breakdown": bill,
                "baseline_bill": baseline_bill,
                "curtailment": res.get('curtailment', 0),
                "capex_per_kwh": fin_engine.config.capex_per_kwh,
                "policy_applied": billing_engine.tariff.__dict__,
                "report_meta": {
                    "site_id": "Industrial_Site_01",
                    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                    "policy_state": req.state
                }
            }, filename=report_filename)

            report_id = os.path.basename(report_path)
        else:
            report_id = None

        return {
            "summary": {
                "daily_savings": daily_savings,
                "savings_pct": (daily_savings / (baseline_bill['total_bill']/30.0) * 100) if baseline_bill['total_bill'] > 0 else 0,
                "peak_reduction_pct": ((baseline_df['net_load_kw'].max() - res['peak_demand']) / baseline_df['net_load_kw'].max() * 100) if baseline_df['net_load_kw'].max() > 0 else 0,
                "payback_years": roi['payback_period_years']
            },
            "results": {
                "load": load_preds.tolist(),
                "solar": solar_preds.tolist(),
                "grid_import": res['grid_import'].tolist(),
                "soc": res['soc'].tolist(),
                "total_cost": res['total_cost'],
                "peak_demand": res['peak_demand']
            },
            "recommendation": {
                "optimal_size": recommendation['size'],
                "confidence": recommendation['confidence'],
                "reasoning": recommendation['reasoning'],
                "strategic_actions": explanations
            },
            "bill_breakdown": {
                "energy_cost": bill['energy_cost'],
                "demand_cost": bill['demand_cost'],
                "fixed_cost": bill['fixed_cost'],
                "pf_impact": bill['pf_impact'],
                "tax": bill['tax'],
                "total_bill": bill['total_bill']
            },
            "business_models": biz_models,
            "report_meta": {
                "site_id": "Industrial_Site_01",
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "policy_state": req.state
            },
            "policy_applied": billing_engine.tariff.__dict__,
            "report_id": report_id
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
