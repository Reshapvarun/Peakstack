# Refactoring Guide: From Current to Production Architecture

## Complete Step-by-Step Migration Path

---

## Phase 1: Analyze Current Code & Plan (Week 1)

### 1.1 Audit Existing Modules

```bash
# Map what you have to new structure
# Run this to get file sizes/dependencies

find app -name "*.py" -type f -exec wc -l {} + | sort -n

# Identify tight coupling:
# - Look for circular imports
# - Count hard-coded instantiations (vs dependency injection)
# - List all database/file I/O operations
```

### 1.2 Documentation
- [ ] Create ARCHITECTURE_REDESIGN/ folder (✅ done)
- [ ] Read all 3 design docs (00_FOLDER_STRUCTURE, 01_API_DESIGN, 02_PIPELINE, 03_REALISM)
- [ ] Map current modules → new locations:

| Current | New Location | Rename? |
|---------|--------------|---------|
| `app/api/main.py` | `app/api/main.py` + `app/api/v1/routes/analysis.py` | Split |
| `app/core/optimizer.py` | `app/domain/services/optimization_service.py` | Rename |
| `app/core/billing/engine.py` | `app/domain/services/billing_service.py` | Move |
| `app/core/finance.py` | `app/domain/services/financial_service.py` | Rename |
| `app/core/decision_engine.py` | `app/application/pipeline/stages/decision_stage.py` | Move |
| `app/ml/forecaster.py` | `app/infrastructure/ml/xgboost_forecaster.py` | Move |
| `app/core/xai.py` | `app/application/services/realism_calibrator.py` | Rename |
| `app/core/scenario_engine.py` | `app/application/use_cases/run_scenario.py` | Move |
| `app/core/what_if.py` | `app/application/use_cases/what_if_analysis.py` | Move |

---

## Phase 2: Create Domain Layer (Week 2)

### 2.1 Extract Business Models (Immutable Entities)

**Create domain models WITHOUT FastAPI/ORM dependencies:**

```bash
mkdir -p app/domain/models
touch app/domain/models/{__init__,battery,tariff,load_profile,financial}.py
```

**Example: domain/models/battery.py**

```python
"""Pure domain model - NO imports from app.api or FastAPI"""

from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)  # Immutable
class BatteryConfig:
    """Battery physical & economic parameters"""
    capacity_kwh: float
    power_kw: float
    round_trip_efficiency: float = 0.85
    degradation_cost_per_kwh: float = 0.05
    min_soc_percent: int = 20
    
    def validate(self) -> List[str]:
        """Returns list of validation errors (empty if valid)"""
        errors = []
        if self.capacity_kwh <= 0 or self.capacity_kwh > 2000:
            errors.append(f"Invalid capacity: {self.capacity_kwh}")
        if self.power_kw <= 0:
            errors.append(f"Invalid power: {self.power_kw}")
        return errors


@dataclass(frozen=True)
class BatteryState:
    """Runtime state (SOC, charge/discharge)"""
    soc_percent: float  # 0-100
    charge_rate_kw: float  # Current charge rate
    discharge_rate_kw: float  # Current discharge rate
    
    @property
    def current_energy_kwh(self, capacity: BatteryConfig) -> float:
        return capacity.capacity_kwh * self.soc_percent / 100
```

**Extract from current code:**

- `app/core/battery.py` → `domain/models/battery.py`
- `app/core/tariff.py` → `domain/models/tariff.py`
- Rename, remove Flask/FastAPI decorators
- Keep pure Python dataclasses

### 2.2 Create Domain Services (Interfaces)

```bash
mkdir -p app/domain/services
touch app/domain/services/{__init__,optimization_service,billing_service,financial_service,forecasting_service}.py
```

**Example: domain/services/optimization_service.py**

```python
"""Abstract interface for optimizer (implementation-agnostic)"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from app.domain.models.battery import BatteryConfig

@dataclass
class OptimizationResult:
    recommended_capacity_kwh: float
    recommended_power_kw: float
    dispatch_schedule: dict  # Hourly dispatch
    objective_value_inr: float
    optimization_status: str  # 'optimal', 'feasible', 'infeasible'
    why_this_size: str


class OptimizationService(ABC):
    """Abstract optimization interface"""
    
    @abstractmethod
    async def solve(
        self,
        load_profile_hourly: List[float],
        solar_profile_hourly: List[float],
        battery_config: BatteryConfig,
        tariff: dict,
        policies: dict,
    ) -> OptimizationResult:
        """Solve MILP / greedy optimization"""
        pass
```

**Extract:** `app/core/optimizer.py` → `domain/services/optimization_service.py` as interface

### 2.3 Create Policies (State-Specific Rules)

```bash
mkdir -p app/domain/policies
touch app/domain/policies/{__init__,state_policy,policies_registry,tariff_profiles}.py
```

**Extract:** `app/core/policy_manager.py` → `domain/policies/`

---

## Phase 3: Create Application Layer (Week 3)

### 3.1 Build Pipeline Orchestrator

```bash
mkdir -p app/application/pipeline/stages
mkdir -p app/application/pipeline/dto
touch app/application/pipeline/{__init__,analysis_pipeline}.py
touch app/application/pipeline/stages/{__init__,data_stage,forecast_stage,optimization_stage,financial_stage,decision_stage,realism_stage}.py
touch app/application/pipeline/dto/{__init__,pipeline_dto}.py
```

**Implement:** Follow `02_PIPELINE_ORCHESTRATOR.md` exactly

- Create `PipelineStage` abstract base
- Implement 6 stages (Data → Forecast → Optimize → Finance → Decision → Realism)
- Create `AnalysisPipeline` orchestrator
- Create `PipelineContext` DTO

### 3.2 Build Use-Cases

```bash
mkdir -p app/application/use_cases
touch app/application/use_cases/{__init__,analyze_investment,run_what_if,run_scenario}.py
```

**Implement:**

```python
# app/application/use_cases/analyze_investment.py

from app.application.pipeline.analysis_pipeline import AnalysisPipeline
from app.api.v1.schemas.analysis import AnalysisRequest, AnalysisResponse

class AnalyzeInvestmentUseCase:
    def __init__(self, pipeline: AnalysisPipeline):
        self.pipeline = pipeline
    
    async def execute(self, request: AnalysisRequest, analysis_id: str) -> AnalysisResponse:
        context = await self.pipeline.execute(...)
        return AnalysisResponse.from_context(context)
```

### 3.3 Realism Calibrator Service

```bash
touch app/application/services/realism_calibrator.py
```

**Implement:** Follow `03_REALISM_CALIBRATOR.md` exactly

- `RealismCalibrationService` class
- Confidence scoring algorithm
- Risk factor detection

---

## Phase 4: Create Infrastructure Layer (Week 4)

### 4.1 ML Infrastructure

```bash
mkdir -p app/infrastructure/ml
touch app/infrastructure/ml/{__init__,xgboost_forecaster,model_loader}.py
```

**Implement:** Extract from `app/ml/forecaster.py`

```python
# app/infrastructure/ml/xgboost_forecaster.py

from app.domain.services.forecasting_service import ForecastingService  # Interface!

class XGBoostForecaster(ForecastingService):
    """Concrete implementation of forecasting interface"""
    
    def __init__(self, model_path: str):
        self.model = load_model(model_path)
    
    async def forecast_load(self, historical: List[float], state: str) -> List[float]:
        # Actual XGBoost prediction logic
        pass
```

### 4.2 Optimization Infrastructure

```bash
mkdir -p app/infrastructure/optimization
touch app/infrastructure/optimization/{__init__,pulp_optimizer,greedy_optimizer}.py
```

**Extract:** `app/core/optimizer.py` implementation → `pulp_optimizer.py`

### 4.3 Persistence Infrastructure

```bash
mkdir -p app/infrastructure/persistence
touch app/infrastructure/persistence/{__init__,load_repository_impl,tariff_repository_impl}.py
```

**Implement:** Adapters that implement domain repository interfaces

```python
# app/infrastructure/persistence/load_repository_impl.py

from app.domain.repositories.load_repository import LoadRepository

class CSVLoadRepository(LoadRepository):
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
    
    async def load_by_state(self, state: str) -> List[float]:
        # CSV reading logic
        pass
```

### 4.4 Caching Infrastructure

```bash
mkdir -p app/infrastructure/cache
touch app/infrastructure/cache/{__init__,redis_cache,memory_cache}.py
```

### 4.5 Logging Infrastructure

```bash
mkdir -p app/infrastructure/logging
touch app/infrastructure/logging/{__init__,pipeline_logger}.py
```

---

## Phase 5: Refactor API Layer (Week 5)

### 5.1 Create Schemas

```bash
mkdir -p app/api/v1/schemas
touch app/api/v1/schemas/{__init__,analysis,common,tariff}.py
```

**Implement:** Follow `01_API_DESIGN_SCHEMAS.md` exactly

- `AnalysisRequest`
- `AnalysisResponse` with all nested schemas
- `RealisticKPIsSchema`
- Error schemas

### 5.2 Create Routes

```bash
mkdir -p app/api/v1/routes
touch app/api/v1/routes/{__init__,analysis,tariffs,uploads}.py
```

**Implement:** Follow `01_API_DESIGN_SCHEMAS.md` exactly

```python
# app/api/v1/routes/analysis.py

from fastapi import APIRouter
from app.application.use_cases.analyze_investment import AnalyzeInvestmentUseCase

router = APIRouter(prefix="/v1/analyses")

@router.post("/analyze")
async def analyze_investment(
    request: AnalysisRequest,
    use_case = Depends(get_analysis_use_case)
) -> AnalysisResponse:
    return await use_case.execute(request, analysis_id=...)
```

### 5.3 Dependencies & Middleware

```python
# app/api/v1/dependencies.py

from fastapi import Depends
from app.infrastructure.container import Container

async def get_analysis_use_case(container: Container = Depends(get_container)):
    return container.analyze_investment_use_case()
```

### 5.4 Update Main App

```python
# app/api/main.py

from fastapi import FastAPI
from app.api.v1.routes import analysis, tariffs, uploads

app = FastAPI(title="PeakStack API")

app.include_router(analysis.router)
app.include_router(tariffs.router)
app.include_router(uploads.router)
```

---

## Phase 6: Setup Dependency Injection (Week 5)

### 6.1 Install dependency-injector

```bash
pip install dependency-injector
```

### 6.2 Create Container

```bash
touch app/infrastructure/container.py
```

**Implement:**

```python
from dependency_injector import containers, providers
from app.infrastructure.ml.xgboost_forecaster import XGBoostForecaster
from app.application.pipeline.analysis_pipeline import create_pipeline

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Services
    forecaster = providers.Singleton(XGBoostForecaster)
    optimizer = providers.Singleton(PuLPOptimizer)
    # ... all services
    
    # Pipeline
    pipeline = providers.Singleton(
        create_pipeline,
        forecaster=forecaster,
        optimizer=optimizer,
        # ... pass all services
    )
    
    # Use-cases
    analyze_use_case = providers.Singleton(
        AnalyzeInvestmentUseCase,
        pipeline=pipeline
    )
```

---

## Phase 7: Write Tests (Week 6)

### 7.1 Unit Tests

```bash
mkdir -p tests/unit/{domain,application,infrastructure}
```

**Test domain services:**

```python
# tests/unit/domain/test_optimization_service.py

@pytest.mark.asyncio
async def test_optimization_finds_best_size():
    # Mock optimizer
    optimizer = MagicMock(spec=OptimizationService)
    optimizer.solve.return_value = OptimizationResult(...)
    
    # Test
    result = await optimizer.solve(...)
    
    # Assert
    assert result.recommended_capacity_kwh > 0
```

### 7.2 Integration Tests

```python
# tests/integration/test_pipeline.py

@pytest.mark.asyncio
async def test_full_pipeline():
    # Create container
    container = create_test_container()
    pipeline = container.pipeline()
    
    # Run
    context = PipelineContext(request=test_request)
    result = await pipeline.execute(context)
    
    # Assert all stages ran
    assert result.load_profile_15min is not None
    assert result.recommendation is not None
```

---

## Phase 8: Migration & Cleanup (Week 7)

### 8.1 Parallel Running

Keep old code + new code running side-by-side:

```python
# app/api/main.py

# Old endpoint (deprecated)
@app.post("/analyze-old")
async def analyze_old(...):
    return old_logic()

# New endpoint (production)
@app.post("/v1/analyses/analyze")
async def analyze(...):
    return new_pipeline()
```

### 8.2 Gradual Cutover

- Week 1-2: New code, feature-parity testing
- Week 2-3: Canary deployment (10% traffic to new)
- Week 3: Full migration
- Week 4: Archive old code

### 8.3 Delete Old Code

Once confident:

```bash
rm -r app/api/old_main.py
rm -r app/core/optimizer.py  (moved to infrastructure)
# etc
```

---

## Phase 9: Documentation & Handoff (Week 8)

### 9.1 Document Everything

```bash
cat > docs/API.md << 'EOF'
# PeakStack API Reference

## POST /v1/analyses/analyze

### Request
...
### Response
...
EOF

cat > docs/PIPELINE.md << 'EOF'
# Pipeline Architecture

## Stage Flow
Data → Forecast → Optimize → Finance → Decision → Realism

## Adding New Stages
...
EOF

cat > docs/DEPLOYMENT.md << 'EOF'
# Deployment Guide

## Environment Variables
...
## Running
...
EOF
```

### 9.2 README Updates

```markdown
# PeakStack Backend

## Architecture

Clean layered architecture:
- **Domain**: Pure business logic
- **Application**: Use-cases & orchestration
- **Infrastructure**: External integrations
- **API**: HTTP interface

## Folder Structure
See ARCHITECTURE_REDESIGN/ docs

## Running
```bash
pip install -r requirements.txt
python -m uvicorn app.api.main:app
```

## Testing
```bash
pytest tests/
```
```

---

## Checklist: Day-by-Day

### Week 1: Planning & Audit
- [ ] Read all 3 design docs
- [ ] Audit current code (sizes, dependencies)
- [ ] Map old → new modules
- [ ] Set up new folder structure
- [ ] Create design spec document

### Week 2: Domain Layer
- [ ] Extract models (Battery, Tariff, Load, Financial)
- [ ] Create domain service interfaces
- [ ] Create policy/state rules
- [ ] Create repository interfaces
- [ ] Unit test domain models

### Week 3: Application Layer
- [ ] Build pipeline orchestrator
- [ ] Implement 6 pipeline stages
- [ ] Build use-cases
- [ ] Implement realism calibrator
- [ ] Integration test pipeline

### Week 4: Infrastructure Layer
- [ ] ML forecaster adapter
- [ ] Optimization solver adapter
- [ ] Persistence adapters
- [ ] Cache layer
- [ ] Logging setup

### Week 5: API & DI
- [ ] Create Pydantic schemas
- [ ] Build routes (v1/analyses/analyze, etc)
- [ ] Setup dependency injection container
- [ ] Build API middleware
- [ ] API contract tests

### Week 6: Testing
- [ ] Unit tests (all layers)
- [ ] Integration tests (pipeline)
- [ ] API tests (endpoint contracts)
- [ ] Performance tests
- [ ] Load tests (optional)

### Week 7: Parallel & Cutover
- [ ] Deploy both old & new side-by-side
- [ ] Canary test (10% → new)
- [ ] Monitor metrics
- [ ] Full cutover
- [ ] Archive old code

### Week 8: Documentation & Handoff
- [ ] API docs complete
- [ ] Deployment runbook
- [ ] README updated
- [ ] Team training
- [ ] Knowledge transfer

---

## Common Pitfalls to Avoid

| Pitfall | Prevention |
|---------|-----------|
| **Circular dependencies** | Never import from API/infrastructure into domain |
| **Tight coupling to FastAPI** | Keep domain pure Python (no `from fastapi`) |
| **Unmocked external calls in tests** | Use `@patch` or dependency injection mocks |
| **Missing error handling in pipeline** | Wrap each stage in try-catch, log stage name |
| **Cache invalidation issues** | Use immutable DTOs, fingerprint-based keys |
| **ML model versioning** | Store model hashes, track in config |
| **Incomplete data validation** | Validate at API input & domain boundaries |
| **Synchronous I/O blocking async** | Audit all `open()`, `requests.get()` → use async libs |

---

## Success Criteria

✅ **Architecture is production-ready when:**

1. **Testability**: All layers independently testable (>90% coverage)
2. **Dependency Inversion**: No framework imports in domain
3. **Clean Separation**: Each layer has ONE reason to change
4. **Error Handling**: Pipeline catches & logs all failures
5. **Performance**: <2s for full analysis (from API request)
6. **Scalability**: Stateless services, cacheable results
7. **Documentation**: Every module has docstrings, README complete
8. **Tests Pass**: 100% integration test pass rate
9. **API Contracts**: Schema validation on request/response
10. **Realism Feature**: XAI calibrator producing meaningful confidence scores

---

## References

- `ARCHITECTURE_REDESIGN/00_FOLDER_STRUCTURE.md` — Full folder tree & layer responsibilities
- `ARCHITECTURE_REDESIGN/01_API_DESIGN_SCHEMAS.md` — Endpoint design & schemas
- `ARCHITECTURE_REDESIGN/02_PIPELINE_ORCHESTRATOR.md` — Pipeline & stage implementations
- `ARCHITECTURE_REDESIGN/03_REALISM_CALIBRATOR.md` — XAI calibration logic & UI
