from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AnalysisRequest(BaseModel):
    state: str = Field(..., description="Indian state for policy mapping")
    battery_capacity_kwh: float = Field(..., description="BESS capacity in kWh")
    battery_power_kw: float = Field(..., description="BESS max power in kW")
    solar_capacity_kw: float = Field(..., description="Solar capacity in kW")
    wind_capacity_kw: float = Field(..., description="Wind capacity in kW")
    net_metering_enabled: bool = False
    include_emerging_tech: bool = False
    mode: str = Field("demo", description="Data mode: 'demo' or 'real'")
    csv_file_path: Optional[str] = None
    fast_mode: bool = False # Toggle for fast ROI calculations (skips XAI/PDF)

class AnalysisResponse(BaseModel):
    summary: Dict[str, Any] # Top-level business KPIs (Savings, Payback, Peak Red)
    results: Dict[str, Any] # Time-series data for charts
    recommendation: Dict[str, Any] # Optimal size, confidence, reasoning
    report_meta: Dict[str, Any] # Metadata for PDF generation
    policy_applied: Dict[str, Any] # Details of the state policy used
    business_models: List[Dict[str, Any]] = [] # Comparison of CAPEX/EaaS/Hybrid models
    bill_breakdown: Optional[Dict[str, Any]] = None # Monthly bill detailed breakdown
    report_id: Optional[str] = None # ID of the generated PDF report


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
