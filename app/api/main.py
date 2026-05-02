from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Request
from fastapi.exceptions import RequestValidationError
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

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="Peakstack Energy OS", version="2.0.0-saas")

# Restricted CORS for SaaS production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with actual domain
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include production routes
app.include_router(analysis_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"VALIDATION ERROR: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"GLOBAL ERROR: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": str(exc)}
    )

@app.get("/api/v1/test")
def test_route():
    return {"message": "API is working"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0-saas"}

# --- SINGLE DOMAIN SERVING ---

# Serve Frontend Static Files
dist_path = "peakstack-ui/dist"
if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=f"{dist_path}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Check if the request is for an API route
        if full_path.startswith("api/v1") or full_path == "health":
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        
        # Serve index.html for all other routes to support React Router (SPA)
        index_file = os.path.join(dist_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        
        return JSONResponse(status_code=404, content={"detail": "Frontend build not found"})
else:
    logger.warning("Frontend build not found at peakstack-ui/dist. Run 'npm run build' first.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
