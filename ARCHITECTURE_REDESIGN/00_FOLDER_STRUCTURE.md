# PeakStack Backend Architecture - Folder Structure

## Clean Layered Architecture (DDD-inspired)

```
peakstack/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analysis.py          # POST /analyze, /what-if, /scenario
│   │   │   │   ├── tariffs.py           # GET /tariffs/{state}
│   │   │   │   └── uploads.py           # POST /upload
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analysis.py          # AnalysisRequest, AnalysisResponse, RealisticKPIs
│   │   │   │   ├── tariff.py            # TariffSchema
│   │   │   │   └── common.py            # BatteryConfig, SolarConfig, etc
│   │   │   └── dependencies.py          # FastAPI dependencies (db, cache, etc)
│   │   ├── middleware/
│   │   │   └── error_handlers.py        # Custom exception handlers
│   │   └── main.py                      # FastAPI app initialization
│   │
│   ├── domain/                          # Core business logic (IMMUTABLE, NO FRAMEWORK DEPS)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── battery.py               # Battery entity (value objects)
│   │   │   ├── tariff.py                # Tariff & rate structures
│   │   │   ├── load_profile.py          # Load profile model
│   │   │   └── financial.py             # Financial models (NPV, IRR, etc)
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── optimization_service.py  # Interface + logic for MILP/greedy
│   │   │   ├── billing_service.py       # HT tariff billing logic
│   │   │   ├── financial_service.py     # Financial calculations
│   │   │   └── forecasting_service.py   # Load/solar forecasting
│   │   │
│   │   ├── policies/
│   │   │   ├── __init__.py
│   │   │   ├── state_policy.py          # Abstract policy interface
│   │   │   ├── policies_registry.py     # State-specific implementations
│   │   │   └── tariff_profiles.py       # Hardcoded tariff by state
│   │   │
│   │   └── repositories/                # Ports (interfaces, NO implementation)
│   │       ├── __init__.py
│   │       ├── load_repository.py       # Interface for load data
│   │       ├── tariff_repository.py     # Interface for tariff data
│   │       └── model_repository.py      # Interface for ML models
│   │
│   ├── application/                     # Use-cases / Orchestration
│   │   ├── __init__.py
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── analysis_pipeline.py     # Main orchestrator (steps 1-6)
│   │   │   ├── stages/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── data_stage.py        # Data ingestion & validation
│   │   │   │   ├── forecast_stage.py    # Load/solar forecasting
│   │   │   │   ├── optimization_stage.py # Battery optimization
│   │   │   │   ├── financial_stage.py   # ROI/NPV/payback
│   │   │   │   ├── decision_stage.py    # Recommendation logic
│   │   │   │   └── realism_stage.py     # Realism gap calibration
│   │   │   │
│   │   │   └── dto/                     # Data Transfer Objects
│   │   │       ├── __init__.py
│   │   │       ├── pipeline_dto.py      # Objects flowing through stages
│   │   │       └── kpi_dto.py           # KPI calculations
│   │   │
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── analyze_investment.py    # Use-case: Analyze BESS investment
│   │   │   ├── run_what_if.py           # Use-case: What-if scenarios
│   │   │   └── run_scenario.py          # Use-case: Scenario comparison
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       └── realism_calibrator.py    # XAI + realism gap engine
│   │
│   ├── infrastructure/                  # Adapters & implementations
│   │   ├── __init__.py
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── xgboost_forecaster.py    # XGBoost implementation
│   │   │   └── model_loader.py          # Model persistence
│   │   │
│   │   ├── optimization/
│   │   │   ├── __init__.py
│   │   │   ├── pulp_optimizer.py        # PuLP MILP solver adapter
│   │   │   └── greedy_optimizer.py      # Fallback greedy solver
│   │   │
│   │   ├── persistence/
│   │   │   ├── __init__.py
│   │   │   ├── load_repository_impl.py  # CSV/DB adapter
│   │   │   ├── tariff_repository_impl.py
│   │   │   └── model_repository_impl.py
│   │   │
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── redis_cache.py           # In-memory/Redis caching
│   │   │
│   │   └── logging/
│   │       ├── __init__.py
│   │       └── pipeline_logger.py       # Structured logging
│   │
│   └── config/
│       ├── __init__.py
│       ├── settings.py                  # Pydantic BaseSettings
│       ├── constants.py                 # Hardcoded constants (costs, thresholds)
│       └── logging_config.py            # Logging setup
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   │   └── pipeline_test.py
│   └── fixtures/
│       └── sample_data.py
│
├── scripts/
│   ├── generate_test_data.py
│   ├── run_analysis_demo.py
│   └── train_forecaster.py
│
├── docs/
│   ├── API.md                           # API documentation
│   ├── PIPELINE.md                      # Pipeline flow
│   ├── REALISM_GAP.md                   # Realism calibration docs
│   └── REFACTORING_GUIDE.md             # Step-by-step migration
│
├── pyproject.toml
├── requirements.txt
└── main.py                              # Entry point
```

---

## Layer Responsibilities

### 1. **Domain Layer** (business logic, framework-agnostic)
- **Models**: Pure Python dataclasses (battery state, tariff structure, financial metrics)
- **Services**: Core algorithms (MILP solving, tariff calculation, forecasting inference)
- **Policies**: State-specific rules (net metering, export limits, tariff rates)
- **Repositories**: Interfaces/ports (abstract data access)
- **No dependencies on:** FastAPI, databases, ML frameworks (only interfaces)

### 2. **Application Layer** (use-case orchestration)
- **Pipeline**: Defines step-by-step flow (ingestion → forecast → optimize → finance → decision → realism)
- **Stages**: Individual transformations (each stage is testable)
- **Use-Cases**: Business operations (AnalyzeInvestment, RunWhatIf, etc)
- **DTOs**: Data transfer objects flowing through pipeline
- **Realism Calibrator**: XAI + confidence scoring

### 3. **Infrastructure Layer** (adapters & implementations)
- **ML**: XGBoost forecaster, model loading
- **Optimization**: PuLP solver, greedy fallback
- **Persistence**: CSV/database adapters
- **Cache**: Redis/in-memory caching
- **Logging**: Structured logging for debugging

### 4. **API Layer** (HTTP interface)
- **Routes**: FastAPI endpoints (v1/analyze, v1/tariffs, etc)
- **Schemas**: Pydantic models (request validation, response serialization)
- **Middleware**: Error handling, CORS, rate limiting
- **Dependencies**: FastAPI dependency injection (repositories, services)

### 5. **Config Layer** (settings & constants)
- **Settings**: Environment variables via Pydantic
- **Constants**: Business rules (degradation cost, payback threshold, etc)
- **Logging**: Configuration for structured logging

---

## Data Flow: API → Pipeline → Response

```
POST /analyze
  ↓
API Layer (FastAPI validation)
  ├─ AnalysisRequest schema
  ├─ Resolve dependencies (repositories, services)
  ↓
Application Layer (Pipeline Orchestration)
  ├─ Stage 1: Data Ingestion
  │  └─ Validate input, load CSV or demo data
  ├─ Stage 2: Forecasting
  │  └─ XGBoost: predict 24h load, solar
  ├─ Stage 3: Optimization
  │  └─ MILP: minimize cost, respect constraints
  ├─ Stage 4: Financial Analysis
  │  └─ Calculate ROI, NPV, payback, IRR
  ├─ Stage 5: Decision Engine
  │  └─ Score battery sizes, recommend INSTALL/DO_NOT_INSTALL
  ├─ Stage 6: Realism Calibration
  │  └─ XAI: realistic savings, confidence, gap analysis
  ↓
Domain Layer (Pure business logic)
  ├─ Models: Battery, Tariff, Load, Financial
  ├─ Services: Optimization, Billing, Forecasting
  ├─ Policies: State-specific rules
  ↓
Infrastructure Layer (Implementations)
  ├─ XGBoost forecaster
  ├─ PuLP MILP solver
  ├─ Repository implementations
  ↓
API Layer (Response Serialization)
  └─ AnalysisResponse schema
    ├─ KPIs (savings, payback, ROI, confidence)
    ├─ Charts (monthly savings, load curves, SOC)
    ├─ Realism Gap (theoretical vs realistic)
    ├─ Recommendation (size, CAPEX/EaaS/Hybrid)
    └─ Return JSON
```

---

## Module Interaction (Dependency Injection)

```python
# Example flow (pseudo-code)

class AnalysisPipeline:
    def __init__(
        self, 
        data_service,      # Load CSV/demo
        forecast_service,  # XGBoost
        optimizer_service, # MILP
        billing_service,   # HT tariff
        financial_service, # ROI/NPV
        policy_service,    # State rules
        realism_service    # XAI calibrator
    ):
        self.stages = [
            DataStage(data_service),
            ForecastStage(forecast_service),
            OptimizationStage(optimizer_service, policy_service, billing_service),
            FinancialStage(financial_service),
            DecisionStage(),
            RealismStage(realism_service)
        ]
    
    def run(self, request: AnalysisRequest) -> AnalysisPipelineDTO:
        context = {}
        for stage in self.stages:
            context = stage.execute(context, request)
        return context
```

---

## Naming Conventions (Industry Standard)

| Old Name | New Name | Reasoning |
|----------|----------|-----------|
| `optimizer.py` | `optimization_service.py` | Service = business logic |
| `decision_engine.py` | `decision_stage.py` + `use_case` | Stages are pipeline components |
| `billing/engine.py` | `billing_service.py` | Domain service |
| `scenario_engine.py` | `scenario_use_case.py` | Use-case pattern |
| `what_if.py` | `what_if_use_case.py` | Explicit use-case naming |
| `finance.py` | `financial_service.py` | Consistency |
| `xai.py` | `realism_calibrator.py` | More descriptive |
| `data_gen.py` | `synthetic_data_generator.py` | Infrastructure |
| `main.py` (API) | `main.py` + `routes/analysis.py` | Separation of concerns |

---

## Key Design Principles

1. **Dependency Inversion**: Inject services, don't hard-code imports
2. **Single Responsibility**: Each class has ONE reason to change
3. **Testability**: All layers independently testable with mocks
4. **Scalability**: Stateless services, cacheable results, async-ready
5. **Domain Purity**: Domain ≠ Framework (no FastAPI in models)
6. **Pipeline Pattern**: Linear flow, easy to insert/remove stages
7. **Configuration**: Externalize all constants (no magic numbers)

---

## Migration Path

1. **Phase 1**: Create new folder structure, move modules
2. **Phase 2**: Extract domain models (immutable entities)
3. **Phase 3**: Create service interfaces in domain/
4. **Phase 4**: Implement infrastructure adapters
5. **Phase 5**: Build pipeline orchestrator
6. **Phase 6**: Redesign API schemas & routes
7. **Phase 7**: Integrate realism calibrator
8. **Phase 8**: Write tests, deprecate old code
