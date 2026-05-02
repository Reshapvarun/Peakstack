"""
Production Pydantic Models for BESS Analysis API
TASKS #3 & #4: Request & Response Schemas

Includes:
- AnalysisRequest: Input validation
- AnalysisResponse: Frontend-friendly output
- Intermediate schemas: KPI, Realism, ChartData, Insights
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


# ============= ENUMS =============

class StateEnum(str, Enum):
    """Indian states for policy/tariff lookup"""
    MAHARASHTRA = "maharashtra"
    KARNATAKA = "karnataka"
    TAMIL_NADU = "tamil_nadu"
    DELHI = "delhi"
    RAJASTHAN = "rajasthan"
    ANDHRA_PRADESH = "andhra_pradesh"
    GUJARAT = "gujarat"


# ============= TASK #3: REQUEST MODEL =============

class AnalysisRequest(BaseModel):
    """
    Request model for /analyze endpoint
    Validates input parameters for energy storage optimization analysis
    """

    # ========== Required Fields ==========

    state: StateEnum = Field(
        ...,
        description="Indian state (for policy, tariff, solar irradiance lookup)"
    )

    battery_kwh: float = Field(
        ...,
        gt=0,
        le=2000,
        description="Battery capacity in kWh (10-2000 range)"
    )

    battery_power_kw: float = Field(
        ...,
        gt=0,
        le=500,
        description="Battery power rating in kW (max charge/discharge rate)"
    )

    # ========== Optional Fields ==========

    solar_kw: float = Field(
        0,
        ge=0,
        le=500,
        description="Solar PV capacity in kW (default: 0, no solar)"
    )

    load_profile: Optional[List[float]] = Field(
        None,
        description=(
            "Custom load profile: 96 values (15-min intervals for 1 day) "
            "or 8760 values (hourly for 1 year). "
            "If None, uses synthetic profile based on annual_kwh."
        )
    )

    annual_kwh: Optional[float] = Field(
        None,
        gt=0,
        description="Annual energy consumption in kWh (used if load_profile not provided)"
    )

    analysis_name: Optional[str] = Field(
        None,
        description="Human-readable name for this analysis (e.g., 'Q4_2024_scenario')"
    )

    # ========== Validators ==========

    @validator('load_profile')
    def validate_load_profile(cls, v):
        """Load profile must be 96 or 8760 points, all non-negative"""
        if v is not None:
            if len(v) not in [96, 8760]:
                raise ValueError(
                    f"Load profile must have 96 (15-min daily) or 8760 (hourly yearly) values, "
                    f"got {len(v)}"
                )
            if any(x < 0 for x in v):
                raise ValueError("All load profile values must be non-negative (≥ 0)")
        return v

    @validator('battery_kwh')
    def validate_battery_kwh(cls, v):
        """Battery capacity must be realistic"""
        if v < 10 or v > 2000:
            raise ValueError(f"Battery capacity must be 10-2000 kWh, got {v}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "state": "maharashtra",
                "battery_kwh": 250,
                "battery_power_kw": 75,
                "solar_kw": 100,
                "annual_kwh": 500000,
                "load_profile": None,
                "analysis_name": "Factory_Scenario_1"
            }
        }


# ============= TASK #4: RESPONSE SCHEMAS =============

class KPISchema(BaseModel):
    """Key Performance Indicators for investor presentation"""

    monthly_savings_inr: float = Field(
        ...,
        description="Average monthly savings in ₹"
    )
    annual_savings_inr: float = Field(
        ...,
        description="Total annual savings in ₹/year"
    )
    payback_years: float = Field(
        ...,
        ge=0,
        description="Break-even period in years"
    )
    payback_months: float = Field(
        ...,
        description="Break-even period in months"
    )
    roi_percent: float = Field(
        ...,
        description="Annual Return on Investment (%)"
    )
    npv_10yr_inr: float = Field(
        ...,
        description="10-year Net Present Value @ 10% discount rate (₹)"
    )
    peak_demand_reduction_kw: float = Field(
        ...,
        description="Maximum kW reduction in peak demand"
    )
    peak_demand_reduction_percent: float = Field(
        ...,
        description="Peak reduction as % of original peak"
    )


class RealismSchema(BaseModel):
    """
    Realism Calibration: confidence scoring + risk factors
    MOAT: Competitor tools show theoretical 100K, we show realistic 65K
    """

    theoretical_savings_inr: float = Field(
        ...,
        description="Idealized model output (no real-world adjustments)"
    )
    realistic_savings_inr: float = Field(
        ...,
        description="XAI-adjusted for real-world conditions (state-specific, data quality, risks)"
    )
    realism_gap_percent: float = Field(
        ...,
        description="Gap between theoretical and realistic as %"
    )
    confidence_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence 0-1: how much we trust this estimate (0.3-0.95 typical range)"
    )
    confidence_reason: str = Field(
        ...,
        description="Human-readable explanation of confidence score"
    )
    risk_factors: List[str] = Field(
        default=[],
        description=(
            "Risk factors reducing savings: "
            "low_data_quality, forecast_uncertainty, unproven_large_battery, tariff_volatility"
        )
    )
    recommended_buffer_percent: int = Field(
        default=10,
        description="Conservative buffer: use savings * (1 - buffer%/100)"
    )
    conservative_estimate_inr: float = Field(
        ...,
        description="Conservative savings for investor deck = realistic * (1 - buffer%)"
    )


class ChartDataSchema(BaseModel):
    """Time-series data for frontend charts"""

    timestamps: List[str] = Field(
        ...,
        description="Time labels: ['00:00', '00:15', ..., '23:45'] (96 points) or monthly"
    )
    load_kw: List[float] = Field(
        ...,
        description="Load profile (kW)"
    )
    solar_generation_kw: List[float] = Field(
        ...,
        description="Solar PV generation (kW)"
    )
    battery_charge_kw: List[float] = Field(
        default=[],
        description="Battery charging (positive = charging)"
    )
    battery_discharge_kw: List[float] = Field(
        default=[],
        description="Battery discharging (positive = discharging)"
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
        description="Grid import WITHOUT battery (baseline for comparison)"
    )


class InsightSchema(BaseModel):
    """Business insight from XAI engine"""

    type: str = Field(
        ...,
        description="Type: peak_shaving, arbitrage, solar_buffering, demand_response, etc"
    )
    description: str = Field(
        ...,
        description="Human-readable insight for investor presentation"
    )
    impact_inr: float = Field(
        ...,
        description="Financial impact (₹/year)"
    )
    impact_percent: float = Field(
        default=0,
        description="Percentage of total savings"
    )


class AnalysisResponse(BaseModel):
    """
    Complete response from /analyze endpoint
    TASK #4: Response structure for frontend integration
    """

    # ========== Metadata ==========

    analysis_id: str = Field(
        ...,
        description="Unique analysis identifier (UUID)"
    )
    timestamp: datetime = Field(
        ...,
        description="When analysis was performed (ISO format)"
    )
    state: str
    battery_kwh: float
    battery_power_kw: float
    solar_kw: float

    # ========== Core Results ==========

    kpis: KPISchema = Field(
        ...,
        description="Key performance indicators for investor presentation"
    )

    realism: RealismSchema = Field(
        ...,
        description="Realism calibration with confidence scoring"
    )

    # ========== Charts for Frontend ==========

    daily_chart: ChartDataSchema = Field(
        ...,
        description="Typical day profile (96 points x 15 min)"
    )

    yearly_chart: Optional[ChartDataSchema] = Field(
        None,
        description="Monthly aggregated profile (12 months)"
    )

    # ========== Insights ==========

    insights: List[InsightSchema] = Field(
        default=[],
        description="XAI-generated business insights"
    )

    # ========== Recommendation ==========

    recommendation: str = Field(
        ...,
        description="INSTALL, INVESTIGATE, or DO_NOT_INSTALL"
    )
    recommendation_reason: str = Field(
        ...,
        description="Why this recommendation (investor-friendly)"
    )

    # ========== Data Quality ==========

    data_quality_score: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Data quality 0-1 (affects confidence)"
    )
    data_quality_issues: List[str] = Field(
        default=[],
        description="Issues found in input data"
    )

    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "state": "maharashtra",
                "battery_kwh": 250,
                "battery_power_kw": 75,
                "solar_kw": 100,
                "kpis": {
                    "monthly_savings_inr": 18500,
                    "annual_savings_inr": 222000,
                    "payback_years": 6.8,
                    "payback_months": 81.6,
                    "roi_percent": 14.8,
                    "npv_10yr_inr": 1250000,
                    "peak_demand_reduction_kw": 65,
                    "peak_demand_reduction_percent": 32.5
                },
                "realism": {
                    "theoretical_savings_inr": 280000,
                    "realistic_savings_inr": 222000,
                    "realism_gap_percent": 20.7,
                    "confidence_score": 0.82,
                    "confidence_reason": "High-quality load data, moderate confidence in estimates.",
                    "risk_factors": ["forecast_uncertainty"],
                    "recommended_buffer_percent": 12,
                    "conservative_estimate_inr": 195360
                },
                "daily_chart": {
                    "timestamps": ["00:00", "00:15", "00:30", "..."],
                    "load_kw": [50, 48, 52, "..."],
                    "solar_generation_kw": [0, 0, 0, "..."],
                    "battery_soc_percent": [80, 80, 80, "..."]
                },
                "insights": [
                    {
                        "type": "peak_shaving",
                        "description": "Peak demand reduction of 65 kW during 6PM-10PM, saving demand charges",
                        "impact_inr": 133200,
                        "impact_percent": 60
                    }
                ],
                "recommendation": "INSTALL",
                "recommendation_reason": "ROI 14.8% > 5% threshold, payback 6.8y < 10y threshold",
                "data_quality_score": 0.92
            }
        }
