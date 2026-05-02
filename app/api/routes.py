"""
Task #1 & #9: FastAPI /analyze endpoint + refactored structure
Production-ready API endpoint for BESS optimization
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import uuid

from app.schemas import (
    AnalysisRequest, AnalysisResponse, UserCreate, UserResponse, Token,
    ChartDataSchema, KPISchema, RealismSchema, InsightSchema
)
from app.pipeline import PipelineOrchestrator
from app.core.data_processor import DataProcessor
from app.core.auth import (
    get_password_hash, verify_password, create_access_token, 
    get_current_user_email, get_current_user_from_cookie
)
from app.db.session import get_db, init_db, SessionLocal
from app.db.models import User, AnalysisRecord
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import File, UploadFile, Depends, Response, BackgroundTasks
import os
import uuid
from typing import Optional, List

router = APIRouter(prefix="/api/v1", tags=["analyses"])
logger = logging.getLogger(__name__)
orchestrator = PipelineOrchestrator()
data_processor = DataProcessor()

# Initialise DB on startup
init_db()

# --- AUTH ENDPOINTS ---

@router.post("/auth/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account"""
    logger.info(f"Signup attempt for email: {user_data.email}")
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Signup failed: Email {user_data.email} already exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        hashed_pwd = get_password_hash(user_data.password)
        new_user = User(email=user_data.email, hashed_password=hashed_pwd)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User created successfully: {user_data.email}")
        return new_user
    except Exception as e:
        logger.error(f"Database error during signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during registration")

@router.post("/auth/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and set HTTP-only cookie"""
    logger.info(f"Login attempt for email: {form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: Invalid credentials for {form_data.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400, # 24 hours
        expires=86400,
        samesite="lax",
        secure=False # Set to True in production with HTTPS
    )
    
    logger.info(f"Login successful for {form_data.username}")
    return {"message": "Logged in successfully", "email": user.email}

@router.post("/auth/logout")
async def logout(response: Response):
    """Clear the auth cookie"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/auth/me", response_model=UserResponse)
async def get_me(email: str = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    """Get current authenticated user info"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
    return user



# Simple Rate Limiting (In-memory, reset on restart)
rate_limit_data = {}

def check_rate_limit(email: str, limit: int, window_seconds: int = 60):
    now = datetime.utcnow().timestamp()
    if email not in rate_limit_data:
        rate_limit_data[email] = []
    
    # Filter out old requests
    rate_limit_data[email] = [t for t in rate_limit_data[email] if now - t < window_seconds]
    
    if len(rate_limit_data[email]) >= limit:
        return False
    
    rate_limit_data[email].append(now)
    return True

@router.post("/upload-data")
async def upload_data(
    file: UploadFile = File(...),
    email: str = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Upload CSV data with security validation"""
    if not check_rate_limit(email, 10): # 10 uploads per min
        raise HTTPException(status_code=429, detail="Too many uploads. Please wait.")

    # Validate file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    os.makedirs("data/uploads", exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = f"data/uploads/{file_id}.csv"
    
    # Limit file size to 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
    with open(file_path, "wb") as f:
        f.write(content)
        
    try:
        # Validate CSV Schema
        import pandas as pd
        df = pd.read_csv(file_path)
        required_cols = ['load_kw', 'solar_kw'] # User requirement
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
             os.remove(file_path)
             raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")

        preview = await data_processor.process_csv(file_path)
        return {"file_id": file_id, "preview": preview}
    except Exception as e:
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

@router.post(
    "/analyze",
    status_code=202,
    summary="Analyze BESS (Background Job)",
)
async def analyze(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    email: str = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
) -> dict:
    """Protected analysis orchestration (Background Job)"""
    if not check_rate_limit(email, 5): # 5 analyses per min
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 1. Create Job Record
    job_id = str(uuid.uuid4())
    analysis_record = AnalysisRecord(
        id=None,
        user_id=user.id,
        status="processing",
        analysis_name=request.analysis_name or f"Analysis {job_id[:8]}",
        csv_file_id=request.csv_file_id,
        inputs=request.dict()
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)
    
    # 2. Run heavy logic in background
    background_tasks.add_task(
        _run_heavy_analysis,
        job_record_id=analysis_record.id,
        request=request
    )
    
    return {
        "job_id": analysis_record.id,
        "status": "processing",
        "message": "Analysis started in background"
    }

def _run_heavy_analysis(job_record_id: int, request: AnalysisRequest):
    """Background execution of the full pipeline (runs in threadpool)"""
    import asyncio
    logger.info(f"[Worker] Starting heavy analysis for job {job_record_id} (use_real_data={request.use_real_data})")
    print(f"DEBUG: use_real_data={request.use_real_data}")
    
    db = SessionLocal()
    try:
        # Define a callback to update DB status
        async def update_job_status(new_status: str):
            temp_db = SessionLocal()
            try:
                record = temp_db.query(AnalysisRecord).filter(AnalysisRecord.id == job_record_id).first()
                if record:
                    record.status = new_status
                    temp_db.commit()
            finally:
                temp_db.close()

        # Run the async pipeline in a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pipeline_context = loop.run_until_complete(orchestrator.run(request, status_callback=update_job_status))
        loop.close()
        
        logger.info(f"[Worker] Pipeline finished for job {job_record_id}. Building response...")
        response_data = _build_analysis_response(job_record_id, request, pipeline_context)
        
        # Update record
        record = db.query(AnalysisRecord).filter(AnalysisRecord.id == job_record_id).first()
        record.status = "completed"
        # Ensure result is JSON serializable (converts datetimes to strings)
        record.results = response_data.model_dump(mode='json')
        db.commit()
        logger.info(f"[Worker] Job {job_record_id} marked as completed")
        
    except Exception as e:
        logger.error(f"[Worker] Job {job_record_id} failed: {str(e)}", exc_info=True)
        try:
            record = db.query(AnalysisRecord).filter(AnalysisRecord.id == job_record_id).first()
            if record:
                record.status = "failed"
                record.error_message = str(e)
                db.commit()
        except Exception as db_err:
            logger.error(f"[Worker] Critical DB failure while marking job as failed: {str(db_err)}")
    finally:
        db.close()

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: int, email: str = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    """Poll job status and get results if ready"""
    user = db.query(User).filter(User.email == email).first()
    job = db.query(AnalysisRecord).filter(AnalysisRecord.id == job_id, AnalysisRecord.user_id == user.id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "error": job.error_message,
        "results": job.results if job.status == "completed" else None
    }



@router.get("/analyses", response_model=list[dict])
async def list_analyses(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)):
    """List all previous analyses for the current user"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    analyses = db.query(AnalysisRecord).filter(AnalysisRecord.user_id == user.id).all()
    return [{"id": a.id, "name": a.analysis_name, "timestamp": a.timestamp} for a in analyses]

@router.post("/dispatch", response_model=dict)
async def get_dispatch_schedule(request: AnalysisRequest, email: str = Depends(get_current_user_email)):
    """Get detailed dispatch schedule for a configuration"""
    try:
        pipeline_context = await orchestrator.run(request)
        return {
            "analysis_id": str(uuid.uuid4()),
            "schedule": pipeline_context.optimal_dispatch.get('schedule', []),
            "summary": {
                "total_savings": pipeline_context.realistic_savings_inr,
                "confidence": pipeline_context.confidence_score
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Retrieve Previous Analysis"
)
async def get_analysis(
    analysis_id: int, 
    email: str = Depends(get_current_user_email), 
    db: Session = Depends(get_db)
) -> AnalysisResponse:
    """
    GET /api/v1/analyses/{analysis_id}
    
    Retrieve stored analysis result
    """
    user = db.query(User).filter(User.email == email).first()
    analysis = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == analysis_id, 
        AnalysisRecord.user_id == user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis.results


# ============= HELPER FUNCTIONS =============

def _calculate_peak_reduction_percent(peak_reduction_kw: float, battery_kwh: float) -> float:
    """Calculate peak reduction as percentage"""
    if battery_kwh <= 0:
        return 0.0
    
    # Assume baseline peak demand ~ 4x battery capacity
    baseline_peak = battery_kwh * 4
    return (peak_reduction_kw / baseline_peak * 100) if baseline_peak > 0 else 0.0


def _generate_daily_chart(load_profile, solar_profile, dispatch) -> ChartDataSchema:
    """Generate typical day chart data with 96 intervals (15-min)"""
    
    # Ensure we have 96 intervals
    load_96 = load_profile[-96:] if len(load_profile) >= 96 else (load_profile + [0] * (96 - len(load_profile)))
    solar_96 = solar_profile[-96:] if len(solar_profile) >= 96 else (solar_profile + [0] * (96 - len(solar_profile)))
    
    # Generate timestamps (00:00, 00:15, ...)
    timestamps = []
    for h in range(24):
        for m in [0, 15, 30, 45]:
            timestamps.append(f"{h:02d}:{m:02d}")
    
    # Generate dispatch data
    battery_charge = dispatch.get('charge', [0] * 96)
    battery_discharge = dispatch.get('discharge', [0] * 96)
    
    # Requirement: Discharge should be negative for bars if frontend doesn't handle it
    # But usually, it's better to provide raw values and let frontend decide.
    # User said "Discharge (negative bars)", so I'll provide them as negative.
    battery_discharge_neg = [-x for x in battery_discharge]
    
    soc = dispatch.get('soc', [50] * 96)
    
    # Calculate grid import
    grid_import = []
    grid_import_no_bess = []
    for i in range(96):
        grid_no_bess = max(0, load_96[i] - solar_96[i])
        grid_with_bess = max(0, load_96[i] - solar_96[i] + battery_charge[i] - battery_discharge[i])
        grid_import_no_bess.append(grid_no_bess)
        grid_import.append(grid_with_bess)
    
    return ChartDataSchema(
        timestamps=timestamps,
        load_kw=load_96,
        solar_generation_kw=solar_96,
        battery_charge_kw=battery_charge,
        battery_discharge_kw=battery_discharge_neg,
        battery_soc_percent=soc,
        grid_import_kw=grid_import,
        grid_import_without_bess_kw=grid_import_no_bess,
        dg_offset_kw=dispatch.get('dg_offset', [0] * 96)
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


def _build_analysis_response(job_id: int, request: AnalysisRequest, pipeline_context) -> AnalysisResponse:
    """Helper to build AnalysisResponse from pipeline context"""
    return AnalysisResponse(
        analysis_id=str(job_id),
        timestamp=datetime.utcnow(),
        state=request.state.value,
        battery_kwh=request.battery_kwh,
        battery_power_kw=request.battery_power_kw,
        solar_kw=request.solar_kw,
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
        daily_chart=_generate_daily_chart(
            pipeline_context.load_profile_hourly or [],
            pipeline_context.solar_forecast_24h or [],
            pipeline_context.optimal_dispatch or {}
        ),
        yearly_chart=_generate_yearly_chart(
            pipeline_context.load_profile_15min or []
        ),
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
        recommendation=pipeline_context.recommendation,
        recommendation_reason=pipeline_context.recommendation_reason,
        data_quality_score=pipeline_context.data_quality_score,
        data_quality_issues=pipeline_context.data_quality_issues,
        healing_logs=getattr(pipeline_context, 'healing_logs', []),
        recommended_sizing=pipeline_context.recommended_sizing,
        dg_savings=pipeline_context.dg_savings_meta if hasattr(pipeline_context, 'dg_savings_meta') else None,
        scenarios=pipeline_context.scenarios,
        sensitivity=pipeline_context.sensitivity
    )

async def _store_analysis_result(analysis_id: str, user_id: int, request: AnalysisRequest, response: AnalysisResponse):
    """Background task: store analysis result in database"""
    logger.info(f"[Background] Storing analysis {analysis_id} for user {user_id}")
    
    db = SessionLocal()
    try:
        record = AnalysisRecord(
            id=None, # Auto-increment
            user_id=user_id,
            analysis_name=request.analysis_name or f"Analysis {analysis_id[:8]}",
            csv_file_id=request.csv_file_id,
            inputs=request.dict(),
            results=response.dict()
        )
        db.add(record)
        db.commit()
        logger.info(f"[Background] Successfully stored analysis {analysis_id}")
    except Exception as e:
        logger.error(f"[Background] Failed to store analysis {analysis_id}: {str(e)}")
    finally:
        db.close()
