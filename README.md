# Peakstack — Industrial EMS Platform

Rule-based Energy Management System for Indian HT industrial consumers.
Optimizes BESS dispatch to reduce peak demand charges, arbitrage ToD 
tariffs, and minimize DG dependency.

## What It Does
- Simulates battery charge/discharge against real Indian ToD tariffs
  (TANGEDCO HT-1, MSEDCL HT-2, BESCOM HT)
- Calculates demand charge savings for HT consumers using kVA-based billing
- Enforces operational constraints: 20–90% SOC window, 1 cycle/day limit,
  morning + evening peak discharge, solar-first priority
- Investor-grade financial model: 10-yr NPV, IRR, degradation, O&M costs
- Multi-site fleet analysis with 12% IRR hurdle rate screening

## Quickstart
pip install -r requirements.txt
python validate_logic.py        # single-site audit (energy conservation check)
python run_business_demo.py     # multi-site enterprise fleet analysis

## API
uvicorn app.api.main:app --reload
# POST /api/v1/analyze  →  savings, payback, NPV, recommendation
# GET  /api/v1/states   →  supported Indian states
# GET  /health          →  service status

## Tech Stack
Python · FastAPI · React · NumPy · PuLP · SHAP

## Status
MVP complete. Rule-based dispatch engine operational across TN, MH, KA.
ML forecasting layer (XGBoost load prediction) in development.