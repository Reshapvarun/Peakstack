"""
Pydantic models for BESS analysis API
Task #3 & #4: Request and Response schemas
"""

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
    GUJARAT = "gujarat"


class IndustryEnum(str, Enum):
    MANUFACTURING = "manufacturing"
    COMMERCIAL = "commercial"
    HOSPITALITY = "hospitality"
    OTHER = "other"


# ============= REQUEST SCHEMA (#3) =============

class AnalysisRequest(BaseModel):
    """
    Request model for /analyze endpoint
    Task #3: Fix your request model
    """
    
    # Required fields
    state: StateEnum = Field(
        ...,
        description="State code (maharashtra, karnataka, etc)"
    )
    industry: IndustryEnum = Field(
        IndustryEnum.MANUFACTURING,
        description="Industry type for load factor calculation"
    )
    battery_kwh: float = Field(
        ...,
        gt=0,
        le=2000,
        description="Battery capacity in kWh (10-2000)"
    )
    battery_power_kw: float = Field(
        ...,
        gt=0,
        le=500,
        description="Battery power rating in kW"
    )
    
    # Optional fields with defaults
    solar_kw: float = Field(
        0,
        ge=0,
        le=500,
        description="Solar PV capacity in kW (default: 0)"
    )
    load_profile: Optional[List[float]] = Field(
        None,
        description="Optional: 96 values (15-min intervals for 24h) or 8760 (hourly for 1 year). If None, use synthetic."
    )
    
    # Optional configuration
    annual_kwh: Optional[float] = Field(
        None,
        gt=0,
        description="Annual energy consumption (if load_profile not provided)"
    )
    
    analysis_name: Optional[str] = Field(
        None,
        description="Human-readable name for this analysis"
    )

    # Real-world Financial Parameters
    tariff_energy: float = Field(
        8.0,
        ge=4.0,
        le=15.0,
        description="Base energy tariff (₹/kWh)"
    )
    demand_charge: float = Field(
        300.0,
        ge=100.0,
        le=1000.0,
        description="Monthly demand charge (₹/kVA or ₹/kW)"
    )
    peak_tariff_difference: float = Field(
        3.0,
        ge=0.0,
        le=10.0,
        description="Difference between peak and off-peak tariff (₹/kWh)"
    )
    battery_cost_per_kwh: float = Field(
        18000.0,
        ge=10000.0,
        le=50000.0,
        description="Total system cost per installed kWh (₹)"
    )
    solar_cost_per_kwh: float = Field(
        3.0,
        ge=2.5,
        le=6.0,
        description="Levelized cost of solar energy (₹/kWh)"
    )
    utilization_factor: float = Field(
        0.8,
        ge=0.5,
        le=1.0,
        description="Daily battery throughput utilization factor (0.5-1.0)"
    )
    
    # Validators
    @validator('load_profile')
    def validate_load_profile(cls, v):
        if v is not None:
            if len(v) not in [96, 8760]:
                raise ValueError("Load profile must be 96 (15-min daily) or 8760 (hourly yearly) values")
            if any(x < 0 for x in v):
                raise ValueError("Load profile values must be non-negative")
        return v
    
    @validator('battery_kwh')
    def validate_battery_kwh(cls, v):
        if v < 10 or v > 2000:
            raise ValueError("Battery capacity must be 10-2000 kWh")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "state": "maharashtra",
                "battery_kwh": 250,
                "battery_power_kw": 75,
                "solar_kw": 100,
                "annual_kwh": 500000,
                "load_profile": None
            }
        }


# ============= RESPONSE SCHEMAS (#4) =============

class KPISchema(BaseModel):
    """Key Performance Indicators"""
    
    monthly_savings_inr: float = Field(
        ...,
        description="Average monthly savings in ₹"
    )
    annual_savings_inr: float = Field(
        ...,
        description="Total annual savings in ₹"
    )
    payback_years: float = Field(
        ...,
        ge=0,
        description="Years to payback (break-even)"
    )
    payback_months: float = Field(
        ...,
        description="Months to payback"
    )
    roi_percent: float = Field(
        ...,
        description="Annual ROI as percentage"
    )
    npv_10yr_inr: float = Field(
        ...,
        description="10-year NPV at 10% discount rate"
    )
    peak_demand_reduction_kw: float = Field(
        ...,
        description="Maximum kW reduction in peak demand"
    )
    peak_demand_reduction_percent: float = Field(
        ...,
        description="Peak reduction as percentage of original"
    )


class RealismSchema(BaseModel):
    """Realism calibration with confidence scoring"""
    
    theoretical_savings_inr: float = Field(
        ...,
        description="Idealized model output (no real-world adjustments)"
    )
    realistic_savings_inr: float = Field(
        ...,
        description="XAI-adjusted for real-world conditions"
    )
    realism_gap_percent: float = Field(
        ...,
        description="Gap between theoretical and realistic as percentage"
    )
    confidence_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence (0-1): how much we trust this estimate"
    )
    confidence_reason: str = Field(
        ...,
        description="Why we have this confidence level"
    )
    risk_factors: List[str] = Field(
        default=[],
        description="Risk factors reducing confidence: tariff_volatility, low_data_quality, etc"
    )
    recommended_buffer_percent: int = Field(
        default=10,
        description="Conservative buffer: use savings * (1 - buffer%)"
    )
    conservative_estimate_inr: float = Field(
        ...,
        description="Conservative savings = realistic * (1 - buffer%)"
    )


class ChartDataSchema(BaseModel):
    """Time-series chart data for frontend"""
    
    timestamps: List[str] = Field(
        ...,
        description="Time labels (e.g., ['00:00', '00:15', ...])"
    )
    load_kw: List[float] = Field(
        ...,
        description="Load profile in kW"
    )
    solar_generation_kw: List[float] = Field(
        ...,
        description="Solar generation in kW"
    )
    battery_charge_kw: List[float] = Field(
        default=[],
        description="Battery charging rate (positive = charging)"
    )
    battery_discharge_kw: List[float] = Field(
        default=[],
        description="Battery discharge rate (positive = discharging)"
    )
    battery_soc_percent: List[float] = Field(
        default=[],
        description="Battery State of Charge (%)"
    )
    grid_import_kw: List[float] = Field(
        default=[],
        description="Grid import WITH battery (optimized)"
    )
    grid_import_without_bess_kw: List[float] = Field(
        default=[],
        description="Grid import WITHOUT battery (baseline)"
    )


class InsightSchema(BaseModel):
    """Business insight from XAI engine"""
    
    time: str = Field(
        ...,
        description="Timestamp or timeframe of the insight"
    )
    explanation: str = Field(
        ...,
        description="Human-readable insight or mathematical explanation"
    )
    impact_percent: float = Field(
        default=0,
        description="Percentage impact of the primary driver"
    )
    direction: str = Field(
        ...,
        description="Direction of impact: increase, decrease, or neutral"
    )
    type: Optional[str] = Field(
        None,
        description="Type of event (peak, solar_dip, normal)"
    )


class AnalysisResponse(BaseModel):
    """
    Complete response from /analyze endpoint
    Task #4: Response structure
    """
    
    # Metadata
    analysis_id: str = Field(
        ...,
        description="Unique analysis identifier"
    )
    timestamp: datetime = Field(
        ...,
        description="When analysis was performed"
    )
    state: str
    battery_kwh: float
    battery_power_kw: float
    solar_kw: float
    
    # Core results
    kpis: KPISchema = Field(
        ...,
        description="Key performance indicators"
    )
    realism: RealismSchema = Field(
        ...,
        description="Realism calibration with confidence"
    )
    
    # Charts for frontend
    daily_chart: ChartDataSchema = Field(
        ...,
        description="Typical day profile"
    )
    yearly_chart: Optional[ChartDataSchema] = Field(
        None,
        description="Monthly aggregated profile"
    )
    
    # Insights
    insights: List[InsightSchema] = Field(
        default=[],
        description="XAI-generated business insights"
    )
    
    # Recommendation
    recommendation: str = Field(
        ...,
        description="INSTALL, INVESTIGATE, or DO_NOT_INSTALL"
    )
    recommendation_reason: str = Field(
        ...,
        description="Why this recommendation"
    )
    
    # Data quality
    data_quality_score: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Input data quality (0-1)"
    )
    data_quality_issues: List[str] = Field(
        default=[],
        description="Any data quality concerns"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-04-30T10:30:00Z",
                "state": "maharashtra",
                "battery_kwh": 250,
                "battery_power_kw": 75,
                "solar_kw": 100,
                "kpis": {
                    "monthly_savings_inr": 7500,
                    "annual_savings_inr": 90000,
                    "payback_years": 5.2,
                    "payback_months": 62.4,
                    "roi_percent": 15.3,
                    "npv_10yr_inr": 420000,
                    "peak_demand_reduction_kw": 80,
                    "peak_demand_reduction_percent": 22.5
                },
                "realism": {
                    "theoretical_savings_inr": 100000,
                    "realistic_savings_inr": 85000,
                    "realism_gap_percent": 15.0,
                    "confidence_score": 0.88,
                    "confidence_reason": "Good load data, proven tariffs",
                    "risk_factors": [],
                    "recommended_buffer_percent": 10,
                    "conservative_estimate_inr": 76500
                },
                "recommendation": "INSTALL",
                "recommendation_reason": "ROI 15.3% > 5%, payback 5.2y < 10y"
            }
        }
