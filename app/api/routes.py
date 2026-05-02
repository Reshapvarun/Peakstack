"""
Task #1 & #9: FastAPI /analyze endpoint + refactored structure
Production-ready API endpoint for BESS optimization
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import uuid

from app.schemas import AnalysisRequest, AnalysisResponse, ChartDataSchema, KPISchema, RealismSchema, InsightSchema
from app.pipeline import PipelineOrchestrator

router = APIRouter(prefix="/api/v1", tags=["analyses"])
logger = logging.getLogger(__name__)
orchestrator = PipelineOrchestrator()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze BESS Investment Opportunity",
    description="Full pipeline: ingestion → simulation → optimizer → finance → decision → realism"
)
async def analyze(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks = None
) -> AnalysisResponse:
    """
    Task #1 & #9: Production-ready /analyze endpoint
    
    POST /api/v1/analyze
    
    Example request:
    {
        "state": "maharashtra",
        "battery_kwh": 250,
        "battery_power_kw": 75,
        "solar_kw": 100,
        "annual_kwh": 500000
    }
    
    Returns: Full analysis response with KPIs, realism, charts, insights
    """
    
    analysis_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[API] /analyze request: state={request.state}, battery={request.battery_kwh}kWh, solar={request.solar_kw}kW")
        
        # Validate request
        validation_errors = request.load_profile is not None and any(x < 0 for x in request.load_profile)
        if validation_errors:
            raise ValueError("Load profile values must be non-negative")
        
        # Run pipeline
        pipeline_context = await orchestrator.run(request)
        
        # Build response
        response = AnalysisResponse(
            analysis_id=analysis_id,
            timestamp=datetime.utcnow(),
            state=request.state.value,
            battery_kwh=request.battery_kwh,
            battery_power_kw=request.battery_power_kw,
            solar_kw=request.solar_kw,
            
            # KPIs
            kpis=KPISchema(
                monthly_savings_inr=pipeline_context.monthly_savings_inr,
                annual_savings_inr=pipeline_context.annual_savings_inr,
                payback_years=pipeline_context.payback_years,
                payback_months=pipeline_context.payback_months,
                roi_percent=pipeline_context.roi_percent,
                npv_10yr_inr=pipeline_context.npv_10yr_inr,
                peak_demand_reduction_kw=pipeline_context.peak_reduction_kw,
                peak_demand_reduction_percent=_calculate_peak_reduction_percent(
                    pipeline_context.peak_reduction_kw,
                    request.battery_kwh
                )
            ),
            
            # Realism calibration
            realism=RealismSchema(
                theoretical_savings_inr=pipeline_context.theoretical_savings_inr,
                realistic_savings_inr=pipeline_context.realistic_savings_inr,
                realism_gap_percent=pipeline_context.realism_gap_percent,
                confidence_score=pipeline_context.confidence_score,
                confidence_reason=pipeline_context.confidence_reason,
                risk_factors=pipeline_context.risk_factors,
                recommended_buffer_percent=pipeline_context.recommended_buffer_percent,
                conservative_estimate_inr=int(
                    pipeline_context.realistic_savings_inr * 
                    (1 - pipeline_context.recommended_buffer_percent / 100)
                )
            ),
            
            # Charts
            daily_chart=_generate_daily_chart(
                pipeline_context.load_profile_hourly or [],
                pipeline_context.solar_forecast_24h or [],
                pipeline_context.optimal_dispatch or {}
            ),
            yearly_chart=_generate_yearly_chart(
                pipeline_context.load_profile_15min or []
            ),
            
            # Insights
            insights=[
                InsightSchema(
                    time=insight['time'],
                    explanation=insight['explanation'],
                    direction=insight['direction'],
                    impact_percent=insight.get('impact_percent', 0.0),
                    type=insight.get('type')
                )
                for insight in pipeline_context.insights
            ],
            
            # Recommendation
            recommendation=pipeline_context.recommendation,
            recommendation_reason=pipeline_context.recommendation_reason,
            
            # Data quality
            data_quality_score=pipeline_context.data_quality_score,
            data_quality_issues=pipeline_context.data_quality_issues
        )
        
        logger.info(f"[API] Analysis {analysis_id} completed: recommendation={response.recommendation}")
        
        # Optional: Store in background
        if background_tasks:
            background_tasks.add_task(
                _store_analysis_result,
                analysis_id=analysis_id,
                response=response
            )
        
        return response
        
    except ValueError as e:
        logger.warning(f"[API] Validation error: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail={"error": "Validation error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"[API] Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Analysis failed",
                "analysis_id": analysis_id,
                "message": str(e)
            }
        )


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Retrieve Previous Analysis"
)
async def get_analysis(analysis_id: str) -> AnalysisResponse:
    """
    GET /api/v1/analyses/{analysis_id}
    
    Retrieve cached analysis result (future: from database)
    """
    
    logger.info(f"[API] GET /analyses/{analysis_id}")
    
    # TODO: Implement caching/database storage
    raise HTTPException(
        status_code=404,
        detail="Analysis not found. Currently analyses are not persisted."
    )


# ============= HELPER FUNCTIONS =============

def _calculate_peak_reduction_percent(peak_reduction_kw: float, battery_kwh: float) -> float:
    """Calculate peak reduction as percentage"""
    if battery_kwh <= 0:
        return 0.0
    
    # Assume baseline peak demand ~ 4x battery capacity
    baseline_peak = battery_kwh * 4
    return (peak_reduction_kw / baseline_peak * 100) if baseline_peak > 0 else 0.0


def _generate_daily_chart(load_hourly, solar_24h, dispatch) -> ChartDataSchema:
    """Generate typical day chart data"""
    
    # Ensure we have 24 hours of data
    load_24h = load_hourly[-24:] if len(load_hourly) >= 24 else (load_hourly + [0] * (24 - len(load_hourly)))
    solar_24h = solar_24h[:24] if len(solar_24h) >= 24 else (solar_24h + [0] * (24 - len(solar_24h)))
    
    # Generate timestamps
    timestamps = [f"{h:02d}:00" for h in range(24)]
    
    # Generate dispatch data (charging/discharging)
    battery_charge = dispatch.get('charge', [0] * 24)[:24]
    battery_discharge = dispatch.get('discharge', [0] * 24)[:24]
    
    # Calculate SOC (simple: starts at 50%)
    soc = [50]
    for i in range(24):
        change = battery_discharge[i] - battery_charge[i]  # Discharge reduces, charge increases
        soc.append(max(20, min(100, soc[-1] + change)))
    soc = soc[1:]  # Remove first dummy value
    
    # Calculate grid import (load - solar - discharge + charge)
    grid_import = []
    grid_import_no_bess = []
    for i in range(24):
        grid_no_bess = max(0, load_24h[i] - solar_24h[i])
        grid_with_bess = max(0, load_24h[i] - solar_24h[i] + battery_charge[i] - battery_discharge[i])
        grid_import_no_bess.append(grid_no_bess)
        grid_import.append(grid_with_bess)
    
    return ChartDataSchema(
        timestamps=timestamps,
        load_kw=load_24h,
        solar_generation_kw=solar_24h,
        battery_charge_kw=battery_charge,
        battery_discharge_kw=battery_discharge,
        battery_soc_percent=soc,
        grid_import_kw=grid_import,
        grid_import_without_bess_kw=grid_import_no_bess
    )


def _generate_yearly_chart(load_profile_15min) -> ChartDataSchema:
    """Generate monthly aggregated chart"""
    
    if not load_profile_15min:
        return None
    
    # Convert to monthly (rough: divide into 12 months)
    points_per_month = len(load_profile_15min) // 12
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    monthly_load = []
    for month in range(12):
        start = month * points_per_month
        end = start + points_per_month if month < 11 else len(load_profile_15min)
        monthly_avg = sum(load_profile_15min[start:end]) / (end - start) if end > start else 0
        monthly_load.append(monthly_avg)
    
    return ChartDataSchema(
        timestamps=months,
        load_kw=monthly_load,
        solar_generation_kw=[0] * 12,  # TODO: Calculate from solar data
        battery_charge_kw=[0] * 12,
        battery_discharge_kw=[0] * 12,
        battery_soc_percent=[50] * 12
    )


async def _store_analysis_result(analysis_id: str, response: AnalysisResponse):
    """Background task: store analysis result (future: database)"""
    # TODO: Implement database storage
    logger.info(f"[Background] Storing analysis {analysis_id}")
    pass
