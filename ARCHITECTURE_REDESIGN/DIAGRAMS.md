# PeakStack Architecture: Visual Overview

## 1. Layered Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                        │
│  POST /v1/analyses/analyze → AnalysisRequest → AnalysisResponse│
│  GET /v1/analyses/{id}                                          │
│  Schemas: Pydantic validation, error handling                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               APPLICATION LAYER (Orchestration)                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AnalysisPipeline (orchestrator)                         │   │
│  │  + error handling, caching, logging                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────┬─────────┬──────────┬─────────┬────────┬─────────┐  │
│  │ Stage 1 │ Stage 2 │ Stage 3  │Stage 4  │Stage 5 │ Stage 6 │  │
│  │  Data   │Forecast │Optimize  │Finance  │Decide  │Realism  │  │
│  │Ingestion│         │(MILP)    │Analysis │Engine  │Calibrat│  │
│  └─────────┴─────────┴──────────┴─────────┴────────┴─────────┘  │
│                                                                   │
│  Uses Cases:                                                     │
│  - AnalyzeInvestmentUseCase                                     │
│  - WhatIfAnalysisUseCase                                        │
│  - ScenarioComparisonUseCase                                    │
│                                                                   │
│  Services:                                                       │
│  - RealismCalibrator (XAI engine)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  DOMAIN LAYER (Business Logic)                  │
│                        (Framework-free)                         │
│                                                                   │
│  Models:                      Services (Interfaces):            │
│  - Battery                    - OptimizationService             │
│  - Tariff                     - BillingService                  │
│  - LoadProfile                - FinancialService                │
│  - FinancialMetrics           - ForecastingService              │
│                                                                   │
│  Policies:                    Repositories (Interfaces):        │
│  - StatePolicy (net metering) - LoadRepository                  │
│  - TariffProfiles             - TariffRepository                │
│  - ExportLimits               - ModelRepository                 │
│                                                                   │
│  Business Rules:                                                 │
│  - MILP constraints (min SOC, BTM compliance, etc)              │
│  - Demand charge calculations                                    │
│  - Payback/ROI thresholds                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                INFRASTRUCTURE LAYER (Adapters)                  │
│                                                                   │
│  ML:                  Optimization:      Persistence:           │
│  - XGBoostForecaster  - PuLPOptimizer   - CSVLoadRepository     │
│  - ModelLoader        - GreedyOptimizer - DBTariffRepository    │
│                                                                   │
│  Cache:               Logging:           Config:                │
│  - RedisCache         - PipelineLogger   - Settings.py          │
│  - MemoryCache                          - Constants.py          │
│                                                                   │
│  DI Container:                                                   │
│  - ServiceProvider (dependency-injector)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Request → Pipeline → Response Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. API Layer: Accept AnalysisRequest                                │
│    {state, annual_kwh, battery_size (optional), business_models}   │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Create PipelineContext (mutable container)                       │
│    - analysis_id, request, state, annual_kwh                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. STAGE 1: Data Ingestion                                          │
│    Input: AnalysisRequest (load_profile or annual_kwh)              │
│    Output: PipelineContext.load_profile_15min (35,040 points)      │
│    Output: PipelineContext.solar_generation_15min                   │
│    Output: PipelineContext.data_quality_score                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. STAGE 2: Forecasting                                             │
│    Input: PipelineContext.load_hourly, forecast_service             │
│    Output: PipelineContext.load_forecast_24h                        │
│    Output: PipelineContext.solar_forecast_24h                       │
│    Output: PipelineContext.forecast_confidence                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. STAGE 3: Optimization (MILP)                                     │
│    Input: forecast + battery config + tariff + policies             │
│    For each battery size (10-2000 kWh):                             │
│      - Solve MILP: min(energy_cost + demand_cost + degradation)     │
│      - Respect constraints: min SOC, BTM compliance, max power       │
│    Output: PipelineContext.optimization_result                      │
│    Output: PipelineContext.optimal_dispatch (hourly schedule)       │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 6. STAGE 4: Financial Analysis                                      │
│    Input: optimal_dispatch + battery_size + business_models         │
│    For each model (CAPEX, EaaS, Hybrid):                            │
│      - Calculate: annual_savings, payback_months, ROI%, NPV, IRR    │
│    Output: PipelineContext.kpis_by_model = {                        │
│      'capex': KPISchema(...),                                       │
│      'eaas': KPISchema(...),                                        │
│      'hybrid': KPISchema(...)                                       │
│    }                                                                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 7. STAGE 5: Decision Engine                                         │
│    Input: kpis_by_model, thresholds (payback < 120mo, ROI > 5%)    │
│    Logic: Pick best model by ROI                                    │
│           If passes thresholds → INSTALL                            │
│           Else → DO_NOT_INSTALL                                     │
│    Output: PipelineContext.recommendation = RecommendationSchema    │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 8. STAGE 6: Realism Calibration (XAI)                               │
│    Input: kpis + data_quality + forecast_confidence + state + risks │
│    For each business model:                                         │
│      - Apply state calibration factor (-15% to -22%)                │
│      - Apply data quality discount                                  │
│      - Identify risk factors (8 types)                              │
│      - Calculate confidence (0-1)                                   │
│      - Generate conservative buffer                                 │
│      - Generate human-readable insights                             │
│    Output: PipelineContext.realistic_kpis = {                       │
│      'capex': RealisticKPIsSchema(theoretical, realistic, gap,      │
│               confidence, risk_factors, buffer, ...),               │
│      ...                                                             │
│    }                                                                 │
│    Output: PipelineContext.insights = [InsightSchema(...), ...]    │
│    Output: PipelineContext.annual_chart, typical_day_chart         │
│    Output: PipelineContext.scenarios = [ScenarioResultSchema, ...] │
└──────────────────────────────┬──────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 9. API Layer: Convert PipelineContext → AnalysisResponse            │
│    Return 200 OK with JSON:                                         │
│    {                                                                 │
│      analysis_id: "...",                                            │
│      timestamp: "...",                                              │
│      optimization_result: {...},                                    │
│      recommendation: {...},                                         │
│      kpis_by_model: {...},                                          │
│      realistic_kpis: {...},    ← XAI REALISM CALIBRATION           │
│      annual_load_chart: {...},                                      │
│      monthly_savings_chart: {...},                                  │
│      insights: [...],          ← EXPLAINABLE AI                     │
│      scenarios: [...],                                              │
│      data_quality_score: 0.92,                                      │
│      dashboard_url: "..."                                           │
│    }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 10. Frontend: React Dashboard Powers Up with Data                   │
│     <KPICard> shows: theoretical vs realistic savings               │
│     <ConfidenceScore> shows: 0.85 (high confidence)                 │
│     <RealisismGapChart> shows: 15% gap (reasonable)                 │
│     <RiskFactorsTag> shows: ['tariff_volatility', ...]             │
│     <InsightCard> shows: "Peak shaving saves ₹52K/yr"              │
│     <RecommendationCard> shows: "INSTALL, 250 kWh, CAPEX model"    │
│     <ScenarioChart> shows: with/without BESS comparison             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Realism Calibrator Algorithm (Stage 6 Deep Dive)

```
┌──────────────────────────────────────────────────────────────────────┐
│ INPUT: Optimizer Output (Theoretical)                                │
│ ┌─ Annual Savings (CAPEX): ₹100,000 / year                          │
│ ├─ Payback: 7.5 years                                               │
│ └─ ROI: 12.5% annually                                              │
│                                                                       │
│ INPUT: Environmental Factors                                         │
│ ├─ state: Maharashtra                                               │
│ ├─ data_quality: 0.85 (load profile 12 months, complete)           │
│ ├─ forecast_mape: 0.12 (forecast accuracy)                         │
│ ├─ load_history_days: 365                                           │
│ ├─ load_volatility: 0.35 (coefficient of variation)                │
│ ├─ solar_data_completeness: 0.90                                    │
│ └─ tariff_changes_2y: 1 (one change in past 2 years)               │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │ STEP 1: STATE CALIBRATION               │
        │ Base factor (MH): 0.85 (historical avg) │
        │ Realistic v1 = 100,000 × 0.85           │
        │             = ₹85,000                   │
        └────────────────┬────────────────────────┘
                         ↓
        ┌─────────────────────────────────────────┐
        │ STEP 2: DATA QUALITY ADJUSTMENT         │
        │ score=0.85 → factor=0.855               │
        │ Realistic v2 = 85,000 × 0.855           │
        │             = ₹72,675                   │
        └────────────────┬────────────────────────┘
                         ↓
        ┌─────────────────────────────────────────┐
        │ STEP 3: RISK IDENTIFICATION             │
        │ Check each of 8 risk factors:           │
        │ ✓ HIGH_FORECAST_ERROR (MAPE > 0.15)?   │
        │   NO (0.12 < 0.15)                      │
        │ ✓ SHORT_HISTORY (< 180 days)?          │
        │   NO (365 days)                         │
        │ ✓ VOLATILE_LOAD (CoV > 0.5)?           │
        │   NO (0.35 < 0.5)                       │
        │ ✓ LOW_SOLAR_DATA (< 80% complete)?     │
        │   NO (90% > 80%)                        │
        │ ✓ TARIFF_CHANGES (≥ 2 in 2y)?          │
        │   NO (1 < 2)                            │
        │ Result: No major risks identified       │
        └────────────────┬────────────────────────┘
                         ↓
        ┌─────────────────────────────────────────┐
        │ STEP 4: RISK FACTOR ADJUSTMENTS         │
        │ risk_factor = 1.0 (no risks)            │
        │ Realistic final = 72,675 × 1.0          │
        │               = ₹72,675                 │
        └────────────────┬────────────────────────┘
                         ↓
        ┌─────────────────────────────────────────┐
        │ STEP 5: CONFIDENCE SCORING              │
        │ Components:                             │
        │ • data_quality = 0.85 (weight 35%)     │
        │ • forecast = 0.88 (MAPE 12%, weight 35%)│
        │ • state_maturity = 0.90 (MH mature, wt20%)│
        │ • historical = 1.00 (365 days, wt 10%) │
        │                                         │
        │ Score = 0.85×0.35 + 0.88×0.35 +        │
        │         0.90×0.20 + 1.00×0.10           │
        │       = 0.2975 + 0.308 + 0.18 + 0.10   │
        │       = 0.8855 ≈ 0.88                   │
        └────────────────┬────────────────────────┘
                         ↓
        ┌─────────────────────────────────────────┐
        │ STEP 6: BUFFER CALCULATION              │
        │ Gap = (100K - 72.7K) / 100K = 27.3%    │
        │ Buffer% = (1-0.88)×30 + 27.3%×20       │
        │         = 3.6% + 5.46%                  │
        │         = 9.06% ≈ 10%                   │
        │ Conservative = 72,675 × (1 - 0.10)     │
        │             = ₹65,408                   │
        └────────────────┬────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────────────┐
│ OUTPUT: Realism Calibration                                          │
│ ┌─ Theoretical Savings: ₹100,000                                    │
│ ├─ Realistic Savings: ₹72,675                                       │
│ ├─ Realism Gap: 27.3%                                               │
│ ├─ Confidence Score: 0.88 (HIGH)                                    │
│ ├─ Risk Factors: (none)                                             │
│ ├─ Recommended Buffer: 10%                                          │
│ ├─ Conservative Estimate: ₹65,408                                   │
│ ├─ Should Show Warning: NO (gap < 30%)                              │
│ └─ Confidence Reason: "Good quality load data, proven tariff       │
│    structure in MH, similar customer base validated."                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Realism Gap Example: With Risks

```
┌──────────────────────────────────────────────────────────────────────┐
│ SCENARIO: Low data quality + volatile load + tariff uncertainty     │
│                                                                       │
│ Theoretical Savings: ₹100,000                                        │
│   ↓ State calibration (-15%): ₹85,000                               │
│   ↓ Data quality discount (low): ₹72,000                            │
│   ↓ Risk: SHORT_HISTORY (-7%): ₹67,000                             │
│   ↓ Risk: VOLATILE_LOAD (-4%): ₹64,000                             │
│   ↓ Risk: TARIFF_CHANGES (-6%): ₹60,000                            │
│   = Realistic Savings: ₹60,000                                       │
│                                                                       │
│ Confidence Score: 0.65 (MODERATE)                                    │
│ Risk Factors: [SHORT_HISTORY, VOLATILE_LOAD, TARIFF_CHANGES]       │
│ Realism Gap: 40% (should show warning!)                             │
│ Recommended Buffer: 20%                                              │
│ Conservative Estimate: ₹48,000                                       │
│                                                                       │
│ UI Representation:                                                    │
│ ┌────────────────────────────────────────────────────────┐          │
│ │ Realistic Savings (CAPEX Model)                        │          │
│ │ Theoretical: ₹100,000  →  Realistic: ₹60,000          │          │
│ │ Realism Gap: 40% ⚠️  [HIGH - see risks below]          │          │
│ │ Confidence: 0.65 (Moderate)                            │          │
│ │                                                         │          │
│ │ Risks:                                                  │          │
│ │ • Short historical data (-7%)                          │          │
│ │ • Volatile load patterns (-4%)                         │          │
│ │ • Tariff changes expected (-6%)                        │          │
│ │                                                         │          │
│ │ Conservative Estimate: ₹48,000                         │          │
│ │ (Savings × (1 - 20% buffer))                           │          │
│ │                                                         │          │
│ │ ⚠️ Warning: Large realism gap (40%). This estimate    │          │
│ │ is conservative. Monitor tariff changes closely.       │          │
│ └────────────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Module Dependency Graph (No Cycles)

```
                 ┌─────────────────┐
                 │   API Layer     │
                 │  (FastAPI app)  │
                 └────────┬────────┘
                          │
                ┌─────────▼─────────┐
                │Application Layer  │
                │  (Use Cases &     │
                │  Pipeline)        │
                └────────┬──────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼─────┐   ┌─────▼──────┐  ┌──────▼─────┐
   │Domain    │   │Infrastructure│ │Config      │
   │(Models & │   │(Adapters)    │ │(Constants &│
   │Services) │   │              │ │Settings)   │
   └──────────┘   └──────────────┘ └────────────┘

Rules:
✗ API → Domain (API depends on Domain) ✓
✓ Application → Domain ✓
✓ Application → Infrastructure ✓
✓ Infrastructure → Domain (implements interfaces) ✓
✗ Domain → Application ✗ (no upward deps)
✗ Domain → Infrastructure ✗ (no impl deps)
```

---

## 6. Test Pyramid

```
                        ▲
                       ╱│╲
                      ╱ │ ╲     API Contract Tests
                     ╱  │  ╲    (Schema validation,
                    ╱   │   ╲   endpoint response)
                   ╱────┼────╲  5-10 tests
                  ╱     │     ╲
                 ╱      │      ╲
                ╱───────┼───────╲ Integration Tests
               ╱        │        ╲ (Pipeline end-to-end,
              ╱         │         ╲ multi-stage flows)
             ╱──────────┼──────────╲ 20-30 tests
            ╱           │           ╲
           ╱────────────┼────────────╲
          ╱             │             ╲ Unit Tests
         ╱              │              ╲ (Each service, stage,
        ╱───────────────┼───────────────╲ model in isolation)
       ╱                │                ╲ 60-100 tests
      ╱                 │                 ╲
     ╱──────────────────┼──────────────────╲
    ╱                   │                   ╲
```

---

## 7. Deployment Timeline (Week 7-8)

```
Day 1-2: Deploy old + new side-by-side
         ┌─────────────────────┐
         │    Load Balancer    │
         └────────┬────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
    ┌───▼────────┐   ┌──────▼────┐
    │  OLD API   │   │ NEW API    │
    │(production)│   │(testing)   │
    └────────────┘   └────────────┘

Day 3-4: Canary (10% traffic to new)
        ┌─────────────────────┐
        │    Load Balancer    │
        │  10% → new          │
        │  90% → old          │
        └────────┬────────────┘
                 │
        ┌────────┴──────────┐
        │  (90%)            │  (10%)
        │                   │
    ┌───▼────────┐   ┌──────▼────┐
    │  OLD API   │   │ NEW API    │
    │(production)│   │(monitoring)│
    └────────────┘   └────────────┘

Day 5: Full migration (100% to new)
        ┌─────────────────────┐
        │    Load Balancer    │
        │ 100% → new          │
        └────────┬────────────┘
                 │
                 │
            ┌────▼────┐
            │ NEW API  │
            │(live)    │
            └──────────┘

Day 6-7: Archive old code
         ┌──────────────────────┐
         │ git tag v1-old-api   │
         │ rm -r app/core/*     │
         │ Cleanup done         │
         └──────────────────────┘
```

---

## References

All diagrams describe concepts in:
- `00_FOLDER_STRUCTURE.md` — architecture layers
- `01_API_DESIGN_SCHEMAS.md` — API request/response flow
- `02_PIPELINE_ORCHESTRATOR.md` — 6 stages detail
- `03_REALISM_CALIBRATOR.md` — confidence algorithm
- `04_REFACTORING_GUIDE.md` — implementation timeline
