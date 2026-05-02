# PeakStack API Design: `/analyze` Endpoint

## Prompt #2 Solution: Request/Response Schemas & Pipeline Flow

---

## 1. Pydantic Schemas (app/api/v1/schemas/analysis.py)

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

# ============= ENUMS =============

class StateEnum(str, Enum):
    MAHARASHTRA = "maharashtra"
    KARNATAKA = "karnataka"
    TAMIL_NADU = "tamil_nadu"
    DELHI = "delhi"
    RAJASTHAN = "rajasthan"
    ANDHRA_PRADESH = "andhra_pradesh"
    GUJARA T = "gujara t"

class BusinessModelEnum(str, Enum):
    CAPEX = "capex"          # 100% client funded
    EAAS = "eaas"            # 0% upfront, energy-as-a-service
    HYBRID = "hybrid"        # 40% client, 60% service provider


# ============= COMMON SCHEMAS =============

class BatteryConfigSchema(BaseModel):
    """Optional: if not provided, decision engine recommends size"""
    capacity_kwh: Optional[float] = Field(None, gt=0, le=2000)
    power_kw: Optional[float] = Field(None, gt=0)
    round_trip_efficiency: float = Field(0.85, ge=0.8, le=0.95)
    degradation_cost_per_kwh: float = Field(0.05)
    min_soc_percent: int = Field(20, ge=0, le=50)

class SolarConfigSchema(BaseModel):
    capacity_kw: float = Field(0, ge=0, le=500)
    export_allowed: bool = True
    capacity_factor: float = Field(0.2, ge=0.1, le=0.35)

class DGConfigSchema(BaseModel):
    """Diesel Generator fallback"""
    capacity_kw: float = Field(0, ge=0)
    cost_per_kwh: float = Field(18.0, gt=0)
    min_load_percent: int = Field(25, ge=0, le=100)

class FinancialConfigSchema(BaseModel):
    """Optional: override defaults"""
    capex_per_kwh: Optional[float] = Field(None, gt=0)
    annual_om_percent: Optional[float] = Field(None, gt=0, le=10)
    discount_rate_percent: float = Field(10.0, ge=1, le=20)
    analysis_years: int = Field(10, ge=5, le=25)


# ============= REQUEST SCHEMA =============

class AnalysisRequest(BaseModel):
    """Main /analyze endpoint request"""
    
    # Core inputs
    state: StateEnum
    annual_kwh_consumption: float = Field(..., gt=0, description="Total annual energy (kWh)")
    
    # Optional: Custom load profile (CSV upload)
    load_profile: Optional[List[float]] = Field(
        None,
        description="15-min interval load values for 1 year (35,040 points). If None, use synthetic."
    )
    solar_pv_capacity_kw: float = Field(0, ge=0)
    solar_export_allowed: bool = True
    
    # Battery config (optional, engine recommends if not provided)
    battery: Optional[BatteryConfigSchema] = None
    solar: Optional[SolarConfigSchema] = None
    dg: Optional[DGConfigSchema] = None
    finance: Optional[FinancialConfigSchema] = None
    
    # Analysis options
    business_models: List[BusinessModelEnum] = Field(
        default=[BusinessModelEnum.CAPEX, BusinessModelEnum.EAAS],
        description="Which business models to analyze"
    )
    include_scenario_comparison: bool = True
    
    # Optional metadata
    customer_id: Optional[str] = None
    description: Optional[str] = None
    
    @validator('load_profile')
    def validate_load_profile(cls, v):
        if v is not None and len(v) != 35040:
            raise ValueError("Load profile must have 35,040 points (15-min intervals for 1 year)")
        return v


# ============= RESPONSE SCHEMAS =============

class KPISchema(BaseModel):
    """Key Performance Indicators"""
    annual_savings_inr: float = Field(..., description="₹/year savings from BESS")
    peak_demand_reduction_kw: float = Field(..., description="Max demand reduction")
    peak_demand_reduction_percent: float
    payback_period_months: float
    roi_percent_annual: float
    npv_inr: float = Field(..., description="10-year NPV @ 10% discount")
    irr_percent: float
    battery_throughput_mwh_annual: float
    grid_import_reduction_percent: float
    diesel_replacement_liters: Optional[float] = None


class RealisticKPIsSchema(BaseModel):
    """XAI-calibrated KPIs with confidence"""
    savings_theoretical_inr: float = Field(..., description="Idealized model output")
    savings_realistic_inr: float = Field(..., description="XAI-adjusted for real-world")
    realism_gap_percent: float = Field(
        ..., 
        description="(Theoretical - Realistic) / Theoretical * 100. If >30%, tool provides warnings."
    )
    confidence_score: float = Field(..., ge=0, le=1, description="0-1 confidence in model")
    confidence_reason: str = Field(..., description="Why confidence is X (data quality, state support, etc)")
    
    # Risk factors
    risk_factors: List[str] = Field(
        default=[],
        description="['tariff_changes', 'low_solar_data', 'unproven_tech', 'policy_risk']"
    )
    recommended_buffer_percent: int = Field(
        default=10,
        description="Conservative estimate: savings * (1 - buffer%)"
    )


class OptimizationResultSchema(BaseModel):
    """Battery sizing recommendation"""
    recommended_capacity_kwh: float
    recommended_power_kw: float
    optimization_status: str = Field(..., description="'optimal', 'feasible', 'infeasible'")
    objective_value_inr: float = Field(..., description="Minimum cost achieved")
    why_this_size: str = Field(
        ...,
        description="Human-readable reason for this size (payback, peak reduction, etc)"
    )


class ChartDataSchema(BaseModel):
    """Time-series data for frontend charts"""
    timestamp: List[str] = Field(..., description="ISO 8601 datetimes")
    load_kw: List[float] = Field(..., description="Original load profile")
    solar_generation_kw: List[float]
    battery_charge_kw: List[float] = Field(..., description="Positive = charging")
    battery_discharge_kw: List[float] = Field(..., description="Positive = discharging")
    battery_soc_percent: List[float] = Field(..., description="State of Charge %")
    grid_import_kw: List[float] = Field(..., description="With BESS (optimized)")
    grid_import_without_bess_kw: List[float] = Field(..., description="Baseline, no BESS")
    
    class Config:
        description = "All arrays must have same length (e.g., 35,040 for 15-min annual)"


class InsightSchema(BaseModel):
    """Human-readable business insights from XAI"""
    type: str = Field(..., description="'peak_shaving', 'arbitrage', 'solar_buffering', 'dg_replacement'")
    description: str = Field(..., description="Natural language explanation")
    impact_inr: float = Field(..., description="Financial impact of this insight")
    frequency: str = Field(..., description="'peak_hours', 'offpeak', 'daily', 'seasonal'")


class ScenarioResultSchema(BaseModel):
    """Scenario comparison (with BESS vs without, with Solar vs without)"""
    scenario_name: str = Field(..., description="'base', 'with_bess', 'with_solar', 'with_both'")
    annual_cost_inr: float
    annual_savings_vs_base_inr: float
    peak_demand_kw: float
    carbon_emissions_tons: Optional[float] = None


class RecommendationSchema(BaseModel):
    """Final decision from decision engine"""
    recommendation: str = Field(..., description="'INSTALL', 'DO_NOT_INSTALL', 'INVESTIGATE'")
    decision_reason: str
    recommended_size_kwh: Optional[float] = None
    recommended_business_model: Optional[BusinessModelEnum] = None
    roi_threshold_met: bool
    payback_threshold_met: bool


class AnalysisResponse(BaseModel):
    """Complete /analyze endpoint response"""
    
    # Metadata
    analysis_id: str = Field(..., description="Unique analysis ID for tracking")
    timestamp: datetime
    state: StateEnum
    annual_kwh: float
    
    # Optimization & Decision
    optimization_result: OptimizationResultSchema
    recommendation: RecommendationSchema
    
    # KPIs (for all business models analyzed)
    kpis_by_model: Dict[str, KPISchema] = Field(
        ...,
        description="{'capex': KPI, 'eaas': KPI, 'hybrid': KPI}"
    )
    
    # XAI + Realism
    realistic_kpis: Dict[str, RealisticKPIsSchema] = Field(
        ...,
        description="Realism-adjusted KPIs per business model"
    )
    
    # Charts (for React dashboard)
    annual_load_chart: ChartDataSchema = Field(..., description="Full year monthly/daily view")
    typical_day_chart: ChartDataSchema = Field(..., description="Typical weekday profile")
    monthly_savings_chart: Dict[str, List[float]] = Field(
        ...,
        description="{'month': ['jan', 'feb', ...], 'savings_inr': [5000, 6000, ...]}"
    )
    
    # Insights
    insights: List[InsightSchema] = Field(..., description="XAI-generated business reasoning")
    
    # Scenarios
    scenarios: List[ScenarioResultSchema] = Field(
        ...,
        description="If include_scenario_comparison=True"
    )
    
    # Validation
    data_quality_score: float = Field(..., ge=0, le=1, description="0-1 quality of input data")
    data_quality_issues: List[str] = Field(
        default=[],
        description="['missing_weekends', 'outliers_detected', 'low_solar_data']"
    )
    
    # URL for dashboard
    dashboard_url: Optional[str] = None


# ============= ERROR SCHEMAS =============

class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
    details: Optional[Dict] = None
```

---

## 2. FastAPI Route Implementation (app/api/v1/routes/analysis.py)

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from datetime import datetime
import uuid
import asyncio
from typing import Optional

from app.api.v1.schemas.analysis import (
    AnalysisRequest, AnalysisResponse, ErrorResponse
)
from app.application.use_cases.analyze_investment import AnalyzeInvestmentUseCase
from app.infrastructure.persistence.load_repository_impl import LoadRepositoryImpl
from app.config.settings import get_settings

router = APIRouter(prefix="/v1/analyses", tags=["Analysis"])
settings = get_settings()


# ============= DEPENDENCIES =============

async def get_analysis_use_case() -> AnalyzeInvestmentUseCase:
    """
    Dependency injection: Create use-case with all services.
    In production, use a service container (e.g., dependency-injector library)
    """
    # Pseudo-code; actual implementation depends on your structure
    return AnalyzeInvestmentUseCase(
        data_service=...,           # Injected
        forecast_service=...,
        optimizer_service=...,
        billing_service=...,
        financial_service=...,
        policy_service=...,
        realism_service=...
    )


# ============= ENDPOINTS =============

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze BESS Investment Opportunity",
    description="Full pipeline: ingestion → forecast → optimize → finance → decision → realism"
)
async def analyze_investment(
    request: AnalysisRequest,
    use_case: AnalyzeInvestmentUseCase = Depends(get_analysis_use_case),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> AnalysisResponse:
    """
    POST /v1/analyses/analyze
    
    Example request:
    {
        "state": "maharashtra",
        "annual_kwh_consumption": 500000,
        "solar_pv_capacity_kw": 100,
        "battery": {
            "capacity_kwh": 200,
            "power_kw": 50
        },
        "business_models": ["capex", "eaas"],
        "include_scenario_comparison": true
    }
    
    Returns: AnalysisResponse with KPIs, charts, insights, recommendation
    """
    try:
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Run use-case (orchestrates entire pipeline)
        response = await use_case.execute(
            request=request,
            analysis_id=analysis_id
        )
        
        # Add metadata
        response.analysis_id = analysis_id
        response.timestamp = datetime.utcnow()
        response.dashboard_url = f"{settings.DASHBOARD_URL}/analyses/{analysis_id}"
        
        # Optional: Log to database in background
        background_tasks.add_task(
            store_analysis_result,
            analysis_id=analysis_id,
            response=response
        )
        
        return response
        
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={"errors": e.errors()}
        )
    except Exception as e:
        # Log structured error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "ANALYSIS_FAILED",
                "error_message": str(e),
                "analysis_id": analysis_id
            }
        )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Retrieve Previous Analysis"
)
async def get_analysis(analysis_id: str):
    """
    GET /v1/analyses/{analysis_id}
    
    Retrieve cached or stored analysis result
    """
    # Pseudo-code: fetch from cache/database
    try:
        result = await cache.get(f"analysis:{analysis_id}")
        if not result:
            result = await db.analyses.find_by_id(analysis_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail="Analysis not found")


@router.post(
    "/what-if",
    response_model=AnalysisResponse,
    summary="What-If Sensitivity Analysis"
)
async def what_if_analysis(
    base_analysis_id: str,
    battery_size_kwh: float,
    solar_capacity_kw: Optional[float] = None,
    use_case = Depends(get_analysis_use_case)
):
    """
    POST /v1/analyses/what-if
    
    Quick re-analysis with changed parameters (cached base data)
    """
    # Pseudo-code: load base analysis, modify, re-optimize
    pass


# ============= BACKGROUND TASKS =============

async def store_analysis_result(analysis_id: str, response: AnalysisResponse):
    """Store analysis result in database for future retrieval"""
    # Pseudo-code
    try:
        await db.analyses.insert({
            "id": analysis_id,
            "result": response.dict(),
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        logging.error(f"Failed to store analysis {analysis_id}: {e}")
```

---

## 3. Use-Case Implementation (app/application/use_cases/analyze_investment.py)

```python
from typing import Optional
from app.api.v1.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.application.pipeline.analysis_pipeline import AnalysisPipeline
from app.application.pipeline.dto.pipeline_dto import PipelineContext

class AnalyzeInvestmentUseCase:
    """Orchestrates the full analysis pipeline"""
    
    def __init__(self, pipeline: AnalysisPipeline):
        self.pipeline = pipeline
    
    async def execute(
        self,
        request: AnalysisRequest,
        analysis_id: str
    ) -> AnalysisResponse:
        """
        Execute analysis pipeline:
        1. Ingest data (load profile)
        2. Forecast load/solar
        3. Optimize battery dispatch
        4. Calculate financials
        5. Generate recommendation
        6. Calibrate realism & confidence
        
        Returns: AnalysisResponse ready for API
        """
        
        # Create pipeline context
        context = PipelineContext(
            analysis_id=analysis_id,
            request=request,
            state=request.state.value,
            annual_kwh=request.annual_kwh_consumption
        )
        
        # Run pipeline (all stages)
        context = await self.pipeline.execute(context)
        
        # Convert context to API response
        return self._context_to_response(context)
    
    def _context_to_response(self, context: PipelineContext) -> AnalysisResponse:
        """Transform pipeline context to API response schema"""
        # Pseudo-code: map all context fields to AnalysisResponse
        return AnalysisResponse(
            state=context.state,
            annual_kwh=context.annual_kwh,
            optimization_result=context.optimization_result,
            recommendation=context.recommendation,
            kpis_by_model=context.kpis_by_model,
            realistic_kpis=context.realistic_kpis,
            annual_load_chart=context.annual_chart,
            typical_day_chart=context.typical_day_chart,
            monthly_savings_chart=context.monthly_savings,
            insights=context.insights,
            scenarios=context.scenarios,
            data_quality_score=context.data_quality_score,
            data_quality_issues=context.data_quality_issues
        )
```

---

## 4. Pipeline DTOs (app/application/pipeline/dto/pipeline_dto.py)

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from app.api.v1.schemas.analysis import (
    AnalysisRequest, KPISchema, RealisticKPIsSchema,
    OptimizationResultSchema, InsightSchema, ScenarioResultSchema, 
    ChartDataSchema, RecommendationSchema
)

@dataclass
class PipelineContext:
    """Mutable context flowing through pipeline stages"""
    
    # Metadata
    analysis_id: str
    request: AnalysisRequest
    state: str
    annual_kwh: float
    
    # Stage 1: Data Ingestion
    load_profile_15min: Optional[List[float]] = None  # 35,040 points
    solar_generation_15min: Optional[List[float]] = None
    load_resampled_hourly: Optional[List[float]] = None
    
    # Stage 2: Forecasting
    load_forecast_24h: Optional[List[float]] = None
    solar_forecast_24h: Optional[List[float]] = None
    forecast_confidence: float = 0.0
    
    # Stage 3: Optimization
    optimal_dispatch: Optional[Dict] = None  # Battery charge/discharge schedule
    optimization_result: Optional[OptimizationResultSchema] = None
    
    # Stage 4: Financial Analysis
    kpis_by_model: Dict[str, KPISchema] = field(default_factory=dict)
    
    # Stage 5: Decision Engine
    recommendation: Optional[RecommendationSchema] = None
    
    # Stage 6: Realism Calibration
    realistic_kpis: Dict[str, RealisticKPIsSchema] = field(default_factory=dict)
    insights: List[InsightSchema] = field(default_factory=list)
    
    # Charts & Scenarios
    annual_chart: Optional[ChartDataSchema] = None
    typical_day_chart: Optional[ChartDataSchema] = None
    monthly_savings: Optional[Dict] = None
    scenarios: List[ScenarioResultSchema] = field(default_factory=list)
    
    # Quality Metrics
    data_quality_score: float = 1.0
    data_quality_issues: List[str] = field(default_factory=list)
```

---

## 5. Example JSON Response

```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-29T15:30:00Z",
  "state": "maharashtra",
  "annual_kwh": 500000,
  "optimization_result": {
    "recommended_capacity_kwh": 250,
    "recommended_power_kw": 75,
    "optimization_status": "optimal",
    "objective_value_inr": 1250000,
    "why_this_size": "Maximizes peak shaving during 5PM-10PM window (₹85/kWh). Payback: 5.2 years."
  },
  "recommendation": {
    "recommendation": "INSTALL",
    "decision_reason": "ROI 15.3% with 5.2yr payback < 10yr threshold. Saves ₹85K annually.",
    "recommended_size_kwh": 250,
    "recommended_business_model": "capex",
    "roi_threshold_met": true,
    "payback_threshold_met": true
  },
  "kpis_by_model": {
    "capex": {
      "annual_savings_inr": 85000,
      "peak_demand_reduction_kw": 80,
      "peak_demand_reduction_percent": 22.5,
      "payback_period_months": 62.4,
      "roi_percent_annual": 15.3,
      "npv_inr": 425000,
      "irr_percent": 18.2,
      "battery_throughput_mwh_annual": 52.5,
      "grid_import_reduction_percent": 18.2,
      "diesel_replacement_liters": null
    },
    "eaas": {
      "annual_savings_inr": 52000,
      "peak_demand_reduction_kw": 80,
      "peak_demand_reduction_percent": 22.5,
      "payback_period_months": null,
      "roi_percent_annual": 10.4,
      "npv_inr": 180000,
      "irr_percent": 12.1,
      "battery_throughput_mwh_annual": 52.5,
      "grid_import_reduction_percent": 18.2,
      "diesel_replacement_liters": null
    }
  },
  "realistic_kpis": {
    "capex": {
      "savings_theoretical_inr": 85000,
      "savings_realistic_inr": 71000,
      "realism_gap_percent": 16.5,
      "confidence_score": 0.82,
      "confidence_reason": "Good quality load data (12mo), proven tariff structure in MH, similar customer base validated.",
      "risk_factors": ["tariff_changes"],
      "recommended_buffer_percent": 15
    },
    "eaas": {
      "savings_theoretical_inr": 52000,
      "savings_realistic_inr": 45000,
      "realism_gap_percent": 13.5,
      "confidence_score": 0.78,
      "confidence_reason": "EaaS provider reliability in region: 85%+ uptime. Service cost stability: moderate.",
      "risk_factors": ["provider_reliability", "tariff_changes"],
      "recommended_buffer_percent": 20
    }
  },
  "annual_load_chart": {
    "timestamp": [
      "2025-01-01T00:15:00Z", "2025-01-01T00:30:00Z", "...", "2025-12-31T23:45:00Z"
    ],
    "load_kw": [45.2, 42.1, 38.5, "..."],
    "solar_generation_kw": [0, 0, 0, "... (appears from 6AM)"],
    "battery_charge_kw": [0, 0, 5, "..."],
    "battery_discharge_kw": [10, 8, 0, "..."],
    "battery_soc_percent": [50, 48, 53, "..."],
    "grid_import_kw": [35.2, 34.1, 33.5, "..."],
    "grid_import_without_bess_kw": [45.2, 42.1, 38.5, "..."]
  },
  "typical_day_chart": {
    "timestamp": ["06:00", "06:15", "...", "23:45"],
    "load_kw": [20, 22, 45, 120, 105, "..."],
    "solar_generation_kw": [0, 1, 15, 45, 50, 40, "... (peaks 1PM)"],
    "battery_charge_kw": [0, 0, 5, 20, 15, 0, "..."],
    "battery_discharge_kw": [5, 3, 0, 0, 20, 50, "... (peaks 5-10PM)"],
    "battery_soc_percent": [45, 42, 47, 62, 57, 20, "..."],
    "grid_import_kw": [25, 24, 40, 75, 50, 30, "..."],
    "grid_import_without_bess_kw": [20, 20, 45, 120, 105, 100, "..."]
  },
  "monthly_savings_chart": {
    "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "savings_capex_inr": [6200, 5800, 7100, 7500, 8200, 7900, 8100, 7800, 7200, 6800, 6500, 6300]
  },
  "insights": [
    {
      "type": "peak_shaving",
      "description": "BESS discharge during 5PM-10PM peak tariff window (₹9/kWh) saves ₹52K annually by avoiding demand surcharge penalties.",
      "impact_inr": 52000,
      "frequency": "daily"
    },
    {
      "type": "solar_buffering",
      "description": "Solar generation (100 kW installed) peaks 1-3PM but load is low. BESS stores 15 MWh excess solar → use during evening peak.",
      "impact_inr": 28000,
      "frequency": "seasonal"
    },
    {
      "type": "arbitrage",
      "description": "Charge BESS during off-peak window (12AM-6AM, ₹4/kWh) → discharge peak (5-10PM, ₹9/kWh).",
      "impact_inr": 15000,
      "frequency": "daily"
    }
  ],
  "scenarios": [
    {
      "scenario_name": "base",
      "annual_cost_inr": 3200000,
      "annual_savings_vs_base_inr": 0,
      "peak_demand_kw": 355,
      "carbon_emissions_tons": 420
    },
    {
      "scenario_name": "with_bess",
      "annual_cost_inr": 3115000,
      "annual_savings_vs_base_inr": 85000,
      "peak_demand_kw": 275,
      "carbon_emissions_tons": 390
    },
    {
      "scenario_name": "with_solar",
      "annual_cost_inr": 2950000,
      "annual_savings_vs_base_inr": 250000,
      "peak_demand_kw": 355,
      "carbon_emissions_tons": 350
    },
    {
      "scenario_name": "with_both",
      "annual_cost_inr": 2850000,
      "annual_savings_vs_base_inr": 350000,
      "peak_demand_kw": 235,
      "carbon_emissions_tons": 310
    }
  ],
  "data_quality_score": 0.92,
  "data_quality_issues": [],
  "dashboard_url": "https://app.peakstack.io/analyses/550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 6. Integration Points (How Schemas Connect to Stages)

| Stage | Input | Output |
|-------|-------|--------|
| **Data Ingestion** | `AnalysisRequest` (load_profile) | `PipelineContext` (load_profile_15min, solar_generation_15min) |
| **Forecast** | `PipelineContext` (load hourly) | `PipelineContext` (load_forecast_24h, forecast_confidence) |
| **Optimization** | `PipelineContext` (forecast) + `request` (battery config) | `PipelineContext` (optimal_dispatch, OptimizationResultSchema) |
| **Financial** | `PipelineContext` (optimal_dispatch) | `PipelineContext` (kpis_by_model: Dict[KPISchema]) |
| **Decision** | `PipelineContext` (kpis) | `PipelineContext` (recommendation: RecommendationSchema) |
| **Realism** | All above | `PipelineContext` (realistic_kpis, insights) |
| **API Response** | `PipelineContext` (all) | `AnalysisResponse` | 

---

## 7. Frontend Integration Example (React)

```javascript
// POST to /v1/analyses/analyze
const response = await fetch(`${API_BASE}/v1/analyses/analyze`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    state: 'maharashtra',
    annual_kwh_consumption: 500000,
    solar_pv_capacity_kw: 100,
    business_models: ['capex', 'eaas'],
    include_scenario_comparison: true
  })
});

const result = await response.json();

// Power UI components
<KPICard kpi={result.kpis_by_model['capex']} />
<RealisticKPICard realistic={result.realistic_kpis['capex']} />
<LineChart data={result.annual_load_chart} />
<BarChart data={result.monthly_savings_chart} />
<InsightCards insights={result.insights} />
<RecommendationCard rec={result.recommendation} />
<ScenarioComparison scenarios={result.scenarios} />
```

This design ensures:
✅ Clean separation of concerns
✅ Testable stages
✅ Direct mapping to React components
✅ No frontend guessing about data structure
✅ Scalable to SaaS (caching, background jobs, multi-tenancy)
