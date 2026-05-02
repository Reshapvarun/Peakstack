# API Reference: /analyze Endpoint

## POST /api/v1/analyze

Analyzes BESS investment opportunity through 6-stage pipeline.

---

## Request

### URL
```
POST http://localhost:8000/api/v1/analyze
Content-Type: application/json
```

### Payload Example

```json
{
  "state": "maharashtra",
  "battery_kwh": 250,
  "battery_power_kw": 75,
  "solar_kw": 100,
  "annual_kwh": 500000,
  "load_profile": null,
  "analysis_name": "Factory_Scenario_Q4_2024"
}
```

### Field Descriptions

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `state` | enum | ✅ | maharashtra, karnataka, tamil_nadu, delhi, rajasthan, andhra_pradesh, gujarat | Indian state for policy/tariff lookup |
| `battery_kwh` | float | ✅ | 10-2000 | Battery capacity in kWh |
| `battery_power_kw` | float | ✅ | 1-500 | Battery max charge/discharge rate |
| `solar_kw` | float | ❌ | 0-500, default=0 | Solar PV capacity in kW |
| `annual_kwh` | float | ❌ | >0 | Annual consumption (ignored if load_profile provided) |
| `load_profile` | array | ❌ | 96 or 8760 floats | 15-min daily (96) or hourly yearly (8760) load data |
| `analysis_name` | string | ❌ | - | Human-readable name for records |

---

## Response

### Status Code
- `200 OK` — Success
- `422 Unprocessable Entity` — Validation error
- `500 Internal Server Error` — Pipeline failure

### Success Response (200)

```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-30T10:30:00Z",
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
    "confidence_reason": "High-quality load data, proven Maharashtra tariffs, forecast uncertainty present",
    "risk_factors": ["forecast_uncertainty"],
    "recommended_buffer_percent": 12,
    "conservative_estimate_inr": 195360
  },
  
  "daily_chart": {
    "timestamps": [
      "00:00", "00:15", "00:30", "00:45",
      "01:00", "01:15", "01:30", "01:45",
      "...",
      "23:00", "23:15", "23:30", "23:45"
    ],
    "load_kw": [
      50.2, 48.5, 52.1, 49.8, 51.3, 47.2, 49.5, 48.9,
      "...",
      280.5, 290.2, 285.8, 292.1
    ],
    "solar_generation_kw": [
      0, 0, 0, 0, 0, 0, 0, 0,
      "...",
      35.2, 28.5, 15.2, 0
    ],
    "battery_charge_kw": [
      50, 48, 45, 42, 0, 0, 0, 0,
      "...",
      0, 0, 0, 0
    ],
    "battery_discharge_kw": [
      0, 0, 0, 0, 15, 18, 22, 20,
      "...",
      65, 70, 68, 62
    ],
    "battery_soc_percent": [
      70, 75, 80, 85, 88, 85, 78, 72,
      "...",
      45, 35, 28, 22
    ],
    "grid_import_kw": [
      40, 35, 42, 38, 50, 52, 48, 55,
      "...",
      150, 165, 172, 185
    ],
    "grid_import_without_bess_kw": [
      50, 48, 52, 50, 65, 70, 70, 75,
      "...",
      215, 235, 240, 247
    ]
  },
  
  "yearly_chart": {
    "timestamps": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "load_kw": [42000, 38000, 45000, 50000, 52000, 55000,
                 58000, 57000, 52000, 48000, 42000, 40000],
    "solar_generation_kw": [8000, 9000, 12000, 14000, 15000, 16000,
                            15000, 14000, 12000, 10000, 8000, 7000],
    "battery_charge_kw": [3000, 3200, 3500, 3800, 4000, 4200,
                          4100, 4000, 3500, 3200, 3000, 2800],
    "battery_discharge_kw": [2800, 2900, 3000, 3200, 3500, 3800,
                             3700, 3600, 3200, 3000, 2900, 2700]
  },
  
  "insights": [
    {
      "type": "peak_shaving",
      "description": "Battery discharges 65 kW during 5PM-10PM peak demand window, reducing peak charge by 32.5%",
      "impact_inr": 133200,
      "impact_percent": 60
    },
    {
      "type": "solar_buffering",
      "description": "Stores 250 kWh excess solar generation daily to shift from peak hours, reducing grid dependency",
      "impact_inr": 55500,
      "impact_percent": 25
    },
    {
      "type": "energy_arbitrage",
      "description": "Charges during off-peak hours (1AM-6AM, ₹3/kWh) and discharges during peak (5PM-10PM, ₹9/kWh)",
      "impact_inr": 33300,
      "impact_percent": 15
    }
  ],
  
  "recommendation": "INSTALL",
  "recommendation_reason": "ROI 14.8% > 5% threshold, payback period 6.8 years < 10 year threshold. Strong financial case with state incentives.",
  
  "data_quality_score": 0.92,
  "data_quality_issues": []
}
```

---

## Response Field Descriptions

### Metadata
- `analysis_id`: UUID for result tracking
- `timestamp`: ISO 8601 datetime of analysis
- `state`, `battery_kwh`, `battery_power_kw`, `solar_kw`: Echo of input

### KPIs (Key Performance Indicators)
- `monthly_savings_inr`: Avg monthly savings (₹)
- `annual_savings_inr`: Annual savings (₹)
- `payback_years`: Break-even period (years)
- `payback_months`: Break-even period (months)
- `roi_percent`: Annual return on investment (%)
- `npv_10yr_inr`: 10-year NPV @ 10% discount (₹)
- `peak_demand_reduction_kw`: Max kW reduction in peak (kW)
- `peak_demand_reduction_percent`: Peak reduction as % (%)

### Realism (XAI Calibration)
- `theoretical_savings_inr`: Idealized model output (₹)
- `realistic_savings_inr`: Adjusted for real-world conditions (₹)
- `realism_gap_percent`: (theoretical - realistic) / theoretical (%)
- `confidence_score`: Confidence in estimates (0-1 scale, 0.3-0.95 typical)
- `confidence_reason`: Why we have this confidence level (text)
- `risk_factors`: List of risks reducing savings (array)
- `recommended_buffer_percent`: Conservative buffer for investors (%)
- `conservative_estimate_inr`: Investor deck savings = realistic * (1 - buffer/100) (₹)

### Charts (Time-Series Data)
- `daily_chart`: Typical 24-hour profile (96 x 15-min intervals)
  - `timestamps[]`: ["00:00", "00:15", ..., "23:45"]
  - `load_kw[]`: Hourly consumption profile
  - `solar_generation_kw[]`: Solar generation profile
  - `battery_charge_kw[]`: Charging rate (positive)
  - `battery_discharge_kw[]`: Discharging rate (positive)
  - `battery_soc_percent[]`: State of charge (0-100%)
  - `grid_import_kw[]`: Grid import WITH battery (optimized)
  - `grid_import_without_bess_kw[]`: Grid import WITHOUT battery (baseline)

- `yearly_chart`: Monthly aggregated profile (12 months)
  - Similar fields as `daily_chart`

### Insights (XAI-Generated)
Array of actionable insights:
- `type`: peak_shaving, arbitrage, solar_buffering, demand_response
- `description`: Human-readable explanation
- `impact_inr`: Annual financial impact (₹)
- `impact_percent`: Percentage of total savings (%)

### Recommendation
- `recommendation`: "INSTALL", "INVESTIGATE", or "DO_NOT_INSTALL"
- `recommendation_reason`: Threshold-based justification (text)

### Data Quality
- `data_quality_score`: 0-1 (affects confidence)
- `data_quality_issues`: List of problems found

---

## Error Response (422)

```json
{
  "detail": "Battery capacity must be 10-2000 kWh"
}
```

---

## Error Response (500)

```json
{
  "detail": {
    "error": "Analysis failed",
    "analysis_id": "550e8400-...",
    "message": "Stage 3 Optimization failed: PuLP solver error"
  }
}
```

---

## cURL Examples

### Basic Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "state": "maharashtra",
    "battery_kwh": 250,
    "battery_power_kw": 75,
    "solar_kw": 100,
    "annual_kwh": 500000
  }'
```

### With Load Profile (96 points)

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "state": "karnataka",
    "battery_kwh": 150,
    "battery_power_kw": 50,
    "solar_kw": 75,
    "load_profile": [50, 48, 52, 49, ..., 280, 290, 285, 292]
  }'
```

### Pretty Print Response

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"state": "maharashtra", "battery_kwh": 250, ...}' | jq .
```

---

## Response Time

- **Typical:** 5-10 seconds
- **With large load profile:** 10-15 seconds
- Breakdown:
  - Stage 1 (Ingestion): ~1s
  - Stage 2 (Forecast): ~1s
  - Stage 3 (Optimize): ~3-5s
  - Stage 4 (Finance): ~1s
  - Stage 5 (Decision): <1s
  - Stage 6 (Realism): ~1s

---

## Testing

### Valid Request
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"state": "maharashtra", "battery_kwh": 250, "battery_power_kw": 75}'
# Expected: 200 OK with AnalysisResponse
```

### Invalid State
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"state": "invalid", "battery_kwh": 250, "battery_power_kw": 75}'
# Expected: 422 Unprocessable Entity
```

### Battery Too Large
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"state": "maharashtra", "battery_kwh": 5000, "battery_power_kw": 75}'
# Expected: 422 Validation Error
```

---

## Integration Checklist

- ✅ Backend running on `http://localhost:8000`
- ✅ Frontend can reach `/api/v1/analyze`
- ✅ Request validation working
- ✅ Pipeline executes all 6 stages
- ✅ Response contains all required fields
- ✅ Realism gap calculated correctly
- ✅ Charts have data
- ✅ Insights generated
- ✅ Recommendation logic working

---

**API Version:** v1  
**Stability:** Stable  
**Last Updated:** April 2026
