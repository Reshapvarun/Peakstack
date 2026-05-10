# Peakstack — India-First Industrial BESS Optimization Platform

Indigenously developed, hardware-agnostic EMS software for Indian HT 
industrial consumers. Optimizes BESS dispatch against state-specific 
ToD tariffs to reduce demand charges and DG dependency.

## Validated Results (Maharashtra HT-2, 250 kWh BESS)
- **12.8% daily cost savings**
- **33% peak demand reduction**
- **21% IRR, 4-year payback** (Pune Automotive site)
- **Fleet savings: ₹55.7L/year** across 3 sites

See [VALIDATION_REPORT.md](./VALIDATION_REPORT.md) for full output.

## Why Peakstack is Different
- Only Indian EMS with hardcoded TANGEDCO / MSEDCL / BESCOM HT tariffs
- kVA-based demand charge math (not generic kWh arbitrage)
- Dual-peak ToD dispatch: morning (09:00-12:00) + evening (18:00-22:00)
- Hardware-agnostic: works with Amara Raja, Exide, Luminous, any BESS
- Qualifies as indigenously developed EMS under MoP VGF mandate (Dec 2025)

## Quickstart
  pip install -r requirements.txt
  python validate_logic.py          # single-site audit
  python run_business_demo.py       # fleet analysis

## API
  uvicorn app.api.main:app --reload
  POST /api/v1/analyze  → savings, payback, NPV, IRR, recommendation
  GET  /api/v1/states   → supported Indian states
  GET  /health          → service status

## Tech Stack
Python · FastAPI · NumPy · PuLP · SHAP (roadmap: XGBoost forecasting)

## Policy Alignment
Qualifies as domestic content under Ministry of Power VGF BESS scheme
(Dec 2025 directive mandating indigenously developed EMS software).
Eligible for DPIIT Deep Tech Startup recognition (G.S.R. 108(E), Feb 2026).

## Status
MVP complete. Rule-based dispatch operational across TN, MH, KA.
Seeking pilot customer: HT industrial site, 250-500 kWh BESS.